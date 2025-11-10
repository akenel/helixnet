#!/bin/sh
set -e
# /home/angel/repos/helixnet/compose/celery/beat-entrypoint.sh
echo "Inside helixnet/compose/celery/beat-entrypoint.sh...."
# Ensure the beat data directory exists and is writable
mkdir -p /app/beat-data
echo "🏗️  ◾ 🚢 ◾ 💦 Inside helixnet/compose/celery/beat-entrypoint.sh...."
chown -R 1003:1003 /app/beat-data
exec "$@"
