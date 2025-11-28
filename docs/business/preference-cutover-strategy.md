# HelixNet Preference & Cutover Strategy

**Version:** 1.0.0
**Date:** 2025-11-27
**Author:** angel
**Target:** Headshop vertical (Artemis first case study)

---

## 🎯 Philosophy: Accept All Defaults = Working System

**Problem:** Most POS systems require weeks of configuration before first transaction.
**Solution:** HelixNet ships **pre-configured** for headshops - working in 5 minutes.

---

## 📦 Out-of-the-Box Defaults

### Company Settings (Example: Artemis Luzern)
```bash
COMPANY_NAME="Artemis Headshop"
VAT_NUMBER="CHE-123.456.789"  # Swiss format
ADDRESS="Bern, Switzerland"
REGISTRATION_DATE="2025-01-01"
CURRENCY="CHF"
LANGUAGE="de"  # de | fr | it | en
TIMEZONE="Europe/Zurich"
```

### LLM Backend (95% Free, 5% Paid)
```bash
# Default: Local-only (FREE)
LLM_MODE="local-only"          # local-only | ollama | claude-api | hybrid
LLM_MODEL="llama3.2"           # llama3.2 (recommended) | tinylama | gpt-4

# Ollama (if user has local server)
OLLAMA_API_URL="http://localhost:11434"
OLLAMA_MODEL="llama3.2"

# Claude API (premium, $0.20/incident)
CLAUDE_API_KEY="${ANTHROPIC_API_KEY:-}"  # Optional
CLAUDE_MODEL="claude-sonnet-3-5"
```

### MvP Sandbox (Recommended for Testing)
```bash
INCLUDE_SANDBOX="yes"          # yes | no
INCLUDE_PRODUCTS="yes"         # 20 headshop products (Felix's catalog)
INCLUDE_EMPLOYEES="yes"        # 5 demo users (manager, cashier, felix, etc.)
INCLUDE_KB="yes"               # Felix's KB (HelixPOS_KB-001)
```

### Keycloak Admin
```bash
KEYCLOAK_ADMIN="helix_user"
KEYCLOAK_ADMIN_PASSWORD="helix_pass"  # CHANGE AFTER FIRST LOGIN!
KEYCLOAK_REALM="kc-realm-dev"         # Dev realm (includes demo users)
```

### Vault (Premium Only)
```bash
VAULT_ENABLED="no"             # no (default) | yes (premium)
# If yes:
# VAULT_API_KEY="..."
# VAULT_URL="https://vault.example.com"
```

### KB Mode
```bash
KB_MODE="default"              # default | premium | trial
# default = Felix's headshop KB (5 pre-seeded + community)
# premium = Import custom domain KB (requires API key)
# trial = Empty KB (build your own, free for 7 days)
```

---

## 🔄 Cutover Strategy: Local → VPS Swiss-Hosted

### Phase 1: Local Development (NOW)
**Hardware:** Laptop/desktop (16GB RAM, Docker)
**URL:** `http://localhost:8000`
**Purpose:** Build, test, demo

**Steps:**
1. Clone repo: `git clone https://github.com/helixnet/helixnet.git`
2. Run setup: `./scripts/helix-setup-wizard.sh`
3. Accept all defaults (5 minutes)
4. Test transaction: Age verify → Scan → Checkout
5. Demo to Felix/Raluca

**Cost:** CHF 0 (using existing hardware)

---

### Phase 2: Mini Lite (UAT Testing)
**Hardware:** CHF 100-200 upgrade (Raspberry Pi 4 or mini PC)
**URL:** `http://192.168.1.100:8000` (local network)
**Purpose:** On-premise testing at Artemis

**Specs:**
- **Option 1 (Budget):** Raspberry Pi 4 (8GB) - CHF 100
  - ARM64, quad-core, 8GB RAM
  - MicroSD 128GB
  - Power supply
  - Case + fan

- **Option 2 (Recommended):** Intel NUC or equivalent - CHF 200
  - x86_64, Intel i3, 8GB RAM
  - 256GB SSD
  - Silent operation
  - More Docker performance

**Setup:**
```bash
# On mini hardware
git clone https://github.com/helixnet/helixnet.git
cd helixnet
./scripts/helix-setup-wizard.sh

# Use same defaults (Felix's config)
# Access from any device on network: http://192.168.1.100:8000
```

**Cost:** CHF 100-200 one-time hardware

---

### Phase 3: Digital Ocean (UAT Cloud)
**Hosting:** DigitalOcean Droplet (or Hetzner)
**URL:** `https://uat.artemis-pos.ch`
**Purpose:** Remote testing, staff training, multi-location UAT

**Specs:**
- **Droplet:** $12/month (2GB RAM, 1 vCPU, 50GB SSD)
- **Location:** Frankfurt (closest to Switzerland, GDPR-compliant)
- **SSL:** Let's Encrypt (free)
- **Backup:** Daily snapshots (+$1.20/month)

**Setup:**
```bash
# SSH into droplet
ssh root@uat.artemis-pos.ch

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone HelixNet
git clone https://github.com/helixnet/helixnet.git
cd helixnet

# Run setup wizard (same defaults)
./scripts/helix-setup-wizard.sh

# Configure Caddy (reverse proxy + SSL)
# Expose 8000 → 443 with auto-SSL
```

**Cost:** CHF 15/month (~$12 + backup)

---

### Phase 4: VPS Swiss-Hosted (PRODUCTION)
**Hosting:** Infomaniak or Swiss-IX (Q2-Q3 2026)
**URL:** `https://pos.artemis-headshop.ch`
**Purpose:** Production, Swiss data residency, compliance

**Specs:**
- **VPS:** CHF 30-50/month (4GB RAM, 2 vCPU, 100GB SSD)
- **Location:** Geneva or Zurich (Swiss data laws)
- **SSL:** Swiss CA or Let's Encrypt
- **Backup:** Nightly (included)
- **Support:** 24/7 Swiss phone support

**Why Swiss Hosting:**
1. **Data Residency:** Swiss Federal Data Protection Act (FADP)
2. **VAT Compliance:** Swiss servers = no export/import VAT issues
3. **Support:** German/French/Italian/English support
4. **Uptime:** 99.9% SLA
5. **Trust:** Felix's customers trust "Made in Switzerland"

**Setup:**
```bash
# Identical to Phase 3, but Swiss location
ssh root@pos.artemis-headshop.ch
# ... same setup wizard ...
```

**Cost:** CHF 30-50/month (production-grade)

---

## ⚙️ Preference Management

### User-Configurable Settings (Post-Install)

**Company Preferences:**
```python
# /settings/company
{
    "name": "Artemis Headshop",
    "vat_number": "CHE-123.456.789",
    "address": "Bern, Switzerland",
    "phone": "+41 31 XXX XX XX",
    "email": "felix@artemis-headshop.ch",
    "website": "https://artemis-headshop.ch",
    "logo_url": "/static/img/artemis-logo.png"
}
```

**Receipt Preferences:**
```python
# /settings/receipt
{
    "header": "ARTEMIS HEADSHOP\nBern, Switzerland",
    "footer": "Thank you! www.artemis-headshop.ch",
    "show_vat_breakdown": true,  # Required for Swiss law
    "show_freebie_items": true,  # Transparency
    "receipt_language": "auto",  # auto | de | fr | it | en
    "print_qr_code": false,      # Twint QR on receipt (premium)
}
```

**Discount Preferences:**
```python
# /settings/discounts
{
    "loyalty_enabled": true,
    "loyalty_threshold": 1000,  # CHF spent/year
    "loyalty_discount": 5,      # 5% off
    "bulk_discount_threshold": 300,  # CHF single transaction
    "bulk_discount": 10,        # 10% off
    "freebie_enabled": true,
    "freebie_threshold": 100,   # CHF purchase
    "freebie_max_value": 5,     # CHF max per transaction
}
```

**Age Verification Preferences:**
```python
# /settings/age_verify
{
    "required": true,           # Cannot disable (Swiss law)
    "min_age": 18,
    "acceptable_ids": ["swiss_id", "passport", "eu_id", "driving_license"],
    "log_all_checks": true,     # Audit trail
    "tourist_passport_only": true,  # Stricter for tourists
}
```

**KB Contribution Preferences:**
```python
# /settings/kb
{
    "contribution_enabled": true,
    "auto_assign": true,        # System assigns KBs to Felix
    "approval_required": true,  # Felix approves all KBs
    "points_per_kb": 1,         # Gamification
    "rookie_threshold": 5,      # 5 KBs = Rookie badge
    "email_notifications": true,
}
```

---

## 🎮 Keycloak Gamification: Pot Rookie → Felix Club

### Badge Progression

**Level 1: Pot Rookie (0 KBs)**
- **Entry:** New user, no KBs contributed
- **Access:** Read-only KB (200+ community notes)
- **Permissions:** Browse products, basic POS features
- **Goal:** Contribute first KB

**Level 2: Pot Rookie (1-4 KBs)**
- **Entry:** First KB submitted (under review or approved)
- **Rewards:**
  - Profile badge "🌱 Pot Rookie"
  - Email signature badge
  - Access to Rookie forum (community Q&A)
- **Permissions:** Same as Level 1
- **Goal:** Reach 5 approved KBs

**Level 3: Felix/Mosey Club (5+ KBs)**
- **Entry:** 5 approved KBs (Felix-reviewed quality)
- **Rewards:**
  - Profile badge "🥈 Felix Club Member"
  - Free file adapter (CHF 50 value)
  - Priority email support (48h response)
  - Access to Felix Club forum (expert discussions)
  - Revenue share eligibility (50% on referrals)
- **Permissions:**
  - Vote on KB proposals
  - Suggest product catalog additions
  - Early access to new features
- **Goal:** Reach 15 KBs (Gold) or 50 KBs (Platinum)

**Level 4: Gold Contributor (15+ KBs)**
- **Entry:** 15 approved KBs + 6 months active
- **Rewards:**
  - Profile badge "🥇 Gold Contributor"
  - CHF 200 credit (any HelixNet service)
  - Phone support (business hours)
  - Custom branding (receipt, POS screen)
  - Co-branding on case studies
- **Permissions:**
  - Approve KBs (delegate Felix's workload)
  - Mentor Rookies (earn +1 point per mentee)
- **Goal:** Reach 50 KBs (Platinum)

**Level 5: Platinum Partner (50+ KBs)**
- **Entry:** 50 approved KBs + 1 year active + 3+ referrals
- **Rewards:**
  - Profile badge "💎 Platinum Partner"
  - Lifetime free upgrades (all features)
  - Revenue share (10% on ALL network sales, not just referrals)
  - VIP support (24/7 phone + Slack channel)
  - Named in HelixNet Hall of Fame
  - Exclusive Platinum Partner swag (t-shirt, stickers, etc.)
- **Permissions:**
  - Roadmap voting (influence features)
  - Beta tester (early access to all new features)
  - Co-owner vibe (profit-sharing, not just credits)

---

### Keycloak Implementation

**Custom Attributes (User Profile):**
```json
{
  "username": "felix",
  "email": "felix@artemis-headshop.ch",
  "attributes": {
    "kb_contributions_total": "12",
    "kb_contributions_approved": "12",
    "kb_contributions_pending": "0",
    "kb_points": "12",
    "badge_level": "felix_club",  // pot_rookie | felix_club | gold | platinum
    "referrals_count": "2",
    "revenue_share_earned": "150.00",  // CHF
    "joined_date": "2025-01-01",
    "last_kb_date": "2025-11-27"
  }
}
```

**Keycloak Roles (Permissions):**
```
pot_rookie:
  - read_kb
  - use_pos_basic

felix_club:
  - read_kb
  - contribute_kb
  - use_pos_full
  - access_file_adapter
  - refer_shop

gold_contributor:
  - approve_kb
  - mentor_rookie
  - use_pos_premium
  - custom_branding

platinum_partner:
  - all_permissions
  - vote_roadmap
  - beta_access
  - revenue_share_network
```

**Gamification Dashboard (HelixNet UI):**
```
┌─────────────────────────────────────────┐
│ 👤 Felix (felix@artemis-headshop.ch)   │
├─────────────────────────────────────────┤
│ 🥈 Felix Club Member                    │
│ 12 KBs Approved • 2 Referrals           │
│                                         │
│ Progress to Gold:                       │
│ ████████░░░░░░░░░░ 80% (12/15 KBs)      │
│                                         │
│ Rewards Earned:                         │
│ ✅ Free file adapter (CHF 50)           │
│ ✅ Priority support                     │
│ ✅ Revenue share: CHF 150 earned        │
│                                         │
│ Next Milestone:                         │
│ 3 more KBs → Gold badge (CHF 200 credit)│
│                                         │
│ [Contribute KB] [View My KBs] [Refer]   │
└─────────────────────────────────────────┘
```

---

## 🚀 Cutover Checklist (Local → Production)

### Pre-Cutover (1 Week Before)
- [ ] Backup local database (`pg_dump`)
- [ ] Export all products to CSV
- [ ] Export all employees to CSV
- [ ] Export all KBs to Git (already versioned)
- [ ] Test Banana export (verify VAT calculations)
- [ ] Felix reviews all data (products, prices, VAT)

### Cutover Day (Saturday, Off-Hours)
**Timeline: 6 hours (18:00 → 00:00)**

**18:00 - 19:00: VPS Preparation**
- [ ] Provision VPS (Infomaniak, Geneva)
- [ ] Install Docker + Compose
- [ ] Clone HelixNet repo
- [ ] Run setup wizard (same config as UAT)
- [ ] Configure SSL (Let's Encrypt)
- [ ] Configure firewall (ports 80, 443, 22 only)

**19:00 - 20:00: Data Migration**
- [ ] Import database dump (products, employees, transactions)
- [ ] Verify data integrity (row counts, checksums)
- [ ] Import KB files (already in Git)
- [ ] Test admin login (helix_user / felix)

**20:00 - 21:00: Integration Testing**
- [ ] Test age verify flow
- [ ] Test product scan (all 20 products)
- [ ] Test discount calculation (VAT-correct)
- [ ] Test receipt printing (Swiss compliant)
- [ ] Test Banana export (VAT breakdown)

**21:00 - 22:00: DNS Cutover**
- [ ] Update DNS: `pos.artemis-headshop.ch` → VPS IP
- [ ] Propagation wait (15-60 minutes)
- [ ] Verify SSL certificate (HTTPS working)
- [ ] Test from external network (mobile, tablet)

**22:00 - 23:00: Final Verification**
- [ ] Felix performs test transactions (3-5 real scenarios)
- [ ] Verify receipt formatting
- [ ] Verify VAT calculations (audit trail)
- [ ] Test KB email workflow (MailHog → Felix inbox)

**23:00 - 00:00: Go-Live**
- [ ] Announce go-live (email to Felix, staff)
- [ ] Monitor logs (errors, warnings)
- [ ] Standby for first hour (angel on call)
- [ ] Backup production database (first snapshot)

### Post-Cutover (Next Day)
- [ ] Felix opens shop, uses HelixNet for real transactions
- [ ] Monitor performance (response times, errors)
- [ ] Collect feedback from staff (cashiers, manager)
- [ ] Fix any UX issues (hotfix deploy within 24h)

### Week 1 Post-Cutover
- [ ] Daily check-ins with Felix (phone, email)
- [ ] Monitor transaction volume (compare to old POS)
- [ ] Review VAT calculations (audit readiness)
- [ ] Gather customer feedback (receipt readability, speed)
- [ ] Case study draft (Artemis success story)

---

## 🔧 Hardware Upgrade Path

### Scenario: Felix Wants On-Premise Backup

**Problem:** VPS is great, but what if internet goes down?
**Solution:** Mini hardware on-premise (CHF 100-200) + sync to VPS

**Architecture:**
```
┌──────────────────────────────────────────┐
│ Artemis Shop Floor                       │
│                                          │
│ ┌─────────────┐   ┌─────────────┐       │
│ │ Tablet POS  │   │ Tablet POS  │       │
│ │ Cashier 1   │   │ Cashier 2   │       │
│ └──────┬──────┘   └──────┬──────┘       │
│        │                  │              │
│        └─────────┬────────┘              │
│                  │                       │
│         ┌────────▼────────┐              │
│         │ Mini PC (NUC)   │              │
│         │ HelixNet Local  │              │
│         │ http://192.x.x  │              │
│         └────────┬────────┘              │
│                  │                       │
│         ┌────────▼────────┐              │
│         │ Router (4G/5G)  │              │
│         │ Backup Internet │              │
│         └────────┬────────┘              │
└──────────────────┼──────────────────────┘
                   │
                   │ Sync every 5 min
                   │
           ┌───────▼───────┐
           │ VPS Swiss     │
           │ Infomaniak    │
           │ pos.artemis.ch│
           └───────────────┘
```

**Costs:**
- Mini PC (NUC): CHF 200 (one-time)
- 4G/5G backup router: CHF 50/month (optional, Swisscom)
- VPS: CHF 30-50/month (unchanged)

**Benefits:**
- Internet down? Local POS keeps working
- Sync resumes when internet returns
- Zero downtime for customers

---

## 📊 Cutover Metrics

**Success Criteria:**
- [ ] Zero data loss (all products, transactions migrated)
- [ ] <5 second page load (VPS performance)
- [ ] 100% VAT accuracy (Felix's audit trail clean)
- [ ] <1 hour downtime (DNS cutover only)
- [ ] Staff trained (3-5 test transactions each)

**KPIs (Week 1 Post-Cutover):**
- Transactions/day: Target 15-30 (same as old POS)
- Average ticket: CHF 40-60 (Felix's baseline)
- System uptime: 99.9% (VPS SLA)
- Support tickets: <5 (UX issues only)
- Felix satisfaction: 8+/10 (survey)

---

## 🎓 Training Materials

**For Felix (Manager):**
- [ ] Admin dashboard walkthrough (30 min video)
- [ ] KB approval workflow (email-based, 15 min)
- [ ] Banana export (how to import, 10 min)
- [ ] Troubleshooting common issues (20 min)

**For Cashiers:**
- [ ] Age verify workflow (5 min demo)
- [ ] Product scan + checkout (10 min hands-on)
- [ ] Discount application (5 min)
- [ ] Refund/void transaction (5 min)

**For Pot Rookies (New Contributors):**
- [ ] How to contribute KB via email (10 min video)
- [ ] PDF form filling (5 min example)
- [ ] Badge system explained (5 min)
- [ ] Referral program (how to earn CHF)

---

## 🔐 Security Hardening (Production)

**VPS Firewall:**
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH (change port from default)
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw allow 443/tcp   # HTTPS
ufw enable
```

**Fail2Ban:**
```bash
# Block brute-force attempts
apt install fail2ban
systemctl enable fail2ban
```

**SSL Configuration:**
```bash
# Use strong cipher suites (A+ rating)
# Caddy handles this automatically
```

**Database Access:**
```bash
# No direct access from internet
# Postgres bound to localhost only
# Access via SSH tunnel if needed
```

**Backup Strategy:**
```bash
# Daily automated backups
# Retention: 30 days
# Offsite backup: AWS S3 or Infomaniak Object Storage
```

---

**End of Preference & Cutover Strategy**
