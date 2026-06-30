#!/usr/bin/env python3
"""set-banco-secret — graceful, safe secret setter for the shared banco env (uat.env).

Replaces the brittle bash rotation for the banco stack. All three banco envs
(sandbox / staging / prod) share /opt/helixnet/hetzner/uat.env, so ONE write +
a recreate of each container sets the same secret everywhere at once.

What it does, in order (each step prints, nothing secret is ever echoed):
  1. Hidden prompt for the new value (getpass — paste from KeePass).
  2. VALIDATE it before touching anything (for BH_GOOGLE_API_KEY: a live Gemini
     models-list call). A bad key ABORTS — so we never ship a dead one again.
  3. Timestamped backup of uat.env, then upsert KEY=value in place.
  4. Recreate the chosen container(s) so they actually load the new value
     (a plain `restart` does NOT re-read env_file — that's why the old key was
     stuck). Recreate makes a fresh container, so we also re-ensure Pillow
     (the image doesn't bake it yet — see --no-pillow / the requirements TODO).
  5. Health-check each container + a vision smoke test (confirm the AI answers).

Run ON THE BOX:
    python3 /opt/ops/set-banco-secret.py            # BH_GOOGLE_API_KEY -> all 3 envs
    python3 /opt/ops/set-banco-secret.py --env sandbox
    python3 /opt/ops/set-banco-secret.py --key SOME_OTHER_SECRET --no-validate
    python3 /opt/ops/set-banco-secret.py --dry-run  # show the plan, change nothing
"""
import argparse
import datetime
import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error

HETZNER = "/opt/helixnet/hetzner"
ENV_FILE = f"{HETZNER}/uat.env"
COMPOSE = [
    "docker-compose.uat.yml", "docker-compose.helix-staging.yml",
    "docker-compose.banco-prod.yml", "docker-compose.banco-sandbox.yml",
    "docker-compose.banco-staging.yml",
]
# env name -> (compose service, container name)
ENVS = {
    "sandbox": ("helix-platform-sandbox", "helix-platform-sandbox"),
    "staging": ("helix-platform-banco-staging", "helix-platform-banco-staging"),
    "prod":    ("helix-platform-banco", "helix-platform-banco"),
}
C = {"g": "\033[0;32m", "y": "\033[1;33m", "r": "\033[0;31m", "b": "\033[0;34m", "n": "\033[0m"}


def say(c, m): print(f"{C[c]}{m}{C['n']}")


def sh(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, **kw)


def validate_gemini(key: str) -> bool:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.status == 200
    except urllib.error.HTTPError as e:
        say("r", f"  Gemini rejected the key: HTTP {e.code} — {e.read()[:120].decode(errors='replace')}")
        return False
    except Exception as e:
        say("r", f"  Could not reach Gemini to validate: {e}")
        return False


def upsert(path: str, key: str, value: str):
    lines = open(path).read().splitlines()
    out, found = [], False
    for ln in lines:
        if ln.startswith(f"{key}=") or ln.startswith(f"{key} ="):
            out.append(f"{key}={value}"); found = True
        else:
            out.append(ln)
    if not found:
        out.append(f"{key}={value}")
    open(path, "w").write("\n".join(out) + "\n")
    return found


def ensure_pillow(container: str):
    chk = sh(["docker", "exec", container, "/app/venv/bin/python", "-c", "import PIL"])
    if chk.returncode == 0:
        say("g", f"  [{container}] Pillow present ✓")
        return
    say("y", f"  [{container}] installing Pillow (image doesn't bake it yet)…")
    sh(["docker", "exec", container, "/app/venv/bin/pip", "install", "--no-cache-dir", "Pillow"])


def smoke_vision(container: str):
    code = ('import asyncio,io;from PIL import Image;from src.services.vision import analyze_image,PRODUCT;'
            'buf=io.BytesIO();Image.new("RGB",(96,96),(20,90,30)).save(buf,"JPEG");'
            'r=asyncio.run(analyze_image(buf.getvalue(),"image/jpeg",domain=PRODUCT,hint="a green tube"));'
            'print("provider="+r["provider"]+" model="+(r["model"] or "-")+" note="+str(r.get("note")))')
    out = sh(["docker", "exec", container, "/app/venv/bin/python", "-c", code])
    line = (out.stdout + out.stderr).strip().splitlines()[-1] if (out.stdout or out.stderr) else "(no output)"
    ok = "note=None" in (out.stdout + out.stderr) or ("provider=gemini" in out.stdout and "unavailable" not in out.stdout)
    say("g" if ok else "y", f"  [{container}] vision smoke: {line}")
    return ok


# ── --doctor: are the DEPLOYED keys actually alive? (values never printed) ──────
def _http(url, headers=None, timeout=15):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()


def _chk_gemini(v):
    c, _ = _http(f"https://generativelanguage.googleapis.com/v1beta/models?key={v}")
    return (c == 200, f"Gemini HTTP {c}")


def _chk_telegram(v):
    c, b = _http(f"https://api.telegram.org/bot{v}/getMe")
    if c == 200:
        try:
            return True, "Telegram @" + json.loads(b)["result"]["username"]
        except Exception:
            return True, "Telegram ok"
    return False, f"Telegram HTTP {c}"


def _chk_resend(v):
    c, _ = _http("https://api.resend.com/api-keys", {"Authorization": f"Bearer {v}"})
    return (c == 200, f"Resend HTTP {c}")


def _chk_ollama(v):
    c, _ = _http("https://ollama.com/v1/models", {"Authorization": f"Bearer {v}"})
    return (c == 200, f"Ollama HTTP {c}")


CHECKERS = {
    "BH_GOOGLE_API_KEY": _chk_gemini, "TELEGRAM_BOT_TOKEN": _chk_telegram,
    "BH_RESEND_API_KEY": _chk_resend, "BH_OLLAMA_KEY": _chk_ollama,
}
# The vault inventory (mirrors KeePass: "La Piazza - Production").
KNOWN = ["BH_GOOGLE_API_KEY", "BH_OLLAMA_KEY", "BH_RESEND_API_KEY", "TELEGRAM_BOT_TOKEN",
         "BH_KC_CLIENT_SECRET", "KC_GITHUB_CLIENT_SECRET", "KC_GOOGLE_CLIENT_SECRET",
         "BH_PAYPAL_CLIENT_SECRET", "BH_DATABASE_URL", "BH_SECRET_KEY"]


def _read_env(path):
    d = {}
    for ln in open(path):
        s = ln.strip()
        if "=" in s and not s.startswith("#"):
            k, _, v = s.partition("=")
            d[k.strip()] = v.strip().strip('"')
    return d


def _container_env(container):
    """The container's ACTUAL env (uat.env + compose overrides + everything it really sees)."""
    r = sh(["docker", "exec", container, "printenv"])
    if r.returncode != 0:
        return None
    d = {}
    for ln in r.stdout.splitlines():
        if "=" in ln:
            k, _, v = ln.partition("=")
            d[k] = v
    return d


def doctor():
    say("b", "╔════════════════════════════════════════════════════════════════════╗")
    say("b", "║  KEY DOCTOR — live health of each container's REAL env (no values)  ║")
    say("b", "╚════════════════════════════════════════════════════════════════════╝")
    order = ["sandbox", "staging", "prod"]
    envs = {n: _container_env(ENVS[n][1]) for n in order}
    for n in order:
        ok = envs[n] is not None
        say("g" if ok else "y", f"  {n:<8} {ENVS[n][1]}: {'read ✓' if ok else 'unreadable (not running?) — column shows —'}")
    print(f"\n  {'KEY':<26} {'SBX':^6}{'STG':^6}{'PRD':^6}  CHECK")
    print("  " + "-" * 62)
    cache, dead = {}, set()
    for k in KNOWN:
        cells, detail = [], ""
        for n in order:
            e = envs[n]
            if e is None:
                cells.append("—"); continue
            v = e.get(k, "")
            if not v:
                cells.append("⬜"); continue
            if k in CHECKERS:
                if v not in cache:
                    cache[v] = CHECKERS[k](v)
                ok, d = cache[v]
                cells.append("✅" if ok else "❌"); detail = d
                if not ok:
                    dead.add(k)
            else:
                cells.append("🔒")
        print(f"  {k:<26} {cells[0]:^6}{cells[1]:^6}{cells[2]:^6}  {detail}")
    print("\n  legend: ✅ live · ❌ DEAD · 🔒 set (no standalone check) · ⬜ not set · — env unreadable")
    if dead:
        say("r", f"  {len(dead)} DEAD key(s): {', '.join(sorted(dead))} → rotate with --key <NAME> --env all")
    else:
        say("g", "  All auto-checkable keys are LIVE across every env ✓")
    return len(dead)


def main():
    ap = argparse.ArgumentParser(description="Set a secret across the shared banco env, safely.")
    ap.add_argument("--key", default="BH_GOOGLE_API_KEY")
    ap.add_argument("--env", default="all", choices=["all", *ENVS])
    ap.add_argument("--no-validate", action="store_true", help="skip the live key check")
    ap.add_argument("--no-pillow", action="store_true", help="skip the Pillow re-ensure")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--doctor", action="store_true", help="check key health only — change nothing")
    ap.add_argument("--pick", action="store_true", help="choose which key to set from a numbered menu")
    a = ap.parse_args()

    if not os.path.exists(ENV_FILE):
        say("r", f"ERROR: {ENV_FILE} not found — run this ON THE BOX."); sys.exit(1)

    if a.doctor:
        sys.exit(1 if doctor() else 0)

    if a.pick:
        print("  Pick a key to set:")
        for i, k in enumerate(KNOWN, 1):
            print(f"    {i:>2}. {k}")
        sel = input("  # (empty = abort): ").strip()
        if not (sel.isdigit() and 1 <= int(sel) <= len(KNOWN)):
            say("y", "  No valid pick — aborted."); sys.exit(0)
        a.key = KNOWN[int(sel) - 1]
        say("g", f"  → selected {a.key}")

    targets = list(ENVS) if a.env == "all" else [a.env]
    say("b", "╔══════════════════════════════════════════════════════╗")
    say("b", f"║  set-banco-secret — {a.key:<32}║")
    say("b", "╚══════════════════════════════════════════════════════╝")
    print(f"  env file : {ENV_FILE} (shared by all banco envs)")
    print(f"  targets  : {', '.join(targets)}")
    print(f"  validate : {'no' if a.no_validate else 'yes'}   dry-run: {a.dry_run}\n")

    value = getpass.getpass(f"  Paste {a.key} from KeePass (hidden, empty=abort): ").strip()
    if not value:
        say("y", "  Empty — aborted, nothing changed."); sys.exit(0)

    if not a.no_validate and a.key == "BH_GOOGLE_API_KEY":
        say("b", "→ validating the key against Gemini…")
        if not validate_gemini(value):
            say("r", "  ABORT: key did not validate. Nothing was changed."); sys.exit(2)
        say("g", "  key VALID ✓")

    if a.dry_run:
        say("y", f"\n  [dry-run] would back up {ENV_FILE}, upsert {a.key}, then recreate: {targets}")
        sys.exit(0)

    ts = subprocess.check_output(["date", "+%Y%m%d-%H%M%S"]).decode().strip()
    bak = f"{ENV_FILE}.bak-{ts}"
    shutil.copy2(ENV_FILE, bak); os.chmod(bak, 0o600)
    say("g", f"→ backed up uat.env → {bak}")
    found = upsert(ENV_FILE, a.key, value)
    say("g", f"→ {a.key} {'updated' if found else 'added'} in uat.env")

    for e in targets:
        svc, cont = ENVS[e]
        say("b", f"→ recreating {e} ({cont}) to load the new value…")
        flags = []
        for f in COMPOSE:
            flags += ["-f", f]
        r = sh(["docker", "compose", *flags, "up", "-d", "--no-deps", svc], cwd=HETZNER)
        if r.returncode != 0:
            say("r", f"  recreate FAILED:\n{r.stderr[-400:]}"); continue
        sh(["docker", "exec", cont, "true"])  # settle
        if not a.no_pillow:
            ensure_pillow(cont)
        hc = sh(["docker", "inspect", "-f", "{{.State.Health.Status}}", cont]).stdout.strip()
        say("g" if hc in ("healthy", "") else "y", f"  [{cont}] health: {hc or 'no healthcheck'}")
        if a.key == "BH_GOOGLE_API_KEY":
            smoke_vision(cont)

    say("g", "\n✓ done. (Backup kept; the dead key is replaced. Snap-photo AI should answer now.)")
    say("y", "  NOTE: Pillow is re-ensured at runtime — add it to the image (requirements.txt + rebuild) to make it permanent.")


if __name__ == "__main__":
    main()
