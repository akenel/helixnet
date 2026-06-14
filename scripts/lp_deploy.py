#!/usr/bin/env python3
"""lp_deploy.py -- the deploy SOP as one command that can't skip a step.

The Deploy SOP currently lives in memory (commit -> deploy -> smoke -> read the
output). A checklist in someone's head is a swallowed exception: it works until
the one tired night it doesn't, and then it fails silent and wide (that's how
BUG-015 shipped). This turns the checklist into an executable that *cannot* skip
the smoke gate and *cannot* clobber box-local edits, and that rolls itself back
when verify goes red.

THIN SLICE (2026-06-14): staging target ONLY. `prod` is intentionally refused
until the full Rung-1 build -- see docs/ops/LP-DEPLOY-DESIGN.md. The full design
adds: prod target with extra guards, exercised-rollback proof, drift
reconciliation, and `lp` as a proper multi-verb CLI.

Failure-mode-first -- every step that can break refuses loudly or reverses:
  preflight  refuse if any NAMED file carries uncommitted edits on the box
             (checkout would destroy a possible prod hotfix -- the #140 trap)
  record     capture the current staging image id == the rollback point
  deploy     materialize the named files from origin/main (the proven safe
             single-file pattern, NOT a blind `git pull`) + rebuild ONLY the
             staging container (--no-deps)
  verify     run smoke-test.sh against staging (pushed fresh from THIS repo, so
             box drift on the smoke script itself can't give a false green)
  rollback   on red verify or any build error: retag the recorded image + restore
             the named files to box HEAD, then re-smoke to confirm recovery

Usage:
  # read-only: drift + health report (safe, run anytime, no files):
  python scripts/lp_deploy.py staging

  # see the exact plan + rollback commands without touching anything:
  python scripts/lp_deploy.py staging src/routers/locandina.py --dry-run

  # real deploy of one or more files (confirms unless --yes):
  python scripts/lp_deploy.py staging src/routers/locandina.py src/templates/locandina/card.html
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

import typer

# --- box / stack facts (verified against 46.62.138.218 on 2026-06-14) ---------
BOX = "root@46.62.138.218"
HELIX_DIR = "/opt/helixnet"
COMPOSE_DIR = f"{HELIX_DIR}/hetzner"
BH_TREE = f"{HELIX_DIR}/BorrowHood"          # the diverged tree staging builds from (#140)
STAGING_SVC = "borrowhood_staging"
STAGING_IMG = "borrowhood:staging"
COMPOSE = ("docker compose -f docker-compose.uat.yml "
           "-f docker-compose.staging.yml --env-file uat.env")
LOCAL_SMOKE = Path(__file__).resolve().parent / "smoke-test.sh"
REMOTE_SMOKE = "/tmp/lp-smoke.sh"

app = typer.Typer(add_completion=False, help=__doc__)


# --- shell helpers ------------------------------------------------------------
def _run(argv: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(argv, text=True, capture_output=True, check=check)


def box(remote_cmd: str, check: bool = True) -> str:
    """Run one command on the box. remote_cmd is passed as a single ssh argv
    element -- no local shell re-parses it (avoids the multi-shell quoting trap)."""
    cp = _run(["ssh", "-o", "ConnectTimeout=15", BOX, remote_cmd], check=check)
    return cp.stdout.strip()


def info(msg: str) -> None: typer.secho(msg, fg=typer.colors.CYAN)
def ok(msg: str) -> None: typer.secho(f"OK   {msg}", fg=typer.colors.GREEN)
def warn(msg: str) -> None: typer.secho(f"WARN {msg}", fg=typer.colors.YELLOW)
def die(msg: str) -> None:
    typer.secho(f"REFUSE {msg}", fg=typer.colors.RED, bold=True)
    raise typer.Exit(code=1)


# --- box state probes (read-only) ---------------------------------------------
def box_drift() -> tuple[int, int]:
    out = box(f"cd {BH_TREE} && git fetch -q origin 2>/dev/null; "
              f"echo $(git rev-list --count HEAD..origin/main); "
              f"git status --porcelain | wc -l")
    behind, dirty = (out.split() + ["?", "?"])[:2]
    return int(behind), int(dirty)


def staging_image_id() -> str:
    return box(f"docker inspect --format '{{{{.Image}}}}' {STAGING_SVC}")


def named_files_dirty(files: list[str]) -> list[str]:
    """Which of the named files carry uncommitted edits on the box."""
    listing = box(f"cd {BH_TREE} && git status --porcelain -- {' '.join(files)}")
    return [ln[3:] for ln in listing.splitlines() if ln.strip()]


def named_files_changed_vs_box(files: list[str]) -> list[str]:
    """Which named files actually differ between box HEAD and origin/main."""
    out = box(f"cd {BH_TREE} && git fetch -q origin 2>/dev/null; "
              f"git diff --name-only HEAD origin/main -- {' '.join(files)}")
    return [ln for ln in out.splitlines() if ln.strip()]


# --- mutating steps -----------------------------------------------------------
def materialize(files: list[str]) -> None:
    box(f"cd {BH_TREE} && git fetch -q origin && git checkout origin/main -- {' '.join(files)}")


def restore(files: list[str]) -> None:
    box(f"cd {BH_TREE} && git checkout HEAD -- {' '.join(files)}", check=False)


def rebuild_staging() -> None:
    box(f"cd {COMPOSE_DIR} && {COMPOSE} up -d --build --no-deps {STAGING_SVC}")


def retag_and_restart(old_image_id: str) -> None:
    box(f"docker tag {old_image_id} {STAGING_IMG} && "
        f"cd {COMPOSE_DIR} && {COMPOSE} up -d --no-deps --no-build {STAGING_SVC}", check=False)


def run_smoke() -> tuple[bool, str]:
    """Push THIS repo's smoke script to the box and run it against staging."""
    _run(["scp", "-o", "ConnectTimeout=15", str(LOCAL_SMOKE), f"{BOX}:{REMOTE_SMOKE}"])
    cp = _run(["ssh", "-o", "ConnectTimeout=30", BOX,
               f"cd {HELIX_DIR} && bash {REMOTE_SMOKE} staging"], check=False)
    tail = "\n".join((cp.stdout + cp.stderr).strip().splitlines()[-12:])
    return cp.returncode == 0, tail


# --- the command --------------------------------------------------------------
@app.command()
def staging(
    files: Optional[list[str]] = typer.Argument(
        None,
        help="BorrowHood-relative path(s) to materialize from origin/main. "
             "Omit for a read-only drift + health report."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show the plan; touch nothing."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the confirm prompt."),
):
    """Deploy named files to the STAGING marketplace (borrowhood_staging), or --
    with no --files -- just report drift and run the health check."""
    files = files or []

    # 1. preflight ------------------------------------------------------------
    info("== preflight ==")
    behind, dirty = box_drift()
    (warn if (behind or dirty) else ok)(
        f"box BorrowHood tree: {behind} behind origin/main, {dirty} uncommitted "
        f"(#140 -- staging builds from this tree by design)")

    if files:
        clobber = named_files_dirty(files)
        if clobber:
            die("these named files have uncommitted edits ON THE BOX -- a checkout "
                f"would destroy them (possible prod hotfix, see #140): {clobber}")
        changed = named_files_changed_vs_box(files)
        ok(f"named files clean on box; {len(changed)} differ vs origin/main: "
           f"{changed or '(none -- nothing to deploy)'}")

    # 2. record the rollback point -------------------------------------------
    old_img = staging_image_id()
    info(f"== rollback point: {STAGING_IMG} == {old_img[:19]} ==")

    # no files -> this is a read-only status + health run
    if not files:
        info("== health (no --files: read-only report) ==")
        good, tail = run_smoke()
        typer.echo(tail)
        (ok if good else warn)("smoke staging: " + ("GREEN" if good else "RED"))
        raise typer.Exit(code=0 if good else 1)

    # 3. dry run --------------------------------------------------------------
    if dry_run:
        info("== plan (dry-run -- nothing executed) ==")
        typer.echo(f"  1. ssh box: git checkout origin/main -- {' '.join(files)}")
        typer.echo(f"  2. ssh box: {COMPOSE} up -d --build --no-deps {STAGING_SVC}")
        typer.echo(f"  3. scp smoke-test.sh -> box; bash {REMOTE_SMOKE} staging")
        typer.echo(f"  4a. GREEN -> done")
        typer.echo(f"  4b. RED   -> rollback: docker tag {old_img[:19]} {STAGING_IMG}; "
                   f"up -d --no-build; git checkout HEAD -- {' '.join(files)}; re-smoke")
        raise typer.Exit(code=0)

    if not yes:
        typer.confirm(f"Deploy {len(files)} file(s) to STAGING and rebuild "
                      f"{STAGING_SVC}?", abort=True)

    # 4. deploy + verify, rollback on any failure -----------------------------
    try:
        info("== materialize from origin/main ==")
        materialize(files)
        info("== rebuild staging container ==")
        rebuild_staging()
        info("== verify (smoke staging) ==")
        good, tail = run_smoke()
        typer.echo(tail)
        if good:
            ok("smoke GREEN -- staging deploy complete")
            raise typer.Exit(code=0)
        warn("smoke RED -- rolling back")
    except typer.Exit:
        raise
    except Exception as e:  # build/ssh failure -> roll back too
        warn(f"deploy step failed ({e}) -- rolling back")

    # 5. rollback -------------------------------------------------------------
    info("== rollback ==")
    retag_and_restart(old_img)
    restore(files)
    good, tail = run_smoke()
    typer.echo(tail)
    (ok if good else die)("post-rollback smoke: " + ("GREEN (recovered)" if good
                          else "STILL RED -- staging needs hands"))
    raise typer.Exit(code=1)


@app.command()
def prod():
    """Intentionally not in the thin slice."""
    die("prod deploy is not in the thin slice. See docs/ops/LP-DEPLOY-DESIGN.md "
        "for the full Rung-1 build (extra guards + exercised rollback) before "
        "this command is wired.")


if __name__ == "__main__":
    app()
