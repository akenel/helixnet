#!/usr/bin/env bash
# ================================================================
# DebLLM Dashboard - Status and Control Panel
# ================================================================
set -euo pipefail

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config/debllm.conf"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ================================================================
# Helper Functions
# ================================================================

# Print section header
print_header() {
    local title="$1"
    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  $title${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Get KB statistics
get_kb_stats() {
    local total=$(find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" | wc -l)
    local auto_fixable=$(grep -l "^auto_fix: true$" "$DEBLLM_NOTES_DIR"/**/ERROR-*.md 2>/dev/null | wc -l)
    local critical=$(grep -l "^severity: critical$" "$DEBLLM_NOTES_DIR"/**/ERROR-*.md 2>/dev/null | wc -l)
    local high=$(grep -l "^severity: high$" "$DEBLLM_NOTES_DIR"/**/ERROR-*.md 2>/dev/null | wc -l)

    echo "$total|$auto_fixable|$critical|$high"
}

# Get queue stats
get_queue_stats() {
    local drafts=$(find "$DEBLLM_QUEUE_DIR" -name "DRAFT-*.md" 2>/dev/null | wc -l)
    local draft_critical=0
    local draft_high=0

    if [[ $drafts -gt 0 ]]; then
        draft_critical=$(grep -l "^severity: critical$" "$DEBLLM_QUEUE_DIR"/DRAFT-*.md 2>/dev/null | wc -l || echo "0")
        draft_high=$(grep -l "^severity: high$" "$DEBLLM_QUEUE_DIR"/DRAFT-*.md 2>/dev/null | wc -l || echo "0")
    fi

    echo "$drafts|$draft_critical|$draft_high"
}

# Get recent activity
get_recent_activity() {
    if [[ -f "$DEBLLM_LOG_FILE" ]]; then
        tail -n 20 "$DEBLLM_LOG_FILE" | tac
    else
        echo "No activity logged yet."
    fi
}

# Get most frequent errors (last 7 days)
get_top_errors() {
    local cutoff_date=$(date -d '7 days ago' +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d 2>/dev/null)

    find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" -type f | while read -r note; do
        local error_id=$(grep "^error_id:" "$note" | cut -d: -f2 | xargs)
        local title=$(grep "^title:" "$note" | cut -d: -f2- | xargs)
        local count=$(grep "^occurrence_count:" "$note" | cut -d: -f2 | xargs)
        local last_seen=$(grep "^last_seen:" "$note" | cut -d: -f2 | xargs)

        # Check if seen in last 7 days
        if [[ "$last_seen" > "$cutoff_date" ]] || [[ "$last_seen" == "$cutoff_date" ]]; then
            echo "$count|$error_id|$title"
        fi
    done | sort -rn -t'|' -k1 | head -n 5
}

# ================================================================
# Display Functions
# ================================================================

display_system_status() {
    print_header "📊 DebLLM System Status"

    echo -e "  ${BOLD}Mode:${NC}              $DEBLLM_MODE"
    echo -e "  ${BOLD}LLM Backend:${NC}       $DEBLLM_LLM_MODE"
    echo -e "  ${BOLD}Auto-Fix:${NC}          $([ "$AUTO_FIX_ENABLED" == "true" ] && echo -e "${GREEN}Enabled${NC}" || echo -e "${RED}Disabled${NC}")"
    echo -e "  ${BOLD}Check Interval:${NC}    ${CHECK_INTERVAL}s ($(( CHECK_INTERVAL / 60 )) minutes)"

    # Hyper-care status
    if is_hypercare_active; then
        local remaining=$(get_hypercare_remaining)
        echo -e "  ${BOLD}Hyper-Care:${NC}        ${YELLOW}⚠️ ACTIVE${NC} ($remaining minutes remaining)"
    else
        echo -e "  ${BOLD}Hyper-Care:${NC}        ${GREEN}Inactive${NC}"
    fi

    # Maintenance window
    if is_maintenance_window; then
        echo -e "  ${BOLD}Maintenance:${NC}       ${YELLOW}⚠️ IN PROGRESS${NC}"
    else
        echo -e "  ${BOLD}Maintenance:${NC}       ${GREEN}Normal operations${NC}"
    fi
}

display_kb_status() {
    print_header "📚 Knowledge Base Statistics"

    IFS='|' read -r total auto_fixable critical high <<< "$(get_kb_stats)"

    echo -e "  ${BOLD}Total Errors:${NC}      $total notes"
    echo -e "  ${BOLD}Auto-Fixable:${NC}      ${GREEN}$auto_fixable${NC} ($(( total > 0 ? auto_fixable * 100 / total : 0 ))%)"
    echo -e "  ${BOLD}Critical:${NC}          ${RED}$critical${NC}"
    echo -e "  ${BOLD}High Priority:${NC}     ${YELLOW}$high${NC}"

    echo ""
    echo "  ${BOLD}By Service:${NC}"
    for service_dir in "$DEBLLM_NOTES_DIR"/*; do
        if [[ -d "$service_dir" ]]; then
            local service=$(basename "$service_dir")
            local count=$(find "$service_dir" -name "ERROR-*.md" | wc -l)
            if [[ $count -gt 0 ]]; then
                echo "    • $service: $count notes"
            fi
        fi
    done
}

display_queue_status() {
    print_header "📋 Review Queue (New/Unknown Errors)"

    IFS='|' read -r drafts draft_critical draft_high <<< "$(get_queue_stats)"

    if [[ $drafts -eq 0 ]]; then
        echo -e "  ${GREEN}✅ No errors in review queue${NC}"
    else
        echo -e "  ${YELLOW}⚠️  $drafts errors awaiting review${NC}"
        echo -e "     Critical: ${RED}$draft_critical${NC}"
        echo -e "     High: ${YELLOW}$draft_high${NC}"
        echo ""
        echo "  ${BOLD}Recent Drafts:${NC}"

        find "$DEBLLM_QUEUE_DIR" -name "DRAFT-*.md" -type f | sort -r | head -n 5 | while read -r draft; do
            local title=$(grep "^title:" "$draft" | cut -d: -f2- | xargs)
            local severity=$(grep "^severity:" "$draft" | cut -d: -f2 | xargs)

            case "$severity" in
                critical) local icon="🚨" ;;
                high) local icon="⚠️" ;;
                medium) local icon="📝" ;;
                *) local icon="ℹ️" ;;
            esac

            echo "    $icon [$severity] $title"
            echo "       File: $(basename "$draft")"
        done

        echo ""
        echo "  ${BOLD}Action:${NC} Review with: ${BLUE}debllm-dashboard.sh --review-queue${NC}"
    fi
}

display_top_errors() {
    print_header "🔥 Most Frequent Errors (Last 7 Days)"

    local top_errors=$(get_top_errors)

    if [[ -z "$top_errors" ]]; then
        echo -e "  ${GREEN}✅ No errors in the last 7 days${NC}"
    else
        echo "$top_errors" | while IFS='|' read -r count error_id title; do
            echo -e "  ${BOLD}$count×${NC} [$error_id] $title"
        done
    fi
}

display_recent_activity() {
    print_header "📜 Recent Activity (Last 20 Events)"

    if [[ ! -f "$DEBLLM_LOG_FILE" ]]; then
        echo "  No activity logged yet."
    else
        tail -n 20 "$DEBLLM_LOG_FILE" | while IFS= read -r line; do
            # Color code by log level
            if echo "$line" | grep -q "\[ERROR\]"; then
                echo -e "  ${RED}$line${NC}"
            elif echo "$line" | grep -q "\[WARN\]"; then
                echo -e "  ${YELLOW}$line${NC}"
            elif echo "$line" | grep -q "\[INFO\]"; then
                echo -e "  $line"
            else
                echo "  $line"
            fi
        done
    fi
}

display_monitored_services() {
    print_header "🐳 Monitored Services"

    for service in "${MONITORED_SERVICES[@]}"; do
        if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
            echo -e "  ${GREEN}✔${NC} $service (running)"
        else
            echo -e "  ${RED}✘${NC} $service (not running)"
        fi
    done
}

# ================================================================
# Main Dashboard
# ================================================================

main_dashboard() {
    clear
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  DebLLM Dashboard - Self-Healing Monitoring System${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  $(date '+%Y-%m-%d %H:%M:%S')"

    display_system_status
    display_kb_status
    display_queue_status
    display_top_errors
    display_monitored_services
    display_recent_activity

    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "  Commands:"
    echo "    debllm-watcher.sh           - Run scan now"
    echo "    debllm-search-note.sh       - Search knowledge base"
    echo "    debllm-dashboard.sh         - Refresh this dashboard"
    echo "    debllm-dashboard.sh --watch - Auto-refresh every 30s"
    echo ""
}

# ================================================================
# Entry Point
# ================================================================

if [[ "${1:-}" == "--watch" ]]; then
    # Auto-refresh mode
    while true; do
        main_dashboard
        sleep 30
    done
else
    # Single display
    main_dashboard
fi
