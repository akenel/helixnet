#!/usr/bin/env python3
"""Banco offsite backup pull — the 3-2-1 rule's "1 offsite" copy (P5).

The box already makes GPG-encrypted, restore-verified nightly dumps — but they all
live on ONE disk. If that disk dies, every backup dies with it. This pulls the
encrypted blobs OFF the box to a second physical location and PROVES each pulled
file is bit-identical to the source (end-to-end sha256), so the offsite copy is
trustworthy, not just present.

The blobs are AES256-encrypted at rest, so they are opaque ciphertext in transit
and on disk here — safe to hold off-box. They are ONLY recoverable with the backup
key (/root/.banco-backup-key on the box), which Angel must ALSO keep off-box (in
KeePass). Ciphertext offsite + key in KeePass = a real disaster-recovery pair.

Python-first per CLAUDE.md rule #11. Stdlib only (argparse + subprocess) so it runs
from a bare cron with no venv. Transport is scp (present everywhere; no rsync/sudo
needed) — blobs are immutable and timestamp-named, so a matching-size local file is
a safe skip, and every kept blob is sha256-checked against the box regardless. Exits
non-zero on any failure for alerting parity with the box's own backup/smoke jobs.

Usage:
    python3 banco_offsite_pull.py                 # pull with defaults
    python3 banco_offsite_pull.py --dest DIR --retention-days 90 --verify 3
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BOX = "root@46.62.138.218"
REMOTE_DIR = "/opt/backups/banco"
PATTERN = "banco_prod_*.sql.gz.gpg"
DEFAULT_DEST = Path.home() / "backups" / "banco-offsite"


def _log(dest: Path, msg: str) -> None:
    line = f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S UTC}] {msg}"
    print(line)
    try:
        with (dest / "offsite-pull.log").open("a") as fh:
            fh.write(line + "\n")
    except OSError:
        pass  # logging must never sink the run


def _die(dest: Path, msg: str, code: int = 1) -> "None":
    _log(dest, f"FAILED: {msg}")
    try:
        (dest / "STATUS.txt").write_text(f"FAIL {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} — {msg}\n")
    except OSError:
        pass
    sys.exit(code)


def _ssh(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", BOX, *args],
        capture_output=True, text=True, timeout=timeout,
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Pull Banco encrypted backups offsite + verify.")
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST, help=f"local offsite dir (default {DEFAULT_DEST})")
    ap.add_argument("--retention-days", type=int, default=90, help="keep local blobs this many days (default 90; box keeps 30)")
    ap.add_argument("--verify", type=int, default=3, help="sha256-verify the N newest blobs against the box (default 3; 0=skip)")
    args = ap.parse_args()

    dest: Path = args.dest
    dest.mkdir(parents=True, exist_ok=True)

    if not shutil.which("scp"):
        _die(dest, "scp not installed on this machine (openssh-client)")

    # 0. reachability + the box's blob manifest (name + size)
    probe = _ssh(f"stat -c '%n %s' {REMOTE_DIR}/{PATTERN} 2>/dev/null")
    if probe.returncode != 0 or not probe.stdout.strip():
        _die(dest, f"box unreachable or ZERO backups: {probe.stderr.strip() or 'ssh failed'}")
    manifest: dict[str, int] = {}
    for row in probe.stdout.splitlines():
        path, _, size = row.rpartition(" ")
        manifest[Path(path).name] = int(size)
    remote_count = len(manifest)
    _log(dest, f"box holds {remote_count} encrypted backup(s); syncing to {dest}")

    # 1. scp only the blobs we don't already hold at the right size (immutable files)
    t0 = time.monotonic()
    fetched = 0
    for name, size in manifest.items():
        lp = dest / name
        if lp.exists() and lp.stat().st_size == size:
            continue  # already have this exact blob
        cp = subprocess.run(
            ["scp", "-q", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes",
             f"{BOX}:{REMOTE_DIR}/{name}", str(lp)],
            capture_output=True, text=True, timeout=300,
        )
        if cp.returncode != 0:
            _die(dest, f"scp {name} failed: {cp.stderr.strip()[:200]}")
        fetched += 1
    _log(dest, f"fetched {fetched} new blob(s) in {time.monotonic() - t0:.1f}s ({remote_count - fetched} already present)")

    local = sorted(dest.glob(PATTERN))
    if len(local) < remote_count:
        _die(dest, f"local has {len(local)} blobs but box has {remote_count} — pull incomplete")

    # 2. PROVE integrity: sha256 the N newest local blobs == the box's own sha256
    if args.verify > 0:
        newest = sorted(local, key=lambda p: p.stat().st_mtime, reverse=True)[: args.verify]
        for p in newest:
            r = _ssh(f"sha256sum {REMOTE_DIR}/{p.name}")
            if r.returncode != 0:
                _die(dest, f"could not sha256 {p.name} on box")
            box_hash = r.stdout.split()[0]
            loc_hash = _sha256(p)
            if box_hash != loc_hash:
                _die(dest, f"CHECKSUM MISMATCH {p.name}: box={box_hash[:16]} local={loc_hash[:16]}")
            _log(dest, f"verified bit-identical: {p.name} ({box_hash[:16]}…)")

    # 3. retention: keep N days locally (longer than the box — offsite outlives primary)
    cutoff = time.time() - args.retention_days * 86400
    pruned = 0
    for p in local:
        if p.stat().st_mtime < cutoff:
            p.unlink()
            pruned += 1
    kept = len(list(dest.glob(PATTERN)))

    newest_name = sorted(dest.glob(PATTERN))[-1].name if kept else "none"
    total_mb = sum(p.stat().st_size for p in dest.glob(PATTERN)) / 1e6
    _log(dest, f"OK: {kept} blobs offsite ({total_mb:.1f} MB), newest={newest_name}, pruned={pruned}")
    (dest / "STATUS.txt").write_text(
        f"OK {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} — {kept} blobs ({total_mb:.1f} MB), "
        f"newest={newest_name}, verified={min(args.verify, kept)}\n"
    )


if __name__ == "__main__":
    main()
