#!/usr/bin/env python3
"""
yt_upload.py — upload a video to YouTube via the Data API v3 (the automated ship step).

Once set up, publishing an episode is ONE command:
    python scripts/yt_upload.py upload DreamWeavers-Ep01.mp4 \
        --title "Welcome to La Piazza 🐺 | Dream Weavers Ep 1" \
        --desc-file ep01-description.txt \
        --tags "la piazza,dream weavers,build in public" \
        --playlist "Dream Weavers — Mike's Big Move" \
        --privacy public

ONE-TIME SETUP (~10 min, Google's side — you do this once):
  1. https://console.cloud.google.com → create a project (e.g. "lapiazza-youtube").
  2. APIs & Services → Library → enable "YouTube Data API v3".
  3. APIs & Services → OAuth consent screen → External → add yourself as a test user.
  4. Credentials → Create credentials → OAuth client ID → "Desktop app".
  5. Download the JSON → save as scripts/yt_client_secret.json (git-ignored).
  6. pip install google-api-python-client google-auth-oauthlib typer
  7. First run opens a browser to authorize (as @theSAPspecialist); the token caches to
     scripts/yt_token.json so you're never asked again.

Per CLAUDE.md rule 11: Python + Typer.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

try:
    import typer
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    sys.exit("Missing deps. Run:\n  pip install google-api-python-client google-auth-oauthlib typer")

HERE = Path(__file__).resolve().parent
CLIENT_SECRET = HERE / "yt_client_secret.json"
TOKEN = HERE / "yt_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

app = typer.Typer(add_completion=False, help="Upload videos to YouTube (Data API v3).")


def _service():
    """Authorize (cached) and return the YouTube API client."""
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CLIENT_SECRET.exists():
                sys.exit(f"Missing {CLIENT_SECRET.name}. See the setup steps at the top of this file.")
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def _ensure_playlist(yt, name: str) -> str | None:
    """Find a playlist by title (mine), or create it. Returns its id."""
    if not name:
        return None
    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req:
        res = req.execute()
        for pl in res.get("items", []):
            if pl["snippet"]["title"].strip() == name.strip():
                return pl["id"]
        req = yt.playlists().list_next(req, res)
    created = yt.playlists().insert(
        part="snippet,status",
        body={"snippet": {"title": name}, "status": {"privacyStatus": "public"}},
    ).execute()
    return created["id"]


@app.command()
def upload(
    video: Path = typer.Argument(..., exists=True, readable=True, help="The .mp4 to upload"),
    title: str = typer.Option(..., "--title", help="Video title"),
    desc_file: Path = typer.Option(None, "--desc-file", help="File with the description"),
    desc: str = typer.Option("", "--desc", help="Inline description (if no file)"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
    playlist: str = typer.Option("", "--playlist", help="Playlist title (created if missing)"),
    privacy: str = typer.Option("private", "--privacy", help="public | unlisted | private"),
    category: str = typer.Option("28", "--category", help="YouTube category id (28=Science&Tech, 27=Education)"),
    kids: bool = typer.Option(False, "--kids/--not-kids", help="Made for kids? default not-kids"),
):
    """Upload VIDEO with metadata; optionally add to a playlist."""
    description = desc_file.read_text() if desc_file else desc
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    yt = _service()

    body = {
        "snippet": {"title": title, "description": description, "tags": tag_list, "categoryId": category},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": kids},
    }
    media = MediaFileUpload(str(video), chunksize=-1, resumable=True, mimetype="video/*")
    typer.echo(f"⬆️  uploading {video.name} …")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            typer.echo(f"   {int(status.progress() * 100)}%")
    vid = resp["id"]
    url = f"https://youtu.be/{vid}"
    typer.echo(f"✅ uploaded: {url}")

    if playlist:
        pid = _ensure_playlist(yt, playlist)
        yt.playlistItems().insert(
            part="snippet",
            body={"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}},
        ).execute()
        typer.echo(f"📑 added to playlist: {playlist}")
    typer.echo(f"\n🔗 {url}")


if __name__ == "__main__":
    app()
