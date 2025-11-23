#!/usr/bin/env python3
import os, time, json
import docker, requests
from datetime import datetime, timezone
from qdrant_client import QdrantClient
import psycopg2
import boto3

# ENV
OLLAMA_URL = os.environ.get("OLLAMA_API_URL","http://ollama:11434")
QDRANT_HOST = os.environ.get("QDRANT_HOST","qdrant")
POSTGRES_DSN = os.environ.get("POSTGRES_DSN","postgresql://helix_user:helix_pass@postgres:5432/helix_db")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT","minio:9000")
MINIO_ACCESS = os.environ.get("MINIO_ACCESS","minioadmin")
MINIO_SECRET = os.environ.get("MINIO_SECRET","minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET","logs")

# init clients
docker_client = docker.from_env()
qdrant = QdrantClient(host=QDRANT_HOST, prefer_grpc=False)
s3 = boto3.client("s3", endpoint_url=f"http://{MINIO_ENDPOINT}", aws_access_key_id=MINIO_ACCESS, aws_secret_access_key=MINIO_SECRET)
conn = psycopg2.connect(POSTGRES_DSN)
conn.autocommit = True

# helper: persist raw logs to MinIO
def store_raw_log(container, identifier, content):
    key = f"{container}/{identifier}.log"
    try:
        s3.put_object(Bucket=MINIO_BUCKET, Key=key, Body=content.encode("utf-8"))
    except Exception:
        # create bucket then retry
        try:
            s3.create_bucket(Bucket=MINIO_BUCKET)
            s3.put_object(Bucket=MINIO_BUCKET, Key=key, Body=content.encode("utf-8"))
        except Exception as e:
            print("S3 write failed:", e)
            return None
    return f"s3://{MINIO_BUCKET}/{key}"

# helper: basic summarization call to Ollama
def summarize_text(text):
    prompt = {
      "model": "llama2-3b",  # or small model you have
      "prompt": f"Summarize the following logs, list top 3 probable causes and 3 pragmatic remediation steps. Keep terse, numbered. \\n\\n{text}"
    }
    # Ollama http API example (adjust to your local api)
    resp = requests.post(f"{OLLAMA_URL}/v1/generate", json=prompt, timeout=30)
    if resp.ok:
        return resp.json().get("completion","").strip()
    return "ERROR: no response"

# detect function (very simple rules to start)
ERROR_TRIGGERS = ["ERROR", "Exception", "Traceback", "panic", "failed", "CRITICAL"]

def is_interesting(line):
    u = line.upper()
    return any(t in u for t in ERROR_TRIGGERS)

def write_event(container, raw_s3, summary, suggestion):
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO debllm_events(container, raw_s3, summary, suggestion, created_at, status)
      VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
    """, (container, raw_s3, summary, suggestion, datetime.now(timezone.utc), "new"))
    try:
        id = cur.fetchone()[0]
        cur.close()
        return id
    except Exception:
        return None

def main():
    # tail last 100 lines for every running container once at startup, then watch new logs
    seen = set()
    for c in docker_client.containers.list():
        try:
            logs = c.logs(tail=200).decode("utf-8", errors="ignore")
            if any(is_interesting(l) for l in logs.splitlines()):
                raw_s3 = store_raw_log(c.name, int(time.time()), logs)
                summary = summarize_text(logs)
                suggestion = summary # for now same
                rid = write_event(c.name, raw_s3, summary, suggestion)
                print("Event stored:", rid)
        except Exception as e:
            print("startup inspect fail", e)
    # then follow logs streaming (simple)
    for line in docker_client.events(decode=True):
        # We get container lifecycle events - also can use logs(stream=True) per container if needed
        try:
            if line.get("Type") == "container" and "status" in line and line["status"] in ("die","kill","oom"):
                cid = line.get("Actor",{}).get("ID")
                c = docker_client.containers.get(cid)
                logs = c.logs(tail=500).decode("utf-8", errors="ignore")
                if any(is_interesting(l) for l in logs.splitlines()):
                    raw_s3 = store_raw_log(c.name, int(time.time()), logs)
                    summary = summarize_text(logs)
                    suggestion = summary
                    write_event(c.name, raw_s3, summary, suggestion)
                    print("Event written for", c.name)
        except Exception as e:
            print("event processing error", e)

if __name__ == "__main__":
    main()
