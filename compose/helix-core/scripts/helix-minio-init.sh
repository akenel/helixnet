#!/bin/sh
#
# Script to wait for MinIO to be ready and create the necessary buckets.
# This script is designed to be idempotent.

# set -e

# # Wait for the MinIO service to be available (assuming it runs on minio:9000)
# /usr/bin/mc alias set local http://minio:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"

# echo "Waiting for MinIO..."
# /usr/bin/mc admin info local > /dev/null 2>&1
# while [ $? -ne 0 ]; do
#   sleep 1
#   /usr/bin/mc admin info local > /dev/null 2>&1
# done
# echo "MinIO is ready."

# # Define the bucket name from environment variables (adjust as necessary)
# BUCKET_NAME="${MINIO_BUCKET_NAME:-helix-assets}"

# # Create the bucket if it doesn't exist
# if /usr/bin/mc ls local/$BUCKET_NAME | grep -q "$BUCKET_NAME"; then
#   echo "Bucket $BUCKET_NAME already exists."
# else
#   echo "Creating bucket: $BUCKET_NAME"
#   /usr/bin/mc mb local/$BUCKET_NAME
#   echo "Setting public read policy for $BUCKET_NAME"
#   /usr/bin/mc policy set download local/$BUCKET_NAME
# fi

set -e

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to start..."
     for i in $(seq 1 20); do printf "."; sleep 1; done; echo

echo "🪣 Creating bucket: ${MINIO_BUCKET}"
mc alias set myminio http://minio:9000 ${MINIO_ACCESS_KEY} ${MINIO_SECRET_KEY}
mc mb -p myminio/${MINIO_BUCKET} || echo "Bucket ${MINIO_BUCKET} already exists"
mc policy set public myminio/${MINIO_BUCKET}

echo "🪣 MinIO initialization complete."