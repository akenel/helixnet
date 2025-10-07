#!/bin/bash
# ==========================================
# HelixNet E2E API Smoke Test Script
# Purpose: Verify core Auth, User, and Job endpoints via cURL.
# Relies on: 'make seed-data' having created a known user.
# ==========================================

# Exit immediately if a command exits with a non-zero status
set -e

# --- Configuration ---
API_BASE="http://localhost:8000/api/v1"
HEALTH_CHECK_URL="http://localhost:8000/health"
# NOTE: Replace these with the actual credentials from your .env/seed-data script
TEST_USERNAME="admin@helix.net" 
TEST_PASSWORD="securepassword" 

# --- Helpers ---
LOG_INFO() { echo "🟦 [INFO] $1"; }
LOG_SUCCESS() { echo "🟩 [SUCCESS] $1"; }
LOG_ERROR() { echo "🟥 [ERROR] $1"; exit 1; }

# Function to wait for the API to be ready
wait_for_service() {
    LOG_INFO "Waiting for FastAPI service to become healthy..."
    for i in {1..10}; do
        # Check /health/ endpoint
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL")
        if [ "$STATUS" -eq 200 ]; then
            LOG_SUCCESS "API is healthy (Status: 200)."
            return 0
        fi
        sleep 2
    done
    LOG_ERROR "API failed to become healthy after 20 seconds (Last status: $STATUS)."
}

# --- Main Test Flow ---

wait_for_service

# 1. AUTHENTICATION: Get JWT Token (/api/v1/token)
LOG_INFO "1. Testing Login and Token Acquisition..."

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/token" \
  -F "username=$TEST_USERNAME" \
  -F "password=$TEST_PASSWORD")

# Use jq to safely extract the token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r .access_token)

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null" ]; then
    LOG_ERROR "Token acquisition FAILED. Response: $LOGIN_RESPONSE"
fi

AUTH_HEADER="Authorization: Bearer $ACCESS_TOKEN"
LOG_SUCCESS "Login successful. JWT token acquired."

# 2. USER PROFILE: Read Current User (/api/v1/me)
LOG_INFO "2. Testing Protected Endpoint (/api/v1/me)..."

ME_RESPONSE=$(curl -s -X GET "$API_BASE/me" \
  -H "$AUTH_HEADER")

ME_STATUS=$(echo "$ME_RESPONSE" | jq -r .email)

if [ "$ME_STATUS" == "$TEST_USERNAME" ]; then
    USER_ID=$(echo "$ME_RESPONSE" | jq -r .id)
    LOG_SUCCESS "Authenticated profile retrieval successful. User ID: $USER_ID"
else
    LOG_ERROR "Profile retrieval FAILED. Response: $ME_RESPONSE"
fi

# 3. JOB SUBMISSION: Submit Async Job (POST /api/v1/)
LOG_INFO "3. Testing Job Submission (POST /api/v1/)..."

JOB_PAYLOAD='{"input_data": {"file_name": "data_set_1.csv", "task_type": "analysis"}}'
JOB_RESPONSE=$(curl -s -X POST "$API_BASE/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d "$JOB_PAYLOAD")

JOB_HTTP_STATUS=$(echo "$JOB_RESPONSE" | head -n 1 | awk '{print $2}')
if [ "$JOB_HTTP_STATUS" -ne 202 ]; then
    LOG_ERROR "Job submission FAILED. Expected 202. Status: $JOB_HTTP_STATUS. Response: $JOB_RESPONSE"
fi

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r .job_id)

if [ -z "$JOB_ID" ] || [ "$JOB_ID" == "null" ]; then
    LOG_ERROR "Job ID not returned. Response: $JOB_RESPONSE"
fi

LOG_SUCCESS "Job successfully submitted. Job ID: $JOB_ID"

# 4. JOB STATUS: Retrieve Job Status (GET /api/v1/{job_id})
LOG_INFO "4. Testing Job Status Retrieval (GET /api/v1/$JOB_ID)..."

# Give the worker a moment to pick up the task (simulating real async behavior)
sleep 2

STATUS_RESPONSE=$(curl -s -X GET "$API_BASE/$JOB_ID" \
  -H "$AUTH_HEADER")

JOB_STATUS=$(echo "$STATUS_RESPONSE" | jq -r .status)

if [ "$JOB_STATUS" == "PENDING" ] || [ "$JOB_STATUS" == "STARTED" ]; then
    LOG_SUCCESS "Job status retrieval successful. Status is currently: $JOB_STATUS"
else
    LOG_ERROR "Job status retrieval FAILED. Status: $JOB_STATUS. Full response: $STATUS_RESPONSE"
fi

# --- Final Cleanup/Success ---
LOG_SUCCESS "All HelixNet API Smoke Tests Passed! Infrastructure confirmed operational. 🎉"
