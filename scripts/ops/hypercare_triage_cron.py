#!/usr/bin/env python3
"""Hypercare cadence cron — triage pending feedback at the configured cadence, per env.

Cron fires this often (e.g. every 5 min); the SCRIPT decides whether it's actually due, based
on a per-env **cadence setting** file. That's Angel's one knob:

    /opt/hypercare/<env>.cadence  contains one of:  hypercare | high | medium | low | off
        hypercare = every 15 min   (war-room)
        high      = every 30 min
        medium    = every 60 min
        low       = once a day
        off       = paused

It gets a felix token off the KC docker network, POSTs /pos/feedback/triage (the in-app brain),
logs the count, and stamps last-run. Idempotent end-to-end (the endpoint skips already-triaged).

Usage (installed on the box, called by cron):
    python3 hypercare_triage_cron.py <BASE_URL> <REALM> <ENV> [--force]
e.g. python3 hypercare_triage_cron.py https://sandbox-banco.lapiazza.app borrowhood sandbox
"""
import json
import pathlib
import subprocess
import sys
import time
import urllib.request as u

CADENCE_MIN = {"hypercare": 15, "high": 30, "medium": 60, "low": 1440, "off": None}
STATE = pathlib.Path("/opt/hypercare")

BASE = sys.argv[1] if len(sys.argv) > 1 else "https://sandbox-banco.lapiazza.app"
REALM = sys.argv[2] if len(sys.argv) > 2 else "borrowhood"
ENV = sys.argv[3] if len(sys.argv) > 3 else "sandbox"
FORCE = "--force" in sys.argv


def _read(name, default):
    try:
        return (STATE / name).read_text().strip()
    except Exception:
        return default


def cadence():
    return _read(f"{ENV}.cadence", "hypercare").lower()


def due(mins):
    if mins is None:
        return False
    try:
        last = float(_read(f"{ENV}.last_run", "0"))
    except Exception:
        last = 0.0
    return (time.time() - last) >= (mins * 60 - 30)   # 30s slack so a 15m tier fires on a 15m cron


def token():
    out = subprocess.check_output([
        "docker", "run", "--rm", "--network", "hetzner_helixnet", "curlimages/curl:latest",
        "-s", "-X", "POST",
        f"http://keycloak:8080/realms/{REALM}/protocol/openid-connect/token",
        "-d", "client_id=helix_pos_web", "-d", "username=felix",
        "-d", "password=helix_pass", "-d", "grant_type=password"], timeout=30)
    return json.loads(out)["access_token"]


def main():
    cad = cadence()
    mins = CADENCE_MIN.get(cad, 15)
    if not FORCE and not due(mins):
        return  # not time yet, or off
    try:
        tok = token()
        req = u.Request(f"{BASE}/api/v1/pos/feedback/triage?limit=15", method="POST",
                        headers={"Authorization": "Bearer " + tok})
        with u.urlopen(req, timeout=180) as r:
            res = json.loads(r.read())
        (STATE / f"{ENV}.last_run").write_text(str(time.time()))
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{stamp}] env={ENV} cadence={cad} triaged={res.get('triaged')} "
              f"titles={[i.get('clean_title') for i in res.get('items', [])][:5]}")
    except Exception as e:  # noqa: BLE001 — a cron must never crash-loop; log + move on
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] env={ENV} ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
