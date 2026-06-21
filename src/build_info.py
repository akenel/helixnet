"""Build stamp for the status bar -- the version + the git SHA actually deployed.

The container only mounts `src/` (not `.git`), and the staging/prod deploy is a
`git checkout <files> + docker restart` (no rebuild), so we can't rely on running
git inside the container or on an env var (restart keeps the old env). The robust
source is a deploy-written stamp file under the mounted `src/` tree, with sensible
fallbacks. Resolved order:

  1. HELIX_GIT_SHA env var        (if a deploy chooses to inject it)
  2. src/static/build-sha.txt     (written by the deploy into the mounted tree)
  3. live `git rev-parse`         (works in local dev where .git is present)
  4. "dev"                        (last resort -- never crashes the status bar)

Computed once and cached so it costs nothing per request.
"""
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from src import __version__

_SRC_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SRC_DIR.parent
_STAMP = _SRC_DIR / "static" / "build-sha.txt"


def get_version() -> str:
    return __version__


@lru_cache(maxsize=1)
def get_git_sha() -> str:
    sha = (os.environ.get("HELIX_GIT_SHA") or "").strip()
    if sha:
        return sha[:7]
    try:
        if _STAMP.exists():
            stamped = _STAMP.read_text().strip()
            if stamped:
                return stamped[:7]
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(_REPO_ROOT), text=True, stderr=subprocess.DEVNULL,
        ).strip()
        return out or "dev"
    except Exception:
        return "dev"
