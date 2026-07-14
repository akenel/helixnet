#!/usr/bin/env python3
"""app-gate — prove the APP actually came back after a deploy, and that it is
serving the code we just shipped.

WHY THIS EXISTS (2026-07-14):
The login gate (kc-login-audit.js) proves KEYCLOAK's login page is readable. But a
deploy restarts the APP container, and Keycloak is not restarted at all — so the login
gate would happily pass while the app itself came back broken. Two green lights, one
blind spot.

And "container: healthy" is not proof either. Per the deploy SOP: the healthcheck greens
a BEAT BEFORE the first request actually serves, so a snapshot taken too early can show
the OLD process answering and masquerade as the new one. PROVE, DON'T ASSUME — re-probe
from the outside, over the real public URL, and keep probing until it answers.

What it proves, in order:
  1. /health/healthz returns 200          (the exact path the container healthcheck uses)
  2. /pos returns 200                     (the till — the page a cashier actually opens)
  3. the build stamp the app RENDERS matches the SHA we just deployed
     ^ this is the one that catches a restart that silently kept the old code:
       build_info caches the stamp per process, so a stale process serves a stale SHA.

Usage:
    python3 scripts/ops/app-gate.py <sandbox|staging|prod> [--expect-sha 08af5a2]

Exit 0 only when every check passes. Stdlib only — runs on the laptop or the box.
"""
import argparse
import re
import sys
import time
import urllib.error
import urllib.request

HOSTS = {
    "sandbox": "sandbox-banco.lapiazza.app",
    "staging": "staging-banco.lapiazza.app",
    "prod":    "banco.lapiazza.app",
}

# The container healthcheck probes /health/healthz — NOT /health (that 404s).
# Probe exactly what the container probes, or you are testing a different thing.
HEALTH = "/health/healthz"
TILL = "/pos"

TIMEOUT = 10
RETRIES = 10
BACKOFF = 3


def get(url):
    """Return (status, body). Never raises for HTTP errors — a 404 is data, not a crash."""
    req = urllib.request.Request(url, headers={"User-Agent": "banco-app-gate"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:  # connection refused / TLS / DNS — mid-restart is normal
        return 0, str(e)


def probe(name, url, want=200):
    """Retry past the restart window: the healthcheck greens before the app serves."""
    for attempt in range(1, RETRIES + 1):
        status, body = get(url)
        if status == want:
            print(f"  ✅ {name:<24} {status}  {url}")
            return body
        print(f"  .. {name:<24} {status or 'no answer'} (attempt {attempt}/{RETRIES})")
        if attempt < RETRIES:
            time.sleep(BACKOFF)
    print(f"  ❌ {name:<24} never returned {want}  {url}")
    return None


def main():
    ap = argparse.ArgumentParser(description="prove the app is serving the code we deployed")
    ap.add_argument("env", choices=sorted(HOSTS))
    ap.add_argument("--expect-sha", help="short SHA the app must be SERVING (not just checked out)")
    args = ap.parse_args()

    base = f"https://{HOSTS[args.env]}"
    print(f"🚦 APP GATE — {args.env} ({base})")

    ok = True
    if probe("health/healthz", base + HEALTH) is None:
        ok = False

    till = probe("till /pos", base + TILL)
    if till is None:
        ok = False

    # The stamp check is the whole point: a restart that quietly kept the old process
    # still passes health + 200. Only the RENDERED sha proves the new code is live.
    if args.expect_sha:
        if till is None:
            print(f"  ❌ build stamp             cannot check — /pos never served")
            ok = False
        else:
            sha = args.expect_sha.strip()
            # build_info renders like "b1768 · 08af5a2 · 1"
            served = re.findall(r"b\d{3,5}\s*[·.\-]\s*([0-9a-f]{7,40})", till)
            if sha in till or any(s.startswith(sha) or sha.startswith(s) for s in served):
                shown = served[0] if served else sha
                print(f"  ✅ {'build stamp':<24} serving {shown} (expected {sha})")
            else:
                print(f"  ❌ {'build stamp':<24} expected {sha}, but the app is serving "
                      f"{served or 'NO STAMP FOUND'}")
                print(f"     -> the restart did not pick up the new code (stale process?)")
                ok = False

    print("✅ APP GATE PASS" if ok else "❌ APP GATE FAIL — do NOT call this deployed")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
