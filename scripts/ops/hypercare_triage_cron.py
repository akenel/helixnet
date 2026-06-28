#!/usr/bin/env python3
"""Hypercare cadence cron — triage pending feedback at the configured cadence, per env.

Cron fires this often (e.g. every minute); the SCRIPT decides whether it's actually due,
based on a per-env **cadence setting** file. That's Angel's one knob:

    /opt/hypercare/<env>.cadence  contains one of:  hypercare | high | medium | low | off
        hypercare = every  1 min   (live war-room — feedback gets cleaned almost instantly)
        high      = every 15 min
        medium    = every 60 min
        low       = once a day
        off       = paused
    (cron must fire at least as often as the tightest tier — set the crontab to * * * * *.)

It gets a token off the KC docker network, POSTs /pos/feedback/triage (the in-app brain),
logs the count, and stamps last-run. Idempotent end-to-end (the endpoint skips already-triaged).

CREDENTIALS (v2 — never hard-coded). Resolved in order, NO default password ever:
    1. env  HYPERCARE_SVC_USER / HYPERCARE_SVC_PASS
    2. file /opt/hypercare/<env>.creds   (mode 600; line 1 = user, line 2 = password)
    3. none → FAIL LOUD (record the failure, exit 1).

FAILURE VISIBILITY (v2). The box cron must never crash-loop, but a failure must never be
silent either. Every run that actually fires stamps /opt/hypercare/<env>.status with OK/FAIL,
and any failure also appends to /opt/hypercare/<env>.FAILURES — the pull-based alerting
surface (same pattern as the nightly backup + smoke). A "not due" tick is a no-op (no stamp).

Usage (installed on the box, called by cron):
    python3 hypercare_triage_cron.py <BASE_URL> <REALM> <ENV> [--force]
e.g. python3 hypercare_triage_cron.py https://sandbox-banco.lapiazza.app borrowhood sandbox
"""
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request as u

CADENCE_MIN = {"hypercare": 1, "high": 15, "medium": 60, "low": 1440, "off": None}
STATE = pathlib.Path("/opt/hypercare")

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://sandbox-banco.lapiazza.app"
REALM = sys.argv[2] if len(sys.argv) > 2 else "borrowhood"
ENV = sys.argv[3] if len(sys.argv) > 3 else "sandbox"
FORCE = "--force" in sys.argv
CLIENT_ID = os.getenv("HYPERCARE_CLIENT_ID", "helix_pos_web")


def _read(name: str, default: str = "") -> str:
    try:
        return (STATE / name).read_text().strip()
    except Exception:
        return default


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def stamp(ok: bool, detail: str) -> None:
    """Record OK/FAIL for this env; failures also append to the pull-able FAILURES surface."""
    try:
        (STATE / f"{ENV}.status").write_text(f"{'OK' if ok else 'FAIL'} {_now()} {detail}\n")
        if not ok:
            with (STATE / f"{ENV}.FAILURES").open("a") as fh:
                fh.write(f"{_now()} env={ENV} {detail}\n")
    except Exception as e:  # noqa: BLE001 — never let the alerting write crash the cron
        print(f"[{_now()}] env={ENV} WARN could not write status/FAILURES: {e}")


def fail(stage: str, err) -> "NoReturn":  # type: ignore[name-defined]
    detail = f"{stage}: {err}".strip()
    print(f"[{_now()}] env={ENV} ERROR {detail}")
    stamp(False, detail)
    sys.exit(1)


def creds() -> tuple[str | None, str | None]:
    user = os.getenv("HYPERCARE_SVC_USER")
    pw = os.getenv("HYPERCARE_SVC_PASS")
    if user and pw:
        return user, pw
    raw = _read(f"{ENV}.creds")
    if raw:
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if len(lines) >= 2:
            return lines[0], lines[1]
        if ":" in raw:  # single-line user:password fallback
            u_, _, p_ = raw.partition(":")
            return u_.strip(), p_.strip()
    return None, None


def cadence() -> str:
    return _read(f"{ENV}.cadence", "hypercare").lower()


def due(mins: int | None) -> bool:
    if mins is None:
        return False
    try:
        last = float(_read(f"{ENV}.last_run", "0"))
    except Exception:
        last = 0.0
    return (time.time() - last) >= (mins * 60 - 30)  # 30s slack so a 15m tier fires on a 15m cron


def token(user: str, pw: str) -> str:
    out = subprocess.check_output([
        "docker", "run", "--rm", "--network", "hetzner_helixnet", "curlimages/curl:latest",
        "-s", "-X", "POST",
        f"http://keycloak:8080/realms/{REALM}/protocol/openid-connect/token",
        "-d", f"client_id={CLIENT_ID}", "-d", f"username={user}",
        "-d", f"password={pw}", "-d", "grant_type=password"], timeout=30)
    data = json.loads(out)
    if "access_token" not in data:
        # surface KC's reason (e.g. invalid_grant) without leaking the password
        raise RuntimeError(data.get("error_description") or data.get("error") or "no access_token")
    return data["access_token"]


def main() -> None:
    mins = CADENCE_MIN.get(cadence(), 15)
    if not FORCE and not due(mins):
        return  # not time yet, or off — leave prior status untouched

    user, pw = creds()
    if not user or not pw:
        fail("creds", f"no credentials — set HYPERCARE_SVC_USER/PASS or /opt/hypercare/{ENV}.creds")

    try:
        tok = token(user, pw)
    except Exception as e:  # noqa: BLE001
        fail("token", f"{type(e).__name__}: {e}")

    try:
        req = u.Request(f"{BASE}/api/v1/pos/feedback/triage?limit=15", method="POST",
                        headers={"Authorization": "Bearer " + tok})
        with u.urlopen(req, timeout=180) as r:
            res = json.loads(r.read())
    except Exception as e:  # noqa: BLE001
        fail("triage", f"{type(e).__name__}: {e}")

    (STATE / f"{ENV}.last_run").write_text(str(time.time()))
    n = res.get("triaged")
    titles = [i.get("clean_title") for i in res.get("items", [])][:5]
    print(f"[{_now()}] env={ENV} cadence={cadence()} triaged={n} titles={titles}")
    stamp(True, f"triaged={n}")


if __name__ == "__main__":
    main()
