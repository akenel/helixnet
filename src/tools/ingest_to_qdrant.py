#!/usr/bin/env python3
# python3 src/tools/ingest_to_qdrant.py <service-name> <log-file>
#
# Description:
# This script reads a container log file, generates a vector embedding using
# an Ollama model, and upserts the vector and log text into a Qdrant collection.
#
# Environment Variables (MUST be set):
# OLLAMA_ADDR: URL for the Ollama service (e.g., http://ollama:11434)
# QDRANT_URL: URL for the Qdrant service (e.g., http://qdrant:6333)
#
# Example Usage:
# OLLAMA_ADDR=http://ollama:11434 QDRANT_URL=http://qdrant:6333 \
# python3 src/tools/ingest_to_qdrant.py helix /tmp/helix_logs/app.log
# ----------------------------------------------------------------------
import sys
import os
import json
import requests
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

# --- Configuration ---
# Use environment variables for service discovery/endpoints
try:
    OLLAMA_ADDR = os.environ['OLLAMA_ADDR']
    QDRANT_URL = os.environ['QDRANT_URL']
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'embeddinggemma')
except KeyError as e:
    print(f"Error: Missing required environment variable {e}")
    sys.exit(1)

# Ensure required command-line arguments are provided
if len(sys.argv) != 3:
    print("Usage: python3 src/tools/ingest_to_qdrant.py <service-name> <log-file>")
    sys.exit(1)

SERVICE_NAME = sys.argv[1]
LOG_FILE_PATH = sys.argv[2]
COLLECTION_NAME = f"helix_{SERVICE_NAME}"


def get_embedding(text: str) -> list[float]:
    """Calls Ollama's /api/embed endpoint to get a vector embedding."""
    url = f"{OLLAMA_ADDR}/api/embed"
    print(f"-> Requesting embedding from Ollama ({EMBEDDING_MODEL})...")
    
    payload = {"model": EMBEDDING_MODEL, "input": text}
    
    try:
        r = requests.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json().get("embedding")
        if data:
            print("-> Embedding received.")
            return data
        else:
            raise ValueError("Ollama response did not contain an embedding.")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama at {OLLAMA_ADDR}: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error processing Ollama response: {e}")
        sys.exit(1)


def upsert_to_qdrant(vector: list[float], text: str):
    """Initializes Qdrant client, ensures collection exists, and upserts the data."""
    print(f"-> Connecting to Qdrant at {QDRANT_URL}...")
    
    # Use a single client instance
    qdrant_client = QdrantClient(url=QDRANT_URL)
    
    vector_size = len(vector)
    
    # 1. Check/Create Collection (Idempotent)
    collections = [c.name for c in qdrant_client.get_collections().collections]
    
    if COLLECTION_NAME not in collections:
        print(f"-> Creating collection '{COLLECTION_NAME}' (Size: {vector_size}, Distance: Cosine)...")
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME, 
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
    else:
        print(f"-> Collection '{COLLECTION_NAME}' already exists.")

    # 2. Prepare Data and Upsert
    # Use a unique ID based on the content (hash of the log text) for idempotency
    # and tracking across runs.
    unique_id = int(hash(text) % (2**63 - 1)) # Python hash is stable within a process run
    
    payload = {
        "service": SERVICE_NAME, 
        "logfile": LOG_FILE_PATH,
        "text": text # WARNING: If logs are very large, this can hit Qdrant payload limits.
    }
    
    print(f"-> Upserting vector data with ID: {unique_id}...")
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[{
            "id": unique_id,
            "vector": vector,
            "payload": payload
        }]
    ).wait() # Wait for confirmation of successful upsert

    print(f"✅ Indexed {SERVICE_NAME} log into Qdrant collection '{COLLECTION_NAME}'.")


# --- Main Execution Flow ---
def main():
    try:
        # Read the entire log file content
        log_text = Path(LOG_FILE_PATH).read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"Error: Log file not found at {LOG_FILE_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading log file: {e}")
        sys.exit(1)
        
    # 1. Get Embedding
    vector = get_embedding(log_text)

    # 2. Upsert to Qdrant
    upsert_to_qdrant(vector, log_text)

if __name__ == "__main__":
    main()