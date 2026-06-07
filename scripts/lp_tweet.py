#!/usr/bin/env python3
"""lp_tweet.py — La Piazza X (Twitter) posting tool.

Parses a markdown batch file of tweets (see docs/business/marketing/twitter/tweets-batch-01.md),
validates them, and posts them to X one at a time. Dry-run by default — nothing leaves the
machine unless you pass --live.

Per CLAUDE.md rule 11 (Python first) and rule 9 (real libraries, no toy subsets):
    pip install typer pydantic tweepy

X API setup (do once):
    1. Create the account with artemisthinking@gmail.com
    2. developer.x.com -> create a Project + App. Free tier is write-only (~1.5k posts/mo) -- enough.
    3. In the App: enable OAuth 1.0a, set permissions to "Read and Write", generate:
         - API Key + Secret (a.k.a. consumer key/secret)
         - Access Token + Secret (for the account itself)
    4. Put them in a .env file (NEVER commit it):
         X_API_KEY=...
         X_API_SECRET=...
         X_ACCESS_TOKEN=...
         X_ACCESS_TOKEN_SECRET=...
    5. Test: python scripts/lp_tweet.py whoami

Usage:
    python scripts/lp_tweet.py list                       # show the queue
    python scripts/lp_tweet.py validate                   # check all tweets fit & are well-formed
    python scripts/lp_tweet.py post --next                # post the next unposted tweet (DRY RUN)
    python scripts/lp_tweet.py post --next --live         # actually post it
    python scripts/lp_tweet.py post --index 3 --live      # post a specific one
    python scripts/lp_tweet.py whoami                      # verify credentials
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:
    import typer
    from pydantic import BaseModel, field_validator
except ImportError:  # pragma: no cover
    raise SystemExit("Missing deps. Run: pip install typer pydantic tweepy")

REPO = Path(__file__).resolve().parent.parent
DEFAULT_BATCH = REPO / "docs/business/marketing/twitter/tweets-batch-01.md"
STATE_FILE = REPO / "docs/business/marketing/twitter/.post-state.json"
ENV_FILE = REPO / ".env"
TWEET_LIMIT = 280  # standard X limit; premium allows more, don't assume it

app = typer.Typer(add_completion=False, help="La Piazza X posting tool (dry-run by default).")


class Tweet(BaseModel):
    index: int
    pillar: str
    text: str

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def length(self) -> int:
        # X counts URLs as 23 chars regardless of real length (t.co wrapping).
        counted = re.sub(r"https?://\S+", "x" * 23, self.text)
        return len(counted)

    @property
    def ok(self) -> bool:
        return 0 < self.length <= TWEET_LIMIT


def load_env() -> None:
    """Minimal .env loader so we don't add python-dotenv just for four keys."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def parse_batch(path: Path) -> list[Tweet]:
    """Split a batch markdown file into Tweet objects.

    Each tweet is a block introduced by a line like:  ## --- pillar: build log
    Block ends at the next such header (or EOF). The header line itself is not posted.
    """
    if not path.exists():
        raise typer.BadParameter(f"Batch file not found: {path}")
    text = path.read_text()
    header_re = re.compile(r"^##\s*---\s*(?:pillar:\s*)?(.*)$", re.MULTILINE)
    matches = list(header_re.finditer(text))
    tweets: list[Tweet] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        tweets.append(Tweet(index=i + 1, pillar=m.group(1).strip() or "unlabeled", text=body))
    return tweets


def read_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"posted": []}  # list of indexes already posted


def write_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_client():
    """Return an authenticated tweepy client, or raise a clear error."""
    load_env()
    try:
        import tweepy
    except ImportError:
        raise typer.Exit("tweepy not installed. Run: pip install tweepy")
    keys = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        raise typer.Exit(f"Missing credentials in env/.env: {', '.join(missing)}")
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


@app.command(name="list")
def list_cmd(batch: Path = DEFAULT_BATCH):
    """Show every tweet in the queue with length and posted status."""
    tweets = parse_batch(batch)
    state = read_state()
    posted = set(state["posted"])
    for t in tweets:
        flag = "✓ posted" if t.index in posted else ("  ok   " if t.ok else " TOO LONG")
        typer.echo(f"[{t.index:>2}] {flag} {t.length:>3}/{TWEET_LIMIT}  ({t.pillar})")
        typer.echo(f"      {t.text.splitlines()[0][:80]}")
    remaining = [t for t in tweets if t.index not in posted]
    typer.echo(f"\n{len(tweets)} tweets, {len(remaining)} unposted.")


@app.command()
def validate(batch: Path = DEFAULT_BATCH):
    """Fail if any tweet is empty or over the character limit."""
    tweets = parse_batch(batch)
    bad = [t for t in tweets if not t.ok]
    for t in bad:
        typer.echo(f"[{t.index}] {t.length} chars — OVER LIMIT ({t.pillar})", err=True)
    if bad:
        raise typer.Exit(f"\n{len(bad)} tweet(s) need trimming.")
    typer.echo(f"All {len(tweets)} tweets valid (≤{TWEET_LIMIT} chars).")


@app.command()
def whoami():
    """Verify credentials by fetching the authenticated account."""
    client = get_client()
    me = client.get_me()
    typer.echo(f"Authenticated as @{me.data.username} ({me.data.name})")


@app.command()
def post(
    batch: Path = DEFAULT_BATCH,
    index: int = typer.Option(None, help="Post this specific tweet number."),
    next_: bool = typer.Option(False, "--next", help="Post the next unposted tweet."),
    live: bool = typer.Option(False, "--live", help="Actually post. Without this, dry-run only."),
):
    """Post one tweet. DRY RUN unless --live is passed."""
    tweets = parse_batch(batch)
    state = read_state()
    posted = set(state["posted"])

    if next_:
        candidates = [t for t in tweets if t.index not in posted]
        if not candidates:
            raise typer.Exit("Nothing left to post — whole batch is done.")
        target = candidates[0]
    elif index is not None:
        target = next((t for t in tweets if t.index == index), None)
        if target is None:
            raise typer.Exit(f"No tweet with index {index}.")
    else:
        raise typer.BadParameter("Pass --next or --index N.")

    if not target.ok:
        raise typer.Exit(f"[{target.index}] is {target.length} chars — fix it before posting.")

    typer.echo(f"--- tweet [{target.index}] ({target.pillar}), {target.length}/{TWEET_LIMIT} ---")
    typer.echo(target.text)
    typer.echo("-" * 40)

    if not live:
        typer.echo("DRY RUN — not posted. Re-run with --live to send it.")
        return

    client = get_client()
    resp = client.create_tweet(text=target.text)
    tweet_id = resp.data["id"]
    state["posted"] = sorted(posted | {target.index})
    write_state(state)
    typer.echo(f"Posted ✓  https://x.com/i/web/status/{tweet_id}")


if __name__ == "__main__":
    app()
