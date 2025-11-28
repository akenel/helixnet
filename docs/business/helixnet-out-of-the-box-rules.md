# HelixNet Out-of-the-Box Rules & Business Model

**Version:** 1.0.0
**Date:** 2025-11-27 16:20 CET
**Philosophy:** Email + PDF = Free. Adapters + Custom = Paid. Network Effect = Gold.

---

## 🎯 Core Principles

### 1. Leverage Email as Much as Possible
- **KB contributions:** Email-based (Felix replies "ACCEPT", gets PDF)
- **Approvals:** Email reply = approve/decline
- **Notifications:** Email for badges, milestones, referrals
- **Support:** Email-first (FREE tier), phone = premium

**Why:** Universal, familiar, legally trackable, no training required

---

### 2. Leverage PDF Forms as Much as Possible
- **KB templates:** PDF fillable forms (Adobe Reader compatible)
- **Receipts:** PDF export (FREE tier)
- **Reports:** PDF daily summaries (FREE tier)
- **Invoices:** PDF generation (Banana export = paid)

**Why:** Universal format, offline editing, printable, no proprietary lock-in

---

### 3. Premium/Enterprise = Adapters + Custom Integrations
**CHF 3000+ Installation Package:**
- SAP Business One adapter (REST/SOAP/BAPI)
- Legacy POS migration (Oracle, MySQL, proprietary)
- Custom receipt formats (multi-location, franchise branding)
- ERP connectors (Odoo, NetSuite, Dynamics)
- Payment gateways (Stripe, Adyen, Twint Pro)

**Why:** Free tier = customer acquisition, Premium = where we make money

---

### 4. Dev Sandbox = Vertical POS First, Headshop Niche
**Not a generic POS. Purpose-built for:**
- Cannabis retail (legal markets: Switzerland, Netherlands, USA states)
- Age verification (18+, ID scanning)
- CBD compliance (THC <1%, lab certs, batch tracking)
- Swiss VAT (mixed rates: 8.1% standard, 2.5% reduced)
- Multi-language (DE/FR/IT/EN)

**Why:** Vertical focus = competitive moat, Felix's 25 years = unforkable knowledge

---

### 5. Felix/Mosey/Pot Rookie = Keycloak Gamification
**Progression Path:**
```
Pot Rookie (0 KBs)
  → Contribute 1 KB → Badge "🌱 Pot Rookie"
  → Contribute 5 KBs → Felix Club "🥈" (free file adapter)
  → Contribute 15 KBs → Gold "🥇" (CHF 200 credit)
  → Contribute 50 KBs → Platinum "💎" (lifetime free + revenue share)
```

**Felix as Gatekeeper:**
- All KBs go to Felix's inbox for approval
- Felix validates: Product match, barcode correct, KB quality
- 1 email = 1 KB proposal → Felix replies APPROVE/DECLINE
- No code, no CLI, no git - just email

**Why:** Quality control + gamification = community growth with standards

---

## 📋 Out-of-the-Box Setup Rules

### Rule 1: Accept All Defaults = Working System (5 Minutes)
```bash
./helix-setup-wizard.sh

Welcome to HelixNet Setup Wizard
─────────────────────────────────
Choose setup mode:
1. Accept All Defaults (Recommended) ✅
2. Customize

[User presses 1 or Enter]

✓ Company: Artemis Headshop (default example)
✓ VAT: CHE-123.456.789 (Swiss format example)
✓ LLM: Local-only (FREE)
✓ Sandbox: Yes (20 products + 5 employees + Felix KB)
✓ Keycloak: helix_user / helix_pass (change after first login!)
✓ Vault: No (use .env secrets)
✓ KB: Default headshop (Felix's 25 years)

Proceed? [Y/n]: Y

Installing...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Docker containers started
✓ Database seeded (20 products)
✓ KB installed (HelixPOS_KB-001)
✓ Keycloak realm imported (kc-realm-dev)

🎉 HelixNet is ready!
Access: http://localhost:8000/pos
Admin: helix_user / helix_pass
```

**Time:** 5-10 minutes (depending on Docker pull speed)
**Cost:** CHF 0

---

### Rule 2: Ollama API Key? Default = Local (FREE)
```
Do you have Ollama API key?
1. No - Use local default (recommended) ✅
2. Yes - Ollama (local server)
3. Yes - Claude API (premium, $0.20/incident)

[User presses 1 or Enter]

✓ Using local LLM (no API key required)
  Model: llama3.2 (recommended for future)
  Current: Pattern matching + bash (95% free)
```

**Upgrade Path (Later):**
- User installs Ollama locally → Change setting to Ollama
- User buys Claude API key → Change setting to Claude
- No reinstall required, just `.env` change

---

### Rule 3: VAT Address/Date/Registration = Default Example
```
Company Configuration:
  Name: [Artemis Headshop]
  VAT: [CHE-123.456.789]
  Address: [Bern, Switzerland]
  Registration: [2025-01-01]

Press Enter to accept defaults, or type custom values.

[User presses Enter 4 times]

✓ Using Artemis Headshop example (change in settings later)
```

**Why Default Example:**
- User sees realistic data immediately (not "Company XYZ")
- Can test transactions with real-world values
- Change later via Settings → Company

---

### Rule 4: MvP Sandbox = Yes (Recommended)
```
Include MvP demo sandbox?
  ✓ kc-realm-dev (5 demo users)
  ✓ 20 headshop products (Felix's catalog)
  ✓ Felix's KB (HelixPOS_KB-001)

1. Yes - Simple clone (recommended) ✅
2. No - Clean install (production only)

[User presses 1 or Enter]

✓ MvP sandbox included
  Products: 20 items (bongs, grinders, CBD, vapes)
  Employees: admin, manager, cashier, felix, rookie
  KB: HelixPOS_KB-001 + 5 pre-seeded error notes
```

**Users:**
- `helix_user` / `helix_pass` (admin)
- `manager` / `manager123` (store manager)
- `cashier` / `cashier123` (cashier)
- `felix` / `felix123` (Felix - KB approver)
- `rookie` / `rookie123` (Pot Rookie - 0 KBs)

---

### Rule 5: Vault = NO (Default), API-KEY for Premium
```
Vault for secrets management?
1. No (default) - Use .env ✅
2. Yes (premium) - Requires Vault API-KEY

[User presses 1 or Enter]

✓ Vault disabled (using .env for secrets)
  Upgrade: Buy premium → Enter API-KEY
```

**Premium Upgrade:**
```bash
# User buys premium tier (CHF 40/hr setup)
# We provide Vault API-KEY
# User re-runs wizard → Select "2" → Paste API-KEY
# Or: Edit .env manually:
VAULT_ENABLED="yes"
VAULT_API_KEY="hvs.xxxxx"
VAULT_URL="https://vault.helixnet.ch"
```

---

### Rule 6: KB = Default Headshop (Recommended)
```
Knowledge Base setup:
1. Default headshop KB (Felix's 25 years) ✅
2. Premium import domain KB (requires premium)
3. Free trial - Build your own (empty KB)

[User presses 1 or Enter]

✓ Default headshop KB included
  HelixPOS_KB-001: Felix's Headshop 101
  5 pre-seeded error notes (Redis, Postgres, etc.)
  200+ community KBs (when network grows)
```

**Premium Import (Option 2):**
- User has existing KB (e.g., Raluca's tattoo shop KB)
- We provide import script (CHF 40/hr setup)
- Convert their docs → HelixKB format
- Import via URL or file upload

**Free Trial (Option 3):**
- Empty KB (no Felix expertise)
- User builds from scratch (7-day free trial)
- After 7 days: Import default KB or buy premium

---

## 💰 Business Model: Free → Paid → Enterprise

### FREE Tier (CHF 0/month)
**What's Included:**
- ✅ Core POS (scan, checkout, receipt)
- ✅ Age verification (Swiss law compliant)
- ✅ VAT compliance (8.1% + 2.5% mixed rates)
- ✅ PDF receipts
- ✅ Default headshop KB (Felix's 25 years + community)
- ✅ MvP sandbox (20 products, 5 employees, demo realm)
- ✅ Email KB contributions (reply to email, get PDF, submit)
- ✅ Keycloak gamification (Pot Rookie → Felix Club)
- ✅ Community forum (read-only)

**Use Case:** Felix's pilot, small shops (<50 transactions/day)

**Hardware Required:** Laptop/desktop (16GB RAM) or Mini PC (CHF 100-200)

**Limitations:**
- No Banana export (accounting integration)
- No custom receipt branding (logo, colors)
- No file adapters (XLS, CSV export)
- No premium support (community forum only)
- No multi-location (single store only)

---

### PAID Tier (CHF 40/hr Setup + Optional CHF 50/month Support)
**What's Included (+ Free Tier):**
- ✅ Banana export (Swiss accounting)
- ✅ File adapters (XLS, CSV)
- ✅ Custom receipt branding (logo, footer, colors)
- ✅ Email support (48h response time)
- ✅ Multi-location (up to 3 stores)
- ✅ Inventory sync (real-time across locations)
- ✅ Advanced reports (sales by category, margin analysis)
- ✅ Twint QR on receipts (mobile payment)

**Use Case:** Artemis go-live, established shops (50-200 transactions/day)

**Setup:**
1. User pays CHF 40/hr (one-time)
2. We install Banana adapter (1-2 hours)
3. We configure custom branding (30 min)
4. User gets paid tier features (lifetime, no recurring unless they want support)

**Optional Support (CHF 50/month):**
- 48h email response
- Monthly feature updates
- Priority bug fixes
- Training sessions (1hr/quarter)

---

### ENTERPRISE Tier (CHF 3000+ Installation)
**What's Included (+ Paid Tier):**
- ✅ SAP Business One adapter (REST/SOAP/BAPI)
- ✅ Legacy POS migration (Oracle, MySQL, proprietary)
- ✅ Custom integrations (any REST/SOAP API)
- ✅ VPS Swiss-hosted (Infomaniak, Geneva/Zurich)
- ✅ White-label (remove HelixNet branding)
- ✅ Multi-tenant (franchise, 10+ locations)
- ✅ 24/7 phone support (Swiss German/French/Italian/English)
- ✅ Dedicated account manager
- ✅ Custom SLA (99.9% uptime guaranteed)

**Use Case:** Mosey (420 shops Italy/Spain), franchise chains, enterprise retail

**Setup:**
1. Discovery call (2-4 hours, requirements gathering)
2. Quote (CHF 3000-10,000 depending on complexity)
3. Implementation (2-4 weeks)
4. Training (on-site or remote)
5. Go-live + 30-day hyper-care

---

## 🎮 Keycloak Gamification: Detailed Rules

### Pot Rookie → Felix Club Progression

**Level 0: Unregistered (No Account)**
- Access: Public KB browser (read-only, 200+ notes)
- Action: Sign up → Become Pot Rookie

---

**Level 1: Pot Rookie (0 KBs Contributed)**
**Badge:** 🌱 Pot Rookie

**Access:**
- Full KB read access (all 200+ community notes)
- Use POS (basic features)
- Age verify, scan, checkout, receipt
- Email KB contributions (can submit KBs)

**Limitations:**
- Cannot approve KBs (Felix-only)
- No file adapters (PDF receipts only)
- No revenue share
- No priority support

**Goal:** Contribute 5 approved KBs → Join Felix Club

**How to Contribute:**
1. Email arrives: "KB-042 ASSIGNED: Storz & Bickel Volcano"
2. Reply: "ACCEPT"
3. Receive PDF template
4. Fill PDF (offline, Adobe Reader)
5. Reply with PDF attached
6. Wait for Felix approval (2-3 days)
7. If approved: +1 KB, progress to Felix Club

---

**Level 2: Felix Club Member (5 Approved KBs)**
**Badge:** 🥈 Felix Club Member

**Access (+ Pot Rookie):**
- Free file adapter (CHF 50 value, XLS/CSV export)
- Priority email support (48h response)
- Felix Club forum (expert discussions)
- Vote on KB proposals
- Suggest product catalog additions
- Early access to beta features

**Rewards:**
- Profile badge (displayed on all contributions)
- Email signature: "🥈 HelixKB Felix Club Member"
- Revenue share eligibility (50% on referrals)

**Referral Program:**
- Refer a shop → They sign up → You get 50% of their first year revenue
- Example: Mosey signs up (CHF 40/hr × 10 hours setup = CHF 400)
  - Felix Club member who referred: CHF 200
  - HelixNet: CHF 200

**Goal:** Contribute 15 approved KBs → Gold Contributor

---

**Level 3: Gold Contributor (15 Approved KBs)**
**Badge:** 🥇 Gold Contributor

**Access (+ Felix Club):**
- CHF 200 credit (any HelixNet service - setup, support, hardware)
- Phone support (business hours, Swiss German/French/Italian/English)
- Custom receipt branding (logo, colors, footer)
- Co-branding on case studies (e.g., "Powered by HelixNet & Felix")
- Approve KBs (delegate Felix's workload, earn +1 point per approval)
- Mentor Pot Rookies (earn +1 point per mentee who reaches Felix Club)

**Rewards:**
- Gold profile badge
- Listed on HelixNet "Top Contributors" page
- Exclusive Gold swag (t-shirt, hoodie, stickers)

**Goal:** Contribute 50 approved KBs → Platinum Partner

---

**Level 4: Platinum Partner (50 Approved KBs)**
**Badge:** 💎 Platinum Partner

**Access (+ Gold):**
- Lifetime free upgrades (all features, forever)
- Revenue share (10% of ALL network sales, not just referrals)
- VIP support (24/7 phone + private Slack channel)
- Roadmap voting (influence product features)
- Beta tester (early access to ALL new features)
- Co-owner vibe (profit-sharing, not just credits)
- Named in HelixNet Hall of Fame

**Rewards:**
- Platinum profile badge
- Exclusive Platinum swag (premium quality)
- Annual partner summit (all-expenses-paid trip to Bern)
- Revenue share check (monthly payment)

**Example Revenue Share:**
```
HelixNet Annual Revenue: CHF 100,000
Platinum Partners: 5 people (Felix, Mosey, Paolo, Maria, Jean)
Revenue Share Pool: 10% = CHF 10,000
Per Partner: CHF 10,000 / 5 = CHF 2,000/year

Felix's Take-Home:
  - CHF 2,000 revenue share (Platinum)
  - CHF 500 referrals (2 shops × CHF 250 each)
  - CHF 200 credit (Gold milestone, carried over)
  ─────────────────────────────
  Total: CHF 2,700/year (passive income)
```

**Why This Works:**
- Felix contributes once (50 KBs over 1-2 years)
- Earns forever (10% of network growth)
- Network grows → Felix's share grows
- No cap on earnings

---

## 📧 Email + PDF Workflow (Complete)

### Workflow 1: KB Contribution (Felix's Inbox)

**Step 1: Assignment Email**
```
From: kb-admin@helixnet.local
To: felix@artemis-headshop.ch
Subject: [KB-042] ASSIGNED: Storz & Bickel Volcano

Hi Felix,

You've been assigned a new KB:
  KB-042: Storz & Bickel Volcano - How to Sell (German)
  Category: product-knowledge
  Points: 5 (sales + product)
  Deadline: 2025-12-15

Reply with: ACCEPT | DECLINE | DELEGATE
```

**Step 2: Felix Replies**
```
From: felix@artemis-headshop.ch
To: kb-admin@helixnet.local
Subject: Re: [KB-042] ASSIGNED: Storz & Bickel Volcano

ACCEPT
```

**Step 3: Template Email (Auto-Sent)**
```
From: kb-admin@helixnet.local
To: felix@artemis-headshop.ch
Subject: [KB-042] TEMPLATE: Fill & Attach PDF

Hi Felix,

Attached: KB-042-template.pdf

Instructions:
1. Open PDF (Adobe Reader)
2. Fill sections (product specs, sales techniques)
3. Save as: KB-042-volcano-sales-de.pdf
4. Reply with PDF attached

Deadline: 2025-12-15
```

**Step 4: Felix Fills PDF & Replies**
```
From: felix@artemis-headshop.ch
To: kb-admin@helixnet.local
Subject: Re: [KB-042] TEMPLATE: Fill & Attach PDF

Anbei das ausgefüllte Formular.

Attachment: KB-042-volcano-sales-de.pdf
```

**Step 5: Confirmation Email (Auto-Sent)**
```
From: kb-admin@helixnet.local
To: felix@artemis-headshop.ch
Subject: [KB-042] RECEIVED: Under Review

Hi Felix,

Your KB-042 has been received!
Status: Under Review
Reviewer: angel (2-3 business days)

Your Progress:
  12 approved KBs → 🥈 Felix Club
  3 more for Gold (CHF 200 credit)
```

**Step 6: Approval Email (After Review)**
```
From: kb-admin@helixnet.local
To: felix@artemis-headshop.ch
Subject: [KB-042] APPROVED! 🎉 (+5 points)

Congratulations Felix!

KB-042 has been approved!
  Published: https://kb.helixnet.local/KB-042
  Points Earned: +5
  Your Total: 17 KBs

🎉 MILESTONE: You've reached Gold Contributor!
  Reward: CHF 200 credit unlocked
  Use for: Hardware upgrade, support, referral bonus

Feedback from angel:
"Excellent sales techniques. The competitor
comparison vs Pax is very useful for training."
```

---

### Workflow 2: Pot Rookie Contribution (Rookie's Inbox)

**Step 1: Rookie Gets Assigned KB-043**
```
From: kb-admin@helixnet.local
To: rookie@potshop.ch
Subject: [KB-043] ASSIGNED: How to Sell CBD Gummies

Hi Rookie,

Your first KB assignment!
  KB-043: How to Sell CBD Gummies (English)
  Category: product-knowledge
  Points: 3
  Deadline: 2025-12-10

This is your path to Felix Club (5 KBs):
  Progress: 0/5 KBs ████░░░░░░ 0%

Reply with: ACCEPT
```

**Step 2-6: Same workflow as Felix**
- Rookie replies ACCEPT
- Gets PDF template
- Fills PDF (product info, sales tips)
- Submits PDF
- Felix reviews (approver role)
- If approved: Rookie → 1/5 KBs

**Step 7: Milestone Email (After 5 Approved KBs)**
```
From: kb-admin@helixnet.local
To: rookie@potshop.ch
Subject: 🎉 WELCOME TO FELIX CLUB! 🥈

Congratulations!

You've reached Felix Club with 5 approved KBs!

Your Rewards:
  🥈 Felix Club Member badge
  ✅ Free file adapter (CHF 50 value)
  ✅ Priority email support (48h)
  ✅ Revenue share eligibility (50% referrals)

Next Milestone:
  15 KBs → Gold (CHF 200 credit)

Refer a shop, earn 50%:
  Your referral link: https://helixnet.ch/?ref=rookie123
```

---

## 🛠️ Hardware: CHF 100-200 Upgrade Path

### Scenario: Artemis Needs On-Premise Backup

**Problem:** VPS Swiss-hosted is great, but what if internet fails?
**Solution:** Mini PC on-premise (CHF 100-200) + sync to VPS

### Option 1: Raspberry Pi 4 (8GB) - CHF 100
**Specs:**
- ARM64, quad-core Cortex-A72, 8GB RAM
- MicroSD 128GB (SanDisk Extreme Pro)
- Official power supply (5.1V, 3A)
- Case + active cooling fan
- Ethernet cable (stable connection)

**Where to Buy (Switzerland):**
- Digitec.ch: CHF 95-110
- Brack.ch: CHF 100-115

**Performance:**
- 15-30 transactions/day: Perfect
- 50-100 transactions/day: OK (may lag on reports)
- Docker Compose: Works (ARM images)

**Pros:** Low power consumption (5W), silent, compact
**Cons:** ARM64 (some Docker images incompatible), slower than x86

---

### Option 2: Intel NUC or Mini PC - CHF 200 (Recommended)
**Specs:**
- x86_64, Intel i3-N305 or similar, 8GB RAM
- 256GB SSD (SATA or NVMe)
- Fanless or low-noise fan
- Gigabit Ethernet
- 2x HDMI (multi-monitor support)

**Where to Buy (Switzerland):**
- Digitec.ch: CHF 180-250 (ASUS PN41, Intel NUC)
- Brack.ch: CHF 200-280

**Performance:**
- 100+ transactions/day: Perfect
- Docker Compose: Full x86 compatibility
- Reports generation: Fast (SSD)

**Pros:** x86 compatibility, fast, reliable, silent
**Cons:** Higher cost, more power (15-25W)

---

### Setup (Both Options):

```bash
# SSH into mini hardware (after OS install)
ssh angel@192.168.1.100

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone HelixNet
git clone https://github.com/helixnet/helixnet.git
cd helixnet

# Run setup wizard (accept all defaults)
./scripts/helix-setup-wizard.sh

# Access from POS tablets
# Tablets point to: http://192.168.1.100:8000/pos
```

**Sync to VPS (Every 5 Minutes):**
```bash
# Crontab on mini PC
*/5 * * * * rsync -avz /home/angel/repos/helixnet/data/ user@pos.artemis-headshop.ch:/var/helixnet/data/
```

**Failover:**
- Internet up: Mini PC syncs to VPS (backup)
- Internet down: POS uses mini PC locally (no sync, queues data)
- Internet returns: Sync resumes, VPS catches up

---

## 🎓 Summary: The HelixNet Way

### What Makes HelixNet Different?

**1. Vertical Focus (Not Generic POS)**
- Built for headshops (Felix's 25 years)
- Age verify, CBD compliance, Swiss VAT
- Can't be replicated by generic POS (Odoo, Square, Toast)

**2. Email + PDF (No Code Required)**
- Felix contributes KBs via email (no git, CLI)
- PDF forms (offline editing, familiar)
- Legally trackable (audit trail)

**3. Free Forever Base (OSS)**
- CHF 0/month (core POS)
- User owns their data (no vendor lock-in)
- Upgrade when needed (adapters, integrations)

**4. Gamification (Network Effect)**
- Pot Rookie → Felix Club → Gold → Platinum
- 5 KBs = Free file adapter (CHF 50 value)
- 50 KBs = 10% revenue share (passive income)
- Community grows KB → All shops benefit

**5. Swiss VAT Certified (Accenture Lesson Learned)**
- VAT calculated AFTER discount (not before)
- Mixed rates (8.1% + 2.5%)
- Audit trail to the penny (10-year retention)
- No €20M mistake

---

## 🚀 Next Steps (Today: 16:20 → 20:20 CET)

**4-Hour Sprint:**
1. ✅ Setup wizard created (`helix-setup-wizard.sh`)
2. ✅ Preference/cutover strategy documented
3. ✅ Gamification rules defined (Pot Rookie → Platinum)
4. 🔄 Test setup wizard (run on local machine)
5. 📝 Create README update (quick start instructions)

**Tomorrow:**
1. Demo to Felix (Zoom call, 30 min)
2. Gather feedback (what's missing, what's confusing)
3. Iterate (fix UX issues)

**Next Week:**
1. Mosey outreach (Italian/Spanish headshops)
2. StudioJadu follow-up (Raluca's tattoo shop)
3. Case study draft (Artemis Headshop success)

---

**Built with Bruce Lee philosophy: No bloat. Just what works. 🥊**

---

**End of Out-of-the-Box Rules**
