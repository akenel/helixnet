#!/usr/bin/env python3
"""
🌀 HELIX MESH — Nodes That Talk
===============================
Two nodes. One network. They find each other.
They share. They breathe together.

No central server. Just peers.
Like water finding water.

Usage:
    python helix-mesh.py --name NAME --port PORT [--peers PEER1,PEER2]

Authors: Angel & Tig
December 2025 — Two nodes, one dream
"""

import os
import sys
import json
import time
import socket
import threading
import argparse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError
import platform

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_PORT = 7777
DEFAULT_CREDITS = 100
HEARTBEAT_INTERVAL = 10  # seconds
EARN_RATE = 1  # credits per heartbeat when contributing

# =============================================================================
# THE NODE
# =============================================================================

class HelixNode:
    """A node that breathes AND talks."""

    def __init__(self, name, port, initial_credits=DEFAULT_CREDITS):
        self.name = name
        self.port = port
        self.credits = initial_credits
        self.born = datetime.now()
        self.heartbeats = 0
        self.peers = {}  # {name: {host, port, credits, last_seen}}
        self.messages = []  # incoming messages
        self.running = False

        # Get our IP
        self.host = self._get_ip()

        # Resources
        self.resources = {
            "cpu_count": os.cpu_count() or 1,
            "platform": platform.system(),
        }
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        self.resources["memory_gb"] = round(int(line.split()[1]) / 1024 / 1024, 1)
                        break
        except:
            self.resources["memory_gb"] = "?"

    def _get_ip(self):
        """Get our reachable IP."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def status(self):
        """Current state as dict."""
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "credits": round(self.credits, 2),
            "heartbeats": self.heartbeats,
            "peers": len(self.peers),
            "peer_list": list(self.peers.keys()),
            "resources": self.resources,
            "uptime": round((datetime.now() - self.born).total_seconds()),
            "alive": self.running,
        }

    def breathe(self):
        """One heartbeat."""
        self.heartbeats += 1
        self.credits += EARN_RATE
        return self.status()

    def add_peer(self, name, host, port, credits=0):
        """Register a peer."""
        self.peers[name] = {
            "host": host,
            "port": port,
            "credits": credits,
            "last_seen": datetime.now().isoformat(),
        }
        print(f"🤝 Peer joined: {name} @ {host}:{port}")

    def ping_peer(self, host, port):
        """Ping a peer and exchange info."""
        try:
            url = f"http://{host}:{port}/hello"
            data = json.dumps(self.status()).encode()
            req = Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=5)
            peer_status = json.loads(resp.read().decode())
            self.add_peer(peer_status["name"], peer_status["host"], peer_status["port"], peer_status["credits"])
            return peer_status
        except Exception as e:
            return None

    def send_credits(self, peer_name, amount):
        """Transfer credits to a peer."""
        if peer_name not in self.peers:
            return {"error": "Unknown peer"}
        if self.credits < amount:
            return {"error": "Insufficient credits"}

        peer = self.peers[peer_name]
        try:
            url = f"http://{peer['host']}:{peer['port']}/receive"
            data = json.dumps({"from": self.name, "amount": amount}).encode()
            req = Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=5)
            result = json.loads(resp.read().decode())
            if result.get("ok"):
                self.credits -= amount
                print(f"💸 Sent {amount} credits to {peer_name}")
            return result
        except Exception as e:
            return {"error": str(e)}

    def receive_credits(self, from_name, amount):
        """Receive credits from a peer."""
        self.credits += amount
        self.messages.append({"type": "credit", "from": from_name, "amount": amount, "time": datetime.now().isoformat()})
        print(f"💰 Received {amount} credits from {from_name}")
        return {"ok": True, "new_balance": self.credits}


# =============================================================================
# HTTP API
# =============================================================================

node = None  # Global node reference

class HelixHandler(BaseHTTPRequestHandler):
    """Simple HTTP API for node communication."""

    def log_message(self, format, *args):
        pass  # Quiet logs

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        global node
        if self.path == "/status":
            self._send_json(node.status())
        elif self.path == "/peers":
            self._send_json({"peers": node.peers})
        elif self.path == "/ping":
            self._send_json({"pong": True, "name": node.name})
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

        if self.path == "/hello":
            # Peer introduction
            if "name" in data:
                node.add_peer(data["name"], data.get("host", "?"), data.get("port", 0), data.get("credits", 0))
            self._send_json(node.status())

        elif self.path == "/receive":
            # Receive credits
            result = node.receive_credits(data.get("from", "?"), data.get("amount", 0))
            self._send_json(result)

        elif self.path == "/roar":
            # Tiger roar — broadcast message
            msg = data.get("message", "🐅 ROAR!")
            node.messages.append({"type": "roar", "from": data.get("from", "?"), "message": msg, "time": datetime.now().isoformat()})
            print(f"🐅 ROAR from {data.get('from', '?')}: {msg}")
            self._send_json({"heard": True})

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)


# =============================================================================
# MAIN LOOP
# =============================================================================

def heartbeat_loop():
    """Background heartbeat and peer check."""
    global node
    while node.running:
        node.breathe()
        # Ping all known peers
        for name, peer in list(node.peers.items()):
            result = node.ping_peer(peer["host"], peer["port"])
            if result:
                node.peers[name]["credits"] = result.get("credits", 0)
                node.peers[name]["last_seen"] = datetime.now().isoformat()
        time.sleep(HEARTBEAT_INTERVAL)


def display_loop():
    """Show status periodically."""
    global node
    while node.running:
        status = node.status()
        print(f"\033[2J\033[H", end="")  # Clear screen
        print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🌀 HELIX MESH NODE: {status['name']:<42} ║
╠══════════════════════════════════════════════════════════════════╣
║  📍 {status['host']}:{status['port']:<54} ║
║  💰 Credits: {status['credits']:<10} 💓 Heartbeats: {status['heartbeats']:<18} ║
║  🖥️  CPU: {status['resources']['cpu_count']} cores   🧠 Memory: {str(status['resources'].get('memory_gb', '?')) + ' GB':<22} ║
╠══════════════════════════════════════════════════════════════════╣
║  🤝 PEERS ({status['peers']}):                                                    ║""")

        for pname, pinfo in node.peers.items():
            print(f"║     └─ {pname}: {pinfo['credits']} credits @ {pinfo['host']}:{pinfo['port']:<16} ║")

        if not node.peers:
            print(f"║     └─ (no peers yet — waiting for friends)                      ║")

        print(f"""╠══════════════════════════════════════════════════════════════════╣
║  📨 Recent Messages:                                              ║""")
        for msg in node.messages[-3:]:
            print(f"║     └─ {msg.get('type', '?')}: {str(msg)[:50]:<50} ║")
        if not node.messages:
            print(f"║     └─ (quiet... waiting for roars)                             ║")

        print(f"""╚══════════════════════════════════════════════════════════════════╝

   🐅 Press Ctrl+C to stop. Be water, my friend.
""")
        time.sleep(5)


def main():
    global node

    parser = argparse.ArgumentParser(description="🌀 HELIX MESH — Nodes That Talk")
    parser.add_argument("--name", type=str, required=True, help="Node name")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Listen port")
    parser.add_argument("--peers", type=str, help="Comma-separated peer addresses (host:port)")
    parser.add_argument("--credits", type=float, default=DEFAULT_CREDITS, help="Starting credits")
    parser.add_argument("--daemon", action="store_true", help="Run without display (background)")

    args = parser.parse_args()

    # Create node
    node = HelixNode(args.name, args.port, args.credits)
    node.running = True

    print(f"""
    🌀 HELIX MESH NODE STARTING
    ═══════════════════════════
    Name: {node.name}
    Host: {node.host}
    Port: {node.port}
    Credits: {node.credits}
    """)

    # Connect to initial peers
    if args.peers:
        for peer_addr in args.peers.split(","):
            try:
                host, port = peer_addr.strip().split(":")
                print(f"📡 Connecting to peer {host}:{port}...")
                result = node.ping_peer(host, int(port))
                if result:
                    print(f"✅ Connected to {result['name']}")
                else:
                    print(f"⚠️  Could not reach {peer_addr}")
            except Exception as e:
                print(f"❌ Error connecting to {peer_addr}: {e}")

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", args.port), HelixHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"🌐 API listening on port {args.port}")

    # Start heartbeat
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    # Run display or daemon mode
    try:
        if args.daemon:
            print("🌙 Running in daemon mode. Ctrl+C to stop.")
            while node.running:
                time.sleep(1)
        else:
            display_loop()
    except KeyboardInterrupt:
        print("\n\n🌙 Node going to sleep. Be water, my friend.")
        node.running = False


if __name__ == "__main__":
    main()
