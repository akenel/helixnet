#!/usr/bin/env python3
"""
🎨 JOHNNY'S STORY SERVER — Click to Art Book
=============================================
A tiny server that receives story data from johnny-clicks.html
and generates art using THREE TIERS OF FREE IMAGE GENERATION:

    1. COLORING BOOK - Line art for crayons (offline, default)
    2. POLLINATIONS.AI - AI art, no account needed
    3. HUGGING FACE - AI art with free account (rate limited)

ALL FREE. NO CREDIT CARD. EVER.

Usage:
    python johnny-server.py                    # Start server (default: coloring)
    python johnny-server.py --mode pollinations # Use AI art
    python johnny-server.py --mode huggingface  # Use HF (needs token)

Then open johnny-clicks.html in browser!

Authors: Angel & Leo
December 2025 — The 98% deserve free AI art
"""

import json
import argparse
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import base64

# Import our story generator
import sys
import importlib.util
sys.path.insert(0, str(Path(__file__).parent))

# We'll import the Story class and coloring generator
johnny_story = None

# Global art mode (set via CLI, can be overridden per request)
DEFAULT_ART_MODE = "coloring"

def load_johnny_story():
    """Dynamically load johnny-story module (hyphen in name needs special handling)."""
    global johnny_story
    if johnny_story is None:
        spec = importlib.util.spec_from_file_location(
            "johnny_story",
            Path(__file__).parent / "johnny-story.py"
        )
        johnny_story = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(johnny_story)
    return johnny_story

class JohnnyHandler(SimpleHTTPRequestHandler):
    """Handle requests for Johnny's story builder."""

    def __init__(self, *args, **kwargs):
        # Serve from the helix-pod directory
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Handle story generation request."""
        if self.path == '/generate':
            self.handle_generate()
        else:
            self.send_error(404, 'Not Found')

    def handle_generate(self):
        """Generate art book from story data."""
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())

            # Get art mode from request or use server default
            art_mode = data.get('art_mode', DEFAULT_ART_MODE)

            print(f"\n📖 Generating story: {data.get('title', 'Untitled')}")
            print(f"   Author: {data.get('author', 'Johnny')}")
            print(f"   Hero: {data['answers'].get('hero', '?')}")
            print(f"   🎨 Art mode: {art_mode.upper()}")

            # Load the story module
            js = load_johnny_story()

            # Create story object
            story = js.Story(data.get('title', "Johnny's Adventure"))
            story.author = data.get('author', 'Johnny')
            story.answers = data.get('answers', {})

            # Generate scenes
            story.generate_scenes()
            story.status = 'complete'

            # Generate art using the selected mode
            story.generate_all_art(mode=art_mode)

            # Save story
            saved_path = story.save()
            print(f"   💾 Saved: {saved_path}")

            # Export HTML
            html_path = story.export_html()
            print(f"   🌐 HTML: {html_path}")

            # Auto-open the coloring book!
            import subprocess
            subprocess.Popen(['xdg-open', str(html_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Prepare response with image data
            images = []
            for scene in story.scenes:
                if scene.get('image_base64'):
                    images.append({
                        'number': scene['number'],
                        'title': scene['title'],
                        'image': scene['image_base64']
                    })

            mode_names = {
                'coloring': 'coloring pages',
                'pollinations': 'AI art images',
                'ai-coloring': 'AI coloring pages',
                'huggingface': 'HF AI art images',
                'auto': 'art images'
            }
            response = {
                'ok': True,
                'title': story.title,
                'author': story.author,
                'art_mode': art_mode,
                'html_path': str(html_path),
                'saved_path': str(saved_path),
                'images': images,
                'message': f"Created {len(images)} {mode_names.get(art_mode, 'images')}!"
            }

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

            print(f"   ✅ Done! {len(images)} pages generated.\n")

        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'ok': False,
                'error': str(e)
            }).encode())

    def log_message(self, format, *args):
        """Quieter logging."""
        if 'POST' in args[0] or 'error' in format.lower():
            print(f"   {args[0]}")


def main():
    global DEFAULT_ART_MODE

    parser = argparse.ArgumentParser(
        description="🎨 JOHNNY'S STORY SERVER — Click to Art Book\n\n"
                    "THREE TIERS OF FREE ART:\n"
                    "  coloring     - Line art for crayons (offline)\n"
                    "  pollinations - AI art, no account needed\n"
                    "  huggingface  - AI art with free account\n"
                    "  auto         - Try best available",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--port', type=int, default=7791, help='Port to run on')
    parser.add_argument('--mode', type=str, default='coloring',
                       choices=['coloring', 'pollinations', 'ai-coloring', 'huggingface', 'auto'],
                       help='Default art mode (default: coloring)')
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser")
    args = parser.parse_args()

    # Set the global default mode
    DEFAULT_ART_MODE = args.mode

    mode_descriptions = {
        'coloring': '🖍️  COLORING BOOK (line art for crayons)',
        'pollinations': '🌸 POLLINATIONS.AI (AI art, no account)',
        'ai-coloring': '🎨 AI-COLORING (AI art → outlines, best of both!)',
        'huggingface': '🤗 HUGGING FACE (AI art, needs token)',
        'auto': '🔄 AUTO (best available)'
    }

    print(f"""
    🎨 JOHNNY'S STORY SERVER
    ════════════════════════════════════════

    Server running at: http://localhost:{args.port}
    Story builder at:  http://localhost:{args.port}/johnny-clicks.html

    🎯 Art mode: {mode_descriptions.get(args.mode, args.mode)}

    ALL FREE. NO CREDIT CARD. EVER.

    Johnny clicks pictures → Server makes art!

    Press Ctrl+C to stop.
    """)

    # Open browser
    if not args.no_browser:
        webbrowser.open(f'http://localhost:{args.port}/johnny-clicks.html')

    # Start server
    server = HTTPServer(('localhost', args.port), JohnnyHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Bye!")
        server.shutdown()


if __name__ == '__main__':
    main()
