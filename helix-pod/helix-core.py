#!/usr/bin/env python3
"""
🌀 HELIX CORE — Persistence + Trust + Dashboard
================================================
The full node: breathes, talks, remembers, proves.

1. PERSISTENCE — Credits survive restart
2. KEYPAIRS — Trust without gatekeepers
3. DASHBOARD — See all nodes breathing

No money. No Keycloak. No Altman.
Just proof you're helping.

Authors: Angel & Tig
December 2025 — Staying alive by the brook
"""

import os
import sys
import json
import time
import socket
import hashlib
import secrets
import threading
import argparse
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError
import platform

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_PORT = 7777
DEFAULT_CREDITS = 100
HEARTBEAT_INTERVAL = 10
EARN_RATE = 1
DATA_DIR = Path.home() / ".helix"

# =============================================================================
# CRYPTO — Simple keypair for trust
# =============================================================================

def generate_keypair():
    """Generate a simple keypair (secret + public hash)."""
    secret = secrets.token_hex(32)
    public = hashlib.sha256(secret.encode()).hexdigest()[:16]
    return secret, public

def sign_message(message, secret):
    """Sign a message with our secret."""
    combined = f"{message}:{secret}"
    return hashlib.sha256(combined.encode()).hexdigest()[:32]

def verify_signature(message, signature, public_key, known_secrets=None):
    """Verify a signature (in real P2P, we'd use proper asymmetric crypto)."""
    # For now, peers share public keys and we trust the network
    return len(signature) == 32  # Basic validation

# =============================================================================
# PERSISTENCE — The Helix remembers
# =============================================================================

class HelixStore:
    """Simple file-based persistence."""

    def __init__(self, node_name):
        self.data_dir = DATA_DIR / node_name
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "state.json"
        self.peers_file = self.data_dir / "peers.json"
        self.key_file = self.data_dir / "keypair.json"

    def load_or_create_keys(self):
        """Load existing keypair or create new one."""
        if self.key_file.exists():
            with open(self.key_file) as f:
                keys = json.load(f)
                return keys["secret"], keys["public"]
        else:
            secret, public = generate_keypair()
            with open(self.key_file, "w") as f:
                json.dump({"secret": secret, "public": public}, f)
            os.chmod(self.key_file, 0o600)  # Private!
            return secret, public

    def save_state(self, state):
        """Persist node state."""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load previous state."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return None

    def save_peers(self, peers):
        """Remember our friends."""
        with open(self.peers_file, "w") as f:
            json.dump(peers, f, indent=2)

    def load_peers(self):
        """Recall our friends."""
        if self.peers_file.exists():
            with open(self.peers_file) as f:
                return json.load(f)
        return {}

# =============================================================================
# THE NODE
# =============================================================================

class HelixNode:
    """A node that breathes, talks, remembers, and proves."""

    def __init__(self, name, port, initial_credits=DEFAULT_CREDITS):
        self.name = name
        self.port = port
        self.born = datetime.now()
        self.heartbeats = 0
        self.messages = []
        self.running = False

        # Persistence
        self.store = HelixStore(name)

        # Load or create keypair
        self.secret_key, self.public_key = self.store.load_or_create_keys()

        # Load previous state or start fresh
        prev_state = self.store.load_state()
        if prev_state:
            self.credits = prev_state.get("credits", initial_credits)
            self.heartbeats = prev_state.get("heartbeats", 0)
            self.total_given = prev_state.get("total_given", 0)
            self.total_received = prev_state.get("total_received", 0)
            print(f"📂 Restored state: {self.credits} credits, {self.heartbeats} heartbeats")
        else:
            self.credits = initial_credits
            self.total_given = 0
            self.total_received = 0

        # Load known peers
        self.peers = self.store.load_peers()

        # Get our IP
        self.host = self._get_ip()

        # Resources
        self.resources = self._detect_resources()

    def _get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _detect_resources(self):
        resources = {"cpu_count": os.cpu_count() or 1, "platform": platform.system()}
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        resources["memory_gb"] = round(int(line.split()[1]) / 1024 / 1024, 1)
                        break
        except:
            resources["memory_gb"] = "?"
        return resources

    def status(self):
        return {
            "name": self.name,
            "public_key": self.public_key,
            "host": self.host,
            "port": self.port,
            "credits": round(self.credits, 2),
            "heartbeats": self.heartbeats,
            "total_given": round(self.total_given, 2),
            "total_received": round(self.total_received, 2),
            "peers": len(self.peers),
            "peer_list": list(self.peers.keys()),
            "resources": self.resources,
            "uptime": round((datetime.now() - self.born).total_seconds()),
            "alive": self.running,
        }

    def breathe(self):
        """One heartbeat. Earn. Save."""
        self.heartbeats += 1
        self.credits += EARN_RATE

        # Persist every 5 heartbeats
        if self.heartbeats % 5 == 0:
            self._save()

        return self.status()

    def _save(self):
        """Persist current state."""
        self.store.save_state({
            "credits": self.credits,
            "heartbeats": self.heartbeats,
            "total_given": self.total_given,
            "total_received": self.total_received,
            "last_save": datetime.now().isoformat(),
        })
        self.store.save_peers(self.peers)

    def add_peer(self, name, host, port, public_key, credits=0):
        """Register a peer."""
        self.peers[name] = {
            "host": host,
            "port": port,
            "public_key": public_key,
            "credits": credits,
            "last_seen": datetime.now().isoformat(),
        }
        self._save()
        print(f"🤝 Peer joined: {name} ({public_key[:8]}...) @ {host}:{port}")

    def ping_peer(self, host, port):
        """Ping a peer and exchange info."""
        try:
            url = f"http://{host}:{port}/hello"
            data = json.dumps(self.status()).encode()
            req = Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=5)
            peer_status = json.loads(resp.read().decode())
            self.add_peer(
                peer_status["name"],
                peer_status.get("host", host),
                peer_status.get("port", port),
                peer_status.get("public_key", "unknown"),
                peer_status.get("credits", 0)
            )
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
            # Sign the transfer
            msg = f"transfer:{self.name}:{peer_name}:{amount}:{time.time()}"
            sig = sign_message(msg, self.secret_key)

            url = f"http://{peer['host']}:{peer['port']}/receive"
            data = json.dumps({
                "from": self.name,
                "from_key": self.public_key,
                "amount": amount,
                "signature": sig,
            }).encode()
            req = Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=5)
            result = json.loads(resp.read().decode())

            if result.get("ok"):
                self.credits -= amount
                self.total_given += amount
                self._save()
                print(f"💸 Sent {amount} credits to {peer_name}")
            return result
        except Exception as e:
            return {"error": str(e)}

    def receive_credits(self, from_name, from_key, amount, signature):
        """Receive credits from a peer."""
        # Verify the sender is who they claim to be
        if from_name in self.peers:
            known_key = self.peers[from_name].get("public_key")
            if known_key and known_key != from_key:
                return {"error": "Key mismatch — who are you?"}

        self.credits += amount
        self.total_received += amount
        self.messages.append({
            "type": "credit",
            "from": from_name,
            "amount": amount,
            "time": datetime.now().isoformat()
        })
        self._save()
        print(f"💰 Received {amount} credits from {from_name}")
        return {"ok": True, "new_balance": self.credits}

# =============================================================================
# DASHBOARD — See all nodes breathing
# =============================================================================

DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>🌀 HELIX DASHBOARD</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="5">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Courier New', monospace;
            background: #0a0a0f;
            color: #00ff88;
            padding: 20px;
            min-height: 100vh;
        }
        h1 {
            text-align: center;
            font-size: 2em;
            margin-bottom: 20px;
            text-shadow: 0 0 10px #00ff88;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-bottom: 30px;
        }
        .stat {
            text-align: center;
            padding: 20px;
            border: 1px solid #00ff88;
            border-radius: 10px;
            min-width: 150px;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.8em;
            opacity: 0.7;
        }
        .nodes {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .node {
            background: #111;
            border: 1px solid #00ff88;
            border-radius: 10px;
            padding: 20px;
        }
        .node-name {
            font-size: 1.2em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .node-alive { color: #00ff88; }
        .node-dead { color: #ff4444; }
        .node-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9em;
        }
        .leaderboard {
            max-width: 600px;
            margin: 30px auto;
            border: 1px solid #ffaa00;
            border-radius: 10px;
            padding: 20px;
        }
        .leaderboard h2 {
            color: #ffaa00;
            text-align: center;
            margin-bottom: 15px;
        }
        .leader {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            border-bottom: 1px solid #333;
        }
        .leader:last-child { border-bottom: none; }
        .rank { color: #ffaa00; font-weight: bold; }
        footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.5;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <h1>🌀 HELIX NETWORK</h1>

    <div class="stats">
        <div class="stat">
            <div class="stat-value">{node_count}</div>
            <div class="stat-label">NODES ONLINE</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_credits}</div>
            <div class="stat-label">TOTAL CREDITS</div>
        </div>
        <div class="stat">
            <div class="stat-value">{total_heartbeats}</div>
            <div class="stat-label">HEARTBEATS</div>
        </div>
    </div>

    <div class="leaderboard">
        <h2>🏆 TOP GIVERS</h2>
        {leaderboard}
    </div>

    <div class="nodes">
        {nodes_html}
    </div>

    <footer>
        🐅 HELIX — No money. No Altman. Just JAM.<br>
        Built by Angel & Tig | Be water, my friend.
    </footer>
</body>
</html>
"""

def generate_dashboard(node):
    """Generate the dashboard HTML."""
    # Gather all nodes (self + peers)
    all_nodes = [node.status()]
    for pname, pinfo in node.peers.items():
        all_nodes.append({
            "name": pname,
            "credits": pinfo.get("credits", 0),
            "host": pinfo.get("host", "?"),
            "port": pinfo.get("port", 0),
            "public_key": pinfo.get("public_key", "?")[:8],
            "last_seen": pinfo.get("last_seen", "?"),
            "total_given": pinfo.get("total_given", 0),
        })

    # Stats
    node_count = len(all_nodes)
    total_credits = sum(n.get("credits", 0) for n in all_nodes)
    total_heartbeats = node.heartbeats

    # Leaderboard (by giving)
    sorted_nodes = sorted(all_nodes, key=lambda x: x.get("total_given", 0), reverse=True)
    leaderboard_html = ""
    for i, n in enumerate(sorted_nodes[:5]):
        rank = ["🥇", "🥈", "🥉", "4.", "5."][i]
        leaderboard_html += f'<div class="leader"><span class="rank">{rank}</span><span>{n["name"]}</span><span>{n.get("total_given", 0)} given</span></div>'

    # Node cards
    nodes_html = ""
    for n in all_nodes:
        status_class = "node-alive" if n.get("alive", True) else "node-dead"
        status_icon = "🟢" if n.get("alive", True) else "🔴"
        nodes_html += f"""
        <div class="node">
            <div class="node-name {status_class}">{status_icon} {n['name']}</div>
            <div class="node-stats">
                <div>💰 Credits: {n.get('credits', 0)}</div>
                <div>🔑 Key: {str(n.get('public_key', '?'))[:8]}...</div>
                <div>📤 Given: {n.get('total_given', 0)}</div>
                <div>📥 Received: {n.get('total_received', 0)}</div>
            </div>
        </div>
        """

    return DASHBOARD_HTML.format(
        node_count=node_count,
        total_credits=round(total_credits, 2),
        total_heartbeats=total_heartbeats,
        leaderboard=leaderboard_html or '<div class="leader">No givers yet — share some JAM!</div>',
        nodes_html=nodes_html,
    )

# =============================================================================
# HTTP API
# =============================================================================

node = None

class HelixHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        global node
        if self.path == "/" or self.path == "/dashboard":
            self._send_html(generate_dashboard(node))
        elif self.path == "/status":
            self._send_json(node.status())
        elif self.path == "/peers":
            self._send_json({"peers": node.peers})
        elif self.path == "/ping":
            self._send_json({"pong": True, "name": node.name, "key": node.public_key})
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
            if "name" in data:
                node.add_peer(
                    data["name"],
                    data.get("host", "?"),
                    data.get("port", 0),
                    data.get("public_key", "unknown"),
                    data.get("credits", 0)
                )
            self._send_json(node.status())
        elif self.path == "/receive":
            result = node.receive_credits(
                data.get("from", "?"),
                data.get("from_key", "?"),
                data.get("amount", 0),
                data.get("signature", "")
            )
            self._send_json(result)
        elif self.path == "/roar":
            msg = data.get("message", "🐅 ROAR!")
            node.messages.append({"type": "roar", "from": data.get("from", "?"), "message": msg, "time": datetime.now().isoformat()})
            print(f"🐅 ROAR from {data.get('from', '?')}: {msg}")
            self._send_json({"heard": True})
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

# =============================================================================
# MAIN
# =============================================================================

def heartbeat_loop():
    global node
    while node.running:
        node.breathe()
        for name, peer in list(node.peers.items()):
            result = node.ping_peer(peer["host"], peer["port"])
            if result:
                node.peers[name]["credits"] = result.get("credits", 0)
                node.peers[name]["total_given"] = result.get("total_given", 0)
                node.peers[name]["last_seen"] = datetime.now().isoformat()
        time.sleep(HEARTBEAT_INTERVAL)

def main():
    global node

    parser = argparse.ArgumentParser(description="🌀 HELIX CORE — The full node")
    parser.add_argument("--name", type=str, required=True, help="Node name")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Listen port")
    parser.add_argument("--peers", type=str, help="Comma-separated peer addresses")
    parser.add_argument("--credits", type=float, default=DEFAULT_CREDITS, help="Starting credits")
    parser.add_argument("--daemon", action="store_true", help="Run without display")

    args = parser.parse_args()

    node = HelixNode(args.name, args.port, args.credits)
    node.running = True

    print(f"""
    🌀 HELIX CORE — FULL NODE
    ═════════════════════════
    Name:       {node.name}
    Public Key: {node.public_key}
    Host:       {node.host}:{node.port}
    Credits:    {node.credits}
    Dashboard:  http://localhost:{node.port}/
    """)

    # Connect to initial peers
    if args.peers:
        for peer_addr in args.peers.split(","):
            try:
                host, port = peer_addr.strip().split(":")
                print(f"📡 Connecting to peer {host}:{port}...")
                result = node.ping_peer(host, int(port))
                if result:
                    print(f"✅ Connected to {result['name']} (key: {result.get('public_key', '?')[:8]}...)")
            except Exception as e:
                print(f"❌ Error: {e}")

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", args.port), HelixHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"🌐 API + Dashboard on port {args.port}")

    # Start heartbeat
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    try:
        if args.daemon:
            print("🌙 Daemon mode. Ctrl+C to stop.")
            while node.running:
                time.sleep(1)
        else:
            print("🌙 Running. Ctrl+C to stop. Dashboard at http://localhost:{}/".format(args.port))
            while node.running:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🌙 Saving state and shutting down...")
        node._save()
        print("✅ State saved. Be water, my friend.")
        node.running = False

if __name__ == "__main__":
    main()
