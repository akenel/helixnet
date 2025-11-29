#!/bin/bash
# ============================================================================
# HelixNet Restore System - Production Ready
# "Disaster Recovery the BLQ way"
# ============================================================================
set -e

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONFIG_FILE="$HOME/.helix/backup.conf"
DEFAULT_BACKUP_DIR="$HOME/helix-backups"

# --- Colors ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Helper Functions ---
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Load Config ---
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        BACKUP_DIR="$DEFAULT_BACKUP_DIR"
    fi
}

# --- Show Banner ---
show_banner() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  🔄 ${GREEN}HelixNet Restore System${NC} - Disaster Recovery                  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}\"Back to normal in minutes, not hours\"${NC}                          ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# --- Show Usage ---
show_usage() {
    echo "Usage: $0 <backup_id> [component]"
    echo ""
    echo "Arguments:"
    echo "  backup_id     Timestamp of backup to restore (e.g., 20251130_143022)"
    echo "  component     Optional: postgres, keycloak, minio, redis, configs, all"
    echo ""
    echo "Options:"
    echo "  -d, --dir PATH    Backup directory (default: $DEFAULT_BACKUP_DIR)"
    echo "  -y, --yes         Skip confirmation prompts"
    echo "  --dry-run         Show what would be restored without doing it"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 20251130_143022              # Restore everything from backup"
    echo "  $0 20251130_143022 postgres     # Restore only PostgreSQL"
    echo "  $0 latest                       # Restore from most recent backup"
    echo "  $0 list                         # List available backups"
    echo ""
}

# --- List Available Backups ---
list_backups() {
    echo ""
    echo -e "${CYAN}Available Backups:${NC}"
    echo "───────────────────────────────────────────────────────────────"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        return 1
    fi

    local count=0
    for backup in $(ls -1dr "$BACKUP_DIR"/*/ 2>/dev/null | head -10); do
        local name=$(basename "$backup")
        local size=$(du -sh "$backup" 2>/dev/null | cut -f1)

        # Check what's in the backup
        local components=""
        [ -d "$backup/postgres" ] && components+="pg "
        [ -d "$backup/keycloak" ] && components+="kc "
        [ -d "$backup/minio" ] && components+="s3 "
        [ -d "$backup/redis" ] && components+="rd "
        [ -d "$backup/configs" ] && components+="cfg "

        if [ $count -eq 0 ]; then
            echo -e "  ${GREEN}● $name${NC}  ($size)  [$components] ${YELLOW}← latest${NC}"
        else
            echo -e "  ○ $name  ($size)  [$components]"
        fi
        count=$((count + 1))
    done

    if [ $count -eq 0 ]; then
        echo "  No backups found in $BACKUP_DIR"
    fi
    echo ""
}

# --- Find Backup Path ---
find_backup() {
    local backup_id="$1"

    if [ "$backup_id" = "latest" ]; then
        backup_id=$(ls -1d "$BACKUP_DIR"/*/ 2>/dev/null | sort -r | head -1 | xargs basename)
    fi

    local backup_path="$BACKUP_DIR/$backup_id"

    if [ ! -d "$backup_path" ]; then
        log_error "Backup not found: $backup_path"
        echo ""
        list_backups
        return 1
    fi

    echo "$backup_path"
}

# --- Restore PostgreSQL ---
restore_postgres() {
    local backup_path="$1"
    local pg_backup="$backup_path/postgres"

    if [ ! -d "$pg_backup" ]; then
        log_warn "No PostgreSQL backup found in this backup set"
        return 1
    fi

    log_info "Restoring PostgreSQL database..."

    # Find the dump file
    local dump_file=$(ls -1t "$pg_backup"/*.sql.gz "$pg_backup"/*.sql 2>/dev/null | head -1)

    if [ -z "$dump_file" ]; then
        log_error "No database dump found!"
        return 1
    fi

    # Check if postgres is running
    if ! docker ps --format '{{.Names}}' | grep -q '^postgres$'; then
        log_error "PostgreSQL container not running! Start with: make core-up"
        return 1
    fi

    # Confirm before restore
    if [ "$SKIP_CONFIRM" != "true" ]; then
        echo ""
        log_warn "⚠️  This will REPLACE the current database!"
        echo "    Backup file: $(basename "$dump_file")"
        echo ""
        read -p "    Continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Aborted"
            return 1
        fi
    fi

    # Restore
    log_info "Dropping and recreating database..."
    docker exec postgres psql -U helix_user -d postgres -c "DROP DATABASE IF EXISTS helix_db;" 2>/dev/null || true
    docker exec postgres psql -U helix_user -d postgres -c "CREATE DATABASE helix_db;" 2>/dev/null

    log_info "Restoring from $dump_file..."
    if [[ "$dump_file" == *.gz ]]; then
        gunzip -c "$dump_file" | docker exec -i postgres psql -U helix_user -d helix_db
    else
        cat "$dump_file" | docker exec -i postgres psql -U helix_user -d helix_db
    fi

    # Verify
    local row_count=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM products" 2>/dev/null | tr -d ' ')
    log_success "PostgreSQL restored! Products count: $row_count"
}

# --- Restore Keycloak ---
restore_keycloak() {
    local backup_path="$1"
    local kc_backup="$backup_path/keycloak"

    if [ ! -d "$kc_backup" ]; then
        log_warn "No Keycloak backup found"
        return 1
    fi

    log_info "Restoring Keycloak data..."

    # Find volume backup
    local vol_backup=$(ls -1t "$kc_backup"/*.tar.gz 2>/dev/null | head -1)

    if [ -n "$vol_backup" ]; then
        log_warn "Keycloak volume restore requires container restart"

        if [ "$SKIP_CONFIRM" != "true" ]; then
            read -p "    Stop Keycloak and restore? (yes/no): " confirm
            if [ "$confirm" != "yes" ]; then
                return 1
            fi
        fi

        # Stop keycloak
        docker stop keycloak 2>/dev/null || true

        # Restore volume
        docker run --rm \
            -v helix-core_keycloak_data:/data \
            -v "$kc_backup":/backup \
            alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$vol_backup") -C /data"

        # Restart
        docker start keycloak
        log_success "Keycloak restored and restarted"
    else
        log_warn "No Keycloak volume backup found"
    fi
}

# --- Restore MinIO ---
restore_minio() {
    local backup_path="$1"
    local minio_backup="$backup_path/minio"

    if [ ! -d "$minio_backup" ]; then
        log_warn "No MinIO backup found"
        return 1
    fi

    log_info "Restoring MinIO data..."

    local vol_backup=$(ls -1t "$minio_backup"/*.tar.gz 2>/dev/null | head -1)

    if [ -n "$vol_backup" ]; then
        local vol_name=$(docker volume ls --format '{{.Name}}' | grep -E 'minio_data|helix-core_minio_data' | head -1)

        if [ -n "$vol_name" ]; then
            docker run --rm \
                -v "$vol_name":/data \
                -v "$minio_backup":/backup \
                alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$vol_backup") -C /data"
            log_success "MinIO restored"
        fi
    fi
}

# --- Restore Redis ---
restore_redis() {
    local backup_path="$1"
    local redis_backup="$backup_path/redis"

    if [ ! -d "$redis_backup" ]; then
        log_warn "No Redis backup found"
        return 1
    fi

    log_info "Restoring Redis data..."

    local dump_file=$(ls -1t "$redis_backup"/*.rdb 2>/dev/null | head -1)

    if [ -n "$dump_file" ]; then
        docker stop redis 2>/dev/null || true
        docker cp "$dump_file" redis:/data/dump.rdb
        docker start redis
        log_success "Redis restored"
    fi
}

# --- Restore Configs ---
restore_configs() {
    local backup_path="$1"
    local cfg_backup="$backup_path/configs"

    if [ ! -d "$cfg_backup" ]; then
        log_warn "No config backup found"
        return 1
    fi

    log_info "Restoring configuration files..."

    # Restore .env
    local env_file=$(ls -1t "$cfg_backup"/env_* 2>/dev/null | head -1)
    if [ -n "$env_file" ]; then
        cp "$env_file" "$REPO_ROOT/.env.restored"
        log_success "Environment restored to .env.restored (review before using)"
    fi

    log_success "Configs restored"
}

# --- Full Restore ---
restore_all() {
    local backup_path="$1"

    log_info "Starting full restore from $backup_path"
    echo ""

    # Show manifest
    if [ -f "$backup_path/MANIFEST.txt" ]; then
        cat "$backup_path/MANIFEST.txt"
        echo ""
    fi

    if [ "$SKIP_CONFIRM" != "true" ]; then
        echo -e "${RED}⚠️  WARNING: This will overwrite current data!${NC}"
        read -p "    Type 'RESTORE' to confirm: " confirm
        if [ "$confirm" != "RESTORE" ]; then
            log_info "Aborted"
            return 1
        fi
    fi

    echo ""

    [ -d "$backup_path/postgres" ] && restore_postgres "$backup_path"
    [ -d "$backup_path/keycloak" ] && restore_keycloak "$backup_path"
    [ -d "$backup_path/minio" ] && restore_minio "$backup_path"
    [ -d "$backup_path/redis" ] && restore_redis "$backup_path"
    [ -d "$backup_path/configs" ] && restore_configs "$backup_path"

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ RESTORE COMPLETE${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Restored from: $(basename "$backup_path")"
    echo ""
    echo "  Recommended: Restart services with 'make down && make up'"
    echo ""
}

# --- Verify Checksums ---
verify_checksums() {
    local backup_path="$1"
    local checksum_file="$backup_path/CHECKSUMS.sha256"

    if [ ! -f "$checksum_file" ]; then
        log_warn "No checksum file found - cannot verify integrity"
        return 1
    fi

    log_info "Verifying SHA256 checksums..."

    # Verify checksums
    local failed=0
    while IFS= read -r line; do
        local expected_hash=$(echo "$line" | awk '{print $1}')
        local file_path=$(echo "$line" | awk '{print $2}')
        local full_path="$backup_path/$file_path"

        if [ -f "$full_path" ]; then
            local actual_hash=$(sha256sum "$full_path" | awk '{print $1}')
            if [ "$expected_hash" = "$actual_hash" ]; then
                echo -e "  ${GREEN}✓${NC} $file_path"
            else
                echo -e "  ${RED}✗${NC} $file_path - CHECKSUM MISMATCH!"
                echo "      Expected: ${expected_hash:0:16}..."
                echo "      Actual:   ${actual_hash:0:16}..."
                failed=$((failed + 1))
            fi
        else
            echo -e "  ${RED}✗${NC} $file_path - FILE MISSING!"
            failed=$((failed + 1))
        fi
    done < "$checksum_file"

    if [ $failed -gt 0 ]; then
        log_error "$failed file(s) failed checksum verification!"
        return 1
    fi

    log_success "All checksums verified"
    return 0
}

# --- Check Backup Verification Status ---
check_verification_status() {
    local backup_path="$1"
    local verification_file="$backup_path/.verification"

    if [ -f "$verification_file" ]; then
        local status=$(grep "STATUS=" "$verification_file" | cut -d= -f2)
        if [ "$status" = "FAILED" ]; then
            log_error "This backup FAILED verification during creation!"
            echo ""
            echo -e "${RED}⚠️  WARNING: Restoring from a failed backup is dangerous!${NC}"
            echo "    The backup may be empty or corrupted."
            echo ""
            if [ "$SKIP_CONFIRM" != "true" ]; then
                read -p "    Continue anyway? (yes/no): " confirm
                if [ "$confirm" != "yes" ]; then
                    return 1
                fi
            fi
        fi
    fi
    return 0
}

# --- Post-Restore Verification ---
verify_restore() {
    local backup_path="$1"

    log_info "Verifying restore integrity..."

    local backup_counts="$backup_path/postgres/row_counts.txt"
    local all_ok=true

    if [ -f "$backup_counts" ]; then
        # Compare row counts
        local backup_products=$(grep "products" "$backup_counts" 2>/dev/null | awk '{print $NF}' | tr -d ' ')
        local backup_transactions=$(grep "transactions" "$backup_counts" 2>/dev/null | awk '{print $NF}' | tr -d ' ')

        local restored_products=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM products" 2>/dev/null | tr -d ' ')
        local restored_transactions=$(docker exec postgres psql -U helix_user -d helix_db -t -c "SELECT COUNT(*) FROM transactions" 2>/dev/null | tr -d ' ')

        echo ""
        echo "  Row Count Comparison:"
        echo "  ─────────────────────────────────────────────"
        printf "  %-15s %10s %10s %s\n" "Table" "Backup" "Restored" "Status"
        echo "  ─────────────────────────────────────────────"

        # Products
        if [ "$backup_products" = "$restored_products" ]; then
            printf "  %-15s %10s %10s ${GREEN}✓${NC}\n" "products" "$backup_products" "$restored_products"
        else
            printf "  %-15s %10s %10s ${RED}✗ MISMATCH${NC}\n" "products" "$backup_products" "$restored_products"
            all_ok=false
        fi

        # Transactions
        if [ "$backup_transactions" = "$restored_transactions" ]; then
            printf "  %-15s %10s %10s ${GREEN}✓${NC}\n" "transactions" "$backup_transactions" "$restored_transactions"
        else
            printf "  %-15s %10s %10s ${RED}✗ MISMATCH${NC}\n" "transactions" "$backup_transactions" "$restored_transactions"
            all_ok=false
        fi

        echo "  ─────────────────────────────────────────────"
        echo ""
    fi

    if [ "$all_ok" = true ]; then
        log_success "Restore verification PASSED"
        return 0
    else
        log_error "Restore verification FAILED - row counts don't match!"
        return 1
    fi
}

# --- Verify Backup ---
verify_backup() {
    local backup_path="$1"

    echo ""
    echo -e "${CYAN}Verifying backup: $(basename "$backup_path")${NC}"
    echo "───────────────────────────────────────────────────────────────"

    local all_ok=true

    # Check verification status from backup time
    if [ -f "$backup_path/.verification" ]; then
        local status=$(grep "STATUS=" "$backup_path/.verification" | cut -d= -f2)
        local verified_at=$(grep "VERIFIED_AT=" "$backup_path/.verification" | cut -d= -f2)
        if [ "$status" = "VERIFIED" ]; then
            echo -e "  ${GREEN}✓${NC} Backup verified at creation: $verified_at"
        else
            echo -e "  ${RED}✗${NC} Backup FAILED verification at creation!"
            all_ok=false
        fi
    fi

    # Check PostgreSQL
    if [ -d "$backup_path/postgres" ]; then
        local pg_dump=$(ls -1 "$backup_path/postgres"/*.sql* 2>/dev/null | head -1)
        if [ -n "$pg_dump" ]; then
            local size=$(du -h "$pg_dump" | cut -f1)
            echo -e "  ${GREEN}✓${NC} PostgreSQL dump: $size"

            # Check if dump is not suspiciously small
            local bytes
            if stat --version 2>/dev/null | grep -q GNU; then
                bytes=$(stat -c%s "$pg_dump" 2>/dev/null || echo "0")
            else
                bytes=$(stat -f%z "$pg_dump" 2>/dev/null || echo "0")
            fi
            if [ "$bytes" -lt 1000 ]; then
                echo -e "    ${RED}⚠️  WARNING: Dump file is very small - may be empty!${NC}"
                all_ok=false
            fi
        else
            echo -e "  ${RED}✗${NC} PostgreSQL dump: MISSING"
            all_ok=false
        fi
    fi

    # Check row counts if available
    if [ -f "$backup_path/postgres/row_counts.txt" ]; then
        echo "    Expected row counts:"
        grep -E "products|transactions|users" "$backup_path/postgres/row_counts.txt" 2>/dev/null | while read line; do
            echo "      $line"
        done
    fi

    # Verify checksums if available
    if [ -f "$backup_path/CHECKSUMS.sha256" ]; then
        echo ""
        verify_checksums "$backup_path" || all_ok=false
    else
        echo -e "  ${YELLOW}⚠${NC} No checksums file - cannot verify file integrity"
    fi

    # Check other components
    echo ""
    echo "  Components:"
    [ -d "$backup_path/keycloak" ] && echo -e "    ${GREEN}✓${NC} Keycloak data"
    [ -d "$backup_path/minio" ] && echo -e "    ${GREEN}✓${NC} MinIO data"
    [ -d "$backup_path/redis" ] && echo -e "    ${GREEN}✓${NC} Redis data"
    [ -d "$backup_path/configs" ] && echo -e "    ${GREEN}✓${NC} Config files"

    echo ""
    if [ "$all_ok" = true ]; then
        echo -e "  ${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "  ${GREEN}  BACKUP VERIFICATION: PASSED${NC}"
        echo -e "  ${GREEN}═══════════════════════════════════════════════════════════${NC}"
    else
        echo -e "  ${RED}═══════════════════════════════════════════════════════════${NC}"
        echo -e "  ${RED}  BACKUP VERIFICATION: FAILED${NC}"
        echo -e "  ${RED}═══════════════════════════════════════════════════════════${NC}"
    fi
    echo ""

    [ "$all_ok" = true ]
}

# --- Main ---
main() {
    load_config

    local backup_id=""
    local component="all"
    local action="restore"
    SKIP_CONFIRM=false
    DRY_RUN=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -y|--yes)
                SKIP_CONFIRM=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            list)
                action="list"
                shift
                ;;
            verify)
                action="verify"
                backup_id="$2"
                shift 2
                ;;
            postgres|keycloak|minio|redis|configs|all)
                component="$1"
                shift
                ;;
            *)
                if [ -z "$backup_id" ]; then
                    backup_id="$1"
                fi
                shift
                ;;
        esac
    done

    show_banner

    case $action in
        list)
            list_backups
            ;;
        verify)
            backup_path=$(find_backup "$backup_id") || exit 1
            verify_backup "$backup_path"
            ;;
        restore)
            if [ -z "$backup_id" ]; then
                show_usage
                exit 1
            fi

            backup_path=$(find_backup "$backup_id") || exit 1

            if [ "$DRY_RUN" = true ]; then
                log_info "DRY RUN - Would restore from: $backup_path"
                verify_backup "$backup_path"
                exit 0
            fi

            case $component in
                all)
                    restore_all "$backup_path"
                    ;;
                postgres)
                    restore_postgres "$backup_path"
                    ;;
                keycloak)
                    restore_keycloak "$backup_path"
                    ;;
                minio)
                    restore_minio "$backup_path"
                    ;;
                redis)
                    restore_redis "$backup_path"
                    ;;
                configs)
                    restore_configs "$backup_path"
                    ;;
            esac
            ;;
    esac
}

main "$@"
