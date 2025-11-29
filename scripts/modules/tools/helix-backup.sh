#!/bin/bash
# ============================================================================
# HelixNet Backup System - Production Ready
# "Because Chuck needs his formulas safe" - BLQ Edition
# ============================================================================
set -e

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CONFIG_FILE="$HOME/.helix/backup.conf"
DEFAULT_BACKUP_DIR="$HOME/helix-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

# --- Load or Create Config ---
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        mkdir -p "$(dirname "$CONFIG_FILE")"
        cat > "$CONFIG_FILE" <<EOF
# HelixNet Backup Configuration
# Generated: $(date)

# Backup destination directory
BACKUP_DIR="$DEFAULT_BACKUP_DIR"

# Retention: How many backups to keep (0 = unlimited)
BACKUP_RETENTION=7

# Components to backup by default
BACKUP_POSTGRES=true
BACKUP_KEYCLOAK=true
BACKUP_MINIO=true
BACKUP_REDIS=false
BACKUP_CONFIGS=true

# Compression (gzip, none)
COMPRESSION="gzip"
EOF
        log_info "Created default config at $CONFIG_FILE"
        source "$CONFIG_FILE"
    fi
}

# --- Show Banner ---
show_banner() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  💾 ${GREEN}HelixNet Backup System${NC} - Production Ready                    ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}\"Because Chuck needs his formulas safe\"${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# --- Show Usage ---
show_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  all         Backup everything (postgres, keycloak, minio, configs)"
    echo "  postgres    Backup PostgreSQL database only"
    echo "  keycloak    Backup Keycloak data only"
    echo "  minio       Backup MinIO/S3 data only"
    echo "  redis       Backup Redis data only"
    echo "  configs     Backup configuration files only"
    echo "  list        List available backups"
    echo "  config      Show/edit backup configuration"
    echo ""
    echo "Options:"
    echo "  -d, --dir PATH    Override backup directory"
    echo "  -q, --quiet       Minimal output"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Full backup to default location"
    echo "  $0 postgres               # Backup only PostgreSQL"
    echo "  $0 all -d /mnt/usb        # Backup to USB drive"
    echo "  $0 list                   # Show available backups"
    echo ""
}

# --- Backup PostgreSQL ---
backup_postgres() {
    local backup_path="$1/postgres"
    mkdir -p "$backup_path"

    log_info "Backing up PostgreSQL database..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q '^postgres$'; then
        log_error "PostgreSQL container not running!"
        return 1
    fi

    # Full database dump
    local dump_file="$backup_path/helix_db_${TIMESTAMP}.sql"
    if [ "$COMPRESSION" = "gzip" ]; then
        docker exec postgres pg_dump -U helix_user -d helix_db | gzip > "${dump_file}.gz"
        log_success "Database dumped to ${dump_file}.gz"
        echo "$(du -h "${dump_file}.gz" | cut -f1)" > "$backup_path/size.txt"
    else
        docker exec postgres pg_dump -U helix_user -d helix_db > "$dump_file"
        log_success "Database dumped to $dump_file"
        echo "$(du -h "$dump_file" | cut -f1)" > "$backup_path/size.txt"
    fi

    # Record row counts for verification
    docker exec postgres psql -U helix_user -d helix_db -t -c "
        SELECT 'products' as table_name, COUNT(*) as rows FROM products
        UNION ALL SELECT 'transactions', COUNT(*) FROM transactions
        UNION ALL SELECT 'line_items', COUNT(*) FROM line_items
        UNION ALL SELECT 'users', COUNT(*) FROM users
    " > "$backup_path/row_counts.txt" 2>/dev/null || true

    log_success "PostgreSQL backup complete"
}

# --- Backup Keycloak ---
backup_keycloak() {
    local backup_path="$1/keycloak"
    mkdir -p "$backup_path"

    log_info "Backing up Keycloak data..."

    # Export realm via API if possible, otherwise backup volume
    if docker ps --format '{{.Names}}' | grep -q '^keycloak$'; then
        # Try realm export
        docker exec keycloak /opt/keycloak/bin/kc.sh export \
            --dir /tmp/keycloak-export \
            --realm kc-pos-realm-dev 2>/dev/null || true

        docker cp keycloak:/tmp/keycloak-export "$backup_path/" 2>/dev/null || {
            log_warn "Realm export failed, backing up volume instead"
        }
    fi

    # Backup the volume data
    if docker volume ls --format '{{.Name}}' | grep -q 'keycloak_data'; then
        docker run --rm \
            -v helix-core_keycloak_data:/data:ro \
            -v "$backup_path":/backup \
            alpine tar czf /backup/keycloak_volume_${TIMESTAMP}.tar.gz -C /data . 2>/dev/null || {
            log_warn "Volume backup had issues, may be partial"
        }
    fi

    log_success "Keycloak backup complete"
}

# --- Backup MinIO ---
backup_minio() {
    local backup_path="$1/minio"
    mkdir -p "$backup_path"

    log_info "Backing up MinIO/S3 data..."

    # Backup volume
    if docker volume ls --format '{{.Name}}' | grep -q 'minio_data\|helix-core_minio_data'; then
        local vol_name=$(docker volume ls --format '{{.Name}}' | grep -E 'minio_data|helix-core_minio_data' | head -1)
        docker run --rm \
            -v "$vol_name":/data:ro \
            -v "$backup_path":/backup \
            alpine tar czf /backup/minio_volume_${TIMESTAMP}.tar.gz -C /data . 2>/dev/null
        log_success "MinIO volume backed up"
    else
        log_warn "MinIO volume not found"
    fi

    log_success "MinIO backup complete"
}

# --- Backup Redis ---
backup_redis() {
    local backup_path="$1/redis"
    mkdir -p "$backup_path"

    log_info "Backing up Redis data..."

    if docker ps --format '{{.Names}}' | grep -q '^redis$'; then
        # Trigger RDB save
        docker exec redis redis-cli BGSAVE 2>/dev/null || true
        sleep 2

        # Copy dump file
        docker cp redis:/data/dump.rdb "$backup_path/dump_${TIMESTAMP}.rdb" 2>/dev/null || {
            log_warn "Redis dump copy failed"
        }
    fi

    log_success "Redis backup complete"
}

# --- Backup Configs ---
backup_configs() {
    local backup_path="$1/configs"
    mkdir -p "$backup_path"

    log_info "Backing up configuration files..."

    # Backup .env if exists
    [ -f "$REPO_ROOT/.env" ] && cp "$REPO_ROOT/.env" "$backup_path/env_${TIMESTAMP}"

    # Backup Traefik configs
    [ -d "$REPO_ROOT/compose/helix-core/traefik" ] && \
        tar czf "$backup_path/traefik_${TIMESTAMP}.tar.gz" \
            -C "$REPO_ROOT/compose/helix-core" traefik 2>/dev/null || true

    # Backup Keycloak realm files
    [ -d "$REPO_ROOT/compose/helix-core/keycloak/realms" ] && \
        tar czf "$backup_path/keycloak_realms_${TIMESTAMP}.tar.gz" \
            -C "$REPO_ROOT/compose/helix-core/keycloak" realms 2>/dev/null || true

    # Backup helix config
    [ -f "$CONFIG_FILE" ] && cp "$CONFIG_FILE" "$backup_path/backup.conf"

    log_success "Configs backup complete"
}

# --- Generate SHA256 Checksums ---
generate_checksums() {
    local backup_path="$1"
    local checksum_file="$backup_path/CHECKSUMS.sha256"

    log_info "Generating SHA256 checksums..."

    # Find all backup files and generate checksums
    (cd "$backup_path" && find . -type f \( -name "*.sql" -o -name "*.sql.gz" -o -name "*.tar.gz" -o -name "*.rdb" \) \
        -exec sha256sum {} \; > CHECKSUMS.sha256 2>/dev/null) || true

    if [ -s "$checksum_file" ]; then
        log_success "Checksums saved to CHECKSUMS.sha256"
    else
        log_warn "No backup files found for checksumming"
    fi
}

# --- Verify Backup Not Empty ---
verify_backup_integrity() {
    local backup_path="$1"
    local is_valid=true
    local min_dump_size=1000  # Minimum 1KB for a valid dump

    log_info "Verifying backup integrity..."

    # Check PostgreSQL dump
    if [ -d "$backup_path/postgres" ]; then
        local pg_dump=$(ls -1 "$backup_path/postgres"/*.sql* 2>/dev/null | head -1)
        if [ -n "$pg_dump" ] && [ -f "$pg_dump" ]; then
            # Get file size (cross-platform)
            local size
            if stat --version 2>/dev/null | grep -q GNU; then
                size=$(stat -c%s "$pg_dump" 2>/dev/null || echo "0")
            else
                size=$(stat -f%z "$pg_dump" 2>/dev/null || echo "0")
            fi

            if [ "$size" -lt "$min_dump_size" ]; then
                log_error "PostgreSQL dump is too small ($size bytes) - likely empty!"
                is_valid=false
            else
                # Check for actual data (COPY statements in pg_dump format)
                local has_data=0
                if [[ "$pg_dump" == *.gz ]]; then
                    has_data=$(gunzip -c "$pg_dump" 2>/dev/null | grep -c "^COPY public\." 2>/dev/null) || has_data=0
                else
                    has_data=$(grep -c "^COPY public\." "$pg_dump" 2>/dev/null) || has_data=0
                fi
                # Ensure clean integer (remove any non-digits)
                has_data=$(echo "$has_data" | tr -cd '0-9')
                has_data=$((has_data + 0))

                if [ "$has_data" -lt 5 ]; then
                    log_warn "PostgreSQL dump may be empty (only $has_data tables)"
                    # Don't fail, just warn - might be intentionally empty DB
                else
                    log_success "PostgreSQL verified: $has_data tables, $(numfmt --to=iec $size 2>/dev/null || echo "${size}B")"
                fi
            fi
        else
            log_error "No PostgreSQL dump file found!"
            is_valid=false
        fi
    fi

    # Store verification result and timestamp
    if [ "$is_valid" = true ]; then
        echo "STATUS=VERIFIED" > "$backup_path/.verification"
        echo "VERIFIED_AT=$(date -Iseconds)" >> "$backup_path/.verification"
        echo "VERIFIED_BY=$(whoami)@$(hostname)" >> "$backup_path/.verification"
        return 0
    else
        echo "STATUS=FAILED" > "$backup_path/.verification"
        echo "FAILED_AT=$(date -Iseconds)" >> "$backup_path/.verification"
        log_error "Backup verification FAILED - do not use for restore!"
        return 1
    fi
}

# --- Create Backup Manifest ---
create_manifest() {
    local backup_path="$1"

    # Generate checksums first
    generate_checksums "$backup_path"

    # Get checksum of the database dump for easy verification
    local pg_checksum="N/A"
    local pg_file="N/A"
    if [ -f "$backup_path/CHECKSUMS.sha256" ]; then
        local checksum_line=$(grep -E "helix_db.*\.sql" "$backup_path/CHECKSUMS.sha256" | head -1)
        if [ -n "$checksum_line" ]; then
            pg_checksum=$(echo "$checksum_line" | awk '{print $1}')
            pg_file=$(echo "$checksum_line" | awk '{print $2}')
        fi
    fi

    # Get row counts
    local products_count="N/A"
    local transactions_count="N/A"
    local users_count="N/A"
    if [ -f "$backup_path/postgres/row_counts.txt" ]; then
        products_count=$(grep "products" "$backup_path/postgres/row_counts.txt" 2>/dev/null | awk '{print $NF}' | tr -d ' ' || echo "N/A")
        transactions_count=$(grep "transactions" "$backup_path/postgres/row_counts.txt" 2>/dev/null | awk '{print $NF}' | tr -d ' ' || echo "N/A")
        users_count=$(grep "users" "$backup_path/postgres/row_counts.txt" 2>/dev/null | awk '{print $NF}' | tr -d ' ' || echo "N/A")
    fi

    cat > "$backup_path/MANIFEST.txt" <<EOF
═══════════════════════════════════════════════════════════════════
HelixNet Backup Manifest
═══════════════════════════════════════════════════════════════════

Backup ID:      ${TIMESTAMP}
Created:        $(date)
Host:           $(hostname)
User:           $(whoami)

Components Included:
$([ -d "$backup_path/postgres" ] && echo "  ✓ PostgreSQL" || echo "  ✗ PostgreSQL")
$([ -d "$backup_path/keycloak" ] && echo "  ✓ Keycloak" || echo "  ✗ Keycloak")
$([ -d "$backup_path/minio" ] && echo "  ✓ MinIO" || echo "  ✗ MinIO")
$([ -d "$backup_path/redis" ] && echo "  ✓ Redis" || echo "  ✗ Redis")
$([ -d "$backup_path/configs" ] && echo "  ✓ Configs" || echo "  ✗ Configs")

Database Integrity:
  Products:       ${products_count}
  Transactions:   ${transactions_count}
  Users:          ${users_count}

SHA256 Checksum (PostgreSQL):
  File:     ${pg_file}
  SHA256:   ${pg_checksum}

Total Size:     $(du -sh "$backup_path" | cut -f1)

═══════════════════════════════════════════════════════════════════
VERIFICATION COMMANDS
═══════════════════════════════════════════════════════════════════

Verify checksums:
  cd $backup_path && sha256sum -c CHECKSUMS.sha256

Restore command:
  make restore BACKUP=$TIMESTAMP

═══════════════════════════════════════════════════════════════════
EOF

    # Verify backup integrity
    if ! verify_backup_integrity "$backup_path"; then
        log_error "Backup created but FAILED verification!"
        echo ""
        echo -e "${RED}⚠️  WARNING: This backup may be corrupt or empty!${NC}"
        echo "    Check the logs above for details."
        echo ""
        return 1
    fi

    log_success "Manifest created with checksums"
}

# --- List Backups ---
list_backups() {
    echo ""
    echo -e "${CYAN}Available Backups in ${BACKUP_DIR}:${NC}"
    echo "───────────────────────────────────────────────────────────────"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_warn "Backup directory does not exist: $BACKUP_DIR"
        return
    fi

    local count=0
    for backup in $(ls -1dr "$BACKUP_DIR"/*/ 2>/dev/null | head -20); do
        local name=$(basename "$backup")
        local size=$(du -sh "$backup" 2>/dev/null | cut -f1)
        local manifest="$backup/MANIFEST.txt"

        if [ -f "$manifest" ]; then
            echo -e "  ${GREEN}●${NC} $name  (${size})"
            count=$((count + 1))
        fi
    done

    if [ $count -eq 0 ]; then
        echo "  No backups found"
    fi
    echo ""
}

# --- Show Config ---
show_config() {
    echo ""
    echo -e "${CYAN}Current Backup Configuration:${NC}"
    echo "───────────────────────────────────────────────────────────────"
    echo "  Config File:     $CONFIG_FILE"
    echo "  Backup Dir:      $BACKUP_DIR"
    echo "  Retention:       $BACKUP_RETENTION backups"
    echo "  Compression:     $COMPRESSION"
    echo ""
    echo "  Components:"
    echo "    PostgreSQL:    $BACKUP_POSTGRES"
    echo "    Keycloak:      $BACKUP_KEYCLOAK"
    echo "    MinIO:         $BACKUP_MINIO"
    echo "    Redis:         $BACKUP_REDIS"
    echo "    Configs:       $BACKUP_CONFIGS"
    echo ""
    echo "Edit with: nano $CONFIG_FILE"
    echo ""
}

# --- Cleanup Old Backups ---
cleanup_old_backups() {
    if [ "$BACKUP_RETENTION" -gt 0 ]; then
        local backup_count=$(ls -1d "$BACKUP_DIR"/*/ 2>/dev/null | wc -l)
        if [ "$backup_count" -gt "$BACKUP_RETENTION" ]; then
            local to_delete=$((backup_count - BACKUP_RETENTION))
            log_info "Cleaning up $to_delete old backup(s)..."
            ls -1dt "$BACKUP_DIR"/*/ | tail -n "$to_delete" | xargs rm -rf
        fi
    fi
}

# --- Full Backup ---
backup_all() {
    local backup_path="$BACKUP_DIR/$TIMESTAMP"
    mkdir -p "$backup_path"

    log_info "Starting full backup to $backup_path"
    echo ""

    [ "$BACKUP_POSTGRES" = "true" ] && backup_postgres "$backup_path"
    [ "$BACKUP_KEYCLOAK" = "true" ] && backup_keycloak "$backup_path"
    [ "$BACKUP_MINIO" = "true" ] && backup_minio "$backup_path"
    [ "$BACKUP_REDIS" = "true" ] && backup_redis "$backup_path"
    [ "$BACKUP_CONFIGS" = "true" ] && backup_configs "$backup_path"

    create_manifest "$backup_path"
    cleanup_old_backups

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ BACKUP COMPLETE${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Backup ID:    $TIMESTAMP"
    echo "  Location:     $backup_path"
    echo "  Size:         $(du -sh "$backup_path" | cut -f1)"
    echo ""
    echo "  To restore:   make restore BACKUP=$TIMESTAMP"
    echo "  To list:      make backup-list"
    echo ""
}

# --- Main ---
main() {
    load_config

    # Parse arguments
    local command="${1:-help}"
    shift || true

    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dir)
                BACKUP_DIR="$2"
                shift 2
                ;;
            -q|--quiet)
                exec > /dev/null 2>&1
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done

    show_banner

    case $command in
        all)
            backup_all
            ;;
        postgres)
            backup_path="$BACKUP_DIR/$TIMESTAMP"
            mkdir -p "$backup_path"
            backup_postgres "$backup_path"
            create_manifest "$backup_path"
            ;;
        keycloak)
            backup_path="$BACKUP_DIR/$TIMESTAMP"
            mkdir -p "$backup_path"
            backup_keycloak "$backup_path"
            create_manifest "$backup_path"
            ;;
        minio)
            backup_path="$BACKUP_DIR/$TIMESTAMP"
            mkdir -p "$backup_path"
            backup_minio "$backup_path"
            create_manifest "$backup_path"
            ;;
        redis)
            backup_path="$BACKUP_DIR/$TIMESTAMP"
            mkdir -p "$backup_path"
            backup_redis "$backup_path"
            create_manifest "$backup_path"
            ;;
        configs)
            backup_path="$BACKUP_DIR/$TIMESTAMP"
            mkdir -p "$backup_path"
            backup_configs "$backup_path"
            create_manifest "$backup_path"
            ;;
        list)
            list_backups
            ;;
        config)
            show_config
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
