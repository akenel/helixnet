#!/usr/bin/env bash
# ===============================================================================================
# 🧩 helix-ollama.sh — Self-Healing Log Doctor (Sherlock Edition)
# Purpose: collect problematic service logs, pre-digest, consult Ollama,
#          auto-fallback to smaller model or cloud key if needed.
# ===============================================================================================
set -Eeuo pipefail
IFS=$'\n\t'
# -----------------------------------------------------------------------------------------------
# ---- Configurable defaults 
# -----------------------------------------------------------------------------------------------
# Example: Load variables from a .env file first
if [[ -f ".env" ]]; then
    source "env/helix.env"
fi
KEYCLOAK_DEV_REALM="${KEYCLOAK_DEV_REALM:=unknown}"
# -----------------------------------------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$ROOT_DIR/ollama/config/ollama.yaml"
TMP_DIR="./LOGS/tmp/helix_ollama"
SUMMARY_FILE="$TMP_DIR/helix-health.md"
STATUS_SCRIPT="$ROOT_DIR/scripts/helix-status-v2.sh"    # your health dashboard script
COMPOSE_FILE="compose/llm-stack.yml"              # change if you use separate compose
TAIL_DEFAULT=50                   # tail when verbose or when nothing else found
SNIPPET_LINES=200                 # maximum lines to send to model
SNIPPET_BYTES=10000               # also limit bytes (safety)
MIN_MEM_GB_FOR_BIG=12             # threshold to allow the biggest local model
DEFAULT_LOCAL_MODEL="llama3.2"    # prefer local model name (could be "llama3.2:latest")
FALLBACK_MODEL="llama3.2:3b"      # smaller variant
CLOUD_MODEL="ollama-turbo"        # remote turbo route (if using cloud key)
TOKENS_DEFAULT=2048
TEMP_DEFAULT=0.3
# -----------------------------------------------------------------------------------------------
mkdir -p "$TMP_DIR"
# ---- Colors ------------------------------------------------------------------------------------
# Set colors for output
CHECK="✔️"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
CYAN='\033[0;39m'
NC='\033[0m' # No Color
BOLD="\033[1m"; RESET="\033[0m"
OK="${GREEN}✅${NC}"; FAIL="${RED}❌${NC}"; WARN="${YELLOW}⚠️${NC}"; INFO="${BLUE}ℹ️${NC}"
# -----------------------------------------------------------------------------------------------
# ---- Read config YAML (very small/simple parser) ----
get_yaml_value() {
  # simple: lines like 'key: value'
  [[ -f "$CONFIG_FILE" ]] || return 0
  awk -F': *' -v k="$1" '$1==k {print $2; exit}' "$CONFIG_FILE" | tr -d '"' || true
}
# ---- More flexible by adding environment overrides (so .env wins over YAML):
MODEL_CFG=$(get_yaml_value "default_model" || true)
MODEL=${OLLAMA_MODEL:-$(get_yaml_value "default_model")}
# -----------------------------------------------------------------------------------------------
TEMP=$(get_yaml_value "temperature" || true)
TEMP=${OLLAMA_TEMPERATURE:-$(get_yaml_value "temperature")}
# -----------------------------------------------------------------------------------------------
TOKENS=$(get_yaml_value "max_tokens" || true)
TOKENS=${OLLAMA_MAX_TOKENS:-$(get_yaml_value "max_tokens")}
# ---- Auto memory check: decide model ---------------------------------------------------------
TOTAL_MEM_KB=$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)
TOTAL_MEM_GB=$(( TOTAL_MEM_KB / 1024 / 1024 ))
if (( TOTAL_MEM_GB < MIN_MEM_GB_FOR_BIG )); then
  echo -e "${YELLOW}⚙️  Low memory detected (${TOTAL_MEM_GB} GB). Will use fallback model: ${FALLBACK_MODEL}${RESET}"
  MODEL="$FALLBACK_MODEL"
else
  echo -e "${CYAN}⚙️  Memory OK (${TOTAL_MEM_GB} GB). Will try model: ${MODEL}${RESET}"
fi
# -----------------------------------------------------------------------------------------------
# ---- Ollama cloud key (optional) 
# ---- Set OLLAMA_API_KEY in your .env if you want heavy jobs routed/cloud-accelerated 
# -----------------------------------------------------------------------------------------------
OLLAMA_API_KEY="${OLLAMA_API_KEY:-""}"
# ---- Print header -----------------------------------------------------------------------------
echo -e "${CYAN}"
echo "════════════════════════════════════════════════"
echo -e "${BOLD}${GREEN}  Helix 🧠 Ollama Diagnostic 🦜️ model=${MODEL}      "
echo "═══════════> scripts/helix-ollama.sh <══════════"
# ---- Print header -----------------------------------------------------------------------------
LATEST_HELIX_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "helix" | head -n 1 || true)
# Recommended approach for getting reliable BUILD info
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
BUILD_TIME=$(date '+%Y%m%d_%H%M%S') # Current time, since build time is hard to extract from docker images
echo "🪣️  Latest Image: ${LATEST_HELIX_IMAGE} 🤓️ SHA: ${SHA}"
echo "Build Time: 🤖 ${BUILD_TIME}"
# ------------------------------------------------------------------------------------------------

  echo -e "${GREEN}🧠 Starting... Model: ${MODEL} | Temp: ${TEMP} | Tokens: ${TOKENS}${RESET}"
echo -e "${YELLOW}⏳ Host memory: ${TOTAL_MEM_GB} GB${RESET}"
echo ""
LATEST_HELIX_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -E "helix" | head -n 1 || true)
# Recommended approach for getting reliable BUILD info
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "local")
BUILD_TIME=$(date '+%Y%m%d_%H%M%S') # Current time, since build time is hard to extract from docker images

# -----------------------------------------------------------------------------------------------
# ---- Smart Health Scan (populate UNHEALTHY_SERVICES) 
# -----------------------------------------------------------------------------------------------
UNHEALTHY_SERVICES=()
if [[ -x "$STATUS_SCRIPT" ]]; then
# -----------------------------------------------------------------------------------------------
# run your status script and find lines that indicate problems 
# -----------------------------------------------------------------------------------------------
  while IFS= read -r line; do
# -----------------------------------------------------------------------------------------------
# expected format in the status script: 'name: ...' or first token is name
# -----------------------------------------------------------------------------------------------
    svc=$(echo "$line" | awk '{print $1}')
    UNHEALTHY_SERVICES+=("$svc")
  done < <($STATUS_SCRIPT | grep -E "unhealthy|Restart|CRASH|Down|Down|⬇|❌" || true)
else
  echo -e "${YELLOW}⚠️  Status script not found: $STATUS_SCRIPT. Falling back to 'docker ps' grep Restarting.${RESET}"
  while IFS= read -r name; do
    UNHEALTHY_SERVICES+=("$name")
  done < <(docker ps --format '{{.Names}} {{.Status}}' | grep -i Restarting | awk '{print $1}' || true)
fi
# -----------------------------------------------------------------------------------------------
if [ ${#UNHEALTHY_SERVICES[@]} -eq 0 ]; then
  echo -e "${GREEN}✅  No unhealthy services detected. Nothing to analyze.${RESET}"
  exit 0
fi
echo -e "🩺  Found potential issues in: ${RED}${UNHEALTHY_SERVICES[*]}${RESET}"
echo ""
# -----------------------------------------------------------------------------------------------
# ---- Helper: prepare snippet from logs (prefer errors/warnings) 
# -----------------------------------------------------------------------------------------------
prepare_snippet() {
  local svc="$1"; local out="$2"
  local full_log_tmp="$TMP_DIR/${svc}.full.log"
# -----------------------------------------------------------------------------------------------
# collect logs (use compose file so correct stack) 
# -----------------------------------------------------------------------------------------------
  docker compose -f "$COMPOSE_FILE" logs --tail $TAIL_DEFAULT "$svc" >"$full_log_tmp" 2>&1 || true
# -----------------------------------------------------------------------------------------------
# prefer lines with ERROR/WARN/Traceback/Exception 
# -----------------------------------------------------------------------------------------------
  if grep -Ei "error|err |exception|traceback|warn" "$full_log_tmp" >/dev/null 2>&1; then
# -----------------------------------------------------------------------------------------------
# extract up to SNIPPET_LINES matching lines (context preserved a bit)
# -----------------------------------------------------------------------------------------------
    grep -Ei "error|err |exception|traceback|warn" "$full_log_tmp" | sed -n "1,${SNIPPET_LINES}p" >"$out"
  else
# -----------------------------------------------------------------------------------------------
# fallback: take last SNIPPET_LINES lines trimmed to SNIPPET_BYTES 
# -----------------------------------------------------------------------------------------------
    tail -n "$SNIPPET_LINES" "$full_log_tmp" | head -n "$SNIPPET_LINES" >"$out"
  fi
# -----------------------------------------------------------------------------------------------
# enforce byte limit 
# -----------------------------------------------------------------------------------------------
  head -c "$SNIPPET_BYTES" "$out" >"${out}.tmp" && mv "${out}.tmp" "$out" || true
}
# -----------------------------------------------------------------------------------------------
# ---- Iterate services: collect, snippet, ask model 
# -----------------------------------------------------------------------------------------------
: >"$SUMMARY_FILE"   # truncate
for svc in "${UNHEALTHY_SERVICES[@]}"; do
  echo -e "🪵  Collecting logs for ${CYAN}${svc}${RESET}"
  LOG_SNIPPET="$TMP_DIR/${svc}.snippet.log"
  prepare_snippet "$svc" "$LOG_SNIPPET"
# -----------------------------------------------------------------------------------------------
# ---- snippet 
# -----------------------------------------------------------------------------------------------
  preview_lines=$(wc -l < "$LOG_SNIPPET" || echo 0)
  echo -e "   ✂️  Prepared snippet (${preview_lines} lines) -> $LOG_SNIPPET"
# -----------------------------------------------------------------------------------------------
# ----  Build diagnostic prompt (small and precise) 
# -----------------------------------------------------------------------------------------------
  PROMPT=$(cat <<-PROMPT
You are a concise diagnostic assistant for HelixNet (developer audience).
Task: Read the log snippet and reply with:
1) One-line root cause
2) 1-2 likely causes (bullet)
3) 2-3 concrete remediation steps (bullet)
Keep answer short, factual, no speculation. Include exact commands to try when applicable.
Log context (do not hallucinate beyond it):
----
$(cat "$LOG_SNIPPET")
----
End.
Temperature: $TEMP
Max tokens: $TOKENS
PROMPT
)
# -----------------------------------------------------------------------------------------------
# ---- Decide execution mode: local model vs cloud key vs fallback ----
# First try local MODEL; if OLLAMA_API_KEY is set and local fails (OOM), use cloud
# -----------------------------------------------------------------------------------------------
  echo -e "\n🤖  Consulting model '${MODEL}' about '${YELLOW}${svc}${RESET}'..."
  set +e
  if [[ -n "${OLLAMA_API_KEY}" ]]; then
# -----------------------------------------------------------------------------------------------
# ---- Use cloud key env for ollama container to route to cloud if configured upstream
# -----------------------------------------------------------------------------------------------
    RESULT=$(docker compose -f "$COMPOSE_FILE" exec -T ollama \
      env OLLAMA_API_KEY="$OLLAMA_API_KEY" \
      ollama run "$MODEL" --temperature "$TEMP" --max-tokens "$TOKENS" 2>&1 <<EOF
$PROMPT
EOF
) || RC=$?
  else
# -----------------------------------------------------------------------------------------------
# ---- local attempt
# -----------------------------------------------------------------------------------------------
    RESULT=$(docker compose -f "$COMPOSE_FILE" exec -T ollama \
      ollama run "$MODEL" --temperature "$TEMP" --max-tokens "$TOKENS" 2>&1 <<EOF
$PROMPT
EOF
) || RC=$?
  fi
  set -e
# -----------------------------------------------------------------------------------------------
# ---- If the output indicates memory error, retry with fallback smaller model
# -----------------------------------------------------------------------------------------------
  if echo "$RESULT" | grep -iE "requires more system memory|out of memory|OOM|memory" >/dev/null 2>&1; then
    echo -e "${RED}💥 Model '${MODEL}' failed for '${svc}' with memory error. Retrying with fallback model ${FALLBACK_MODEL}${RESET}"
    MODEL="$FALLBACK_MODEL"
    set +e
    if [[ -n "${OLLAMA_API_KEY}" ]]; then
      RESULT=$(docker compose -f "$COMPOSE_FILE" exec -T ollama \
        env OLLAMA_API_KEY="$OLLAMA_API_KEY" \
        ollama run "$MODEL" --temperature "$TEMP" --max-tokens "$TOKENS" 2>&1 <<EOF
$PROMPT
EOF
) || RC=$?
    else
      RESULT=$(docker compose -f "$COMPOSE_FILE" exec -T ollama \
        ollama run "$MODEL" --temperature "$TEMP" --max-tokens "$TOKENS" 2>&1 <<EOF
$PROMPT
EOF
) || RC=$?
    fi
    set -e
  fi
# -----------------------------------------------------------------------------------------------
# ---- If still failed and we have OLLAMA_API_KEY, try cloud-special model name as last resort
# -----------------------------------------------------------------------------------------------
  if [[ -n "${OLLAMA_API_KEY}" ]] && echo "$RESULT" | grep -i "error" >/dev/null 2>&1; then
    echo -e "${YELLOW}⚙️  Last resort: routing to cloud model ${CLOUD_MODEL}${RESET}"
    set +e
    RESULT=$(docker compose -f "$COMPOSE_FILE" exec -T ollama \
      env OLLAMA_API_KEY="$OLLAMA_API_KEY" \
      ollama run "$CLOUD_MODEL" --temperature "$TEMP" --max-tokens "$TOKENS" 2>&1 <<EOF
$PROMPT
EOF
) || RC=$?
    set -e
  fi
# --- Utility Functions --------------------------------------------------------------------------
# 1. Function to clean ANSI color codes from any string
# This uses 'tr' for simplicity and removes all ANSI escape sequences.
# -----------------------------------------------------------------------------------------------
clean_ansi_codes() {
  echo "$1" | tr -d '\033' | sed 's/\[[0-9;]*[A-Za-z]//g'
}
# -----------------------------------------------------------------------------------------------
# 2. Function to clean control characters, trim noise, and pretty-print to markdown
# -----------------------------------------------------------------------------------------------
clean_and_format_result() {
  local raw="$1"
  local cleaned_raw
  # -----------------------------------------------------------------------------------------------
  # Remove ANSI color codes and other control characters
  # -----------------------------------------------------------------------------------------------
  cleaned_raw=$(clean_ansi_codes "$raw")

  echo "$cleaned_raw" |
    sed 's/^[[:space:]]*//' | \
    sed '/^$/N;/^\n$/D' | \
    awk '
      BEGIN {
        # Insert a clear header if needed (can be changed to something else)
        print "🧩 **Diagnostic Summary**"
        print ""
      }
      # Skip redundant or raw error flags
      /Error: unknown flag: --temperature/ { next }

      # Add spacing around section headers
      /^### / { print "\n" $0 "\n"; next }

      # Pretty-print bullet lists with indentation
      /^[-*]/ || /^[[:digit:]]+\./ { print "  " $0; next }

      # Default: print line as-is
      { print $0 }
    '
}
# -----------------------------------------------------------------------------------------------
# Example: Loop that produces the results
# for svc in "🧩" "🌼" "🦄" "❓" "❓" "🥬"; do
# -----------------------------------------------------------------------------------------------
  RESULT="Error: unknown flag: --temperature" # Example $RESULT
# -----------------------------------------------------------------------------------------------
# Sanitize service name to remove color codes (e.g., from an echo in the loop)
# -----------------------------------------------------------------------------------------------
  CLEAN_SVC=$(clean_ansi_codes "$svc")
# -----------------------------------------------------------------------------------------------
# Sanitize result to avoid raw control chars, then format
# -----------------------------------------------------------------------------------------------
  SAFE_RESULT=$(clean_and_format_result "$RESULT")
# -----------------------------------------------------------------------------------------------
# Use Markdown for the header and write to the summary file
# The header is now guaranteed to be clean and uses Markdown (#) and Emojis (🧩)
# -----------------------------------------------------------------------------------------------
  printf "\n### 🧩 Service: **%s**\n\n%s\n\n---\n" "$CLEAN_SVC" "$SAFE_RESULT" >> "$SUMMARY_FILE"
# -----------------------------------------------------------------------------------------------
 # The terminal output still uses colors, which is fine!
# -----------------------------------------------------------------------------------------------
  echo -e "${GREEN}✅  Analysis for ${svc} saved to ${SUMMARY_FILE}${RESET}"