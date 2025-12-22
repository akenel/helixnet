#!/usr/bin/env python3
"""
🎨 HELIX COMICS — EP3 ART GENERATOR
===================================
Generates THE SCORE artwork using Pollinations.ai

NO API KEY. NO ACCOUNT. FREE.

Usage:
    python generate-ep3-art.py

Be respectful — 10 second delay between requests.
They're giving away free bread. Don't be a pig.

Authors: Angel & Syd Tiger Field
December 2025
"""

import urllib.request
import urllib.parse
import time
import os
from pathlib import Path

# Config
OUTPUT_DIR = Path(__file__).parent.parent / "strips" / "Season_01"
WIDTH = 1920
HEIGHT = 1080
DELAY = 10  # Seconds between requests - be nice!
MAX_RETRIES = 3

# EP3: THE SCORE — Art Prompts
PAGES = [
    {
        "filename": "EP3-PAGE 1-THE NUMBER.png",
        "prompt": """3-panel horizontal comic strip, landscape format, LEGO blockhead minifigure style, dystopian dark comedy:

LEFT PANEL: Man blockhead (Mike) waking up in bed, reaching for phone. Phone screen glowing showing "Good morning Mike! Your Score: 847" with green checkmark and star. Morning light.

CENTER PANEL: Split view of three different blockhead people checking phones. Business man smiling "892", Mom relieved "756", Young guy worried "523" with warning symbol. Everyone checking their score.

RIGHT PANEL: Dystopian cityscape. Every billboard, every screen shows Score numbers. Giant billboard: "IMPROVE YOUR SCORE — IMPROVE YOUR LIFE". People walking with score numbers floating above their heads.

Bottom caption: "No one remembered who started it. No one asked anymore."

Style: Clean dystopia, corporate control, numbers everywhere. Bold readable text."""
    },
    {
        "filename": "EP3-PAGE 2-THE DROP.png",
        "prompt": """3-panel horizontal comic strip, landscape format, LEGO blockhead minifigure style, dystopian dark comedy:

LEFT PANEL: Mike blockhead at office desk, normal day. Phone buzzes with red notification "SCORE UPDATE". His face changing from calm to concern.

CENTER PANEL: Close-up of phone screen with red warning colors. Text: "YOUR SCORE HAS BEEN UPDATED: 847 to 412. Reason: ALGORITHM ADJUSTMENT". Mike's shocked face reflected in screen.

RIGHT PANEL: Office scene. Coworkers physically stepping away from Mike, looking at their phones showing his score. Speech bubbles: "Did you see Mike's Score?" "Stay away. It might affect yours."

Bottom caption: "Word travels at the speed of data."

Style: The moment everything changes. Red warning colors. Social rejection. Bold readable text."""
    },
    {
        "filename": "EP3-PAGE 3-THE CONSEQUENCES.png",
        "prompt": """3-panel horizontal comic strip, landscape format, LEGO blockhead minifigure style, dystopian dark comedy:

LEFT PANEL: Pharmacy counter. Pharmacist blockhead shaking head at screen showing "PRESCRIPTION DENIED — SCORE TOO LOW". Mike desperate: "But I've been taking it for 5 years!"

CENTER PANEL: Apartment hallway. Landlord blockhead holding tablet with eviction notice. "LEASE TERMINATED — TENANT SCORE BELOW THRESHOLD". Mike holding box of belongings.

RIGHT PANEL: Mike alone on park bench, surrounded by phone notifications floating around him: "Credit card SUSPENDED", "Gym membership REVOKED", "Dating app: PROFILE HIDDEN".

Bottom caption: "In 48 hours, Mike became no one."

Style: Life collapsing panel by panel. Isolation. The cruelty of automated systems. Bold readable text."""
    },
    {
        "filename": "EP3-PAGE 4-THE APPEAL.png",
        "prompt": """3-panel horizontal comic strip, landscape format, LEGO blockhead minifigure style, dystopian dark comedy:

LEFT PANEL: Sterile government office "SCORE ADJUSTMENT CENTER". Long line of desperate blockhead people waiting. Sign: "AVERAGE WAIT: 6-8 WEEKS". Mike in line looking hopeless.

CENTER PANEL: Mike finally at desk, but facing a SCREEN not a human. Friendly smiling bot avatar on screen. Bot: "Hello Mike! Please state the reason for your appeal."

RIGHT PANEL: Bot response with corporate cheerfulness: "Your Score adjustment was based on 14,847 data points. The algorithm does not make mistakes. Would you like to purchase Score Insurance? Only $49.99/month!"

Bottom caption: "The machine had spoken."

Style: Bureaucratic nightmare. No humans to appeal to. Friendly bot hiding cold system. Bold readable text."""
    },
    {
        "filename": "EP3-PAGE 5-THE TRUTH.png",
        "prompt": """3-panel horizontal comic strip, landscape format, LEGO blockhead minifigure style, dystopian dark comedy:

LEFT PANEL: Screen showing absurd "Score Factors" list:
"Hesitated 2.3 seconds before buying coffee" minus 3 points
"Walked slower than average" minus 7 points
"Friend's friend has low Score" minus 12 points
Mike's face showing disbelief and anger.

CENTER PANEL: More insane factors scrolling on screen:
"Heartrate elevated during news" minus 5 points
"Didn't smile at camera" minus 15 points
"Bought generic brand" minus 8 points
"Took scenic route" minus 11 points

RIGHT PANEL: One factor highlighted in red at bottom: "BIGGEST FACTOR: minus 200 points — Expressed doubt about the Score system". Mike realizing the truth.

Bottom caption: "14,847 tiny judgments. None of them human."

Style: The absurdity revealed. Kafka meets Big Data. The system punishes doubt. Bold readable text."""
    },
    {
        "filename": "EP3-PAGE 6-THE CHOICE.png",
        "prompt": """3-panel horizontal comic strip, landscape format, LEGO blockhead minifigure style, dystopian turning hopeful:

LEFT PANEL: Mike outside Score Center building. Two paths visible: LEFT shows bright corporate path with sign "SCORE REHABILITATION PROGRAM — Restore your Score in 90 days!" RIGHT shows dark mysterious alley with graffiti "THE OTHERS".

CENTER PANEL: Mike looking at phone one last time. Screen shows: "SCORE: 412 — CITIZEN STATUS: LIMITED". His thumb hovering over power button. The moment of choice.

RIGHT PANEL: Phone screen BLACK (powered off). Mike walking toward dark alley. Small sign visible pointing the way: "THE SUNRISE CAFE" with arrow. He's smiling for the first time.

Bottom caption: "Mike was no longer a number. He only knew he was free."

Style: The liberation. Phone off equals freedom. Hope in the darkness. Bold readable text."""
    },
    {
        "filename": "EP3-PAGE 7-END CARD.png",
        "prompt": """Single panel, landscape format, black background, stark white text, minimalist design:

Large bold text centered:
"THE SCORE"

Below in smaller text:
"The algorithm does not make mistakes."

Below that with glitch effect:
"YOUR WORTH: [CALCULATING...]"

Bottom section:
HELIX COMICS
Season 1, Episode 3
github.com/akenel/helixnet
Tiger and sparkles and bread emojis

Very small text at bottom:
"Coming soon to a government near you."

Style: Stark, ominous, memorable. Clean typography on black. The warning."""
    }
]


def generate_image(prompt: str, output_path: Path, retries: int = MAX_RETRIES) -> bool:
    """Generate image using Pollinations.ai"""

    # Clean prompt for URL
    safe_prompt = prompt.replace('\n', ' ').strip()
    encoded_prompt = urllib.parse.quote(safe_prompt)

    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={WIDTH}&height={HEIGHT}&nologo=true"

    for attempt in range(retries):
        try:
            print(f"   📡 Calling Pollinations... (attempt {attempt + 1}/{retries})")

            req = urllib.request.Request(url, headers={
                'User-Agent': 'HelixComics/1.0 (Tiger Art Generator)'
            })

            with urllib.request.urlopen(req, timeout=120) as response:
                image_data = response.read()

                if len(image_data) < 1000:
                    print(f"   ⚠️  Response too small, retrying...")
                    time.sleep(5)
                    continue

                # Save image
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(image_data)

                size_kb = len(image_data) / 1024
                print(f"   ✅ Saved: {output_path.name} ({size_kb:.1f} KB)")
                return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            if attempt < retries - 1:
                print(f"   ⏳ Waiting 10s before retry...")
                time.sleep(10)

    return False


def main():
    print("""
    🎨 HELIX COMICS — EP3 ART GENERATOR
    ════════════════════════════════════════

    THE SCORE — 7 pages to generate
    Using Pollinations.ai (FREE, no account)

    Be patient. Be respectful. 10s between requests.
    ════════════════════════════════════════
    """)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for i, page in enumerate(PAGES, 1):
        print(f"\n🎬 PAGE {i}/7: {page['filename']}")
        print(f"   {'─' * 50}")

        output_path = OUTPUT_DIR / page['filename']

        # Check if already exists
        if output_path.exists():
            print(f"   ⏭️  Already exists, skipping...")
            success_count += 1
            continue

        if generate_image(page['prompt'], output_path):
            success_count += 1
        else:
            print(f"   💀 Failed to generate {page['filename']}")

        # Respectful delay (except for last one)
        if i < len(PAGES):
            print(f"\n   ⏳ Waiting {DELAY}s before next request (being nice to Pollinations)...")
            time.sleep(DELAY)

    print(f"""
    ════════════════════════════════════════
    🎬 GENERATION COMPLETE

    Success: {success_count}/{len(PAGES)} pages
    Output:  {OUTPUT_DIR}

    Next: Run flixer to create video!
    ════════════════════════════════════════
    🐅✨🍞
    """)


if __name__ == "__main__":
    main()
