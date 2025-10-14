#!/bin/bash

# ======================================================================
# 🚀 HelixNet Job Lifecycle Test (Create & Retrieve)
# Uses robust curl commands to separate HTTP status code from response body.
# ======================================================================

# --- ⚙️ Configuration ---
BASE_URL="https://helix.local/api/v1"
JOB_ENDPOINT="${BASE_URL}/job"

# Placeholder for your real token (Please ensure this token is fresh!)
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZDA1ODdjYy1jNjRlLTQ2ZGQtYTcyNC0yNTU5MzA2OGY3YjciLCJzY29wZXMiOlsidXNlciJdLCJpYXQiOjE3NjA0NDMzMjIsImV4cCI6MTc2MDQ0NDIyMiwidHlwZSI6ImFjY2VzcyIsImp0aSI6IjU2ODY2N2MxLTRmZmMtNDUxZC1hZDFmLWI2Yjc4Mzg4YmY5YiJ9.7Y9T8aodabZvNufNh7voSa8YX2dfEvdiqsRuwiGmF-Q"

JOB_ID=""

echo " "
echo "=========================================================="
echo " 🛠️ Testing Job Creation and Retrieval (Using Robust Shell)"
echo "=========================================================="
echo " "


# --- 1️⃣ Create Job (POST /job) ---
echo "➡️ 1/2 | Creating new job via POST ${JOB_ENDPOINT}..."
JOB_PAYLOAD='{
  "input_data": {
    "format": "json",
    "name": "Smoke Test Job $(date +%s)",
    "source_url": "http://data.com/file.csv"
  },
  "task_name": "app.tasks.process_data"
}'
# --- CN FIX: Capture status and body separately and use -s (silent)
CREATE_RESPONSE_BODY=$(curl -k -s -X POST "${JOB_ENDPOINT}" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "$JOB_PAYLOAD" \
  -w "%{http_code}")
# HTTP Status code is the last 3 characters of the output
CREATE_STATUS=${CREATE_RESPONSE_BODY: -3}
CREATE_BODY=${CREATE_RESPONSE_BODY:0:$((${#CREATE_RESPONSE_BODY}-3))}


if [ "$CREATE_STATUS" == "202" ]; then
  JOB_ID=$(echo "$CREATE_BODY" | jq -r '.job_id')
  USER_ID=$(echo "$CREATE_BODY" | jq -r '.user_id')
  CELERY_ID=$(echo "$CREATE_BODY" | jq -r '.celery_task_id')

  echo "  ✅ Success: Job submitted (HTTP 202 ACCEPTED)."
  echo "  - Generated Job ID:   $JOB_ID"
  echo "  - User ID (from DB):  $USER_ID"
  echo "  - Celery Task ID:     ${CELERY_ID:0:8}..."
else
  echo "  ❌ FAILURE: Job creation failed."
  echo "  - Expected Status: 202 | Actual Status: $CREATE_STATUS"
  echo "  - Full Response Body: $CREATE_BODY"
  exit 1
fi
echo " "


# --- 2️⃣ Retrieve Job Status (GET /job/{job_id}) ---
# NOTE THE CORRECT PATH: /job/ followed by the ID
echo "➡️ 2/2 | Retrieving job status from CORRECT route ${JOB_ENDPOINT}/${JOB_ID}..."

# --- CN FIX: Capture status and body separately
STATUS_RESPONSE_BODY=$(curl -k -s -X GET "${JOB_ENDPOINT}/${JOB_ID}" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -w "%{http_code}")
# HTTP Status code is the last 3 characters of the output
STATUS_STATUS=${STATUS_RESPONSE_BODY: -3}
STATUS_BODY=${STATUS_RESPONSE_BODY:0:$((${#STATUS_RESPONSE_BODY}-3))}


if [ "$STATUS_STATUS" == "200" ]; then
  RETRIEVED_STATUS=$(echo "$STATUS_BODY" | jq -r '.status')

  echo "  ✅ Success: Job retrieved (HTTP 200 OK)."
  echo "  - Current Status: $RETRIEVED_STATUS"
  echo "  - Confirmed ID:   $(echo "$STATUS_BODY" | jq -r '.job_id')"
else
  # This section tests for the correct 404/403 access control
  echo "  ❌ FAILURE: Job retrieval failed. This indicates a routing or permissions issue."
  echo "  - Expected Status: 200 | Actual Status: $STATUS_STATUS"
  echo "  - Full Response Body: $STATUS_BODY"
  exit 1
fi
echo " "

echo "=========================================================="
echo " 🎉 Job Test Completed Successfully (Routing Confirmed)!"
echo "=========================================================="
echo " "
