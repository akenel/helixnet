#!/bin/bash

# --- Configuration ---
API_BASE_URL="https://helix.local/api/v1"
ADMIN_USER="admin@helix.net"     # Assuming you'll create an admin user
ADMIN_PASS="your-secure-password" # REPLACE WITH YOUR INITIAL ADMIN PASSWORD

echo "--- 1. 🔑 LOGIN TO GET ACCESS TOKEN ---"
# Note: The /api/v1/token endpoint uses x-www-form-urlencoded
LOGIN_RESPONSE=$(curl -k -s -X POST "${API_BASE_URL}/token" \
  -H "accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=${ADMIN_USER}&password=${ADMIN_PASS}")

# Extract token using jq (ensure 'jq' is installed: sudo apt install jq)
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$ACCESS_TOKEN" == "null" ] || [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Login Failed. Check credentials or API endpoint."
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login Successful. Token obtained."
# echo "Token: $ACCESS_TOKEN" # Uncomment to debug

# --- 2. 👤 TEST AUTHENTICATED ROUTE (GET Current User) ---
echo -e "\n--- 2. 👤 GET CURRENT USER PROFILE ---"
curl -k -s -X GET "${API_BASE_URL}/me" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# --- 3. 📬 SUBMIT NEW ASYNCHRONOUS JOB ---
echo -e "\n--- 3. 📬 SUBMIT ASYNCHRONOUS JOB ---"
JOB_DATA='{"input_data": {"file_path": "/data/input/123.csv", "processor_type": "high_res_model"}}'

JOB_RESPONSE=$(curl -k -s -X POST "${API_BASE_URL}/" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$JOB_DATA")

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')

if [ "$JOB_ID" == "null" ] || [ -z "$JOB_ID" ]; then
  echo "❌ Job Submission Failed."
  echo "Response: $JOB_RESPONSE"
  exit 1
fi

echo "✅ Job Submitted. ID: $JOB_ID"

# --- 4. 📊 CHECK JOB STATUS (Wait a few seconds) ---
echo -e "\n--- 4. 📊 CHECK JOB STATUS (Waiting 5s...) ---"
sleep 5

curl -k -s -X GET "${API_BASE_URL}/$JOB_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

echo -e "\n--- 🚀 Script Complete ---"