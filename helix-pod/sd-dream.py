#!/usr/bin/env python3
"""
🐉 SD DREAM — Johnny's Magic Wand
=================================
Type a dream. Get art. No money.

Usage:
    python sd-dream.py "dragon riding a skateboard"
    python sd-dream.py "sunset over mountains" --open
    python sd-dream.py "cyberpunk city" --sd-node localhost:7790

This is the simple interface. For Johnny. For everyone.

Authors: Angel & Tig
December 2025 — Dreams come true
"""

import os
import sys
import json
import base64
import argparse
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

OUTPUT_DIR = Path.home() / ".helix" / "dreams"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def dream(prompt, sd_node, negative_prompt="", steps=30, open_image=False):
    """Submit a dream, get art back."""

    print(f"""
    🐉 SD DREAM — JOHNNY'S MAGIC WAND
    ══════════════════════════════════
    Dream: {prompt}
    Node: {sd_node}
    """)

    # Build request
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or "blurry, bad quality, distorted, ugly",
        "steps": steps,
        "width": 1024,
        "height": 1024,
    }

    try:
        # Call SD node directly
        url = f"http://{sd_node}/generate"
        data = json.dumps(payload).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/json"})

        print("🎨 Generating... (this may take 30-60 seconds)")
        resp = urlopen(req, timeout=180)  # 3 min timeout for slow models
        result = json.loads(resp.read().decode())

        if result.get("ok"):
            # Decode and save image
            image_data = base64.b64decode(result["image_base64"])
            filename = result.get("filename", f"dream-{int(__import__('time').time())}.png")
            output_path = OUTPUT_DIR / filename
            output_path.write_bytes(image_data)

            print(f"""
    ✅ DREAM REALIZED!
    ══════════════════════════════════
    Prompt: {prompt}
    Cost: {result.get('cost', '?')} credits
    Saved: {output_path}
    Size: {len(image_data):,} bytes
            """)

            # Open image if requested
            if open_image:
                try:
                    if sys.platform == "darwin":
                        subprocess.run(["open", str(output_path)])
                    elif sys.platform == "linux":
                        subprocess.run(["xdg-open", str(output_path)])
                    elif sys.platform == "win32":
                        os.startfile(str(output_path))
                except:
                    pass

            return str(output_path)

        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
            return None

    except URLError as e:
        print(f"❌ Cannot reach SD node at {sd_node}")
        print(f"   Error: {e}")
        print(f"   Make sure helix-sd.py is running!")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="🐉 SD DREAM — Johnny's Magic Wand",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sd-dream.py "dragon riding a skateboard"
    python sd-dream.py "sunset over mountains" --open
    python sd-dream.py "cyberpunk city at night, neon lights" --steps 50
    python sd-dream.py "portrait of a tiger" --negative "cartoon, anime"
        """
    )
    parser.add_argument("prompt", type=str, help="Your dream (the image prompt)")
    parser.add_argument("--sd-node", type=str, default="localhost:7790", help="SD node address")
    parser.add_argument("--negative", type=str, default="", help="Negative prompt (what to avoid)")
    parser.add_argument("--steps", type=int, default=30, help="Inference steps (more = better but slower)")
    parser.add_argument("--open", action="store_true", help="Open the image when done")

    args = parser.parse_args()

    output = dream(
        prompt=args.prompt,
        sd_node=args.sd_node,
        negative_prompt=args.negative,
        steps=args.steps,
        open_image=args.open,
    )

    if output:
        print(f"\n🐉 Dream saved to: {output}")
        print("   Johnny woke up. Johnny made art. Johnny is happy. 💙")
    else:
        print("\n💤 Dream deferred. Try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
