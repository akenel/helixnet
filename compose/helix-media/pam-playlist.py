#!/usr/bin/env python3
"""
PAM'S PLAYLIST GENERATOR
========================
The LLM does the kicks for you.

Usage:
    python pam-playlist.py "floor scrubbing music"
    python pam-playlist.py "monday morning coffee"
    python pam-playlist.py "the CTO rejected my PR"
"""

import os
import random
import subprocess
import sys
from pathlib import Path

# Where the music lives
MUSIC_DIR = Path(__file__).parent / "music" / "sunrise-chain"

# Mood mappings - the LLM brain (simple version for now)
MOOD_TAGS = {
    # HIGH ENERGY - Floor scrubbing, dancing, moving
    "floor": ["remixes-platinum", "soul-foundation"],
    "scrub": ["remixes-platinum", "soul-foundation"],
    "dance": ["remixes-platinum"],
    "party": ["remixes-platinum", "soul-foundation"],
    "energy": ["remixes-platinum", "australia", "europe-west"],
    "move": ["remixes-platinum", "soul-foundation"],
    "clean": ["remixes-platinum"],
    "friday": ["remixes-platinum", "soul-foundation"],

    # CHILL - Monday coffee, relaxation
    "coffee": ["soul-foundation", "japan-korea", "americas-east"],
    "monday": ["soul-foundation", "japan-korea"],
    "morning": ["soul-foundation", "pacific-dawn", "japan-korea"],
    "chill": ["japan-korea", "soul-foundation", "americas-east"],
    "relax": ["japan-korea", "pacific-dawn", "middle-east"],
    "calm": ["japan-korea", "india-pakistan", "pacific-dawn"],

    # DEEP FOCUS - Coding, working
    "focus": ["japan-korea", "europe-east"],
    "code": ["japan-korea", "europe-east"],
    "work": ["japan-korea", "soul-foundation"],
    "concentrate": ["japan-korea"],

    # REVOLUTION - When you need to fight
    "angry": ["europe-west", "soul-foundation"],
    "revolution": ["europe-west", "soul-foundation", "africa-west"],
    "fight": ["europe-west", "australia"],
    "protest": ["soul-foundation", "europe-west", "americas-east"],

    # HEARTBREAK - Sad but beautiful
    "sad": ["soul-foundation", "europe-west"],
    "heartbreak": ["soul-foundation", "europe-west"],
    "cry": ["soul-foundation", "americas-east"],
    "miss": ["soul-foundation", "europe-west"],

    # CTO MOODS
    "toast": ["remixes-platinum"],  # warm toast = dance music
    "rejected": ["soul-foundation", "europe-west"],  # PR rejected
    "cto": ["japan-korea"],  # ambient focus for the confused CTO
}

# Surprise tracks to pull if user wants fresh music
SURPRISE_SEARCHES = [
    ("Jamiroquai - Virtual Insanity", "remixes-platinum"),
    ("Dua Lipa - Levitating", "remixes-platinum"),
    ("Bruno Mars - Uptown Funk", "remixes-platinum"),
    ("Pharrell - Happy", "remixes-platinum"),
    ("Mark Ronson - Uptown Funk", "remixes-platinum"),
    ("Al Green - Lets Stay Together", "soul-foundation"),
    ("Curtis Mayfield - Move On Up", "soul-foundation"),
    ("Bill Withers - Lovely Day", "soul-foundation"),
    ("Kool and the Gang - Celebration", "remixes-platinum"),
    ("Lipps Inc - Funkytown", "remixes-platinum"),
]


def get_all_tracks():
    """Get all MP3 files from the music directory."""
    tracks = []
    for mp3 in MUSIC_DIR.rglob("*.mp3"):
        region = mp3.parent.name
        tracks.append({
            "path": mp3,
            "name": mp3.stem,
            "region": region,
        })
    return tracks


def parse_mood(query: str) -> list:
    """Parse the user's mood query and return matching regions."""
    query_lower = query.lower()
    matching_regions = set()

    for keyword, regions in MOOD_TAGS.items():
        if keyword in query_lower:
            matching_regions.update(regions)

    # Default to a mix if nothing matches
    if not matching_regions:
        matching_regions = {"soul-foundation", "remixes-platinum", "europe-west"}

    return list(matching_regions)


def generate_playlist(query: str, duration_mins: int = 60, track_count: int = None):
    """Generate a playlist based on mood query."""

    print(f"\n🎵 PAM'S PLAYLIST GENERATOR")
    print(f"═" * 50)
    print(f"Mood: \"{query}\"")
    print(f"═" * 50)

    # Parse mood
    regions = parse_mood(query)
    print(f"\n🎯 Detected vibe: {', '.join(regions)}")

    # Get all tracks
    all_tracks = get_all_tracks()

    # Filter by matching regions
    matching = [t for t in all_tracks if t["region"] in regions]

    # If not enough, add some from other regions
    if len(matching) < 10:
        others = [t for t in all_tracks if t["region"] not in regions]
        random.shuffle(others)
        matching.extend(others[:10 - len(matching)])

    # Shuffle and select
    random.shuffle(matching)

    if track_count:
        selected = matching[:track_count]
    else:
        # Assume ~4 mins per track for duration
        num_tracks = max(5, duration_mins // 4)
        selected = matching[:num_tracks]

    # Print playlist
    print(f"\n📀 YOUR PLAYLIST ({len(selected)} tracks)")
    print(f"─" * 50)

    total_time = 0
    for i, track in enumerate(selected, 1):
        # Estimate 4 mins per track (we don't have actual durations yet)
        est_time = 4
        total_time += est_time
        print(f"  {i:2}. {track['name']}")
        print(f"      └─ [{track['region']}]")

    print(f"─" * 50)
    print(f"⏱️  Estimated: ~{total_time} minutes")
    print(f"─" * 50)

    return selected


def pull_surprise(search_term: str, region: str):
    """Pull a fresh track from YouTube."""
    print(f"\n🎁 Pulling surprise: {search_term}")

    output_path = MUSIC_DIR / region / f"{search_term}.%(ext)s"

    cmd = [
        "yt-dlp", "-x",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "-o", str(output_path),
        f"ytsearch1:{search_term}",
        "--no-playlist"
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ Added to {region}/")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nExamples:")
        print('  python pam-playlist.py "floor scrubbing energy"')
        print('  python pam-playlist.py "monday morning coffee"')
        print('  python pam-playlist.py "sad heartbreak music"')
        print('  python pam-playlist.py "CTO rejected my PR"')
        return

    query = " ".join(sys.argv[1:])

    # Generate playlist
    playlist = generate_playlist(query)

    # Ask about surprises
    print(f"\n🎲 Want me to pull 2 surprise tracks from the river? (y/n): ", end="")

    try:
        answer = input().strip().lower()
        if answer == 'y':
            surprises = random.sample(SURPRISE_SEARCHES, 2)
            for search, region in surprises:
                pull_surprise(search, region)
            print("\n🔄 Restart player to index new tracks:")
            print("   docker compose -f media-stack.yml restart swingmusic")
    except EOFError:
        pass

    print(f"\n🐅 Enjoy the music, Pam!")
    print(f"   \"The LLM does the kicks for you.\"")
    print()


if __name__ == "__main__":
    main()
