#!/bin/bash
# =======================================================
# HelixNet Service Sanity Check Script
# =======================================================
# Helper function to check a service status
# The script assumes the .env file is either in the current directory or one level up.

ENV_FILE="../.env"
if [ -f .env ]; then
ENV_FILE="./.env"
fi
echo "Using environment file: $ENV_FILE"
if [ -f "$ENV_FILE" ]; then
# set -a exports all variables defined after it, making them available for echo
set -a
source "$ENV_FILE"
set +a
fi
echo "Loaded environment variables from $ENV_FILE"

check_service() {
        URL=$1
        NAME=$2
        HEALTH_PATH=$3
        EXPECTED_CODE=$4

        STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${URL}${HEALTH_PATH}")

        if [ "$STATUS_CODE" -eq "$EXPECTED_CODE" ] || [ "$STATUS_CODE" -eq 200 ]; then
            echo -e "[ \033[32mOK\033[0m ] $NAME is reachable at $URL$HEALTH_PATH (Status: $STATUS_CODE)"
        else
            echo -e "[ \033[31mFAIL\033[0m ] $NAME failed reachability test at $URL$HEALTH_PATH (Status: $STATUS_CODE). Expected: $EXPECTED_CODE or 200"
        fi

}

echo "--- Running HelixNet Core Stack Health Checks ---"
# 1. Web Service (FastAPI)

check_service "http://localhost:8000" "Web App" "/health" 200
# 2. RabbitMQ Management UI (Should respond to root path, 200 or 302 expected before login)

check_service "http://localhost:15672" "RabbitMQ Management UI" "" 302
# 3. MinIO Console UI
# Checking the root console path; 302 or 200 is fine if the service is up.

check_service "http://localhost:9091" "MinIO Console" "/minio/login" 200
# 4. MinIO API Endpoint (Checking the dedicated MinIO health endpoint)

check_service "http://localhost:9090" "MinIO API" "/minio/health/live" 200
# 5. Redis (Not easily tested via HTTP/curl, but if the web/worker services are up, we assume connection via internal network)

echo "[ ---- ] Redis/Postgres are running internally; connectivity is assumed if Web/Worker are OK."

echo "------------------------------------------------"
echo "Sanity Check Complete."
echo "If all services show [ OK ], you are good to go!"
# Usage Reminder:

echo ""
echo "Credential Reminder (Check your .env file):"
echo "  RabbitMQ: http://localhost:15672 (User: $RABBITMQ_USER, Pass: $RABBITMQ_PASS)"
echo "  MinIO Console: http://localhost:9091 (User: $MINIO_ROOT_USER, Pass: $MINIO_ROOT_PASSWORD)"