#!/usr/bin/env python3
"""Upload a local file to MinIO (the artifact vault). Standalone — reads MINIO_* from env, so it
runs in any container with the minio package + MinIO env vars.
Usage: python upload_minio.py <local_file> <object_key> [content_type]
"""
import io
import os
import sys

from minio import Minio

client = Minio(
    f"{os.environ['MINIO_HOST']}:{os.environ['MINIO_PORT']}",
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
)
bucket = os.environ["MINIO_BUCKET"]
local, key = sys.argv[1], sys.argv[2]
ct = sys.argv[3] if len(sys.argv) > 3 else "image/png"

if not client.bucket_exists(bucket):
    client.make_bucket(bucket)
with open(local, "rb") as f:
    data = f.read()
client.put_object(bucket, key, io.BytesIO(data), len(data), content_type=ct)
print(f"uploaded {bucket}/{key} ({len(data)} bytes)")
