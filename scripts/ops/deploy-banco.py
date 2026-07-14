#!/usr/bin/env python3
"""deploy-banco — the one true Banco deploy: checkout → STAMP THE REAL SHA → restart.

Fixes BL-024. The status-bar build (e.g. "3.3.0·62dfd67") was going stale because
hand-deploys (`git checkout` + `docker restart`) never wrote `src/static/build-sha.txt`
— the very file build_info.py reads to show what's running. This script writes that
stamp on EVERY deploy, so the bar (and any "what build are you on?" answer) always tells
the truth. build_info caches the value per process, so we restart to re-read it.

This is also rail #1 of the owner-driven promotion pipeline: a deploy you can trust.

Usage (on the box):
    python3 deploy-banco.py <sandbox|staging|prod> [ref]
        ref defaults to origin/main; a bare name like "feat/x" is resolved to "origin/feat/x".

Read-only on prod data — only touches the code tree + restarts the container. Take a DB
backup first for prod (this script does not — keep that gate human until the rails are proven).
"""
import subprocess
import sys
import time

ENVS = {
    "sandbox": ("/opt/helix-sandbox-tree", "helix-platform-sandbox"),
    "staging": ("/opt/helix-banco-staging-tree", "helix-platform-banco-staging"),
    "prod":    ("/opt/helix-banco-tree", "helix-platform-banco"),
}


def sh(args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ENVS:
        print("usage: deploy-banco.py <sandbox|staging|prod> [ref]")
        sys.exit(2)
    env = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 else "origin/main"
    if not ref.startswith("origin/"):
        ref = "origin/" + ref
    tree, container = ENVS[env]

    print(f"[deploy] {env}: syncing {tree} -> {ref}")
    sh(["git", "-C", tree, "fetch", "origin", "--quiet"])
    sh(["git", "-C", tree, "checkout", "--quiet", ref])
    sha = sh(["git", "-C", tree, "rev-parse", "--short", "HEAD"])
    date = sh(["git", "-C", tree, "show", "-s", "--format=%cI", "HEAD"])
    count = sh(["git", "-C", tree, "rev-list", "--count", "HEAD"])  # auto build number → bNNN

    # THE FIX: stamp the real build so the status bar never lies again. (#3 opt-B: + build number)
    stamp = f"{tree}/src/static/build-sha.txt"
    with open(stamp, "w") as f:
        f.write(f"{sha}\n{date}\n{count}\n")
    print(f"[deploy] stamped build-sha.txt = b{count} {sha}  ({date})")

    sh(["docker", "restart", container])
    # brief health wait so the caller sees green, not a mid-restart blip
    for _ in range(10):
        time.sleep(2)
        status = sh(["docker", "ps", "--filter", f"name={container}", "--format", "{{.Status}}"])
        if "healthy" in status:
            print(f"[deploy] {env}: {sha} live + healthy ✅")
            break
    else:
        print(f"[deploy] {env}: {sha} restarted — status: {status or '(unknown)'} (check it)")

    login_gate_reminder(env)


def login_gate_reminder(env):
    """A container healthcheck is NOT proof a human can log in.

    The Banco login screen shipped BLACK-ON-BLACK (username + password rendered at
    1.17:1 — invisible) while every machine check was green: the container was healthy,
    and the stylesheet returned HTTP 200. Nobody looked at the screen.

    This script runs on the box, which has no Chrome — so it CANNOT run the login gate
    itself. Rather than pretend, it says so loudly. A skipped gate reported as success
    is the same fake green that put a broken login in front of a user.
    """
    print()
    print("  ⚠️  LOGIN GATE NOT RUN — this box has no Chrome, so nothing here proved")
    print("      that a human can actually READ the login screen.")
    print("      From the laptop:")
    print(f"          make login-audit ENV={env}")
    print("      Or skip this warning entirely by deploying through the front door,")
    print("      which runs the gate for you:")
    print(f"          make deploy ENV={env}")
    print()


if __name__ == "__main__":
    main()
