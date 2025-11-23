#!/usr/bin/env python3
# Minimal DebLLM worker: receives /ingest JSON, summarizes with Ollama, gets embedding,
# stores raw log to MinIO (optional), stores embedding+summary to Qdrant and Postgres.

import os, json, time
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import psycopg2  # optional, or use sqlite if postgres not available

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
POSTGRES_DSN = os.environ.get("POSTGRES_DSN", "dbname=helix_db user=helix_user password=helix_pass host=postgres")
MODEL = os.environ.get("OLLAMA_MODEL", "tinyllama:latest")

# Quick helper to call generate
def ollama_generate(prompt, model=MODEL):
    url = f"{OLLAMA_URL}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    return r.json().get("response") or r.text

# Quick helper to get embedding (if server supports /api/embed)
def ollama_embed(text, model=MODEL):
    url = f"{OLLAMA_URL}/api/embed"
    payload = {"model": model, "input": text}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("embedding")

# store to qdrant
def upsert_qdrant(collection, point_id, vector, payload):
    url = f"{QDRANT_URL}/collections/{collection}/points?wait=true"
    data = {"points":[{"id": point_id, "vector": vector, "payload": payload}]}
    r = requests.put(url, json=data, timeout=30)
    r.raise_for_status()

# store event in Postgres
def store_event(conn, container, summary, severity, qid):
    cur = conn.cursor()
    cur.execute("INSERT INTO deb_events (container, summary, severity, qid, created_at) VALUES (%s,%s,%s,%s,now())",
                (container, summary, severity, qid))
    conn.commit()
    cur.close()

class Handler(BaseHTTPRequestHandler):
    def _respond(self, code=200, body="ok"):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"result":body}).encode())

    def do_POST(self):
        if self.path != "/ingest":
            self._respond(404, "not found"); return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        obj = json.loads(raw.decode())
        container = obj.get("container","unknown")
        logs = obj.get("logs","")
        # very naive: if "ERROR" or repeated exceptions -> high severity
        severity = "info"
        if "ERROR" in logs or "Traceback" in logs or "Exception" in logs:
            severity = "error"

        # generate a short diagnosis
        prompt = f"Summarize the following container logs for {container}. If there are errors, explain probable cause and steps to debug:\n\n{logs}\n\nSUMMARY:"
        try:
            summary = ollama_generate(prompt)
        except Exception as e:
            summary = f"(ollama failed: {e})"

        # embedding
        try:
            vector = ollama_embed(summary)
        except Exception:
            vector = None

        qid = f"{container}-{int(time.time())}"
        payload = {"container": container, "summary": summary, "severity": severity, "ts": int(time.time())}
        if vector:
            upsert_qdrant("deb_events", qid, vector, payload)

        # store to Postgres (best-effort)
        try:
            conn = psycopg2.connect(POSTGRES_DSN)
            store_event(conn, container, summary, severity, qid)
            conn.close()
        except Exception as e:
            print("postgres store failed:", e)

        self._respond(200, {"qid": qid, "summary": summary})

def run():
    httpd = HTTPServer(('0.0.0.0', 5001), Handler)
    print("debllm worker listening on :5001")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
