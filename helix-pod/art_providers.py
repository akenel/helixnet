#!/usr/bin/env python3
"""
🎨 ART PROVIDERS — Four Tiers of Free Image Generation
=======================================================
Johnny grows with the system:

Tier 1: COLORING BOOK (default)
    - No network, no account, no nothing
    - Just shapes and lines for crayons
    - Works offline, works forever

Tier 2: POLLINATIONS.AI
    - Free AI art, zero setup
    - No account, no email, no token
    - Just works via HTTP GET

Tier 3: AI-COLORING (NEW!)
    - Pollinations AI art → Edge detection → Outlines
    - Beautiful AI compositions as coloring pages!
    - Best of both worlds

Tier 4: HUGGING FACE
    - Free with account (rate limited)
    - Needs email + token
    - Better quality, learns about APIs

ALL FREE. NO CREDIT CARD. EVER.

Authors: Angel & Leo
December 2025 — The 98% deserve free AI art
"""

import os
import json
import yaml
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any
import time

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_DIR = Path.home() / ".helix"
CONFIG_FILE = CONFIG_DIR / "johnny-config.yaml"

DEFAULT_CONFIG = {
    "art_mode": "coloring",  # coloring | pollinations | ai-coloring | huggingface

    "pollinations": {
        "enabled": True,
        "url": "https://image.pollinations.ai/prompt/",
        "width": 512,
        "height": 512,
        "delay_between_requests": 8,  # Seconds to wait between requests (avoid rate limit)
        "max_retries": 2,  # Retry on failure
    },

    "huggingface": {
        "enabled": False,
        "token": "",  # User adds their HF token
        "model": "stabilityai/stable-diffusion-xl-base-1.0",
        "api_url": "https://api-inference.huggingface.co/models/",
    },

    "coloring": {
        "line_width": 4,
        "background": "white",
        "line_color": "black",
    },

    "ai_coloring": {
        "edge_method": "canny",  # canny | sobel | contour
        "line_thickness": 2,
        "threshold_low": 50,
        "threshold_high": 150,
        "invert": True,  # White background, black lines
    },

    # Child-safe defaults
    "safety": {
        "negative_prompt": "scary, dark, violent, blood, horror, nsfw, adult",
        "style_suffix": ", children's book illustration, friendly, colorful, safe for kids",
    }
}


def load_config() -> Dict[str, Any]:
    """Load config from file or create default."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                user_config = yaml.safe_load(f) or {}
            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            for key, value in user_config.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value
            return config
        except Exception as e:
            print(f"   ⚠️  Config error: {e}, using defaults")
            return DEFAULT_CONFIG.copy()
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> Path:
    """Save config to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    return CONFIG_FILE


def get_art_mode() -> str:
    """Get current art mode from config."""
    config = load_config()
    return config.get("art_mode", "coloring")


def set_art_mode(mode: str) -> bool:
    """Set art mode in config."""
    if mode not in ["coloring", "pollinations", "ai-coloring", "huggingface", "auto"]:
        return False
    config = load_config()
    config["art_mode"] = mode
    save_config(config)
    return True


def set_hf_token(token: str) -> bool:
    """Set Hugging Face token in config."""
    config = load_config()
    config["huggingface"]["token"] = token
    config["huggingface"]["enabled"] = bool(token)
    if token:
        config["art_mode"] = "huggingface"
    save_config(config)
    return True


# =============================================================================
# TIER 1: COLORING BOOK (Local, No Network)
# =============================================================================

def generate_coloring_page(prompt: str, title: str = "") -> Optional[bytes]:
    """
    Generate a coloring book page using simple shapes.
    No network, no AI, no nothing — just Pillow.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import math
        import random

        config = load_config()
        coloring_cfg = config.get("coloring", {})

        WIDTH, HEIGHT = 512, 512
        LINE_WIDTH = coloring_cfg.get("line_width", 4)
        LINE_COLOR = coloring_cfg.get("line_color", "black")
        BACKGROUND = coloring_cfg.get("background", "white")

        img = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        draw = ImageDraw.Draw(img)

        # Parse keywords from prompt
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
        has_robot = "robot" in prompt_lower
        has_unicorn = "unicorn" in prompt_lower
        has_cat = "cat" in prompt_lower
        has_dog = "dog" in prompt_lower
        has_monster = "monster" in prompt_lower
        has_treasure = "treasure" in prompt_lower
        has_castle = "castle" in prompt_lower

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
                points = []
                for i in range(10):
                    angle = math.pi/2 + (i * math.pi / 5)
                    r = 15 if i % 2 == 0 else 7
                    points.append((sx + r * math.cos(angle), sy - r * math.sin(angle)))
                draw.polygon(points, outline=LINE_COLOR, width=LINE_WIDTH)

        if has_tower or has_castle:
            tx, tw, th = WIDTH - 80, 80, 200
            draw.rectangle([tx - tw//2, HEIGHT - 50 - th, tx + tw//2, HEIGHT - 50], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.polygon([(tx - tw//2 - 10, HEIGHT - 50 - th), (tx, HEIGHT - 50 - th - 50), (tx + tw//2 + 10, HEIGHT - 50 - th)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.arc([tx - 15, HEIGHT - 50 - th + 20, tx + 15, HEIGHT - 50 - th + 50], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([tx - 15, HEIGHT - 50 - th + 35, tx + 15, HEIGHT - 50 - th + 65], outline=LINE_COLOR, width=LINE_WIDTH)
            center_x = WIDTH // 3

        if has_dream:
            for offset in [-25, 0, 25]:
                draw.ellipse([center_x + 50 + offset - 30, center_y - 130, center_x + 50 + offset + 30, center_y - 70], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([center_x + 20, center_y - 50, center_x + 40, center_y - 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([center_x + 5, center_y - 25, center_x + 17, center_y - 13], outline=LINE_COLOR, width=LINE_WIDTH)

        # Main characters
        if has_dragon:
            dx = center_x
            dy = center_y + 50 if not has_flying else center_y - 50
            size = 100
            draw.ellipse([dx - size//2, dy - size//3, dx + size//2, dy + size//3], outline=LINE_COLOR, width=LINE_WIDTH)
            hx, hy = dx + size//2, dy - size//4
            draw.ellipse([hx - size//4, hy - size//4, hx + size//4, hy + size//4], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([hx - 13, hy - 10, hx - 3, hy], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([hx + 3, hy - 10, hx + 13, hy], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.arc([hx - 12, hy, hx + 12, hy + 15], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
            draw.polygon([(hx - 20, hy - size//4), (hx - 15, hy - size//4 - 20), (hx - 10, hy - size//4)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.polygon([(hx + 10, hy - size//4), (hx + 15, hy - size//4 - 20), (hx + 20, hy - size//4)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.polygon([(dx - size//4, dy), (dx - size//4, dy - size//2), (dx, dy - size//4)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.line([(dx - size//2, dy), (dx - size//2 - 20, dy + 20), (dx - size//2 - 40, dy + 10), (dx - size//2 - 60, dy + 30)], fill=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([dx - size//4 - 12, dy + size//3 - 10, dx - size//4 + 12, dy + size//3 + 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([dx + size//4 - 12, dy + size//3 - 10, dx + size//4 + 12, dy + size//3 + 30], outline=LINE_COLOR, width=LINE_WIDTH)
            if has_skateboard:
                sy = dy + size//3 + 35
                draw.rounded_rectangle([dx - 50, sy, dx + 50, sy + 12], radius=6, outline=LINE_COLOR, width=LINE_WIDTH)
                draw.ellipse([dx - 43, sy + 12, dx - 27, sy + 28], outline=LINE_COLOR, width=LINE_WIDTH)
                draw.ellipse([dx + 27, sy + 12, dx + 43, sy + 28], outline=LINE_COLOR, width=LINE_WIDTH)

        if has_robot:
            rx, ry = center_x, center_y + 30
            draw.rectangle([rx - 40, ry - 30, rx + 40, ry + 50], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx - 30, ry - 70, rx + 30, ry - 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx - 20, ry - 60, rx - 5, ry - 45], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx + 5, ry - 60, rx + 20, ry - 45], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx - 55, ry - 20, rx - 40, ry + 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx + 40, ry - 20, rx + 55, ry + 30], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx - 25, ry + 50, rx - 10, ry + 90], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([rx + 10, ry + 50, rx + 25, ry + 90], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([rx - 10, ry - 90, rx + 10, ry - 70], outline=LINE_COLOR, width=LINE_WIDTH)

        if has_unicorn:
            ux, uy = center_x, center_y + 40
            draw.ellipse([ux - 50, uy - 20, ux + 50, uy + 40], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([ux + 40, uy - 50, ux + 80, uy - 10], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.polygon([(ux + 60, uy - 50), (ux + 65, uy - 90), (ux + 70, uy - 50)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([ux - 40, uy + 30, ux - 25, uy + 70], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([ux + 25, uy + 30, ux + 40, uy + 70], outline=LINE_COLOR, width=LINE_WIDTH)

        if has_princess:
            if has_tower or has_castle:
                px, py = WIDTH - 80, HEIGHT - 200
                psize = 50
            elif has_dragon and has_flying:
                px, py = center_x + 30, center_y - 80
                psize = 50
            else:
                px, py = center_x + 100, center_y + 50
                psize = 70
            draw.polygon([(px, py), (px - psize//2, py + psize), (px + psize//2, py + psize)], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([px - psize//5, py - psize//2 - psize//5, px + psize//5, py - psize//2 + psize//5], outline=LINE_COLOR, width=LINE_WIDTH)
            cw, ch = 30, 25
            draw.rectangle([px - cw//2, py - psize//2 - psize//5 - ch//3, px + cw//2, py - psize//2 - psize//5], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.line([(px - cw//2, py - psize//2 - psize//5 - ch//3), (px - cw//3, py - psize//2 - psize//5 - ch), (px, py - psize//2 - psize//5 - ch//2), (px + cw//3, py - psize//2 - psize//5 - ch), (px + cw//2, py - psize//2 - psize//5 - ch//3)], fill=LINE_COLOR, width=LINE_WIDTH)

        if has_giant or has_monster:
            gx, gy, gsize = WIDTH - 120, center_y + 30, 120
            draw.rectangle([gx - gsize//3, gy - gsize//4, gx + gsize//3, gy + gsize//2], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.ellipse([gx - gsize//4, gy - gsize//2 - gsize//4, gx + gsize//4, gy - gsize//4], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.line([(gx - 20, gy - gsize//2 + 10), (gx - 5, gy - gsize//2 + 20)], fill=LINE_COLOR, width=LINE_WIDTH)
            draw.line([(gx + 20, gy - gsize//2 + 10), (gx + 5, gy - gsize//2 + 20)], fill=LINE_COLOR, width=LINE_WIDTH)
            draw.arc([gx - 15, gy - gsize//2 + 35, gx + 15, gy - gsize//2 + 55], 180, 360, fill=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([gx - gsize//2 - 15, gy - gsize//6, gx - gsize//3, gy + gsize//3], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.rectangle([gx + gsize//3, gy - gsize//6, gx + gsize//2 + 15, gy + gsize//3], outline=LINE_COLOR, width=LINE_WIDTH)

        if has_treasure:
            tx, ty = center_x + 80, center_y + 80
            draw.rectangle([tx - 40, ty, tx + 40, ty + 35], outline=LINE_COLOR, width=LINE_WIDTH)
            draw.arc([tx - 40, ty - 20, tx + 40, ty + 20], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
            for i in range(3):
                cx = tx - 20 + i * 20
                draw.ellipse([cx - 8, ty - 10, cx + 8, ty + 6], outline=LINE_COLOR, width=LINE_WIDTH)

        if has_action:
            for i in range(5):
                y = center_y - 30 + i * 15
                draw.line([(30, y), (80, y)], fill=LINE_COLOR, width=2)

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
# TIER 2: POLLINATIONS.AI (Free, No Account)
# =============================================================================

def generate_pollinations(prompt: str, width: int = 512, height: int = 512, timeout: int = 60) -> Optional[bytes]:
    """
    Generate AI art using Pollinations.ai.
    FREE. No account. No token. No credit card.

    Just HTTP GET with URL-encoded prompt.
    """
    config = load_config()
    poll_cfg = config.get("pollinations", {})
    safety = config.get("safety", {})

    base_url = poll_cfg.get("url", "https://image.pollinations.ai/prompt/")

    # Add child-safe suffix
    safe_prompt = prompt + safety.get("style_suffix", "")

    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(safe_prompt)

    # Build URL with parameters
    url = f"{base_url}{encoded_prompt}?width={width}&height={height}&nologo=true"

    try:
        print(f"   🌸 Pollinations.ai generating...")
        print(f"   📡 URL: {url[:80]}...")

        req = urllib.request.Request(url, headers={
            "User-Agent": "JohnnyStoryMaker/1.0 (Educational; Children's Book)"
        })

        with urllib.request.urlopen(req, timeout=timeout) as response:
            image_data = response.read()

            # Verify we got an image (not an error page)
            if len(image_data) < 1000:
                print(f"   ⚠️  Response too small, might be an error")
                return None

            print(f"   ✅ Got {len(image_data)} bytes")
            return image_data

    except urllib.error.URLError as e:
        print(f"   ⚠️  Network error: {e}")
        return None
    except Exception as e:
        print(f"   ⚠️  Pollinations error: {e}")
        return None


# =============================================================================
# TIER 3: HUGGING FACE (Free with Account)
# =============================================================================

def generate_huggingface(prompt: str, timeout: int = 120) -> Optional[bytes]:
    """
    Generate AI art using Hugging Face Inference API.
    FREE with account (rate limited).

    Needs: HF_TOKEN environment variable or config file.
    """
    config = load_config()
    hf_cfg = config.get("huggingface", {})
    safety = config.get("safety", {})

    # Get token from config or environment
    token = hf_cfg.get("token") or os.environ.get("HF_TOKEN", "")

    if not token:
        print("   ⚠️  No Hugging Face token found!")
        print("   💡 Set HF_TOKEN env var or run: johnny-config --set-hf-token YOUR_TOKEN")
        return None

    model = hf_cfg.get("model", "stabilityai/stable-diffusion-xl-base-1.0")
    api_base = hf_cfg.get("api_url", "https://api-inference.huggingface.co/models/")
    api_url = f"{api_base}{model}"

    # Add child-safe suffix
    safe_prompt = prompt + safety.get("style_suffix", "")

    payload = {
        "inputs": safe_prompt,
        "parameters": {
            "negative_prompt": safety.get("negative_prompt", ""),
        }
    }

    try:
        print(f"   🤗 Hugging Face generating...")
        print(f"   📡 Model: {model}")

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        with urllib.request.urlopen(req, timeout=timeout) as response:
            image_data = response.read()

            # Check if it's JSON error response
            if image_data.startswith(b'{'):
                error = json.loads(image_data)
                if "error" in error:
                    print(f"   ⚠️  HF API error: {error['error']}")
                    if "loading" in str(error.get("error", "")).lower():
                        print("   💡 Model is loading, try again in 20 seconds...")
                    return None

            print(f"   ✅ Got {len(image_data)} bytes")
            return image_data

    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("   ⚠️  Invalid HF token!")
        elif e.code == 429:
            print("   ⚠️  Rate limited! Wait a bit and try again.")
        elif e.code == 503:
            print("   ⚠️  Model is loading. Try again in 20 seconds.")
        else:
            print(f"   ⚠️  HTTP error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"   ⚠️  Hugging Face error: {e}")
        return None


# =============================================================================
# TIER 3: AI-COLORING (Pollinations + Edge Detection)
# =============================================================================

def convert_to_coloring_page(image_data: bytes) -> Optional[bytes]:
    """
    Convert a color image to black-and-white line art.
    Uses edge detection to create outlines Johnny can color!

    AI art → Edge detection → Coloring page
    Best of both worlds!
    """
    try:
        from PIL import Image, ImageFilter, ImageOps
        import io

        config = load_config()
        ai_cfg = config.get("ai_coloring", {})

        # Load the image
        img = Image.open(io.BytesIO(image_data))

        # Convert to grayscale
        gray = img.convert("L")

        # Apply edge detection based on method
        method = ai_cfg.get("edge_method", "canny")

        if method == "contour":
            # Simple contour detection
            edges = gray.filter(ImageFilter.CONTOUR)
        elif method == "sobel":
            # Sobel edge detection (approximation using PIL)
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edges = edges.filter(ImageFilter.SMOOTH)
        else:
            # Default: Enhanced edge detection for coloring
            # Apply multiple filters for clean lines
            edges = gray.filter(ImageFilter.FIND_EDGES)
            edges = edges.filter(ImageFilter.MaxFilter(3))
            edges = ImageOps.autocontrast(edges)

        # Invert if needed (white background, black lines)
        if ai_cfg.get("invert", True):
            edges = ImageOps.invert(edges)

        # Increase contrast for cleaner lines
        edges = ImageOps.autocontrast(edges, cutoff=10)

        # Convert back to RGB (for PNG)
        edges = edges.convert("RGB")

        # Save to bytes
        buf = io.BytesIO()
        edges.save(buf, format="PNG")
        return buf.getvalue()

    except ImportError:
        print("   ⚠️  Pillow not installed for edge detection")
        return None
    except Exception as e:
        print(f"   ⚠️  Edge detection error: {e}")
        return None


def generate_ai_coloring(prompt: str, title: str = "", width: int = 512, height: int = 512) -> Optional[bytes]:
    """
    Generate AI art and convert to coloring page outlines.

    1. Get beautiful AI art from Pollinations
    2. Convert to black-and-white outlines
    3. Johnny gets Pixar-quality scenes to color!
    """
    print("   🎨 AI-COLORING: Getting AI art → Converting to outlines...")

    # First get the AI art
    ai_art = generate_pollinations(prompt, width, height)

    if not ai_art:
        print("   ⚠️  Couldn't get AI art, falling back to basic coloring")
        return generate_coloring_page(prompt, title)

    # Convert to coloring page
    print("   🖍️  Converting to coloring page outlines...")
    coloring_page = convert_to_coloring_page(ai_art)

    if coloring_page:
        print("   ✅ AI coloring page ready!")
        return coloring_page
    else:
        print("   ⚠️  Conversion failed, returning color art")
        return ai_art


# =============================================================================
# UNIFIED GENERATOR — Pick the Right Tier
# =============================================================================

def generate_art(prompt: str, title: str = "", mode: str = None) -> Optional[bytes]:
    """
    Generate art using the configured mode.

    Modes:
        - coloring: Local line art (no network)
        - pollinations: Free AI art (no account)
        - ai-coloring: AI art converted to outlines (NEW!)
        - huggingface: Free AI art (needs token)
        - auto: Try best available
    """
    if mode is None:
        mode = get_art_mode()

    print(f"\n🎨 ART MODE: {mode.upper()}")

    if mode == "coloring":
        return generate_coloring_page(prompt, title)

    elif mode == "pollinations":
        result = generate_pollinations(prompt)
        if result:
            return result
        print("   ↩️  Falling back to coloring mode...")
        return generate_coloring_page(prompt, title)

    elif mode == "ai-coloring":
        # AI art converted to coloring page outlines!
        result = generate_ai_coloring(prompt, title)
        if result:
            return result
        print("   ↩️  Falling back to basic coloring mode...")
        return generate_coloring_page(prompt, title)

    elif mode == "huggingface":
        result = generate_huggingface(prompt)
        if result:
            return result
        print("   ↩️  Falling back to pollinations...")
        result = generate_pollinations(prompt)
        if result:
            return result
        print("   ↩️  Falling back to coloring mode...")
        return generate_coloring_page(prompt, title)

    elif mode == "auto":
        # Try best available
        config = load_config()

        # If HF token exists, try HF first
        if config.get("huggingface", {}).get("token"):
            result = generate_huggingface(prompt)
            if result:
                return result

        # Try pollinations
        result = generate_pollinations(prompt)
        if result:
            return result

        # Fall back to coloring
        return generate_coloring_page(prompt, title)

    else:
        print(f"   ⚠️  Unknown mode: {mode}, using coloring")
        return generate_coloring_page(prompt, title)


# =============================================================================
# CLI CONFIG TOOL
# =============================================================================

def main():
    """CLI tool for managing Johnny's art config."""
    import argparse

    parser = argparse.ArgumentParser(
        description="🎨 Johnny's Art Config — Manage your free image generation"
    )
    parser.add_argument("--show", action="store_true", help="Show current config")
    parser.add_argument("--mode", choices=["coloring", "pollinations", "huggingface"],
                       help="Set art mode")
    parser.add_argument("--set-hf-token", type=str, metavar="TOKEN",
                       help="Set Hugging Face token")
    parser.add_argument("--test", type=str, metavar="PROMPT",
                       help="Test art generation with a prompt")
    parser.add_argument("--reset", action="store_true", help="Reset to defaults")

    args = parser.parse_args()

    if args.reset:
        save_config(DEFAULT_CONFIG)
        print("✅ Config reset to defaults")
        print(f"   📁 {CONFIG_FILE}")
        return

    if args.mode:
        set_art_mode(args.mode)
        print(f"✅ Art mode set to: {args.mode}")
        return

    if args.set_hf_token:
        set_hf_token(args.set_hf_token)
        print("✅ Hugging Face token saved")
        print("   Art mode automatically set to: huggingface")
        return

    if args.test:
        print(f"\n🧪 Testing art generation...")
        print(f"   Prompt: {args.test}")
        result = generate_art(args.test, "Test")
        if result:
            output = Path.home() / ".helix" / "test-art.png"
            with open(output, "wb") as f:
                f.write(result)
            print(f"\n✅ Test successful!")
            print(f"   📁 {output}")
        else:
            print("\n❌ Test failed")
        return

    # Default: show config
    config = load_config()
    print("\n🎨 JOHNNY'S ART CONFIG")
    print("=" * 50)
    print(f"\n📁 Config file: {CONFIG_FILE}")
    print(f"\n🎯 Current mode: {config.get('art_mode', 'coloring').upper()}")
    print(f"\n📊 Available modes:")
    print(f"   1. coloring     — Line art for crayons (offline)")
    print(f"   2. pollinations — AI art, no account needed")
    print(f"   3. huggingface  — AI art, needs free account")

    hf_token = config.get("huggingface", {}).get("token", "")
    if hf_token:
        print(f"\n🤗 HF Token: {'*' * 8}...{hf_token[-4:]}")
    else:
        print(f"\n🤗 HF Token: (not set)")

    print(f"\n💡 Commands:")
    print(f"   --mode coloring      Switch to coloring book")
    print(f"   --mode pollinations  Switch to Pollinations.ai")
    print(f"   --mode huggingface   Switch to Hugging Face")
    print(f"   --set-hf-token XXX   Set your HF token")
    print(f"   --test 'dragon'      Test art generation")
    print()


if __name__ == "__main__":
    main()
