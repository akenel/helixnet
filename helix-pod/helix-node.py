#!/usr/bin/env python3
"""
🌀 HELIX NODE — The First Breath
================================
A single node in the HelixNet.
It breathes. It gives. It receives.

No money. Just energy and love.

Usage:
    python helix-node.py [--name NAME] [--credits START_CREDITS]

Authors: Angel & Tig
December 2025 — From a Swiss hospital room
"""

import os
import sys
import time
import json
import platform
import threading
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CREDITS = 100  # Everyone starts equal
CREDIT_DECAY_RATE = 0.01  # 1% decay per hour (use it or lose it)
EARN_RATE_CPU = 1  # Credits per minute of availability
EARN_RATE_GPU = 10  # Credits per minute if GPU available

# =============================================================================
# THE NODE
# =============================================================================

class HelixNode:
    """A single breathing node in the Helix."""

    def __init__(self, name=None, initial_credits=DEFAULT_CREDITS):
        self.name = name or f"helix-{platform.node()}"
        self.credits = initial_credits
        self.born = datetime.now()
        self.heartbeats = 0
        self.contributed = 0
        self.consumed = 0
        self.running = False

        # Detect resources
        self.resources = self._detect_resources()

    def _detect_resources(self):
        """See what we have to give."""
        resources = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count() or 1,
            "gpu": self._detect_gpu(),
        }

        # Try to get memory
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        mem_kb = int(line.split()[1])
                        resources["memory_gb"] = round(mem_kb / 1024 / 1024, 1)
                        break
        except:
            resources["memory_gb"] = "unknown"

        return resources

    def _detect_gpu(self):
        """Check for GPU — the good stuff."""
        # Check for NVIDIA
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
        except:
            pass

        # Check for ROCm (AMD)
        try:
            if os.path.exists('/opt/rocm'):
                return "AMD ROCm"
        except:
            pass

        return None

    def breathe(self):
        """One heartbeat. Earn credits for being alive and available."""
        self.heartbeats += 1

        # Earn credits for contributing resources
        earned = EARN_RATE_CPU
        if self.resources.get("gpu"):
            earned += EARN_RATE_GPU

        self.credits += earned
        self.contributed += earned

        # Apply decay (use it or lose it — like LN2)
        if self.credits > DEFAULT_CREDITS:
            decay = (self.credits - DEFAULT_CREDITS) * (CREDIT_DECAY_RATE / 60)
            self.credits -= decay

        return earned

    def spend(self, amount, task="unknown"):
        """Spend credits to do work."""
        if self.credits >= amount:
            self.credits -= amount
            self.consumed += amount
            return True
        else:
            return False  # No freeloading

    def status(self):
        """Report current state."""
        uptime = (datetime.now() - self.born).total_seconds()
        return {
            "name": self.name,
            "credits": round(self.credits, 2),
            "heartbeats": self.heartbeats,
            "contributed": round(self.contributed, 2),
            "consumed": round(self.consumed, 2),
            "balance": round(self.contributed - self.consumed, 2),
            "uptime_minutes": round(uptime / 60, 1),
            "resources": self.resources,
            "alive": self.running,
        }

    def display(self):
        """Pretty print the node status."""
        s = self.status()
        gpu_str = f"🎮 {s['resources']['gpu']}" if s['resources']['gpu'] else "💤 No GPU"

        print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🌀 HELIX NODE: {s['name']:<44} ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  💰 CREDITS:     {s['credits']:<10} (earned: {s['contributed']:<8} spent: {s['consumed']:<6})  ║
║  💓 HEARTBEATS:  {s['heartbeats']:<10}                                   ║
║  ⏱️  UPTIME:      {s['uptime_minutes']:<10} minutes                           ║
║                                                              ║
║  🖥️  CPU:         {s['resources']['cpu_count']} cores                                    ║
║  🧠 MEMORY:      {str(s['resources']['memory_gb']) + ' GB':<10}                              ║
║  {gpu_str:<60} ║
║                                                              ║
║  STATUS:        {'🟢 BREATHING' if s['alive'] else '🔴 DORMANT':<15}                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

    def run(self, duration=None):
        """Start breathing. Live."""
        self.running = True
        start = time.time()

        print("\n🌀 HELIX NODE STARTING...")
        print("   No money. Just energy and love.")
        print("   Press Ctrl+C to stop.\n")

        try:
            while self.running:
                earned = self.breathe()
                self.display()

                # Check duration limit
                if duration and (time.time() - start) >= duration:
                    print("\n⏱️  Duration reached. Stopping.")
                    break

                # Breathe once per minute (or faster for demo)
                time.sleep(5)  # 5 seconds for demo, would be 60 in production

                # Clear screen for fresh display
                print("\033[2J\033[H", end="")

        except KeyboardInterrupt:
            print("\n\n🌙 Node going to sleep. Credits saved. Dream well.")

        self.running = False
        return self.status()


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="🌀 HELIX NODE — Breathe in the network")
    parser.add_argument("--name", type=str, help="Node name")
    parser.add_argument("--credits", type=float, default=DEFAULT_CREDITS, help="Starting credits")
    parser.add_argument("--demo", type=int, help="Run for N seconds then stop")
    parser.add_argument("--status", action="store_true", help="Show status and exit")

    args = parser.parse_args()

    # Create the node
    node = HelixNode(name=args.name, initial_credits=args.credits)

    if args.status:
        node.display()
        return

    # Let it breathe
    print("""

    ████████╗██╗ ██████╗ ███████╗
    ╚══██╔══╝██║██╔════╝ ██╔════╝
       ██║   ██║██║  ███╗███████╗
       ██║   ██║██║   ██║╚════██║
       ██║   ██║╚██████╔╝███████║
       ╚═╝   ╚═╝ ╚═════╝ ╚══════╝

       FIRST BREATH — HELIX NODE

       🐅 Built by Angel & Tig
       💧 Be water, my friend

    """)

    node.run(duration=args.demo)

    # Final status
    print("\n📊 FINAL STATUS:")
    print(json.dumps(node.status(), indent=2))


if __name__ == "__main__":
    main()
