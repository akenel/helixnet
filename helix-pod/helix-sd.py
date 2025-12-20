#!/usr/bin/env python3
"""
🎨 HELIX SD — Stable Diffusion for the People
==============================================
Dragons riding skateboards. For Johnny. For free.

Two modes:
1. LOCAL GPU — Uses diffusers library (when you have an RTX)
2. CLOUD BRIDGE — HuggingFace Inference API (free, for testing)

This node registers with the queue as capable of "stable-diffusion" jobs.
When a job comes in, it generates the image and returns it.

Usage:
    python helix-sd.py --name sd-tiger --port 7790
    python helix-sd.py --name sd-tiger --port 7790 --hf-token YOUR_TOKEN

Authors: Angel & Tig
December 2025 — Art for the people
"""

import os
import sys
import json
import time
import base64
import hashlib
import argparse
import threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError

# =============================================================================
# CONFIGURATION
# =============================================================================

# Try multiple models - some may be rate limited or require auth
HF_MODELS = [
    "stabilityai/stable-diffusion-2-1",
    "runwayml/stable-diffusion-v1-5",
    "CompVis/stable-diffusion-v1-4",
]
HF_MODEL = HF_MODELS[0]  # Start with SD 2.1
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

OUTPUT_DIR = Path.home() / ".helix" / "sd-outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# STABLE DIFFUSION BACKENDS
# =============================================================================

class SDBackend:
    """Base class for SD backends."""

    def generate(self, prompt, negative_prompt="", steps=30, width=1024, height=1024):
        raise NotImplementedError


class MockBackend(SDBackend):
    """Mock backend for testing - generates a placeholder image."""

    def generate(self, prompt, negative_prompt="", steps=30, width=512, height=512):
        """Generate a mock image with the prompt text."""
        print(f"🎭 MOCK: Generating placeholder for: {prompt[:50]}...")

        # Create a simple PNG with prompt text using basic PNG structure
        # This is a valid minimal PNG that says "DREAM: <prompt>"
        import struct
        import zlib

        # Simple solid color image with text description in metadata
        # Purple background (#6b21a8) - 512x512
        width, height = 512, 512

        # Create raw RGB data (purple)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'  # Filter byte
            for x in range(width):
                # Create a gradient effect
                r = min(255, 107 + (x // 5))
                g = min(255, 33 + (y // 10))
                b = min(255, 168 + ((x + y) // 10))
                raw_data += bytes([r, g, b])

        # Compress
        compressed = zlib.compress(raw_data, 9)

        # Build PNG
        def png_chunk(chunk_type, data):
            chunk = chunk_type + data
            return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)

        # PNG signature
        png = b'\x89PNG\r\n\x1a\n'

        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        png += png_chunk(b'IHDR', ihdr_data)

        # tEXt chunk with prompt
        text_data = b'Description\x00HELIX DREAM: ' + prompt[:200].encode('utf-8', errors='replace')
        png += png_chunk(b'tEXt', text_data)

        # IDAT chunk
        png += png_chunk(b'IDAT', compressed)

        # IEND chunk
        png += png_chunk(b'IEND', b'')

        print(f"✅ Mock image generated ({len(png)} bytes)")
        return png


class HuggingFaceBackend(SDBackend):
    """Use HuggingFace Inference API (free, no GPU needed)."""

    def __init__(self, api_token=None):
        self.api_token = api_token or os.environ.get("HF_TOKEN", "")
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"
            print("🔑 Using HuggingFace API with token")
        else:
            print("🌐 Using HuggingFace API (no token, may be rate limited)")

    def generate(self, prompt, negative_prompt="", steps=30, width=1024, height=1024):
        """Generate image via HuggingFace API."""
        # Try each model until one works
        for model in HF_MODELS:
            api_url = f"https://api-inference.huggingface.co/models/{model}"

            # Adjust size for older models (SD 1.x works best at 512)
            if "v1-4" in model or "v1-5" in model:
                width, height = 512, 512
            elif "2-1" in model:
                width, height = 768, 768

            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": negative_prompt or "blurry, bad quality, distorted",
                    "num_inference_steps": min(steps, 50),
                    "width": width,
                    "height": height,
                }
            }

            data = json.dumps(payload).encode()
            req = Request(api_url, data=data, headers=self.headers)

            try:
                print(f"🎨 Trying {model}...")
                print(f"   Prompt: {prompt[:50]}...")
                start = time.time()
                resp = urlopen(req, timeout=120)
                image_bytes = resp.read()

                # Check if we got actual image data
                if len(image_bytes) < 1000:
                    try:
                        error = json.loads(image_bytes.decode())
                        print(f"⚠️  {model}: {error}")
                        continue
                    except:
                        pass

                elapsed = time.time() - start
                print(f"✅ Generated with {model} in {elapsed:.1f}s ({len(image_bytes)} bytes)")
                return image_bytes

            except URLError as e:
                error_msg = str(e)
                if hasattr(e, 'read'):
                    try:
                        error_body = e.read().decode()
                        if "loading" in error_body.lower():
                            print(f"⏳ {model} is loading, waiting 20s...")
                            time.sleep(20)
                            # Retry this model
                            try:
                                resp = urlopen(Request(api_url, data=data, headers=self.headers), timeout=120)
                                return resp.read()
                            except:
                                pass
                        error_msg = error_body
                    except:
                        pass
                print(f"⚠️  {model} failed: {error_msg[:100]}")
                continue

        raise RuntimeError("All models failed. Try again later or provide HF_TOKEN.")


class LocalGPUBackend(SDBackend):
    """Use local GPU with diffusers library."""

    def __init__(self):
        try:
            from diffusers import DiffusionPipeline
            import torch

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"🖥️  Loading SD model on {self.device}...")

            self.pipe = DiffusionPipeline.from_pretrained(
                "stabilityai/stable-diffusion-xl-base-1.0",
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                variant="fp16" if self.device == "cuda" else None,
            )
            self.pipe.to(self.device)
            print("✅ Model loaded!")

        except ImportError:
            raise RuntimeError("diffusers not installed. Use: pip install diffusers torch")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")

    def generate(self, prompt, negative_prompt="", steps=30, width=1024, height=1024):
        """Generate image locally."""
        import io

        print(f"🎨 Generating locally: {prompt[:50]}...")
        start = time.time()

        image = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt or "blurry, bad quality, distorted",
            num_inference_steps=steps,
            width=width,
            height=height,
        ).images[0]

        # Convert to bytes
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        elapsed = time.time() - start
        print(f"✅ Generated in {elapsed:.1f}s ({len(image_bytes)} bytes)")
        return image_bytes


# =============================================================================
# SD NODE
# =============================================================================

class SDNode:
    """Stable Diffusion node for HelixNet."""

    def __init__(self, name, port, queue_url, backend, cost=10):
        self.name = name
        self.port = port
        self.queue_url = queue_url
        self.backend = backend
        self.cost = cost  # Credits per image
        self.jobs_completed = 0
        self.running = False

    def register_with_queue(self):
        """Register as a stable-diffusion capable node."""
        if not self.queue_url:
            print("⚠️  No queue URL, running standalone")
            return

        try:
            data = json.dumps({
                "name": self.name,
                "host": "localhost",  # TODO: Get actual host
                "port": self.port,
                "capabilities": ["stable-diffusion", "image-generation"],
                "max_jobs": 1,  # One at a time
                "min_credits": self.cost,
            }).encode()

            req = Request(
                f"{self.queue_url}/register",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            resp = urlopen(req, timeout=5)
            print(f"📡 Registered with queue: {self.queue_url}")
        except Exception as e:
            print(f"⚠️  Could not register with queue: {e}")

    def generate(self, prompt, negative_prompt="", steps=30, width=1024, height=1024):
        """Generate an image."""
        # Generate
        image_bytes = self.backend.generate(prompt, negative_prompt, steps, width, height)

        # Save locally
        filename = f"{int(time.time())}-{hashlib.md5(prompt.encode()).hexdigest()[:8]}.png"
        output_path = OUTPUT_DIR / filename
        output_path.write_bytes(image_bytes)
        print(f"💾 Saved: {output_path}")

        self.jobs_completed += 1

        return {
            "ok": True,
            "image_base64": base64.b64encode(image_bytes).decode(),
            "filename": filename,
            "path": str(output_path),
            "prompt": prompt,
            "cost": self.cost,
        }

    def status(self):
        """Node status."""
        return {
            "name": self.name,
            "port": self.port,
            "backend": type(self.backend).__name__,
            "cost": self.cost,
            "jobs_completed": self.jobs_completed,
            "capabilities": ["stable-diffusion", "image-generation"],
            "output_dir": str(OUTPUT_DIR),
        }


# =============================================================================
# HTTP API
# =============================================================================

node = None

class SDHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_image(self, image_bytes):
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(image_bytes)

    def do_GET(self):
        global node
        if self.path == "/status":
            self._send_json(node.status())
        elif self.path == "/":
            # Simple dashboard
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>🎨 {node.name} — Helix SD</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ font-family: monospace; background: #1a1a2e; color: #eee; padding: 20px; }}
        h1 {{ color: #ff6b6b; }}
        .stat {{ background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>🎨 {node.name}</h1>
    <div class="stat">Backend: {type(node.backend).__name__}</div>
    <div class="stat">Cost: {node.cost} credits/image</div>
    <div class="stat">Jobs Completed: {node.jobs_completed}</div>
    <div class="stat">Output Dir: {OUTPUT_DIR}</div>
    <hr>
    <p>POST /generate — Generate an image</p>
    <p>POST /execute — Execute a queued job</p>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def do_POST(self):
        global node
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        try:
            data = json.loads(body)
        except:
            data = {}

        if self.path == "/generate":
            # Direct generation request
            try:
                result = node.generate(
                    prompt=data.get("prompt", "a beautiful sunset"),
                    negative_prompt=data.get("negative_prompt", ""),
                    steps=data.get("steps", 30),
                    width=data.get("width", 1024),
                    height=data.get("height", 1024),
                )
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        elif self.path == "/execute":
            # Job execution from queue
            try:
                job = data
                payload = job.get("payload", {})
                result = node.generate(
                    prompt=payload.get("prompt", "a beautiful sunset"),
                    negative_prompt=payload.get("negative_prompt", ""),
                    steps=payload.get("steps", 30),
                    width=payload.get("width", 1024),
                    height=payload.get("height", 1024),
                )
                result["job_id"] = job.get("id", "unknown")
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e), "job_id": data.get("id", "unknown")}, 500)

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)


# =============================================================================
# MAIN
# =============================================================================

def main():
    global node

    parser = argparse.ArgumentParser(description="🎨 HELIX SD — Stable Diffusion for the People")
    parser.add_argument("--name", type=str, default="sd-tiger", help="Node name")
    parser.add_argument("--port", type=int, default=7790, help="Listen port")
    parser.add_argument("--queue", type=str, default="", help="Queue URL (e.g., http://localhost:7788)")
    parser.add_argument("--hf-token", type=str, default="", help="HuggingFace API token")
    parser.add_argument("--local-gpu", action="store_true", help="Use local GPU instead of HF API")
    parser.add_argument("--mock", action="store_true", help="Use mock backend (for testing without API)")
    parser.add_argument("--cost", type=int, default=10, help="Credits per image")

    args = parser.parse_args()

    # Choose backend
    if args.mock:
        backend = MockBackend()
        print("🎭 Using MOCK backend (testing mode)")
    elif args.local_gpu:
        try:
            backend = LocalGPUBackend()
        except RuntimeError as e:
            print(f"❌ {e}")
            print("Falling back to HuggingFace API...")
            backend = HuggingFaceBackend(args.hf_token)
    else:
        backend = HuggingFaceBackend(args.hf_token)

    # Create node
    node = SDNode(
        name=args.name,
        port=args.port,
        queue_url=args.queue,
        backend=backend,
        cost=args.cost,
    )

    print(f"""
    🎨 HELIX SD — STABLE DIFFUSION FOR THE PEOPLE
    ═════════════════════════════════════════════
    Node: {args.name}
    Port: {args.port}
    Backend: {type(backend).__name__}
    Cost: {args.cost} credits/image
    Output: {OUTPUT_DIR}

    POST /generate  — Generate an image
    POST /execute   — Execute a queued job
    GET  /status    — Node status
    GET  /          — Dashboard

    Dragons riding skateboards. For Johnny. 🐉🛹
    """)

    # Register with queue
    node.register_with_queue()
    node.running = True

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", args.port), SDHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🎨 SD node sleeping. Dream on.")
        node.running = False


if __name__ == "__main__":
    main()
