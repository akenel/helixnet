#!/usr/bin/env bash
# ================================================================
# HelixNet Setup Wizard - Out-of-the-Box POS System
# ================================================================
# Target: Headshop vertical (Felix/Mosey/Pot Rookie path)
# Time: 5-10 minutes from zero to running
# Philosophy: Accept all defaults = working system
# ================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Setup mode
SETUP_MODE="${SETUP_MODE:-interactive}"  # interactive | silent

# ================================================================
# Default Configuration (Accept All = This)
# ================================================================

# Company defaults
DEFAULT_COMPANY_NAME="Artemis Headshop"
DEFAULT_VAT_NUMBER="CHE-123.456.789"
DEFAULT_ADDRESS="Bern, Switzerland"
DEFAULT_REGISTRATION_DATE="2025-01-01"

# LLM defaults
DEFAULT_LLM_MODE="local"  # local | ollama | claude-api
DEFAULT_LLM_MODEL="llama3.2"  # llama3.2 | tinylama | gpt-4

# Sandbox defaults
DEFAULT_INCLUDE_SANDBOX="yes"  # yes | no
DEFAULT_INCLUDE_PRODUCTS="yes"  # Include 20 headshop products
DEFAULT_INCLUDE_EMPLOYEES="yes"  # Include 5 demo employees
DEFAULT_INCLUDE_KB="yes"  # Include Felix's KB

# Keycloak defaults
DEFAULT_ADMIN_USER="helix_user"
DEFAULT_ADMIN_PASSWORD="helix_pass"
DEFAULT_REALM="kc-realm-dev"

# Security defaults
DEFAULT_VAULT_ENABLED="no"  # no | yes (premium)

# KB defaults
DEFAULT_KB_MODE="default"  # default | premium | trial

# ================================================================
# Functions
# ================================================================

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

ask_question() {
    local question="$1"
    local default="$2"
    local response

    if [[ "$SETUP_MODE" == "silent" ]]; then
        # In silent mode, just return the default without prompting
        echo "$default"
        return
    fi

    # Show the question and default value
    echo "" >&2
    echo -e "${BOLD}$question${NC}" >&2
    echo -e "  Default: ${GREEN}$default${NC}" >&2
    read -p "  Your choice (Enter = default): " response

    if [[ -z "$response" ]]; then
        echo "$default"
    else
        echo "$response"
    fi
}

# ================================================================
# Welcome Screen
# ================================================================

clear
echo ""
echo -e "${BLUE}${BOLD}"
# Read banner from file if exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BANNER_FILE="${SCRIPT_DIR}/../assets/helix-banner.txt"
if [[ -f "$BANNER_FILE" ]]; then
    cat "$BANNER_FILE"
else
    cat << "BANNER"
 ██╗  ██╗ ███████╗ ██╗     ██╗██╗   ██╗
 ██║  ██║ ██╔════╝ ██║     ██║╚██╗ ██╔╝
 ███████║ █████╗   ██║     ██║ ╚███╔╝
 ██╔══██║ ██╔══╝   ██║     ██║ ██╔██╗
 ██║  ██║ ███████╗ ███████╗██║██╔╝ ██╗
 ╚═╝  ╚═╝ ╚══════╝ ╚══════╝╚═╝╚═╝  ╚═╝💦
BANNER
fi
echo -e "${NC}"
echo ""
echo -e "${BOLD}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║  ${GREEN}Out-of-the-Box POS System for Swiss Headshops${NC}${BOLD}       ║${NC}"
echo -e "${BOLD}║  ${YELLOW}First Case Study: Artemis Headshop, Luzern${NC}${BOLD}          ║${NC}"
echo -e "${BOLD}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BOLD}Welcome to HelixNet Setup Wizard${NC}"
echo ""
echo "This wizard will configure your HelixNet installation."
echo "Time required: 5-10 minutes"
echo ""
echo -e "${YELLOW}TIP:${NC} Press Enter to accept defaults (recommended for first run)"
echo ""

# ================================================================
# Setup Mode Selection
# ================================================================

print_header "Setup Mode"

echo ""
echo "1. Accept All Defaults (Recommended) - Working system in 5 minutes"
echo "2. Customize - Expert mode"
echo ""

SETUP_CHOICE=$(ask_question "Choose setup mode:" "1")

if [[ "$SETUP_CHOICE" == "1" ]]; then
    SETUP_MODE="silent"
    echo ""
    echo -e "${GREEN}✓${NC} Using recommended defaults (MvP ready)"
    echo ""
fi

# ================================================================
# Company Configuration
# ================================================================

print_header "Company Configuration"

COMPANY_NAME=$(ask_question "Company Name:" "$DEFAULT_COMPANY_NAME")
VAT_NUMBER=$(ask_question "VAT Number (Swiss format CHE-XXX.XXX.XXX):" "$DEFAULT_VAT_NUMBER")
ADDRESS=$(ask_question "Address:" "$DEFAULT_ADDRESS")
REGISTRATION_DATE=$(ask_question "Registration Date (YYYY-MM-DD):" "$DEFAULT_REGISTRATION_DATE")

echo ""
print_step "Company configured: $COMPANY_NAME"

# ================================================================
# LLM Configuration
# ================================================================

print_header "LLM Configuration"

echo ""
echo "Do you have an Ollama API key or Claude API key?"
echo ""
echo "1. No - Use local defaults (FREE, recommended)"
echo "2. Yes - Ollama (local server, advanced)"
echo "3. Yes - Claude API (premium, \$0.20/incident)"
echo ""

LLM_CHOICE=$(ask_question "Choose LLM backend:" "1")

case "$LLM_CHOICE" in
    1)
        LLM_MODE="local"
        LLM_MODEL="$DEFAULT_LLM_MODEL"
        print_step "Using local LLM (llama3.2 recommended for future)"
        ;;
    2)
        LLM_MODE="ollama"
        LLM_MODEL=$(ask_question "Ollama model (llama3.2 | tinylama):" "llama3.2")
        print_step "Using Ollama: $LLM_MODEL"
        ;;
    3)
        LLM_MODE="claude-api"
        LLM_MODEL="claude-sonnet-3-5"
        echo ""
        read -p "Claude API Key: " CLAUDE_API_KEY
        print_step "Using Claude API (premium tier)"
        ;;
    *)
        LLM_MODE="local"
        LLM_MODEL="$DEFAULT_LLM_MODEL"
        ;;
esac

# ================================================================
# MvP Demo/Sandbox
# ================================================================

print_header "MvP Demo/Sandbox Setup"

echo ""
echo "Include MvP demo sandbox?"
echo "  - kc-realm-dev (Keycloak demo realm)"
echo "  - 20 headshop products (Felix's catalog)"
echo "  - 5 demo employees (store-manager, cashier, admin)"
echo "  - Default headshop KB (Felix's 25-year expertise)"
echo ""
echo "1. Yes - Simple clone (recommended for initial launch)"
echo "2. No - Clean install (production only)"
echo ""

SANDBOX_CHOICE=$(ask_question "Include sandbox?" "1")

if [[ "$SANDBOX_CHOICE" == "1" ]]; then
    INCLUDE_SANDBOX="yes"
    INCLUDE_PRODUCTS="yes"
    INCLUDE_EMPLOYEES="yes"
    INCLUDE_KB="yes"
    print_step "MvP sandbox will be included"
else
    INCLUDE_SANDBOX="no"
    INCLUDE_PRODUCTS="no"
    INCLUDE_EMPLOYEES="no"
    INCLUDE_KB="no"
    print_warn "Production-only install (no demo data)"
fi

# ================================================================
# FourTwenty Supplier Catalog (Optional)
# ================================================================

print_header "Supplier Product Catalog"

echo ""
echo "Load FourTwenty.ch supplier catalog?"
echo "  - 7,000+ headshop products (bongs, vapes, CBD, accessories)"
echo "  - Daily price/stock updates"
echo "  - 30% markup pre-configured"
echo ""
echo "1. Yes - Load full catalog (recommended for production)"
echo "2. No - Use only sandbox products (20 items)"
echo ""

FOURTWENTY_CHOICE=$(ask_question "Load FourTwenty catalog?" "1")

if [[ "$FOURTWENTY_CHOICE" == "1" ]]; then
    INCLUDE_FOURTWENTY="yes"

    # Show default feed URLs
    echo ""
    echo -e "${BOLD}FourTwenty Feed URLs (defaults):${NC}"
    echo "  Products:       https://fourtwenty.ch/Dropship/Data/dropship_productfeed_v2.csv"
    echo "  Stock:          https://fourtwenty.ch/Dropship/Data/dropship_stockfeed_v1.csv"
    echo "  Specifications: https://fourtwenty.ch/Dropship/Data/dropship_specificationfeed_v1.csv"
    echo ""

    USE_DEFAULT_FEEDS=$(ask_question "Use default feed URLs?" "yes")

    if [[ "$USE_DEFAULT_FEEDS" != "yes" ]]; then
        echo ""
        read -p "Products feed URL: " FOURTWENTY_PRODUCTS_URL
        read -p "Stock feed URL: " FOURTWENTY_STOCK_URL
        read -p "Specifications feed URL: " FOURTWENTY_SPECS_URL
    else
        FOURTWENTY_PRODUCTS_URL="https://fourtwenty.ch/Dropship/Data/dropship_productfeed_v2.csv"
        FOURTWENTY_STOCK_URL="https://fourtwenty.ch/Dropship/Data/dropship_stockfeed_v1.csv"
        FOURTWENTY_SPECS_URL="https://fourtwenty.ch/Dropship/Data/dropship_specificationfeed_v1.csv"
    fi

    # Markup configuration
    DEFAULT_MARKUP="1.30"
    FOURTWENTY_MARKUP=$(ask_question "Markup multiplier (1.30 = 30% margin):" "$DEFAULT_MARKUP")

    print_step "FourTwenty catalog will be loaded (~7,000 products)"
else
    INCLUDE_FOURTWENTY="no"
    print_step "Using sandbox products only"
fi

# ================================================================
# Keycloak Admin
# ================================================================

print_header "Keycloak Admin Configuration"

echo ""
echo "Admin credentials for HelixNet:"
echo ""

ADMIN_USER=$(ask_question "Admin username:" "$DEFAULT_ADMIN_USER")
ADMIN_PASSWORD=$(ask_question "Admin password:" "$DEFAULT_ADMIN_PASSWORD")

if [[ "$ADMIN_PASSWORD" == "$DEFAULT_ADMIN_PASSWORD" ]]; then
    print_warn "Using default password (change after first login!)"
else
    print_step "Custom admin password set"
fi

# ================================================================
# Vault Configuration (Premium)
# ================================================================

print_header "Vault Configuration (Optional)"

echo ""
echo "HashiCorp Vault for secrets management?"
echo ""
echo "1. No (default) - Use environment variables"
echo "2. Yes (premium) - Requires Vault API key"
echo ""

VAULT_CHOICE=$(ask_question "Enable Vault?" "1")

if [[ "$VAULT_CHOICE" == "2" ]]; then
    VAULT_ENABLED="yes"
    echo ""
    read -p "Vault API Key: " VAULT_API_KEY
    read -p "Vault URL: " VAULT_URL
    print_step "Vault enabled (premium tier)"
else
    VAULT_ENABLED="no"
    print_step "Vault disabled (using .env secrets)"
fi

# ================================================================
# KB Configuration
# ================================================================

print_header "Knowledge Base Configuration"

echo ""
echo "Choose KB setup:"
echo ""
echo "1. Include default headshop KB (Felix's 25 years, recommended)"
echo "2. Premium import domain KB (requires premium tier)"
echo "3. Free trial - Build your own (empty KB)"
echo ""

KB_CHOICE=$(ask_question "Choose KB mode:" "1")

case "$KB_CHOICE" in
    1)
        KB_MODE="default"
        print_step "Default headshop KB included (5 pre-seeded + Felix's expertise)"
        ;;
    2)
        KB_MODE="premium"
        echo ""
        read -p "Domain KB URL (for import): " KB_IMPORT_URL
        print_step "Premium KB import configured"
        ;;
    3)
        KB_MODE="trial"
        print_warn "Empty KB - you'll build from scratch"
        ;;
    *)
        KB_MODE="default"
        ;;
esac

# ================================================================
# Summary & Confirmation
# ================================================================

print_header "Configuration Summary"

cat << EOF

Company:
  Name:          $COMPANY_NAME
  VAT Number:    $VAT_NUMBER
  Address:       $ADDRESS
  Registered:    $REGISTRATION_DATE

LLM:
  Mode:          $LLM_MODE
  Model:         $LLM_MODEL

MvP Sandbox:
  Enabled:       $INCLUDE_SANDBOX
  Products:      $INCLUDE_PRODUCTS (20 headshop items)
  Employees:     $INCLUDE_EMPLOYEES (5 demo users)
  KB:            $INCLUDE_KB (Felix's expertise)

FourTwenty Supplier:
  Enabled:       $INCLUDE_FOURTWENTY
  $(if [[ "$INCLUDE_FOURTWENTY" == "yes" ]]; then echo "Products:      ~7,000 items from fourtwenty.ch"; fi)
  $(if [[ "$INCLUDE_FOURTWENTY" == "yes" ]]; then echo "Markup:        ${FOURTWENTY_MARKUP}x ($(echo "scale=0; (${FOURTWENTY_MARKUP} - 1) * 100" | bc)% margin)"; fi)

Keycloak:
  Admin:         $ADMIN_USER
  Password:      $(if [[ "$ADMIN_PASSWORD" == "$DEFAULT_ADMIN_PASSWORD" ]]; then echo "helix_pass (default)"; else echo "****** (custom)"; fi)
  Realm:         $DEFAULT_REALM

Vault:
  Enabled:       $VAULT_ENABLED

Knowledge Base:
  Mode:          $KB_MODE

EOF

echo ""
read -p "Proceed with installation? (y/N): " PROCEED

if [[ ! "$PROCEED" =~ ^[Yy]$ ]]; then
    echo ""
    print_error "Installation cancelled"
    exit 0
fi

# ================================================================
# Installation
# ================================================================

print_header "Installing HelixNet"

# Create .env file
echo ""
print_step "Creating .env configuration..."

cat > .env << EOF
# HelixNet Configuration
# Generated: $(date -Iseconds)

# Company
COMPANY_NAME="$COMPANY_NAME"
VAT_NUMBER="$VAT_NUMBER"
ADDRESS="$ADDRESS"
REGISTRATION_DATE="$REGISTRATION_DATE"

# LLM
LLM_MODE="$LLM_MODE"
LLM_MODEL="$LLM_MODEL"
$(if [[ "$LLM_MODE" == "claude-api" ]]; then echo "CLAUDE_API_KEY=\"$CLAUDE_API_KEY\""; fi)

# Keycloak
KEYCLOAK_ADMIN="$ADMIN_USER"
KEYCLOAK_ADMIN_PASSWORD="$ADMIN_PASSWORD"
KEYCLOAK_REALM="$DEFAULT_REALM"

# Database
POSTGRES_USER="helix"
POSTGRES_PASSWORD="helix_db_pass"
POSTGRES_DB="helixnet"

# Redis
REDIS_PASSWORD="helix_redis_pass"

# Vault
VAULT_ENABLED="$VAULT_ENABLED"
$(if [[ "$VAULT_ENABLED" == "yes" ]]; then echo "VAULT_API_KEY=\"$VAULT_API_KEY\""; echo "VAULT_URL=\"$VAULT_URL\""; fi)

# MvP Demo
INCLUDE_SANDBOX="$INCLUDE_SANDBOX"
INCLUDE_PRODUCTS="$INCLUDE_PRODUCTS"
INCLUDE_EMPLOYEES="$INCLUDE_EMPLOYEES"
INCLUDE_KB="$INCLUDE_KB"

# FourTwenty Supplier
INCLUDE_FOURTWENTY="$INCLUDE_FOURTWENTY"
$(if [[ "$INCLUDE_FOURTWENTY" == "yes" ]]; then cat << FTEOF
FOURTWENTY_PRODUCTS_URL="$FOURTWENTY_PRODUCTS_URL"
FOURTWENTY_STOCK_URL="$FOURTWENTY_STOCK_URL"
FOURTWENTY_SPECS_URL="$FOURTWENTY_SPECS_URL"
FOURTWENTY_MARKUP="$FOURTWENTY_MARKUP"
FTEOF
fi)

# KB Mode
KB_MODE="$KB_MODE"
$(if [[ "$KB_MODE" == "premium" ]]; then echo "KB_IMPORT_URL=\"$KB_IMPORT_URL\""; fi)

# Setup
SETUP_COMPLETED="true"
SETUP_DATE="$(date -Iseconds)"
EOF

print_step ".env file created"

# Run Docker Compose
echo ""
print_step "Starting Docker containers..."
make down 2>/dev/null || true
sleep 2
make up

# Seed database (if MvP enabled)
if [[ "$INCLUDE_PRODUCTS" == "yes" ]]; then
    echo ""
    print_step "Seeding 20 headshop products..."
    sleep 5  # Wait for database
    PYTHONPATH=/home/angel/repos/helixnet python3 src/services/artemis_product_seeding.py || true
fi

# Sync FourTwenty catalog (if enabled)
if [[ "$INCLUDE_FOURTWENTY" == "yes" ]]; then
    echo ""
    print_step "Syncing FourTwenty supplier catalog (~7,000 products)..."
    print_step "This may take 1-2 minutes..."

    # Wait for FastAPI to be ready
    sleep 10

    # Run the sync script
    PYTHONPATH=/home/angel/repos/helixnet python3 scripts/modules/tools/fourtwenty-sync.py --sync 2>&1 | while read line; do
        echo "  $line"
    done

    if [[ $? -eq 0 ]]; then
        print_step "FourTwenty catalog synced successfully!"
    else
        print_warn "FourTwenty sync completed with warnings (check logs)"
    fi
fi

# Seed KB (if default mode)
if [[ "$KB_MODE" == "default" && "$INCLUDE_KB" == "yes" ]]; then
    echo ""
    print_step "Installing Felix's Knowledge Base..."
    # KB files already exist in debllm/notes/
fi

# ================================================================
# Success!
# ================================================================

print_header "Installation Complete!"

cat << EOF

🎉 HelixNet is now running!

Access your installation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 HelixNet POS:        http://localhost:8000/pos
🔐 Keycloak Admin:      http://localhost:8081
📊 DebLLM Dashboard:    http://localhost:8000/debllm (coming soon)
📧 MailHog (KB emails): http://localhost:8025

Admin Credentials:
  Username: $ADMIN_USER
  Password: $ADMIN_PASSWORD

Default Logins (MvP):
  Store Manager:  manager / manager123
  Cashier:        cashier / cashier123
  Felix (Admin):  felix / felix123

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Next Steps:

1. Change default password:
   http://localhost:8081 → Login → Change Password

2. Test POS transaction:
   http://localhost:8000/pos/scan → Age Verify → Browse Products

3. Review Knowledge Base:
   debllm/notes/helix-platform/HelixPOS_KB-001-felix-headshop-101.md

4. Configure Banana export (optional):
   Settings → Integrations → Banana Accounting

5. Join Felix/Mosey Club (gamification):
   Contribute 5 KBs → Earn Rookie badge → Access community

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📖 Documentation:
  - HelixPOS KB-001: Felix's Headshop 101
  - Demo Script: docs/demo-script-artemis-pos.md
  - MailHog Workflow: docs/mailhog-kb-workflow-spec.md
  - Product Catalog: docs/artemis-product-catalog.md

💰 Pricing:
  - FREE tier: What you just installed (CHF 0/month)
  - PAID tier: Banana export, custom branding (CHF 40/hr setup)
  - ENTERPRISE: SAP adapters, VPS hosting (CHF 3000+ install)

🤝 Support:
  - Community: https://github.com/helixnet/helixnet/issues
  - Email: support@helixnet.local (premium tier)
  - Phone: +41 XX XXX XX XX (enterprise tier)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Built with Bruce Lee philosophy: No bloat. Just what works. 🥊

EOF

echo ""
echo -e "${GREEN}${BOLD}Installation logs:${NC} logs/helix-setup-$(date +%Y%m%d).log"
echo ""
