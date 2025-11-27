#!/usr/bin/env bash
# ================================================================
# DebLLM Note Updater - Update Error Note Metadata
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
Usage: $(basename "$0") <error_id> [OPTIONS]

Update an error note's metadata (occurrence count, timestamps, etc.).

OPTIONS:
    --increment             Increment occurrence count (default)
    --set-count <N>         Set occurrence count to N
    --update-timestamp      Update last_seen timestamp to now (default with --increment)
    --add-note <text>       Append a note to the history section
    --set-severity <sev>    Update severity (low|medium|high|critical)
    --set-auto-fix <bool>   Enable/disable auto-fix (true|false)
    -h, --help              Show this help message

EXAMPLES:
    # Increment occurrence count and update timestamp
    $(basename "$0") ERROR-001

    # Add a note to the history
    $(basename "$0") ERROR-001 --add-note "Auto-fixed by debllm at \$(date)"

    # Change severity
    $(basename "$0") ERROR-042 --set-severity critical

    # Disable auto-fix
    $(basename "$0") ERROR-001 --set-auto-fix false

EOF
    exit 0
}

# ================================================================
# Helper Functions
# ================================================================

# Find note file by error ID
find_note() {
    local error_id="$1"
    find "$DEBLLM_NOTES_DIR" -name "ERROR-*.md" -type f | while read -r note; do
        if grep -q "^error_id: $error_id$" "$note"; then
            echo "$note"
            return 0
        fi
    done
    return 1
}

# Increment occurrence count
increment_count() {
    local note_file="$1"
    local current_count=$(grep "^occurrence_count:" "$note_file" | cut -d: -f2 | xargs)
    local new_count=$((current_count + 1))

    sed -i "s/^occurrence_count: .*/occurrence_count: $new_count/" "$note_file"
    debllm_log "INFO" "Updated $note_file occurrence count: $current_count → $new_count"
}

# Set occurrence count
set_count() {
    local note_file="$1"
    local new_count="$2"

    sed -i "s/^occurrence_count: .*/occurrence_count: $new_count/" "$note_file"
    debllm_log "INFO" "Set $note_file occurrence count to $new_count"
}

# Update last_seen timestamp
update_timestamp() {
    local note_file="$1"
    local now=$(date -Iseconds | cut -d'T' -f1)

    sed -i "s/^last_seen: .*/last_seen: $now/" "$note_file"
    debllm_log "INFO" "Updated $note_file last_seen to $now"
}

# Add note to history section
add_history_note() {
    local note_file="$1"
    local note_text="$2"
    local timestamp=$(date -Iseconds)
    local who="${USER:-debllm}"

    # Find the history section and append
    # This is a bit tricky - we'll add before the last ## section or at EOF
    local history_entry="- **$timestamp** ($who): $note_text"

    # Check if ## 📜 History exists
    if grep -q "## 📜 History" "$note_file"; then
        # Insert after the History header
        sed -i "/## 📜 History/a $history_entry" "$note_file"
    else
        # Add History section before ## 🔗 References or at end
        if grep -q "## 🔗 References" "$note_file"; then
            sed -i "/## 🔗 References/i ## 📜 History\n$history_entry\n" "$note_file"
        else
            echo "" >> "$note_file"
            echo "## 📜 History" >> "$note_file"
            echo "$history_entry" >> "$note_file"
        fi
    fi

    debllm_log "INFO" "Added history note to $note_file: $note_text"
}

# Update severity
set_severity() {
    local note_file="$1"
    local new_severity="$2"

    # Validate severity
    if [[ ! "$new_severity" =~ ^(low|medium|high|critical)$ ]]; then
        echo "Error: Invalid severity. Must be: low, medium, high, or critical"
        exit 1
    fi

    sed -i "s/^severity: .*/severity: $new_severity/" "$note_file"
    debllm_log "WARN" "Changed $note_file severity to $new_severity"
}

# Update auto-fix flag
set_auto_fix() {
    local note_file="$1"
    local new_value="$2"

    # Validate boolean
    if [[ ! "$new_value" =~ ^(true|false)$ ]]; then
        echo "Error: Invalid auto-fix value. Must be: true or false"
        exit 1
    fi

    sed -i "s/^auto_fix: .*/auto_fix: $new_value/" "$note_file"
    debllm_log "WARN" "Changed $note_file auto_fix to $new_value"
}

# ================================================================
# Main
# ================================================================

# Parse arguments
if [[ $# -eq 0 ]]; then
    usage
fi

ERROR_ID="$1"
shift

# Find the note file
NOTE_FILE=$(find_note "$ERROR_ID")
if [[ -z "$NOTE_FILE" ]]; then
    echo "Error: Note not found for error ID: $ERROR_ID"
    exit 1
fi

# Default action: increment count and update timestamp
ACTION="increment"
UPDATE_TIMESTAMP=false

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        --increment)
            ACTION="increment"
            UPDATE_TIMESTAMP=true
            shift
            ;;
        --set-count)
            ACTION="set-count"
            SET_COUNT_VALUE="$2"
            shift 2
            ;;
        --update-timestamp)
            UPDATE_TIMESTAMP=true
            shift
            ;;
        --add-note)
            ACTION="add-note"
            NOTE_TEXT="$2"
            shift 2
            ;;
        --set-severity)
            ACTION="set-severity"
            NEW_SEVERITY="$2"
            shift 2
            ;;
        --set-auto-fix)
            ACTION="set-auto-fix"
            NEW_AUTO_FIX="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Error: Unknown option: $1"
            usage
            ;;
    esac
done

# Execute action
case "$ACTION" in
    increment)
        increment_count "$NOTE_FILE"
        UPDATE_TIMESTAMP=true
        ;;
    set-count)
        set_count "$NOTE_FILE" "$SET_COUNT_VALUE"
        ;;
    add-note)
        add_history_note "$NOTE_FILE" "$NOTE_TEXT"
        ;;
    set-severity)
        set_severity "$NOTE_FILE" "$NEW_SEVERITY"
        ;;
    set-auto-fix)
        set_auto_fix "$NOTE_FILE" "$NEW_AUTO_FIX"
        ;;
esac

# Update timestamp if requested
if [[ "$UPDATE_TIMESTAMP" == true ]]; then
    update_timestamp "$NOTE_FILE"
fi

echo "✅ Updated note: $ERROR_ID"
echo "   File: $NOTE_FILE"
