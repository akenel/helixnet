#!/usr/bin/env python3
"""
🌀 HELIX JOBS — Execute Workflows, Spend Credits
=================================================
Call n8n, call webhooks, pay with credits.

Simple job execution:
1. Submit job with payload
2. Spend credits
3. Execute via n8n or any webhook
4. Get result

Usage:
    python helix-jobs.py --node localhost:7776 --webhook http://n8n:5678/webhook/test --payload '{"hello": "world"}' --cost 5

Authors: Angel & Tig
December 2025 — Work costs energy, energy costs credits
"""

import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import URLError

def submit_job(node_url, webhook_url, payload, cost):
    """Submit a job: spend credits, call webhook, return result."""

    print(f"🌀 HELIX JOB SUBMISSION")
    print(f"   Node: {node_url}")
    print(f"   Webhook: {webhook_url}")
    print(f"   Cost: {cost} credits")
    print(f"   Payload: {json.dumps(payload)[:50]}...")
    print()

    # Step 1: Check node balance
    try:
        status_url = f"http://{node_url}/status"
        resp = urlopen(status_url, timeout=5)
        node_status = json.loads(resp.read().decode())
        credits = node_status.get("credits", 0)
        print(f"💰 Current balance: {credits} credits")

        if credits < cost:
            print(f"❌ Insufficient credits! Need {cost}, have {credits}")
            return {"error": "Insufficient credits", "balance": credits, "required": cost}
    except Exception as e:
        print(f"❌ Cannot reach node: {e}")
        return {"error": str(e)}

    # Step 2: Deduct credits (self-spend)
    try:
        spend_url = f"http://{node_url}/receive"
        spend_data = json.dumps({
            "from": "helix-jobs",
            "from_key": "job-system",
            "amount": -cost,  # Negative = spend
            "signature": "job-execution"
        }).encode()
        req = Request(spend_url, data=spend_data, headers={"Content-Type": "application/json"})
        resp = urlopen(req, timeout=5)
        spend_result = json.loads(resp.read().decode())
        print(f"💸 Credits deducted: -{cost}")
        print(f"💰 New balance: {spend_result.get('new_balance', '?')}")
    except Exception as e:
        print(f"⚠️  Could not deduct credits: {e}")

    # Step 3: Execute webhook
    try:
        print(f"🚀 Executing webhook...")
        webhook_data = json.dumps(payload).encode()
        req = Request(webhook_url, data=webhook_data, headers={"Content-Type": "application/json"})
        resp = urlopen(req, timeout=30)
        result = resp.read().decode()
        try:
            result = json.loads(result)
        except:
            pass  # Keep as string if not JSON

        print(f"✅ Job completed!")
        print(f"📤 Result: {str(result)[:200]}")
        return {"ok": True, "result": result, "cost": cost}

    except URLError as e:
        print(f"❌ Webhook failed: {e}")
        return {"error": f"Webhook failed: {e}", "cost": cost}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e), "cost": cost}


def main():
    parser = argparse.ArgumentParser(description="🌀 HELIX JOBS — Execute workflows with credits")
    parser.add_argument("--node", type=str, default="localhost:7776", help="Helix node address")
    parser.add_argument("--webhook", type=str, required=True, help="Webhook URL to call")
    parser.add_argument("--payload", type=str, default="{}", help="JSON payload")
    parser.add_argument("--cost", type=int, default=1, help="Credits to spend")

    args = parser.parse_args()

    try:
        payload = json.loads(args.payload)
    except:
        payload = {"data": args.payload}

    result = submit_job(args.node, args.webhook, payload, args.cost)
    print()
    print("📊 FINAL RESULT:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
