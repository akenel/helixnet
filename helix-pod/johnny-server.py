#!/usr/bin/env python3
"""
🎨 JOHNNY'S STORY SERVER — Click to Coloring Book
==================================================
A tiny server that receives story data from johnny-clicks.html
and generates coloring book pages.

Usage:
    python johnny-server.py          # Start server on port 7791
    python johnny-server.py --port 8080

Then open johnny-clicks.html in browser!

Authors: Angel & Tig
December 2025 — No typing required
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
        """Generate a coloring book from story data."""
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())

            print(f"\n📖 Generating story: {data.get('title', 'Untitled')}")
            print(f"   Author: {data.get('author', 'Johnny')}")
            print(f"   Hero: {data['answers'].get('hero', '?')}")

            # Load the story module
            js = load_johnny_story()

            # Create story object
            story = js.Story(data.get('title', "Johnny's Adventure"))
            story.author = data.get('author', 'Johnny')
            story.answers = data.get('answers', {})

            # Generate scenes
            story.generate_scenes()
            story.status = 'complete'

            # Generate coloring book art
            story.generate_all_art(mode='coloring')

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

            response = {
                'ok': True,
                'title': story.title,
                'author': story.author,
                'html_path': str(html_path),
                'saved_path': str(saved_path),
                'images': images,
                'message': f"Created {len(images)} coloring pages!"
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
    parser = argparse.ArgumentParser(
        description="🎨 JOHNNY'S STORY SERVER — Click to Coloring Book"
    )
    parser.add_argument('--port', type=int, default=7791, help='Port to run on')
    parser.add_argument('--no-browser', action='store_true', help="Don't open browser")
    args = parser.parse_args()

    print(f"""
    🎨 JOHNNY'S STORY SERVER
    ════════════════════════════════════════

    Server running at: http://localhost:{args.port}
    Story builder at:  http://localhost:{args.port}/johnny-clicks.html

    Johnny clicks pictures → Server makes coloring book!

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
