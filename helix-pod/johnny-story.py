#!/usr/bin/env python3
"""
📖 JOHNNY'S STORY SCAFFOLD — Dream It, Build It, Ship It
=========================================================
A 5-year-old doesn't need to be a storyteller.
He needs a SCAFFOLD that asks the right questions.
Then he paints the answers.

Syd Field + Campbell + Gene, simplified for Johnny.

THREE TIERS OF FREE ART:
    1. COLORING BOOK - No network, just shapes (default)
    2. POLLINATIONS.AI - Free AI art, no account needed
    3. HUGGING FACE - Free AI art with account (rate limited)

ALL FREE. NO CREDIT CARD. EVER.

Usage:
    python johnny-story.py                    # Interactive mode
    python johnny-story.py --title "My Story" # Start with a title
    python johnny-story.py --load story.json  # Continue a story
    python johnny-story.py --mode pollinations # Use AI art

Authors: Angel & Leo
December 2025 — For Johnny, for Holly, for the castle in the sky
"""

import os
import json
import argparse
import base64
from datetime import datetime
from pathlib import Path

# Import the tiered art providers
try:
    from art_providers import (
        generate_art as generate_art_unified,
        generate_coloring_page,
        get_art_mode,
        set_art_mode,
        load_config,
    )
    HAS_ART_PROVIDERS = True
except ImportError:
    HAS_ART_PROVIDERS = False
    print("⚠️  art_providers not found, using built-in coloring only")

# =============================================================================
# CONFIGURATION
# =============================================================================

STORIES_DIR = Path.home() / ".helix" / "stories"
STORIES_DIR.mkdir(parents=True, exist_ok=True)

# SD Bridge settings
SD_BRIDGE_URL = os.environ.get("SD_BRIDGE_URL", "http://localhost:7790")


# =============================================================================
# SD BRIDGE CONNECTION
# =============================================================================

def generate_art(prompt, sd_url=SD_BRIDGE_URL, timeout=180):
    """Call the SD bridge to generate art for a scene."""
    try:
        payload = {
            "prompt": prompt,
            "negative_prompt": "blurry, bad quality, scary, dark, violent",
            "steps": 25,
            "width": 512,
            "height": 512,
        }
        data = json.dumps(payload).encode()
        req = Request(
            f"{sd_url}/generate",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        print(f"   🎨 Generating art...")
        resp = urlopen(req, timeout=timeout)
        result = json.loads(resp.read().decode())

        if result.get("ok") and result.get("image_base64"):
            return base64.b64decode(result["image_base64"])
        else:
            print(f"   ⚠️  Art generation failed: {result.get('error', 'Unknown error')}")
            return None

    except URLError as e:
        print(f"   ⚠️  Cannot reach SD bridge at {sd_url}: {e}")
        return None
    except Exception as e:
        print(f"   ⚠️  Error generating art: {e}")
        return None


# =============================================================================
# COLORING BOOK MODE — No AI, Just Shapes
# =============================================================================

def generate_coloring_page(prompt, title=""):
    """Generate a coloring book page using simple shapes."""
    try:
        # Import here to avoid dependency if not using coloring mode
        from PIL import Image, ImageDraw, ImageFont
        import math
        import random

        WIDTH, HEIGHT = 512, 512
        LINE_WIDTH = 4
        LINE_COLOR = "black"

        img = Image.new("RGB", (WIDTH, HEIGHT), "white")
        draw = ImageDraw.Draw(img)

        # Parse keywords
        prompt_lower = prompt.lower()
        has_dragon = "dragon" in prompt_lower
        has_skateboard = "skateboard" in prompt_lower
        has_princess = "princess" in prompt_lower or "holly" in prompt_lower
        has_giant = "giant" in prompt_lower
        has_tower = "tower" in prompt_lower
        has_dream = "dream" in prompt_lower or "thought" in prompt_lower
        has_happy = "happy" in prompt_lower or "celebrat" in prompt_lower
        has_flying = "flying" in prompt_lower
        has_action = "action" in prompt_lower or "dynamic" in prompt_lower
        has_sun = "sun" in prompt_lower or "sunshine" in prompt_lower
        has_stars = "star" in prompt_lower

        # Draw border
        draw.rectangle([10, 10, WIDTH - 10, HEIGHT - 10], outline=LINE_COLOR, width=LINE_WIDTH)

        # Title
        if title:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()
            draw.text((WIDTH//2, 30), title, fill=LINE_COLOR, font=font, anchor="mm")

        center_x, center_y = WIDTH // 2, HEIGHT // 2 + 30

        # Background elements
        if has_sun or has_happy:
            # Sun
            sx, sy, sr = WIDTH - 60, 80, 30
            draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr], outline=LINE_COLOR, width=LINE_WIDTH)
            for i in range(8):
                angle = i * math.pi / 4
                x1 = sx + (sr + 10) * math.cos(angle)
                y1 = sy + (sr + 10) * math.sin(angle)
                x2 = sx + (sr + 30) * math.cos(angle)
                y2 = sy + (sr + 30) * math.sin(angle)
                draw.line([(x1, y1), (x2, y2)], fill=LINE_COLOR, width=LINE_WIDTH)

        if has_stars:
            for _ in range(5):
                sx = random.randint(50, WIDTH - 50)
                sy = random.randint(50, 150)
                # Simple star
                points = []
                for i in range(10):
                    angle = math.pi/2 + (i * math.pi / 5)
                    r = 15 if i % 2 == 0 else 7
                    points.append((sx + r * math.cos(angle), sy - r * math.sin(angle)))
                draw.polygon(points, outline=LINE_COLOR, width=LINE_WIDTH)

        if has_tower:
            # Tower
            tx, tw, th = WIDTH - 80, 80, 200
            draw.rectangle([tx - tw//2, HEIGHT - 50 - th, tx + tw//2, HEIGHT - 50], outline=LINE_COLOR, width=LINE_WIDTH)
            # Roof
            draw.polygon([(tx - tw//2 - 10, HEIGHT - 50 - th), (tx, HEIGHT - 50 - th - 50), (tx + tw//2 + 10, HEIGHT - 50 - th)], outline=LINE_COLOR, width=LINE_WIDTH)
            # Window
            draw.arc([tx - 15, HEIGHT - 50 - th + 20, tx + 15, HEIGHT - 50 - th + 50], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([tx - 15, HEIGHT - 50 - th + 35, tx + 15, HEIGHT - 50 - th + 65], outline=LINE_COLOR, width=LINE_WIDTH)
            center_x = WIDTH // 3

        if has_dream:
            # Thought bubble
            for offset in [-25, 0, 25]:
                draw.ellipse([center_x + 50 + offset - 30, center_y - 130, center_x + 50 + offset + 30, center_y - 70], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([center_x + 20, center_y - 50, center_x + 40, center_y - 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([center_x + 5, center_y - 25, center_x + 17, center_y - 13], outline=LINE_COLOR, width=LINE_WIDTH)

        # Dragon
        if has_dragon:
            dx = center_x
            dy = center_y + 50 if not has_flying else center_y - 50
            size = 100

            # Body
            draw.ellipse([dx - size//2, dy - size//3, dx + size//2, dy + size//3], outline=LINE_COLOR, width=LINE_WIDTH)
            # Head
            hx, hy = dx + size//2, dy - size//4
            draw.ellipse([hx - size//4, hy - size//4, hx + size//4, hy + size//4], outline=LINE_COLOR, width=LINE_WIDTH)
            # Eyes
            draw.ellipse([hx - 13, hy - 10, hx - 3, hy], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([hx + 3, hy - 10, hx + 13, hy], outline=LINE_COLOR, width=LINE_WIDTH)
            # Smile
            draw.arc([hx - 12, hy, hx + 12, hy + 15], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
            # Horns
            draw.polygon([(hx - 20, hy - size//4), (hx - 15, hy - size//4 - 20), (hx - 10, hy - size//4)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.polygon([(hx + 10, hy - size//4), (hx + 15, hy - size//4 - 20), (hx + 20, hy - size//4)], outline=LINE_COLOR, width=LINE_WIDTH)
            # Wings
            draw.polygon([(dx - size//4, dy), (dx - size//4, dy - size//2), (dx, dy - size//4)], outline=LINE_COLOR, width=LINE_WIDTH)
            # Tail
            draw.line([(dx - size//2, dy), (dx - size//2 - 20, dy + 20), (dx - size//2 - 40, dy + 10), (dx - size//2 - 60, dy + 30)], fill=LINE_COLOR, width=LINE_WIDTH)
            # Legs
            draw.ellipse([dx - size//4 - 12, dy + size//3 - 10, dx - size//4 + 12, dy + size//3 + 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([dx + size//4 - 12, dy + size//3 - 10, dx + size//4 + 12, dy + size//3 + 30], outline=LINE_COLOR, width=LINE_WIDTH)

            # Skateboard
            if has_skateboard:
                sy = dy + size//3 + 35
                draw.rounded_rectangle([dx - 50, sy, dx + 50, sy + 12], radius=6, outline=LINE_COLOR, width=LINE_WIDTH)
                draw.ellipse([dx - 43, sy + 12, dx - 27, sy + 28], outline=LINE_COLOR, width=LINE_WIDTH)
                draw.ellipse([dx + 27, sy + 12, dx + 43, sy + 28], outline=LINE_COLOR, width=LINE_WIDTH)

        # Princess
        if has_princess:
            if has_tower:
                px, py = WIDTH - 80, HEIGHT - 200
                psize = 50
            elif has_dragon and has_flying:
                px, py = center_x + 30, center_y - 80
                psize = 50
            else:
                px, py = center_x + 100, center_y + 50
                psize = 70

            # Dress
            draw.polygon([(px, py), (px - psize//2, py + psize), (px + psize//2, py + psize)], outline=LINE_COLOR, width=LINE_WIDTH)
            # Head
            draw.ellipse([px - psize//5, py - psize//2 - psize//5, px + psize//5, py - psize//2 + psize//5], outline=LINE_COLOR, width=LINE_WIDTH)
            # Crown
            cw, ch = 30, 25
            draw.rectangle([px - cw//2, py - psize//2 - psize//5 - ch//3, px + cw//2, py - psize//2 - psize//5], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.line([(px - cw//2, py - psize//2 - psize//5 - ch//3), (px - cw//3, py - psize//2 - psize//5 - ch), (px, py - psize//2 - psize//5 - ch//2), (px + cw//3, py - psize//2 - psize//5 - ch), (px + cw//2, py - psize//2 - psize//5 - ch//3)], fill=LINE_COLOR, width=LINE_WIDTH)

        # Giant
        if has_giant:
            gx, gy, gsize = WIDTH - 120, center_y + 30, 120
            # Body
            draw.rectangle([gx - gsize//3, gy - gsize//4, gx + gsize//3, gy + gsize//2], outline=LINE_COLOR, width=LINE_WIDTH)
            # Head
            draw.ellipse([gx - gsize//4, gy - gsize//2 - gsize//4, gx + gsize//4, gy - gsize//4], outline=LINE_COLOR, width=LINE_WIDTH)
            # Grumpy eyebrows
            draw.line([(gx - 20, gy - gsize//2 + 10), (gx - 5, gy - gsize//2 + 20)], fill=LINE_COLOR, width=LINE_WIDTH)
            draw.line([(gx + 20, gy - gsize//2 + 10), (gx + 5, gy - gsize//2 + 20)], fill=LINE_COLOR, width=LINE_WIDTH)
            # Frown
            draw.arc([gx - 15, gy - gsize//2 + 35, gx + 15, gy - gsize//2 + 55], 180, 360, fill=LINE_COLOR, width=LINE_WIDTH)
            # Arms & legs
            draw.rectangle([gx - gsize//2 - 15, gy - gsize//6, gx - gsize//3, gy + gsize//3], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([gx + gsize//3, gy - gsize//6, gx + gsize//2 + 15, gy + gsize//3], outline=LINE_COLOR, width=LINE_WIDTH)

        # Action lines
        if has_action:
            for i in range(5):
                y = center_y - 30 + i * 15
                draw.line([(30, y), (80, y)], fill=LINE_COLOR, width=2)

        # Celebration stars
        if has_happy:
            for _ in range(8):
                cx = random.randint(50, WIDTH - 50)
                cy = random.randint(50, HEIGHT - 100)
                points = []
                for i in range(10):
                    angle = math.pi/2 + (i * math.pi / 5)
                    r = 8 if i % 2 == 0 else 4
                    points.append((cx + r * math.cos(angle), cy - r * math.sin(angle)))
                draw.polygon(points, outline=LINE_COLOR, width=LINE_WIDTH)

        # Convert to bytes
        import io
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    except ImportError:
        print("   ⚠️  Pillow not installed. Run: pip install Pillow")
        return None
    except Exception as e:
        print(f"   ⚠️  Error generating coloring page: {e}")
        return None


# =============================================================================
# THE SCAFFOLD — 5 QUESTIONS
# =============================================================================

SCAFFOLD_QUESTIONS = [
    {
        "id": "hero",
        "question": "🦸 WHO IS YOUR HERO?",
        "help": "The main character. Could be a dragon, a kid, a robot, YOU!",
        "prompt_template": "{answer}, character design, hero pose, children's book illustration",
    },
    {
        "id": "want",
        "question": "💫 WHAT DO THEY WANT?",
        "help": "Save someone? Find treasure? Get home? Win a race?",
        "prompt_template": "{hero} dreaming of {answer}, thought bubble, children's book illustration",
    },
    {
        "id": "obstacle",
        "question": "🚧 WHAT'S STOPPING THEM?",
        "help": "A monster? A locked door? A mean big brother? A mountain?",
        "prompt_template": "{hero} facing {answer}, dramatic scene, children's book illustration",
    },
    {
        "id": "solution",
        "question": "🔑 HOW DO THEY WIN?",
        "help": "A secret power? A friend helps? A clever trick? Bravery?",
        "prompt_template": "{hero} using {answer} to defeat {obstacle}, action scene, children's book illustration",
    },
    {
        "id": "ending",
        "question": "🏰 THE END — WHAT DOES HAPPY LOOK LIKE?",
        "help": "Castle saved? Friends together? Flying into sunset? Party?",
        "prompt_template": "{hero} celebrating, {answer}, happy ending, children's book illustration",
    },
]

# =============================================================================
# STORY CLASS
# =============================================================================

class Story:
    """Johnny's story — from scaffold to ship."""

    def __init__(self, title="My Story"):
        self.title = title
        self.author = "Johnny"
        self.created = datetime.now().isoformat()
        self.answers = {}
        self.scenes = []
        self.status = "drafting"
        self.images = {}

    def to_dict(self):
        return {
            "title": self.title,
            "author": self.author,
            "created": self.created,
            "answers": self.answers,
            "scenes": self.scenes,
            "status": self.status,
            "images": self.images,
        }

    def generate_all_art(self, mode="coloring", progress_callback=None):
        """Generate art for all scenes.

        FOUR TIERS OF FREE ART:
            - coloring: Simple line art for Johnny to color (default, FREE, OFFLINE)
            - pollinations: AI art via Pollinations.ai (FREE, NO ACCOUNT)
            - ai-coloring: AI art converted to outlines (BEST OF BOTH!)
            - huggingface: AI art via HF (FREE WITH ACCOUNT, rate limited)
            - auto: Try best available, fall back gracefully

        progress_callback: Optional function(scene_num, total, message, time_remaining)
        """
        import time as time_module

        total_scenes = len(self.scenes)
        print(f"\n🎨 GENERATING ART FOR {total_scenes} SCENES...")

        mode_descriptions = {
            "coloring": "COLORING BOOK (line art for crayons!) - FREE, OFFLINE",
            "pollinations": "POLLINATIONS.AI (AI art) - FREE, NO ACCOUNT",
            "ai-coloring": "AI-COLORING (AI art → outlines) - BEST OF BOTH!",
            "huggingface": "HUGGING FACE (AI art) - FREE WITH ACCOUNT",
            "auto": "AUTO (best available)",
        }
        print(f"   Mode: {mode_descriptions.get(mode, mode)}\n")

        # Determine if we need delays (network modes)
        needs_delay = mode in ["pollinations", "ai-coloring", "huggingface", "auto"]
        delay_seconds = 8 if needs_delay else 0

        # Estimate time
        time_per_scene = 15 if needs_delay else 1  # seconds
        total_time_estimate = total_scenes * time_per_scene

        if needs_delay:
            print(f"   ⏱️  Estimated time: ~{total_time_estimate // 60}m {total_time_estimate % 60}s")
            print(f"   💡 Using {delay_seconds}s delays to avoid rate limits\n")

        # Create images directory for this story
        safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in self.title)
        safe_title = safe_title.replace(" ", "-").lower()[:30]
        images_dir = STORIES_DIR / f"{safe_title}-images"
        images_dir.mkdir(parents=True, exist_ok=True)

        self.images = {}
        start_time = time_module.time()

        for i, scene in enumerate(self.scenes):
            scene_num = scene["number"]
            prompt = scene["art_prompt"]
            title = scene["title"]

            # Calculate progress and time remaining
            elapsed = time_module.time() - start_time
            scenes_done = i
            if scenes_done > 0:
                avg_time_per_scene = elapsed / scenes_done
                remaining_scenes = total_scenes - scenes_done
                time_remaining = int(avg_time_per_scene * remaining_scenes)
            else:
                time_remaining = total_time_estimate

            # Progress info
            progress_pct = int((i / total_scenes) * 100)
            remaining_str = f"{time_remaining // 60}m {time_remaining % 60}s" if time_remaining > 60 else f"{time_remaining}s"

            print(f"📍 Scene {scene_num}/{total_scenes}: {title}")
            print(f"   Progress: {progress_pct}% | ~{remaining_str} remaining")
            print(f"   Prompt: {prompt[:50]}...")

            # Call progress callback if provided
            if progress_callback:
                progress_callback(scene_num, total_scenes, title, time_remaining)

            # Add delay between scenes (except first one)
            if needs_delay and i > 0:
                print(f"   ⏳ Waiting {delay_seconds}s to avoid rate limit...")
                time_module.sleep(delay_seconds)

            # Generate using the unified art provider
            if HAS_ART_PROVIDERS:
                image_data = generate_art_unified(prompt, f"Scene {scene_num}: {title}", mode=mode)
            else:
                # Fallback to built-in coloring
                image_data = generate_coloring_page(prompt, f"Scene {scene_num}: {title}")

            if image_data:
                # Save the image
                image_path = images_dir / f"scene-{scene_num}.png"
                with open(image_path, "wb") as f:
                    f.write(image_data)
                print(f"   ✅ Saved: {image_path}")
                self.images[str(scene_num)] = str(image_path)
                scene["image_path"] = str(image_path)
                scene["image_base64"] = base64.b64encode(image_data).decode()
            else:
                print(f"   ⚠️  No image generated (will use placeholder)")
                self.images[str(scene_num)] = None
                scene["image_path"] = None
                scene["image_base64"] = None

            print()

        total_elapsed = int(time_module.time() - start_time)
        print(f"🎉 Art generation complete!")
        print(f"   Total time: {total_elapsed // 60}m {total_elapsed % 60}s")
        print(f"   Images saved to: {images_dir}")
        return self.images

    @classmethod
    def from_dict(cls, data):
        story = cls(data.get("title", "My Story"))
        story.author = data.get("author", "Johnny")
        story.created = data.get("created", datetime.now().isoformat())
        story.answers = data.get("answers", {})
        story.scenes = data.get("scenes", [])
        story.status = data.get("status", "drafting")
        story.images = data.get("images", {})
        return story

    def save(self, filename=None):
        if not filename:
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in self.title)
            safe_title = safe_title.replace(" ", "-").lower()[:30]
            filename = f"{safe_title}-{int(datetime.now().timestamp())}.json"

        filepath = STORIES_DIR / filename
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        return filepath

    @classmethod
    def load(cls, filepath):
        with open(filepath) as f:
            return cls.from_dict(json.load(f))

    def generate_scenes(self):
        """Generate scene descriptions from answers."""
        self.scenes = []

        hero = self.answers.get("hero", "the hero")
        want = self.answers.get("want", "something")
        obstacle = self.answers.get("obstacle", "something")
        solution = self.answers.get("solution", "something")
        ending = self.answers.get("ending", "happiness")

        # Scene 1: Meet the hero
        self.scenes.append({
            "number": 1,
            "title": f"Meet {hero.title()}",
            "description": f"This is {hero}. {hero.title()} is our hero!",
            "art_prompt": f"{hero}, character design, hero pose, friendly, children's book illustration, colorful",
        })

        # Scene 2: The dream
        self.scenes.append({
            "number": 2,
            "title": "The Dream",
            "description": f"{hero.title()} wants to {want}. More than anything!",
            "art_prompt": f"{hero} dreaming about {want}, thought bubble, stars, children's book illustration",
        })

        # Scene 3: The problem
        self.scenes.append({
            "number": 3,
            "title": "Oh No!",
            "description": f"But there's a problem! {obstacle.title()} is in the way!",
            "art_prompt": f"{hero} facing {obstacle}, dramatic, children's book illustration, tense moment",
        })

        # Scene 4: The solution
        self.scenes.append({
            "number": 4,
            "title": "The Clever Plan",
            "description": f"{hero.title()} has an idea! Using {solution}!",
            "art_prompt": f"{hero} using {solution} to overcome {obstacle}, action, dynamic, children's book illustration",
        })

        # Scene 5: Happy ending
        self.scenes.append({
            "number": 5,
            "title": "THE END",
            "description": f"And they all lived happily! {ending.title()}!",
            "art_prompt": f"{hero} celebrating, {ending}, happy, sunshine, children's book illustration, joyful",
        })

        return self.scenes

    def print_story(self):
        """Print the story in a nice format."""
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  📖 {self.title.upper():^54} ║
║  By: {self.author:<55} ║
╚══════════════════════════════════════════════════════════════╝
""")
        for scene in self.scenes:
            print(f"""
┌──────────────────────────────────────────────────────────────┐
│  Scene {scene['number']}: {scene['title']:<50} │
├──────────────────────────────────────────────────────────────┤
│  {scene['description']:<60} │
│                                                              │
│  🎨 Art prompt:                                              │
│  {scene['art_prompt'][:58]:<58} │
└──────────────────────────────────────────────────────────────┘
""")
        print("""
═══════════════════════════════════════════════════════════════
                         THE END
                     Made with ❤️ by Johnny
═══════════════════════════════════════════════════════════════
""")

    def export_html(self, filepath=None):
        """Export story as a simple HTML file."""
        if not filepath:
            safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in self.title)
            safe_title = safe_title.replace(" ", "-").lower()[:30]
            filepath = STORIES_DIR / f"{safe_title}.html"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Comic Sans MS', cursive, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .book {{
            max-width: 600px;
            margin: 0 auto;
            background: #fff;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .cover {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 60px 40px;
            text-align: center;
            color: white;
        }}
        .cover h1 {{
            font-size: 2.5em;
            margin-bottom: 20px;
            text-shadow: 3px 3px 0 rgba(0,0,0,0.2);
        }}
        .cover .author {{
            font-size: 1.3em;
            opacity: 0.9;
        }}
        .scene {{
            padding: 40px;
            border-bottom: 3px dashed #eee;
        }}
        .scene:nth-child(even) {{
            background: #f9f9ff;
        }}
        .scene-number {{
            background: #667eea;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .scene h2 {{
            color: #764ba2;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        .scene p {{
            font-size: 1.2em;
            line-height: 1.6;
            color: #333;
        }}
        .art-prompt {{
            background: #f0f0f0;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #666;
        }}
        .art-prompt::before {{
            content: "🎨 ";
        }}
        .scene-image {{
            width: 100%;
            max-width: 400px;
            margin: 20px auto;
            display: block;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .no-image {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            width: 100%;
            max-width: 400px;
            height: 300px;
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 15px;
            color: white;
            font-size: 3em;
        }}
        .the-end {{
            text-align: center;
            padding: 60px 40px;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}
        .the-end h2 {{
            font-size: 3em;
            margin-bottom: 20px;
        }}
        .the-end p {{
            font-size: 1.2em;
        }}
        .print-btn {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.2em;
            border-radius: 30px;
            cursor: pointer;
            font-family: inherit;
            margin-top: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        }}
        .print-btn:hover {{
            transform: scale(1.05);
        }}
        /* Print styles — Holly wants CLEAN pages */
        @page {{
            size: portrait;
            margin: 0.5cm;  /* Minimal margins, no browser headers/footers */
        }}
        @media print {{
            /* Hide UI elements */
            .print-btn {{ display: none !important; }}
            .art-prompt {{ display: none !important; }}

            /* Clean background */
            html, body {{
                background: white !important;
                padding: 0 !important;
                margin: 0 !important;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}

            /* Remove shadows and borders */
            .book {{
                box-shadow: none !important;
                border-radius: 0 !important;
                max-width: 100% !important;
            }}

            /* Cover gets its own page */
            .cover {{
                page-break-after: always;
                break-after: page;
                min-height: 90vh;
                border-radius: 0 !important;
            }}

            /* Each scene on its own page */
            .scene {{
                page-break-after: always;
                break-after: page;
                page-break-inside: avoid;
                break-inside: avoid;
                padding: 20px !important;
                border: none !important;
                min-height: 90vh;
            }}

            /* Make images BIG for coloring */
            .scene-image {{
                max-width: 90% !important;
                width: 90% !important;
                height: auto !important;
                margin: 20px auto !important;
                box-shadow: none !important;
                border-radius: 0 !important;
                border: 2px solid #333 !important;
            }}

            /* THE END - last page, no break after */
            .the-end {{
                page-break-after: avoid;
                break-after: avoid;
                min-height: 50vh;
                border-radius: 0 !important;
            }}

            /* Ensure colors print */
            .cover, .the-end {{
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="book">
        <div class="cover">
            <h1>📖 {self.title}</h1>
            <p class="author">Written by {self.author}</p>
            <button class="print-btn" onclick="window.print()">🖨️ Print My Book!</button>
        </div>
"""
        for scene in self.scenes:
            # Check if we have an image for this scene
            img_b64 = scene.get('image_base64')
            if img_b64:
                image_html = f'<img class="scene-image" src="data:image/png;base64,{img_b64}" alt="Scene {scene["number"]}">'
            else:
                image_html = '<div class="no-image">🎨</div>'

            html += f"""
        <div class="scene">
            <div class="scene-number">{scene['number']}</div>
            <h2>{scene['title']}</h2>
            {image_html}
            <p>{scene['description']}</p>
            <div class="art-prompt">{scene['art_prompt']}</div>
        </div>
"""
        html += f"""
        <div class="the-end">
            <h2>THE END</h2>
            <p>Made with ❤️ by {self.author}</p>
        </div>
    </div>
</body>
</html>
"""
        with open(filepath, "w") as f:
            f.write(html)
        return filepath


# =============================================================================
# INTERACTIVE SCAFFOLD
# =============================================================================

def run_scaffold(title=None):
    """Run the interactive story scaffold."""

    print("""
    📖 JOHNNY'S STORY SCAFFOLD
    ══════════════════════════════════════════

    Hey! Let's make a story together!
    I'll ask you 5 questions.
    You give me the answers.
    Then we'll have a REAL story!

    Ready? Let's go!
    """)

    # Get title
    if not title:
        title = input("📕 What's your story called? > ").strip()
        if not title:
            title = "My Amazing Story"

    story = Story(title)

    # Get author
    author = input(f"✏️  Who's the author? (that's YOU!) > ").strip()
    if author:
        story.author = author

    print("\n" + "═" * 50)
    print("Great! Now let's build your story!")
    print("═" * 50 + "\n")

    # Ask the 5 questions
    for q in SCAFFOLD_QUESTIONS:
        print(f"\n{q['question']}")
        print(f"   💡 Hint: {q['help']}")
        answer = input("   > ").strip()
        if answer:
            story.answers[q['id']] = answer
        else:
            story.answers[q['id']] = f"something amazing"

    # Generate scenes
    print("\n\n🎬 Building your story...")
    story.generate_scenes()
    story.status = "complete"

    # Ask about art generation
    print("\n" + "═" * 50)
    print("🎨 ART OPTIONS — ALL FREE, NO CREDIT CARD!")
    print("   1. 🖍️  Coloring book (basic shapes) [OFFLINE]")
    print("   2. 🌸 AI Art (Pollinations, full color)")
    print("   3. 🎨 AI Coloring (AI art → outlines!) [BEST!]")
    print("   4. 🤗 Hugging Face (needs free account)")
    print("   5. 🔄 Auto (try best available)")
    print("   6. ❌ No art (just the story)")
    art_choice = input("   Pick 1-6 > ").strip()

    if art_choice == "1":
        story.generate_all_art(mode="coloring")
    elif art_choice == "2":
        story.generate_all_art(mode="pollinations")
    elif art_choice == "3":
        story.generate_all_art(mode="ai-coloring")
    elif art_choice == "4":
        story.generate_all_art(mode="huggingface")
    elif art_choice == "5":
        story.generate_all_art(mode="auto")

    # Save it
    saved_path = story.save()
    print(f"💾 Story saved to: {saved_path}")

    # Export HTML (will include images if we generated them)
    html_path = story.export_html()
    print(f"🌐 HTML exported to: {html_path}")

    # Print the story
    print("\n\n" + "🎉" * 20)
    print("\nHERE'S YOUR STORY!\n")
    story.print_story()

    return story


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="📖 JOHNNY'S STORY SCAFFOLD — Dream It, Build It, Ship It\n\n"
                    "THREE TIERS OF FREE ART:\n"
                    "  coloring     - Line art for crayons (offline, default)\n"
                    "  pollinations - AI art via Pollinations.ai (free, no account)\n"
                    "  huggingface  - AI art via HF (free with account)\n"
                    "  auto         - Try best available",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--title", type=str, help="Story title")
    parser.add_argument("--load", type=str, help="Load existing story JSON")
    parser.add_argument("--list", action="store_true", help="List saved stories")
    parser.add_argument("--art", action="store_true", help="Generate art for loaded story")
    parser.add_argument("--mode", type=str, default="coloring",
                       choices=["coloring", "pollinations", "ai-coloring", "huggingface", "auto"],
                       help="Art mode (default: coloring)")
    parser.add_argument("--set-hf-token", type=str, metavar="TOKEN",
                       help="Set Hugging Face token for AI art")

    args = parser.parse_args()

    # Handle HF token setup
    if args.set_hf_token:
        if HAS_ART_PROVIDERS:
            from art_providers import set_hf_token
            set_hf_token(args.set_hf_token)
            print("✅ Hugging Face token saved!")
            print("   Art mode automatically set to: huggingface")
        else:
            print("⚠️  art_providers module not available")
        return

    if args.list:
        print("\n📚 JOHNNY'S LIBRARY\n")
        stories = list(STORIES_DIR.glob("*.json"))
        if stories:
            for s in sorted(stories, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                print(f"   📖 {s.name}")
        else:
            print("   (No stories yet! Let's make one!)")
        print(f"\n   Stories live in: {STORIES_DIR}\n")

        # Show current art mode
        if HAS_ART_PROVIDERS:
            current_mode = get_art_mode()
            print(f"   🎨 Current art mode: {current_mode}")
            print(f"   💡 Change with: --mode pollinations")
        return

    if args.load:
        story = Story.load(args.load)
        if args.art:
            # Generate art for this story
            story.generate_all_art(mode=args.mode)
            # Re-save with images
            story.save(Path(args.load).name)
            # Re-export HTML
            html_path = story.export_html()
            print(f"🌐 HTML with art exported to: {html_path}")
        story.print_story()
        return

    # Run interactive scaffold
    run_scaffold(args.title)


if __name__ == "__main__":
    main()
