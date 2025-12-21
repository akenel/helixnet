#!/usr/bin/env python3
"""
📖 JOHNNY'S STORY SCAFFOLD — Dream It, Build It, Ship It
=========================================================
A 5-year-old doesn't need to be a storyteller.
He needs a SCAFFOLD that asks the right questions.
Then he paints the answers.

Syd Field + Campbell + Gene, simplified for Johnny.

Usage:
    python johnny-story.py                    # Interactive mode
    python johnny-story.py --title "My Story" # Start with a title
    python johnny-story.py --load story.json  # Continue a story

Authors: Angel & Tig
December 2025 — For Johnny, for Holly, for the castle in the sky
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

STORIES_DIR = Path.home() / ".helix" / "stories"
STORIES_DIR.mkdir(parents=True, exist_ok=True)

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

    def to_dict(self):
        return {
            "title": self.title,
            "author": self.author,
            "created": self.created,
            "answers": self.answers,
            "scenes": self.scenes,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        story = cls(data.get("title", "My Story"))
        story.author = data.get("author", "Johnny")
        story.created = data.get("created", datetime.now().isoformat())
        story.answers = data.get("answers", {})
        story.scenes = data.get("scenes", [])
        story.status = data.get("status", "drafting")
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
    </style>
</head>
<body>
    <div class="book">
        <div class="cover">
            <h1>📖 {self.title}</h1>
            <p class="author">Written by {self.author}</p>
        </div>
"""
        for scene in self.scenes:
            html += f"""
        <div class="scene">
            <div class="scene-number">{scene['number']}</div>
            <h2>{scene['title']}</h2>
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

    # Save it
    saved_path = story.save()
    print(f"💾 Story saved to: {saved_path}")

    # Export HTML
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
        description="📖 JOHNNY'S STORY SCAFFOLD — Dream It, Build It, Ship It"
    )
    parser.add_argument("--title", type=str, help="Story title")
    parser.add_argument("--load", type=str, help="Load existing story JSON")
    parser.add_argument("--list", action="store_true", help="List saved stories")

    args = parser.parse_args()

    if args.list:
        print("\n📚 JOHNNY'S LIBRARY\n")
        stories = list(STORIES_DIR.glob("*.json"))
        if stories:
            for s in sorted(stories, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
                print(f"   📖 {s.name}")
        else:
            print("   (No stories yet! Let's make one!)")
        print(f"\n   Stories live in: {STORIES_DIR}\n")
        return

    if args.load:
        story = Story.load(args.load)
        story.print_story()
        return

    # Run interactive scaffold
    run_scaffold(args.title)


if __name__ == "__main__":
    main()
