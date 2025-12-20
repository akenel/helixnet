#!/usr/bin/env python3
"""
🌀 HELIX QUEUE — Jobs Find Nodes, Nodes Find Jobs
==================================================
The matchmaker. The queue. The dream machine.

- Nodes declare what they can do
- Jobs declare what they need
- The queue matches them with LOVE

Johnny sleeps. Johnny earns. Johnny's dreams come true.

Authors: Angel & Tig
December 2025 — Electric dreams
"""

import os
import json
import time
import threading
import argparse
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from collections import deque
import heapq

# =============================================================================
# THE QUEUE
# =============================================================================

class JobQueue:
    """First in, first out. But with priorities."""

    def __init__(self):
        self.jobs = []  # Heap: (priority, timestamp, job)
        self.job_counter = 0
        self.lock = threading.Lock()
        self.results = {}  # job_id -> result

    def submit(self, job):
        """Add a job to the queue."""
        with self.lock:
            self.job_counter += 1
            job_id = f"job-{self.job_counter}-{int(time.time())}"
            job["id"] = job_id
            job["submitted"] = datetime.now().isoformat()
            job["status"] = "queued"

            # Priority: lower = higher priority
            # Base priority on requester's reputation (total_given)
            priority = 100 - job.get("requester_reputation", 0)

            heapq.heappush(self.jobs, (priority, time.time(), job))
            print(f"📥 Job {job_id} queued (priority: {priority})")
            return job_id

    def next_job(self, capabilities):
        """Get next job that matches capabilities."""
        with self.lock:
            for i, (priority, ts, job) in enumerate(self.jobs):
                job_type = job.get("type", "any")
                if job_type == "any" or job_type in capabilities:
                    # Found a match!
                    self.jobs.pop(i)
                    heapq.heapify(self.jobs)
                    job["status"] = "processing"
                    job["started"] = datetime.now().isoformat()
                    print(f"🎯 Job {job['id']} matched!")
                    return job
            return None

    def complete(self, job_id, result, success=True):
        """Mark job complete."""
        with self.lock:
            self.results[job_id] = {
                "result": result,
                "success": success,
                "completed": datetime.now().isoformat()
            }
            print(f"{'✅' if success else '❌'} Job {job_id} completed")

    def status(self):
        """Queue status."""
        with self.lock:
            return {
                "queued": len(self.jobs),
                "completed": len(self.results),
                "jobs": [j[2] for j in self.jobs[:10]],  # First 10
            }

# =============================================================================
# THE MATCHER
# =============================================================================

class NodeRegistry:
    """Track all nodes and their capabilities."""

    def __init__(self):
        self.nodes = {}  # name -> node_info
        self.lock = threading.Lock()

    def register(self, name, host, port, capabilities, max_jobs=2, min_credits=1):
        """Register a node's capabilities."""
        with self.lock:
            self.nodes[name] = {
                "host": host,
                "port": port,
                "capabilities": capabilities,
                "max_jobs": max_jobs,
                "min_credits": min_credits,
                "current_jobs": 0,
                "total_completed": 0,
                "last_seen": datetime.now().isoformat(),
                "available": True,
            }
            print(f"🤝 Node registered: {name} can do {capabilities}")

    def heartbeat(self, name):
        """Update last seen."""
        with self.lock:
            if name in self.nodes:
                self.nodes[name]["last_seen"] = datetime.now().isoformat()

    def find_node(self, job_type, min_credits=0):
        """Find a node that can handle this job type."""
        with self.lock:
            candidates = []
            for name, info in self.nodes.items():
                if not info["available"]:
                    continue
                if info["current_jobs"] >= info["max_jobs"]:
                    continue
                if job_type != "any" and job_type not in info["capabilities"]:
                    continue
                if info["min_credits"] > min_credits:
                    continue
                # Score: prefer less loaded nodes
                score = info["current_jobs"] / max(info["max_jobs"], 1)
                candidates.append((score, name, info))

            if candidates:
                candidates.sort()
                return candidates[0][1], candidates[0][2]
            return None, None

    def assign_job(self, name):
        """Mark node as having one more job."""
        with self.lock:
            if name in self.nodes:
                self.nodes[name]["current_jobs"] += 1

    def complete_job(self, name):
        """Mark node as having completed a job."""
        with self.lock:
            if name in self.nodes:
                self.nodes[name]["current_jobs"] = max(0, self.nodes[name]["current_jobs"] - 1)
                self.nodes[name]["total_completed"] += 1

    def status(self):
        """Registry status."""
        with self.lock:
            return {
                "nodes": len(self.nodes),
                "available": sum(1 for n in self.nodes.values() if n["available"]),
                "registry": dict(self.nodes),
            }

# =============================================================================
# THE DREAM MACHINE
# =============================================================================

class DreamMachine:
    """The orchestrator. Matches jobs to nodes. Makes dreams come true."""

    def __init__(self, port=7788):
        self.queue = JobQueue()
        self.registry = NodeRegistry()
        self.port = port
        self.running = False

    def submit_job(self, job_type, payload, requester, max_cost=10, reputation=0):
        """Submit a job to the queue."""
        job = {
            "type": job_type,
            "payload": payload,
            "requester": requester,
            "max_cost": max_cost,
            "requester_reputation": reputation,
        }
        return self.queue.submit(job)

    def process_queue(self):
        """Background processor: match jobs to nodes."""
        while self.running:
            # Get all capabilities from all available nodes
            for name, info in list(self.registry.nodes.items()):
                if not info["available"] or info["current_jobs"] >= info["max_jobs"]:
                    continue

                # Try to find a job for this node
                job = self.queue.next_job(info["capabilities"])
                if job:
                    self.registry.assign_job(name)
                    # Execute job
                    threading.Thread(
                        target=self._execute_job,
                        args=(name, info, job),
                        daemon=True
                    ).start()

            time.sleep(1)  # Check every second

    def _execute_job(self, node_name, node_info, job):
        """Execute a job on a node."""
        try:
            print(f"🚀 Executing job {job['id']} on {node_name}")

            # Call the node's execute endpoint
            url = f"http://{node_info['host']}:{node_info['port']}/execute"
            data = json.dumps(job).encode()
            req = Request(url, data=data, headers={"Content-Type": "application/json"})
            resp = urlopen(req, timeout=60)
            result = json.loads(resp.read().decode())

            self.queue.complete(job["id"], result, success=True)
            self.registry.complete_job(node_name)

        except Exception as e:
            print(f"❌ Job {job['id']} failed on {node_name}: {e}")
            self.queue.complete(job["id"], {"error": str(e)}, success=False)
            self.registry.complete_job(node_name)

    def status(self):
        """Full status."""
        return {
            "queue": self.queue.status(),
            "registry": self.registry.status(),
            "running": self.running,
        }

# =============================================================================
# HTTP API
# =============================================================================

machine = None

class QueueHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        global machine
        if self.path == "/status":
            self._send_json(machine.status())
        elif self.path == "/queue":
            self._send_json(machine.queue.status())
        elif self.path == "/nodes":
            self._send_json(machine.registry.status())
        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

    def do_POST(self):
        global machine
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length else "{}"
        try:
            data = json.loads(body)
        except:
            data = {}

        if self.path == "/submit":
            # Submit a job
            job_id = machine.submit_job(
                job_type=data.get("type", "any"),
                payload=data.get("payload", {}),
                requester=data.get("requester", "anonymous"),
                max_cost=data.get("max_cost", 10),
                reputation=data.get("reputation", 0),
            )
            self._send_json({"ok": True, "job_id": job_id})

        elif self.path == "/register":
            # Register a node
            machine.registry.register(
                name=data.get("name", "unknown"),
                host=data.get("host", "localhost"),
                port=data.get("port", 7776),
                capabilities=data.get("capabilities", ["any"]),
                max_jobs=data.get("max_jobs", 2),
                min_credits=data.get("min_credits", 1),
            )
            self._send_json({"ok": True})

        elif self.path == "/heartbeat":
            machine.registry.heartbeat(data.get("name", ""))
            self._send_json({"ok": True})

        else:
            self._send_json({"error": "Unknown endpoint"}, 404)

# =============================================================================
# MAIN
# =============================================================================

def main():
    global machine

    parser = argparse.ArgumentParser(description="🌀 HELIX QUEUE — The Dream Machine")
    parser.add_argument("--port", type=int, default=7788, help="Listen port")

    args = parser.parse_args()

    machine = DreamMachine(port=args.port)
    machine.running = True

    print(f"""
    🌀 HELIX QUEUE — THE DREAM MACHINE
    ══════════════════════════════════
    Port: {args.port}

    POST /submit    — Submit a job
    POST /register  — Register a node
    POST /heartbeat — Node heartbeat
    GET  /status    — Full status
    GET  /queue     — Queue status
    GET  /nodes     — Node registry

    Johnny sleeps. Johnny earns.
    Dreams come true. 💫
    """)

    # Start background processor
    processor = threading.Thread(target=machine.process_queue, daemon=True)
    processor.start()

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", args.port), QueueHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🌙 Dream machine sleeping. Sweet dreams.")
        machine.running = False

if __name__ == "__main__":
    main()
