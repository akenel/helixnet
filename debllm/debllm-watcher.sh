#!/usr/bin/env bash
# ================================================================
# DebLLM Watcher - Core Monitoring Engine
# ================================================================
set -euo pipefail

# Load config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config/debllm.conf"

# ================================================================
# Globals
# ================================================================
TEMP_LOG_FILE="${DEBLLM_LOG_DIR}/current_scan_$(date +%s).log"
ERRORS_FOUND=0
WARNINGS_FOUND=0
ERRORS_FIXED=0
NEW_ERRORS=0

# ================================================================
# Main Functions
# ================================================================

# Collect logs from all monitored services
collect_logs() {
    debllm_log "INFO" "Collecting logs from ${#MONITORED_SERVICES[@]} services..."

    > "$TEMP_LOG_FILE"  # Clear temp file

    for service in "${MONITORED_SERVICES[@]}"; do
        # Check if container exists and is running
        if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
            # Collect last 5 minutes of logs (since last check)
            docker logs "$service" --since="${CHECK_INTERVAL}s" 2>&1 >> "$TEMP_LOG_FILE" || true
        else
            debllm_log "WARN" "Service $service not running - skipping log collection"
        fi
    done

    debllm_log "INFO" "Log collection complete ($(wc -l < "$TEMP_LOG_FILE") lines)"
}

# Search for error patterns
detect_errors() {
    debllm_log "INFO" "Scanning logs for error patterns..."

    # Common error patterns (customize as needed)
    ERRORS_FOUND=$(grep -ciE "error|exception|failed|fatal|critical" "$TEMP_LOG_FILE" || echo "0")
    WARNINGS_FOUND=$(grep -ciE "warn|warning" "$TEMP_LOG_FILE" || echo "0")

    debllm_log "INFO" "Found $ERRORS_FOUND errors, $WARNINGS_FOUND warnings"

    if [[ $ERRORS_FOUND -eq 0 ]] && [[ $WARNINGS_FOUND -eq 0 ]]; then
        return 1  # No issues found
    fi

    return 0  # Issues found
}

# Match error against KB
match_error_to_kb() {
    local error_message="$1"

    # Search all error notes for matching patterns
    find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" -type f | while read -r note; do
        # Extract patterns from note
        local patterns=$(sed -n '/^patterns:/,/^[a-z_]*:/p' "$note" | grep -E '^\s*-' | sed 's/^\s*- "\(.*\)"/\1/')

        # Check each pattern
        while IFS= read -r pattern; do
            if echo "$error_message" | grep -qiE "$pattern"; then
                # Match found!
                local error_id=$(grep "^error_id:" "$note" | cut -d: -f2 | xargs)
                echo "$error_id|$note"
                return 0
            fi
        done <<< "$patterns"
    done

    return 1  # No match
}

# Process a known error
process_known_error() {
    local error_id="$1"
    local note_file="$2"
    local error_message="$3"

    debllm_log "INFO" "Known error detected: $error_id"

    # Update occurrence count
    "${SCRIPT_DIR}/debllm-update-note.sh" "$error_id" --increment

    # Check if auto-fix available
    local auto_fix=$(grep "^auto_fix:" "$note_file" | cut -d: -f2 | xargs)
    local fix_command=$(grep "^fix_command:" "$note_file" | cut -d: -f2- | xargs)

    if [[ "$auto_fix" == "true" ]] && [[ "$AUTO_FIX_ENABLED" == "true" ]]; then
        # Attempt auto-fix
        attempt_auto_fix "$error_id" "$fix_command" "$note_file"
    else
        # Log for manual review
        debllm_log "WARN" "$error_id requires manual intervention (auto_fix=$auto_fix)"

        # Check resolution group and notify
        local resolution_group=$(grep "^resolution_group:" "$note_file" | cut -d: -f2 | xargs)
        notify_resolution_group "$error_id" "$resolution_group" "$error_message"
    fi
}

# Attempt auto-fix
attempt_auto_fix() {
    local error_id="$1"
    local fix_command="$2"
    local note_file="$3"

    debllm_log "INFO" "Attempting auto-fix for $error_id: $fix_command"

    # Execute fix command
    if eval "$fix_command" 2>&1 | tee -a "$DEBLLM_LOG_FILE"; then
        debllm_log "INFO" "✅ Auto-fix successful for $error_id"
        ERRORS_FIXED=$((ERRORS_FIXED + 1))

        # Add note to history
        "${SCRIPT_DIR}/debllm-update-note.sh" "$error_id" --add-note "Auto-fixed successfully"
    else
        debllm_log "ERROR" "❌ Auto-fix failed for $error_id"

        # Add note to history
        "${SCRIPT_DIR}/debllm-update-note.sh" "$error_id" --add-note "Auto-fix attempted but failed"

        # Escalate
        escalate_to_human "$error_id" "Auto-fix failed"
    fi
}

# Process unknown error (create draft note)
process_unknown_error() {
    local error_message="$1"

    debllm_log "WARN" "Unknown error detected: ${error_message:0:100}..."
    NEW_ERRORS=$((NEW_ERRORS + 1))

    # Create draft note
    local draft_file="${DEBLLM_QUEUE_DIR}/DRAFT-$(date +%s)-$NEW_ERRORS.md"

    # Basic draft template
    cat > "$draft_file" <<EOF
---
error_id: DRAFT-$(date +%s)-$NEW_ERRORS
title: Unknown Error (requires classification)
service: unknown
error_domain: unknown
severity: medium
resolution_group: tech-devops
first_seen: $(date -Iseconds | cut -d'T' -f1)
last_seen: $(date -Iseconds | cut -d'T' -f1)
occurrence_count: 1
in_kb: false
auto_fix: false
requires_human: true
patterns:
  - "$(echo "$error_message" | head -n 1)"
---

## 🔍 Symptoms
\`\`\`
$error_message
\`\`\`

## 📝 Notes
This error was auto-detected by DebLLM and requires human classification.

Please review and:
1. Classify error_domain (technical, functional, config, data-quality)
2. Assign severity (low, medium, high, critical)
3. Determine resolution_group
4. Add diagnosis steps and resolution
5. Promote to KB: debllm-promote-note.sh $(basename "$draft_file")

## 📜 History
- **$(date -Iseconds)** (debllm): Auto-detected, created draft
EOF

    debllm_log "INFO" "Created draft note: $draft_file"
}

# Notify resolution group
notify_resolution_group() {
    local error_id="$1"
    local resolution_group="$2"
    local error_message="$3"

    # For now, just log (later: email, Slack, etc.)
    local contact="${RESOLUTION_GROUPS[$resolution_group]:-unknown@helix.local}"

    debllm_log "WARN" "NOTIFY $resolution_group ($contact): $error_id"

    # If notification method is configured, send notification
    if [[ "$NOTIFICATION_METHOD" == "email" ]]; then
        # TODO: Send email
        echo "Subject: [DebLLM] $error_id requires attention" > /tmp/debllm_email.txt
        echo "Error: $error_message" >> /tmp/debllm_email.txt
        echo "Resolution Group: $resolution_group" >> /tmp/debllm_email.txt
        # mail -s "[DebLLM] $error_id" "$contact" < /tmp/debllm_email.txt
        debllm_log "INFO" "Email notification sent to $contact (simulated)"
    fi
}

# Escalate to human
escalate_to_human() {
    local error_id="$1"
    local reason="$2"

    debllm_log "ERROR" "ESCALATION: $error_id - $reason"

    # Add to escalation queue
    echo "$(date -Iseconds)|$error_id|$reason" >> "${DEBLLM_LOG_DIR}/escalations.log"
}

# Main scan routine
run_scan() {
    debllm_log "INFO" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    debllm_log "INFO" "DebLLM Scan Started (mode: $DEBLLM_MODE)"

    # Check if we're in hyper-care mode
    if is_hypercare_active; then
        local remaining=$(get_hypercare_remaining)
        debllm_log "INFO" "🚨 HYPER-CARE MODE ACTIVE ($remaining minutes remaining)"
    fi

    # Check if we're in maintenance window
    if is_maintenance_window; then
        debllm_log "INFO" "🔧 Maintenance window active - severity downgraded"
    fi

    # Collect logs
    collect_logs

    # Detect errors
    if ! detect_errors; then
        debllm_log "INFO" "✅ No errors detected - system healthy"
        return 0
    fi

    # Process each error line
    grep -iE "error|exception|failed|fatal|critical" "$TEMP_LOG_FILE" | while IFS= read -r error_line; do
        # Try to match against KB
        if match_result=$(match_error_to_kb "$error_line"); then
            # Known error
            IFS='|' read -r error_id note_file <<< "$match_result"
            process_known_error "$error_id" "$note_file" "$error_line"
        else
            # Unknown error
            # In hyper-care mode, only alert on NEW critical errors
            if is_hypercare_active && [[ "$ALERT_ONLY_NEW" == "true" ]]; then
                process_unknown_error "$error_line"
            elif ! is_hypercare_active; then
                process_unknown_error "$error_line"
            fi
        fi
    done

    # Summary
    debllm_log "INFO" "Scan complete: $ERRORS_FOUND errors, $WARNINGS_FOUND warnings, $ERRORS_FIXED auto-fixed, $NEW_ERRORS new"
    debllm_log "INFO" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Cleanup
    rm -f "$TEMP_LOG_FILE"
}

# ================================================================
# Entry Point
# ================================================================

# Create log directory if needed
mkdir -p "$DEBLLM_LOG_DIR"

# Run scan
run_scan

# Exit with appropriate code
if [[ $NEW_ERRORS -gt 0 ]] || [[ $((ERRORS_FOUND - ERRORS_FIXED)) -gt 0 ]]; then
    exit 1  # Errors remain
else
    exit 0  # All good
fi
