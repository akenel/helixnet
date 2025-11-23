#!/bin/sh
set -e

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to start..."
     for i in $(seq 1 20); do printf "."; sleep 1; done; echo

echo "🪣 Creating bucket: ${MINIO_BUCKET}"
mc alias set myminio http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
mc mb -p myminio/${MINIO_BUCKET} || echo "Bucket ${MINIO_BUCKET} already exists"
mc policy set public myminio/${MINIO_BUCKET}
