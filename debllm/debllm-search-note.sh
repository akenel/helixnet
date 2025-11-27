#!/usr/bin/env bash
# ================================================================
# DebLLM KB Search - Find Error Notes by Pattern or Error ID
# ================================================================
set -euo pipefail

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config/debllm.conf"

# ================================================================
# Usage
# ================================================================
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] <search_term>

Search the DebLLM Knowledge Base for error notes.

OPTIONS:
    -i, --id <error_id>         Search by error ID (e.g., ERROR-001)
    -p, --pattern <pattern>     Search by error pattern/log message
    -s, --service <service>     Filter by service (redis, postgres, etc.)
    -d, --domain <domain>       Filter by domain (technical, functional, config)
    -v, --severity <severity>   Filter by severity (low, medium, high, critical)
    --auto-fix-only             Only show errors with auto-fix available
    -h, --help                  Show this help message

EXAMPLES:
    # Search by error message
    $(basename "$0") -p "Redis connection refused"

    # Search by error ID
    $(basename "$0") -i ERROR-001

    # Find all auto-fixable Redis errors
    $(basename "$0") -s redis --auto-fix-only

    # Find all critical configuration errors
    $(basename "$0") -d config -v critical

EOF
    exit 0
}

# ================================================================
# Search Functions
# ================================================================

# Search by error ID
search_by_id() {
    local error_id="$1"
    find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" -type f | while read -r note; do
        if grep -q "^error_id: $error_id$" "$note"; then
            echo "$note"
            return 0
        fi
    done
    return 1
}

# Search by pattern (in patterns list or error description)
search_by_pattern() {
    local pattern="$1"
    local matches=()

    find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" -type f | while read -r note; do
        # Search in patterns list
        if grep -A 10 "^patterns:" "$note" | grep -iq "$pattern"; then
            echo "$note"
        # Or search in title/symptoms
        elif grep -E "^title:|## 🔍 Symptoms" "$note" | grep -iq "$pattern"; then
            echo "$note"
        fi
    done
}

# Filter by service
filter_by_service() {
    local service="$1"
    shift
    local notes=("$@")

    for note in "${notes[@]}"; do
        if grep -q "^service: $service$" "$note"; then
            echo "$note"
        fi
    done
}

# Filter by domain
filter_by_domain() {
    local domain="$1"
    shift
    local notes=("$@")

    for note in "${notes[@]}"; do
        if grep -q "^error_domain: $domain$" "$note"; then
            echo "$note"
        fi
    done
}

# Filter by severity
filter_by_severity() {
    local severity="$1"
    shift
    local notes=("$@")

    for note in "${notes[@]}"; do
        if grep -q "^severity: $severity$" "$note"; then
            echo "$note"
        fi
    done
}

# Filter auto-fix only
filter_auto_fix() {
    local notes=("$@")

    for note in "${notes[@]}"; do
        if grep -q "^auto_fix: true$" "$note"; then
            echo "$note"
        fi
    done
}

# Display note summary
display_note_summary() {
    local note="$1"

    local error_id=$(grep "^error_id:" "$note" | cut -d: -f2 | xargs)
    local title=$(grep "^title:" "$note" | cut -d: -f2- | xargs)
    local severity=$(grep "^severity:" "$note" | cut -d: -f2 | xargs)
    local domain=$(grep "^error_domain:" "$note" | cut -d: -f2 | xargs)
    local auto_fix=$(grep "^auto_fix:" "$note" | cut -d: -f2 | xargs)
    local resolution_group=$(grep "^resolution_group:" "$note" | cut -d: -f2 | xargs)

    # Severity emoji
    case "$severity" in
        critical) local sev_icon="🚨" ;;
        high) local sev_icon="⚠️" ;;
        medium) local sev_icon="📝" ;;
        low) local sev_icon="ℹ️" ;;
        *) local sev_icon="❓" ;;
    esac

    # Auto-fix indicator
    if [[ "$auto_fix" == "true" ]]; then
        local fix_icon="🔧"
    else
        local fix_icon="👤"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$sev_icon [$error_id] $title"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Domain: $domain | Severity: $severity | Auto-fix: $auto_fix $fix_icon"
    echo "Resolution Group: $resolution_group"
    echo "File: $note"
}

# Display full note
display_full_note() {
    local note="$1"
    cat "$note"
}

# ================================================================
# Main
# ================================================================

# Parse arguments
SEARCH_MODE=""
SEARCH_TERM=""
FILTER_SERVICE=""
FILTER_DOMAIN=""
FILTER_SEVERITY=""
AUTO_FIX_ONLY=false
SHOW_FULL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--id)
            SEARCH_MODE="id"
            SEARCH_TERM="$2"
            shift 2
            ;;
        -p|--pattern)
            SEARCH_MODE="pattern"
            SEARCH_TERM="$2"
            shift 2
            ;;
        -s|--service)
            FILTER_SERVICE="$2"
            shift 2
            ;;
        -d|--domain)
            FILTER_DOMAIN="$2"
            shift 2
            ;;
        -v|--severity)
            FILTER_SEVERITY="$2"
            shift 2
            ;;
        --auto-fix-only)
            AUTO_FIX_ONLY=true
            shift
            ;;
        --full)
            SHOW_FULL=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            # If no search mode specified, assume pattern search
            if [[ -z "$SEARCH_MODE" ]]; then
                SEARCH_MODE="pattern"
                SEARCH_TERM="$1"
            fi
            shift
            ;;
    esac
done

# Validate search term
if [[ -z "$SEARCH_TERM" ]] && [[ -z "$FILTER_SERVICE" ]] && [[ -z "$FILTER_DOMAIN" ]]; then
    echo "Error: No search criteria provided"
    usage
fi

# Perform search
declare -a RESULTS=()

if [[ "$SEARCH_MODE" == "id" ]]; then
    result=$(search_by_id "$SEARCH_TERM")
    if [[ -n "$result" ]]; then
        RESULTS+=("$result")
    fi
elif [[ "$SEARCH_MODE" == "pattern" ]]; then
    while IFS= read -r note; do
        RESULTS+=("$note")
    done < <(search_by_pattern "$SEARCH_TERM")
else
    # No search term, list all
    while IFS= read -r note; do
        RESULTS+=("$note")
    done < <(find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" -type f)
fi

# Apply filters
if [[ -n "$FILTER_SERVICE" ]]; then
    FILTERED=()
    for note in "${RESULTS[@]}"; do
        if grep -q "^service: $FILTER_SERVICE$" "$note"; then
            FILTERED+=("$note")
        fi
    done
    RESULTS=("${FILTERED[@]}")
fi

if [[ -n "$FILTER_DOMAIN" ]]; then
    FILTERED=()
    for note in "${RESULTS[@]}"; do
        if grep -q "^error_domain: $FILTER_DOMAIN$" "$note"; then
            FILTERED+=("$note")
        fi
    done
    RESULTS=("${FILTERED[@]}")
fi

if [[ -n "$FILTER_SEVERITY" ]]; then
    FILTERED=()
    for note in "${RESULTS[@]}"; do
        if grep -q "^severity: $FILTER_SEVERITY$" "$note"; then
            FILTERED+=("$note")
        fi
    done
    RESULTS=("${FILTERED[@]}")
fi

if [[ "$AUTO_FIX_ONLY" == true ]]; then
    FILTERED=()
    for note in "${RESULTS[@]}"; do
        if grep -q "^auto_fix: true$" "$note"; then
            FILTERED+=("$note")
        fi
    done
    RESULTS=("${FILTERED[@]}")
fi

# Display results
if [[ ${#RESULTS[@]} -eq 0 ]]; then
    echo "No matching error notes found."
    exit 1
fi

echo "Found ${#RESULTS[@]} matching error note(s):"

for note in "${RESULTS[@]}"; do
    if [[ "$SHOW_FULL" == true ]]; then
        display_full_note "$note"
    else
        display_note_summary "$note"
    fi
done

echo ""
