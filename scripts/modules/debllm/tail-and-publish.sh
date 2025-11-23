#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# containers to watch (change to what you need)
CONTAINERS=("traefik")
#
# where summarizer listens (internal in compose)
SUMMARIZER_ENDPOINT="${SUMMARIZER_ENDPOINT:-http://debllm-worker:5001/ingest}"

# When run on host, this will loop forever and post JSON events.
while true; do
  for c in "${CONTAINERS[@]}"; do
    # get last 200 lines from container logs
    lines=$(docker logs --since 5s "$c" 2>/dev/null || true)
    [[ -z "$lines" ]] && continue
    payload=$(jq -Rn --arg c "$c" --arg l "$lines" \
      '{container: $c, timestamp: (now|tostring), logs: $l}')
    # send to worker (fire & forget)
    curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$SUMMARIZER_ENDPOINT" || true
  done
  sleep 5
done
