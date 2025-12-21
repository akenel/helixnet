#!/usr/bin/env python3
"""
🖍️ COLORING BOOK GENERATOR — Line Art for Johnny
=================================================
Generates simple black-and-white line art outlines
that a 5-year-old can color with crayons.

No AI needed. Just shapes, lines, and imagination.

The scaffold gives the STORY.
Johnny gives the COLOR.

Authors: Angel & Tig
December 2025 — Crayons > GPUs
"""

import math
import random
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

WIDTH = 512
HEIGHT = 512
LINE_WIDTH = 4
BACKGROUND = "white"
LINE_COLOR = "black"

# =============================================================================
# SHAPE PRIMITIVES — The Building Blocks
# =============================================================================

def draw_circle(draw, x, y, radius, fill=None):
    """Draw a circle outline."""
    draw.ellipse(
        [x - radius, y - radius, x + radius, y + radius],
        outline=LINE_COLOR,
        fill=fill,
        width=LINE_WIDTH
    )

def draw_oval(draw, x, y, rx, ry, fill=None):
    """Draw an oval/ellipse outline."""
    draw.ellipse(
        [x - rx, y - ry, x + rx, y + ry],
        outline=LINE_COLOR,
        fill=fill,
        width=LINE_WIDTH
    )

def draw_rect(draw, x, y, w, h, fill=None):
    """Draw a rectangle outline."""
    draw.rectangle(
        [x, y, x + w, y + h],
        outline=LINE_COLOR,
        fill=fill,
        width=LINE_WIDTH
    )

def draw_triangle(draw, x, y, size, direction="up"):
    """Draw a triangle outline."""
    if direction == "up":
        points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
    elif direction == "down":
        points = [(x, y + size), (x - size, y - size), (x + size, y - size)]
    elif direction == "left":
        points = [(x - size, y), (x + size, y - size), (x + size, y + size)]
    else:  # right
        points = [(x + size, y), (x - size, y - size), (x - size, y + size)]
    draw.polygon(points, outline=LINE_COLOR, width=LINE_WIDTH)

def draw_star(draw, x, y, outer_r, inner_r, points=5):
    """Draw a star outline."""
    star_points = []
    for i in range(points * 2):
        angle = math.pi / 2 + (i * math.pi / points)
        r = outer_r if i % 2 == 0 else inner_r
        px = x + r * math.cos(angle)
        py = y - r * math.sin(angle)
        star_points.append((px, py))
    draw.polygon(star_points, outline=LINE_COLOR, width=LINE_WIDTH)

def draw_heart(draw, x, y, size):
    """Draw a heart shape."""
    # Two circles for top bumps
    r = size // 3
    draw_circle(draw, x - r, y - r//2, r)
    draw_circle(draw, x + r, y - r//2, r)
    # Triangle for bottom point
    points = [
        (x - size, y),
        (x + size, y),
        (x, y + size + r)
    ]
    draw.polygon(points, outline=LINE_COLOR, width=LINE_WIDTH)

def draw_crown(draw, x, y, width, height):
    """Draw a simple crown."""
    # Base
    draw_rect(draw, x - width//2, y, width, height//3)
    # Points
    points = [
        (x - width//2, y),
        (x - width//3, y - height),
        (x, y - height//2),
        (x + width//3, y - height),
        (x + width//2, y),
    ]
    draw.line(points, fill=LINE_COLOR, width=LINE_WIDTH)

def draw_cloud(draw, x, y, size):
    """Draw a fluffy cloud."""
    # Multiple overlapping circles
    draw_circle(draw, x - size//2, y, size//2)
    draw_circle(draw, x, y - size//3, size//2)
    draw_circle(draw, x + size//2, y, size//2)
    draw_circle(draw, x, y + size//4, size//3)

def draw_sun(draw, x, y, radius):
    """Draw a sun with rays."""
    draw_circle(draw, x, y, radius)
    # Rays
    for i in range(8):
        angle = i * math.pi / 4
        x1 = x + (radius + 10) * math.cos(angle)
        y1 = y + (radius + 10) * math.sin(angle)
        x2 = x + (radius + 30) * math.cos(angle)
        y2 = y + (radius + 30) * math.sin(angle)
        draw.line([(x1, y1), (x2, y2)], fill=LINE_COLOR, width=LINE_WIDTH)

# =============================================================================
# COMPOSITE DRAWINGS — Characters & Objects
# =============================================================================

def draw_dragon(draw, x, y, size=100, on_skateboard=False):
    """Draw a friendly dragon."""
    # Body (oval)
    draw_oval(draw, x, y, size//2, size//3)

    # Head (circle)
    head_x = x + size//2
    head_y = y - size//4
    draw_circle(draw, head_x, head_y, size//4)

    # Eyes (two small circles)
    draw_circle(draw, head_x - 8, head_y - 5, 5)
    draw_circle(draw, head_x + 8, head_y - 5, 5)
    # Pupils
    draw_circle(draw, head_x - 8, head_y - 5, 2, fill=LINE_COLOR)
    draw_circle(draw, head_x + 8, head_y - 5, 2, fill=LINE_COLOR)

    # Smile
    draw.arc([head_x - 12, head_y, head_x + 12, head_y + 15], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)

    # Horns
    draw_triangle(draw, head_x - 15, head_y - size//4 - 10, 12, "up")
    draw_triangle(draw, head_x + 15, head_y - size//4 - 10, 12, "up")

    # Wings (triangles)
    draw_triangle(draw, x - size//4, y - size//3, size//3, "up")
    draw_triangle(draw, x + size//6, y - size//3, size//4, "up")

    # Tail (curved line with spikes)
    tail_points = [
        (x - size//2, y),
        (x - size//2 - 20, y + 20),
        (x - size//2 - 40, y + 10),
        (x - size//2 - 60, y + 30),
    ]
    draw.line(tail_points, fill=LINE_COLOR, width=LINE_WIDTH)
    draw_triangle(draw, x - size//2 - 60, y + 30, 10, "left")

    # Legs
    draw_oval(draw, x - size//4, y + size//3, 12, 20)
    draw_oval(draw, x + size//4, y + size//3, 12, 20)

    # Skateboard if requested
    if on_skateboard:
        draw_skateboard(draw, x, y + size//3 + 30)

def draw_skateboard(draw, x, y):
    """Draw a skateboard."""
    # Board (rounded rectangle)
    draw.rounded_rectangle(
        [x - 50, y, x + 50, y + 12],
        radius=6,
        outline=LINE_COLOR,
        width=LINE_WIDTH
    )
    # Wheels
    draw_circle(draw, x - 35, y + 20, 8)
    draw_circle(draw, x + 35, y + 20, 8)

def draw_princess(draw, x, y, size=80):
    """Draw a princess."""
    # Dress (triangle)
    draw_triangle(draw, x, y + size//4, size//2, "down")

    # Body (small oval)
    draw_oval(draw, x, y - size//6, size//6, size//4)

    # Head (circle)
    head_y = y - size//2
    draw_circle(draw, x, head_y, size//5)

    # Eyes
    draw_circle(draw, x - 8, head_y - 3, 4)
    draw_circle(draw, x + 8, head_y - 3, 4)

    # Smile
    draw.arc([x - 8, head_y + 2, x + 8, head_y + 12], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)

    # Crown
    draw_crown(draw, x, head_y - size//5 - 5, 30, 25)

    # Hair (wavy lines on sides)
    for i in range(3):
        draw.arc([x - size//4 - 10, head_y - 10 + i*15, x - size//6, head_y + 5 + i*15],
                 90, 270, fill=LINE_COLOR, width=LINE_WIDTH)
        draw.arc([x + size//6, head_y - 10 + i*15, x + size//4 + 10, head_y + 5 + i*15],
                 270, 90, fill=LINE_COLOR, width=LINE_WIDTH)

def draw_giant(draw, x, y, size=150):
    """Draw a grumpy giant."""
    # Body (big rectangle)
    draw_rect(draw, x - size//3, y - size//4, size//1.5, size//1.5)

    # Head (circle)
    head_y = y - size//2
    draw_circle(draw, x, head_y, size//4)

    # Grumpy eyebrows (angled lines)
    draw.line([(x - 20, head_y - 15), (x - 5, head_y - 5)], fill=LINE_COLOR, width=LINE_WIDTH)
    draw.line([(x + 20, head_y - 15), (x + 5, head_y - 5)], fill=LINE_COLOR, width=LINE_WIDTH)

    # Eyes (circles)
    draw_circle(draw, x - 12, head_y, 6)
    draw_circle(draw, x + 12, head_y, 6)

    # Frown
    draw.arc([x - 15, head_y + 10, x + 15, head_y + 30], 180, 360, fill=LINE_COLOR, width=LINE_WIDTH)

    # Arms (rectangles)
    draw_rect(draw, x - size//2 - 20, y - size//6, 25, size//2)
    draw_rect(draw, x + size//3 - 5, y - size//6, 25, size//2)

    # Legs
    draw_rect(draw, x - size//4, y + size//4, 25, size//3)
    draw_rect(draw, x + size//12, y + size//4, 25, size//3)

def draw_tower(draw, x, y, width=80, height=200):
    """Draw a tall tower."""
    # Main tower body
    draw_rect(draw, x - width//2, y - height, width, height)

    # Pointed roof
    points = [
        (x - width//2 - 10, y - height),
        (x, y - height - 50),
        (x + width//2 + 10, y - height),
    ]
    draw.polygon(points, outline=LINE_COLOR, width=LINE_WIDTH)

    # Window at top
    draw.arc([x - 15, y - height + 20, x + 15, y - height + 50], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
    draw_rect(draw, x - 15, y - height + 35, 30, 30)

    # More windows
    for i in range(3):
        wy = y - height + 80 + i * 50
        draw_rect(draw, x - 12, wy, 24, 30)

    # Door at bottom
    draw.arc([x - 20, y - 60, x + 20, y - 20], 0, 180, fill=LINE_COLOR, width=LINE_WIDTH)
    draw_rect(draw, x - 20, y - 40, 40, 40)

def draw_thought_bubble(draw, x, y, width=150, height=100):
    """Draw a thought bubble."""
    # Main bubble (cloud-like)
    draw_cloud(draw, x, y, width//2)
    # Small circles leading to thinker
    draw_circle(draw, x - width//3, y + height//2, 10)
    draw_circle(draw, x - width//3 - 15, y + height//2 + 20, 6)

# =============================================================================
# SCENE GENERATORS — Put It All Together
# =============================================================================

def parse_prompt(prompt):
    """Extract keywords from a prompt."""
    prompt_lower = prompt.lower()
    elements = {
        "dragon": "dragon" in prompt_lower,
        "skateboard": "skateboard" in prompt_lower,
        "princess": "princess" in prompt_lower or "holly" in prompt_lower,
        "giant": "giant" in prompt_lower,
        "tower": "tower" in prompt_lower,
        "dream": "dream" in prompt_lower or "thought" in prompt_lower,
        "happy": "happy" in prompt_lower or "celebrat" in prompt_lower or "joyful" in prompt_lower,
        "flying": "flying" in prompt_lower,
        "action": "action" in prompt_lower or "dynamic" in prompt_lower,
        "sun": "sun" in prompt_lower or "sunshine" in prompt_lower,
        "stars": "star" in prompt_lower,
    }
    return elements

def generate_coloring_page(prompt, title=""):
    """Generate a coloring book page from a prompt."""
    # Create image
    img = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(img)

    # Parse what's in the scene
    elements = parse_prompt(prompt)

    # Draw border
    draw_rect(draw, 10, 10, WIDTH - 20, HEIGHT - 20)

    # Add title at top if provided
    if title:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((WIDTH//2, 30), title, fill=LINE_COLOR, font=font, anchor="mm")

    # Determine scene composition based on elements
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 + 30

    # Background elements
    if elements["sun"] or elements["happy"]:
        draw_sun(draw, WIDTH - 60, 80, 30)

    if elements["stars"]:
        for _ in range(5):
            sx = random.randint(50, WIDTH - 50)
            sy = random.randint(50, 150)
            draw_star(draw, sx, sy, 15, 7)

    if elements["tower"]:
        draw_tower(draw, WIDTH - 80, HEIGHT - 50)
        center_x = WIDTH // 3  # Shift other elements left

    if elements["dream"]:
        draw_thought_bubble(draw, center_x + 50, center_y - 100)

    # Main characters
    if elements["dragon"]:
        if elements["flying"]:
            draw_dragon(draw, center_x, center_y - 50, 100, elements["skateboard"])
        else:
            draw_dragon(draw, center_x, center_y + 50, 100, elements["skateboard"])

    if elements["princess"]:
        if elements["tower"]:
            # Princess in tower window
            draw_princess(draw, WIDTH - 80, HEIGHT - 200, 50)
        elif elements["dragon"] and elements["flying"]:
            # Princess riding dragon
            draw_princess(draw, center_x + 30, center_y - 80, 50)
        else:
            draw_princess(draw, center_x + 100, center_y + 50, 70)

    if elements["giant"]:
        draw_giant(draw, WIDTH - 120, center_y + 30, 120)

    # Action effects
    if elements["action"]:
        # Speed lines
        for i in range(5):
            y = center_y - 30 + i * 15
            draw.line([(30, y), (80, y)], fill=LINE_COLOR, width=2)

    if elements["happy"]:
        # Confetti / celebration marks
        for _ in range(8):
            cx = random.randint(50, WIDTH - 50)
            cy = random.randint(50, HEIGHT - 100)
            draw_star(draw, cx, cy, 8, 4, 5)

    return img

# =============================================================================
# MAIN — CLI Interface
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="🖍️ COLORING BOOK GENERATOR — Line Art for Johnny"
    )
    parser.add_argument("prompt", nargs="?", default="a friendly dragon on a skateboard",
                       help="What to draw")
    parser.add_argument("--title", type=str, default="", help="Title for the page")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--show", action="store_true", help="Open image after generating")

    args = parser.parse_args()

    print(f"🖍️  COLORING BOOK GENERATOR")
    print(f"   Prompt: {args.prompt}")

    img = generate_coloring_page(args.prompt, args.title)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path.home() / ".helix" / "coloring" / "page.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

    img.save(output_path)
    print(f"   ✅ Saved: {output_path}")

    if args.show:
        img.show()

    return img

if __name__ == "__main__":
    main()
