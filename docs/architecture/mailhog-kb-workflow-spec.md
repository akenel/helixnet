# MailHog KB Contribution Workflow - Technical Specification

**Version:** 1.0.0
**Date:** 2025-11-27
**Author:** angel
**Status:** Draft (Ready for Implementation)

---

## 🎯 Purpose

Enable **non-technical users** (like Felix) to contribute to HelixKB via **email only** - no git, CLI, or web forms required.

### Design Principles
1. **Email-native:** Felix uses email client (Outlook, Gmail, Thunderbird)
2. **PDF-based:** Familiar format, legally trackable, offline editing
3. **MailHog-powered:** OSS, self-hosted, no external dependencies
4. **Audit trail:** Every email logged, replies traceable
5. **Badge system:** Gamification (5 approved KBs = Silver badge)

---

## 📧 User Workflow (Felix's Perspective)

### Step 1: Receive KB Assignment Email

**From:** `kb-admin@helixnet.local`
**To:** `felix@artemis-headshop.ch`
**Subject:** `[KB-042] ASSIGNED: Storz & Bickel Volcano - How to Sell (German)`

```
Hi Felix,

You've been assigned a new HelixKB contribution:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 KB-042: Storz & Bickel Volcano - How to Sell (German)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Category: product-knowledge
Points: 3 (sales-techniques) + 2 (product-knowledge) = 5 total
Deadline: 2025-12-15
Language: German

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Options:

1. ACCEPT: Reply with "ACCEPT" in body (we'll send template)
2. DECLINE: Reply with "DECLINE [reason]" in body
3. DELEGATE: Reply with "DELEGATE [name@email.com]" in body

Current Progress:
  ✅ 12 approved KBs (Silver badge earned!)
  🎯 3 more for Gold badge (CHF 200 credit)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best regards,
HelixKB Admin (automated)

---
Reference: KB-042-ASSIGN-20251127-001
Do not modify subject line (required for tracking)
```

**Attachments:** None (template sent after ACCEPT)

---

### Step 2A: Felix Accepts

Felix clicks "Reply", types "ACCEPT", sends.

**From:** `felix@artemis-headshop.ch`
**To:** `kb-admin@helixnet.local`
**Subject:** `Re: [KB-042] ASSIGNED: Storz & Bickel Volcano - How to Sell (German)`
**Body:**
```
ACCEPT
```

---

### Step 2B: Felix Receives Template

**From:** `kb-admin@helixnet.local`
**To:** `felix@artemis-headshop.ch`
**Subject:** `[KB-042] TEMPLATE: Fill & Attach PDF`

```
Hi Felix,

Thanks for accepting KB-042!

Attached: PDF template to fill out

Instructions:
1. Open attached PDF (KB-042-template.pdf)
2. Fill in sections (see instructions inside PDF)
3. Save as: KB-042-volcano-sales-de.pdf
4. Reply to THIS email with PDF attached
5. Subject line: Keep as-is (required for tracking)

Deadline: 2025-12-15
Points: 5 (sales + product knowledge)

Need help? Reply with "HELP" for video tutorial.

Best regards,
HelixKB Admin
```

**Attachments:** `KB-042-template.pdf`

---

### Step 3: Felix Fills PDF & Replies

Felix:
1. Opens `KB-042-template.pdf` in Adobe Reader
2. Fills sections:
   - Product overview (Volcano specs, price, margin)
   - Sales techniques (upselling, customer objections)
   - Common questions (warranty, usage, cleaning)
   - Competitor comparison (vs Pax, vs cheap vapes)
3. Saves as `KB-042-volcano-sales-de.pdf`
4. Replies to email, attaches PDF

**From:** `felix@artemis-headshop.ch`
**To:** `kb-admin@helixnet.local`
**Subject:** `Re: [KB-042] TEMPLATE: Fill & Attach PDF`
**Body:**
```
Anbei das ausgefüllte Formular.

Grüsse,
Felix
```
**Attachments:** `KB-042-volcano-sales-de.pdf`

---

### Step 4: Felix Receives Confirmation

**From:** `kb-admin@helixnet.local`
**To:** `felix@artemis-headshop.ch`
**Subject:** `[KB-042] RECEIVED: Under Review`

```
Hi Felix,

Your KB-042 contribution has been received!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 KB-042: Storz & Bickel Volcano (German)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: Under Review
Received: 2025-11-27 15:45:00
Reviewer: angel (estimated 2-3 business days)

Next Steps:
  → Manager review
  → Approval/feedback
  → Publication to HelixKB

Your Progress:
  🎯 13 approved KBs (if approved)
  🥈 Silver badge (earned!)
  📈 2 more for Gold badge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best regards,
HelixKB Admin
```

---

### Step 5A: Approval (Happy Path)

**From:** `kb-admin@helixnet.local`
**To:** `felix@artemis-headshop.ch`
**Subject:** `[KB-042] APPROVED! 🎉 (+5 points)`

```
Hi Felix,

Congratulations! KB-042 has been approved!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ KB-042: Storz & Bickel Volcano (German)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Approved: 2025-11-29 10:30:00
Reviewer: angel
Points Earned: +5

Published: https://kb.helixnet.local/KB-042
Available in: HelixPOS (all shops)

Feedback from angel:
"Excellent sales techniques section. The competitor
comparison is very helpful for new staff training."

Your Progress:
  🎯 13 approved KBs
  🥈 Silver badge
  📈 2 more for Gold badge (CHF 200 credit unlocked!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best regards,
HelixKB Admin
```

---

### Step 5B: Feedback Required (Revision Path)

**From:** `kb-admin@helixnet.local`
**To:** `felix@artemis-headshop.ch`
**Subject:** `[KB-042] FEEDBACK: Minor Revisions Needed`

```
Hi Felix,

KB-042 needs minor revisions before approval.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 KB-042: Storz & Bickel Volcano (German)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: Revisions Requested
Reviewer: angel

Feedback:
1. ✅ Sales techniques: Excellent
2. ⚠️  Price: Update to CHF 700 (current is CHF 650)
3. ⚠️  Warranty: Add Storz & Bickel 3-year info

Action Required:
  → Update attached PDF (see highlighted sections)
  → Reply with revised PDF attached
  → Deadline: 2025-12-05 (8 days remaining)

Need help? Reply with "HELP" for clarification.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best regards,
HelixKB Admin
```

**Attachments:** `KB-042-volcano-sales-de-FEEDBACK.pdf` (with comments)

---

### Step 5C: Decline (Rare)

**From:** `kb-admin@helixnet.local`
**To:** `felix@artemis-headshop.ch`
**Subject:** `[KB-042] DECLINED: See Reason`

```
Hi Felix,

Unfortunately, KB-042 cannot be approved.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ KB-042: Storz & Bickel Volcano (German)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: Declined
Reviewer: angel

Reason:
Product information conflicts with Storz & Bickel
official specs. For legal/compliance reasons, we
cannot publish incorrect technical data.

Options:
1. Submit new KB (different product)
2. Contact support: kb-support@helixnet.local

No points deducted (no penalty).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best regards,
HelixKB Admin
```

---

## 🔧 Technical Implementation (Backend)

### MailHog Setup

**Stack:**
- MailHog: SMTP server + web UI (http://localhost:8025)
- Python script: Email parser + workflow engine
- Celery: Async task processing
- PostgreSQL: Email log + KB metadata

**Compose Service:**
```yaml
mailhog:
  image: mailhog/mailhog:latest
  ports:
    - "1025:1025"  # SMTP
    - "8025:8025"  # Web UI
  environment:
    MH_STORAGE: maildir
    MH_MAILDIR_PATH: /maildir
  volumes:
    - ./mailhog_data:/maildir
  networks:
    - helix_network
```

---

### Email Parser (Python + Celery)

**File:** `src/services/kb_email_processor.py`

```python
import email
import re
from email.parser import Parser
from pathlib import Path
from typing import Optional, Dict

from celery import shared_task
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.kb_model import KBContribution, KBStatus
from src.services.kb_service import KBService


class KBEmailParser:
    """Parse KB contribution emails from MailHog"""

    # Email subject patterns
    ASSIGN_PATTERN = r'\[KB-(\d+)\] ASSIGNED:'
    TEMPLATE_PATTERN = r'\[KB-(\d+)\] TEMPLATE:'
    SUBMIT_PATTERN = r'Re: \[KB-(\d+)\]'

    # Body commands
    ACCEPT = 'ACCEPT'
    DECLINE = 'DECLINE'
    DELEGATE = 'DELEGATE'
    HELP = 'HELP'

    def __init__(self, db: Session):
        self.db = db
        self.kb_service = KBService(db)

    def parse_email(self, raw_email: str) -> Dict:
        """Parse raw email and extract metadata"""
        msg = email.message_from_string(raw_email)

        return {
            'from': msg['From'],
            'to': msg['To'],
            'subject': msg['Subject'],
            'date': msg['Date'],
            'body': self._extract_body(msg),
            'attachments': self._extract_attachments(msg),
            'kb_id': self._extract_kb_id(msg['Subject']),
            'command': self._extract_command(self._extract_body(msg))
        }

    def _extract_body(self, msg) -> str:
        """Extract plain text body"""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    return part.get_payload(decode=True).decode('utf-8')
        else:
            return msg.get_payload(decode=True).decode('utf-8')

    def _extract_attachments(self, msg) -> list:
        """Extract PDF attachments"""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename and filename.endswith('.pdf'):
                        attachments.append({
                            'filename': filename,
                            'data': part.get_payload(decode=True)
                        })

        return attachments

    def _extract_kb_id(self, subject: str) -> Optional[str]:
        """Extract KB-XXX from subject"""
        match = re.search(r'KB-(\d+)', subject)
        return f"KB-{match.group(1)}" if match else None

    def _extract_command(self, body: str) -> Optional[str]:
        """Extract command from body"""
        body_upper = body.strip().upper()

        if body_upper.startswith(self.ACCEPT):
            return self.ACCEPT
        elif body_upper.startswith(self.DECLINE):
            return self.DECLINE
        elif body_upper.startswith(self.DELEGATE):
            return self.DELEGATE
        elif body_upper.startswith(self.HELP):
            return self.HELP

        return None


@shared_task
def process_kb_email(email_id: str):
    """
    Celery task: Process incoming KB email

    Workflow:
    1. Parse email (extract KB ID, command, attachments)
    2. Route based on command:
       - ACCEPT → Send template
       - DECLINE → Log, notify admin
       - DELEGATE → Reassign KB
       - PDF attachment → Submit for review
       - HELP → Send tutorial
    3. Update KB status in database
    4. Send confirmation email
    """
    db = next(get_db())
    parser = KBEmailParser(db)

    # Fetch email from MailHog API
    raw_email = fetch_from_mailhog(email_id)
    parsed = parser.parse_email(raw_email)

    kb_id = parsed['kb_id']
    command = parsed['command']
    sender = parsed['from']

    # Route based on command
    if command == KBEmailParser.ACCEPT:
        handle_accept(db, kb_id, sender)

    elif command == KBEmailParser.DECLINE:
        handle_decline(db, kb_id, sender, parsed['body'])

    elif command == KBEmailParser.DELEGATE:
        delegate_email = extract_delegate_email(parsed['body'])
        handle_delegate(db, kb_id, sender, delegate_email)

    elif command == KBEmailParser.HELP:
        send_help_email(sender, kb_id)

    elif parsed['attachments']:
        # PDF submission
        handle_submission(db, kb_id, sender, parsed['attachments'][0])

    else:
        # Unknown command, log and notify
        log_unknown_command(kb_id, sender, parsed['body'])


def handle_accept(db: Session, kb_id: str, sender: str):
    """User accepted KB assignment → Send template"""
    kb_service = KBService(db)

    # Update status
    kb_service.update_status(kb_id, KBStatus.ACCEPTED)

    # Generate template PDF
    template_path = kb_service.generate_template(kb_id)

    # Send email with template
    send_email(
        to=sender,
        subject=f'[{kb_id}] TEMPLATE: Fill & Attach PDF',
        body=TEMPLATE_EMAIL_BODY.format(kb_id=kb_id),
        attachments=[template_path]
    )

    # Log
    log_kb_event(kb_id, 'ACCEPTED', sender)


def handle_submission(db: Session, kb_id: str, sender: str, attachment: Dict):
    """User submitted PDF → Move to review queue"""
    kb_service = KBService(db)

    # Save PDF
    pdf_path = Path(f'data/kb_submissions/{kb_id}-{sender}.pdf')
    pdf_path.write_bytes(attachment['data'])

    # Update status
    kb_service.update_status(kb_id, KBStatus.UNDER_REVIEW)
    kb_service.attach_submission(kb_id, pdf_path)

    # Send confirmation
    send_email(
        to=sender,
        subject=f'[{kb_id}] RECEIVED: Under Review',
        body=RECEIVED_EMAIL_BODY.format(kb_id=kb_id)
    )

    # Notify reviewer (angel)
    notify_reviewer(kb_id, sender, pdf_path)

    # Log
    log_kb_event(kb_id, 'SUBMITTED', sender)


def handle_decline(db: Session, kb_id: str, sender: str, reason: str):
    """User declined KB assignment"""
    kb_service = KBService(db)

    # Extract reason from body
    reason_text = reason.replace('DECLINE', '').strip()

    # Update status
    kb_service.update_status(kb_id, KBStatus.DECLINED_BY_USER)
    kb_service.add_note(kb_id, f'Declined by {sender}: {reason_text}')

    # Send confirmation
    send_email(
        to=sender,
        subject=f'[{kb_id}] DECLINED: Confirmed',
        body=DECLINE_CONFIRMED_BODY.format(kb_id=kb_id, reason=reason_text)
    )

    # Notify admin to reassign
    notify_admin_reassign(kb_id, sender, reason_text)

    # Log
    log_kb_event(kb_id, 'DECLINED', sender, reason_text)


# Email templates
TEMPLATE_EMAIL_BODY = """
Hi,

Thanks for accepting {kb_id}!

Attached: PDF template to fill out

Instructions:
1. Open attached PDF
2. Fill in sections (see instructions inside PDF)
3. Save and reply with PDF attached

Deadline: See original assignment
Points: See original assignment

Best regards,
HelixKB Admin
"""

RECEIVED_EMAIL_BODY = """
Hi,

Your {kb_id} contribution has been received!

Status: Under Review
Next Steps: Manager review (2-3 business days)

Best regards,
HelixKB Admin
"""

# ... (more templates)
```

---

### MailHog API Integration

**Endpoint:** `http://mailhog:8025/api/v2/messages`

```python
import requests

def fetch_from_mailhog(email_id: str) -> str:
    """Fetch raw email from MailHog API"""
    response = requests.get(f'http://mailhog:8025/api/v2/messages/{email_id}')
    response.raise_for_status()

    data = response.json()
    return data['Raw']['Data']  # Base64-encoded raw email


def poll_mailhog():
    """Poll MailHog for new emails (Celery beat task)"""
    response = requests.get('http://mailhog:8025/api/v2/messages')
    response.raise_for_status()

    messages = response.json()['items']

    for msg in messages:
        email_id = msg['ID']
        subject = msg['Content']['Headers']['Subject'][0]

        # Check if KB-related
        if 'KB-' in subject:
            # Queue for processing
            process_kb_email.delay(email_id)
```

---

### Database Schema

**Table:** `kb_contributions`

```sql
CREATE TABLE kb_contributions (
    id SERIAL PRIMARY KEY,
    kb_id VARCHAR(20) NOT NULL,  -- KB-042
    title VARCHAR(255) NOT NULL,
    contributor_email VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- assigned, accepted, submitted, approved, declined
    points INT DEFAULT 0,
    category VARCHAR(100),
    language VARCHAR(5),
    deadline DATE,
    assigned_at TIMESTAMP,
    accepted_at TIMESTAMP,
    submitted_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewer_email VARCHAR(255),
    submission_path VARCHAR(500),  -- PDF file path
    feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kb_email_log (
    id SERIAL PRIMARY KEY,
    kb_id VARCHAR(20),
    sender VARCHAR(255),
    recipient VARCHAR(255),
    subject TEXT,
    body TEXT,
    attachments JSONB,  -- [{"filename": "...", "path": "..."}]
    direction VARCHAR(10),  -- inbound, outbound
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🎮 Admin Dashboard (HelixKB Manager)

**URL:** `http://localhost:8000/admin/kb`

**Features:**
- 📊 KB pipeline (assigned → submitted → approved)
- 📧 Email log (all inbound/outbound)
- 👥 Contributor leaderboard (badges, points)
- ✅ Approve/feedback workflow (review PDFs, add comments)
- 📈 Analytics (time to approval, acceptance rate)

**Approve Workflow (Manager View):**
```
┌─────────────────────────────────────────┐
│ KB-042: Storz & Bickel Volcano (German) │
│ Submitted: 2025-11-27 15:45             │
│ Contributor: felix@artemis-headshop.ch  │
└─────────────────────────────────────────┘

PDF Preview:
┌─────────────────────────────────────────┐
│ [PDF rendered inline]                   │
│                                         │
│ Sales Techniques:                       │
│ - Upsell cleaning kit (CHF 15-25)      │
│ - Explain warranty (3 years S&B)       │
│ - Compare vs Pax (vapor quality)       │
│ ...                                     │
└─────────────────────────────────────────┘

Actions:
[✅ Approve] [📝 Feedback] [❌ Decline]

Feedback (optional):
┌─────────────────────────────────────────┐
│ Excellent sales techniques section.     │
│ The competitor comparison is helpful.   │
└─────────────────────────────────────────┘

[Send]
```

---

## 🏆 Badge System

### Tiers
| Badge | KBs Required | Rewards |
|-------|--------------|---------|
| **Bronze** | 1 approved KB | Email signature badge, profile icon |
| **Silver** | 5 approved KBs | Free file adapter (CHF 50 value) |
| **Gold** | 15 approved KBs | CHF 200 credit, priority support |
| **Platinum** | 50 approved KBs | Lifetime free upgrades, revenue share |

### Email Signature (Auto-Added)
```
───────────────────────────────────────────
Felix
Artemis Headshop, Bern
🥈 HelixKB Silver Contributor (12 KBs)
───────────────────────────────────────────
```

---

## 🔐 Security & Compliance

### Email Authentication
- **SPF:** Verify sender domain (prevent spoofing)
- **DKIM:** Sign outbound emails (authenticity)
- **Allowlist:** Only registered contributors can submit

### PDF Security
- **Scan:** Virus scan all attachments (ClamAV)
- **Validate:** Check PDF structure (not malicious)
- **Size Limit:** Max 5MB per PDF

### Audit Trail
- Every email logged (sender, recipient, timestamp)
- Every status change logged (who, when, why)
- GDPR-compliant (contributor can request deletion)

### Backup
- MailHog maildir backed up daily
- PDFs stored in Git LFS (version control)
- Email log exported weekly (CSV for compliance)

---

## 📊 Metrics & KPIs

### Contributor Engagement
- **Assignment Acceptance Rate:** Target 80%+
- **Time to Submit:** Target <7 days
- **Revision Rate:** Target <20% (first submission approved)

### Admin Efficiency
- **Time to Review:** Target <3 business days
- **Approval Rate:** Target 70%+ (quality control)
- **Feedback Clarity:** Contributor satisfaction survey

### KB Growth
- **Monthly New KBs:** Target 10+ (year 1)
- **Languages:** 4 (DE, FR, IT, EN)
- **Categories:** 5 (product, sales, compliance, ops, business)

---

## 🚀 Implementation Roadmap

### Phase 1: MVP (Week 1)
- ✅ MailHog setup (Docker Compose)
- ✅ Email parser (basic ACCEPT/DECLINE)
- ✅ Template generation (PDF form)
- ✅ Manual review workflow (admin dashboard)

### Phase 2: Automation (Week 2-3)
- ✅ Celery beat (poll MailHog every 5 min)
- ✅ Auto-send template on ACCEPT
- ✅ PDF extraction and storage
- ✅ Badge calculation (auto-award)

### Phase 3: Enhancements (Week 4+)
- ✅ Multi-language templates (DE/FR/IT/EN)
- ✅ Revision workflow (feedback loop)
- ✅ Delegate function (reassign KB)
- ✅ Analytics dashboard (contributor leaderboard)

---

## 🧪 Testing Plan

### Unit Tests
```python
def test_parse_accept_email():
    raw = """From: felix@artemis.ch
Subject: Re: [KB-042] ASSIGNED
Body: ACCEPT"""

    parser = KBEmailParser(db)
    parsed = parser.parse_email(raw)

    assert parsed['kb_id'] == 'KB-042'
    assert parsed['command'] == 'ACCEPT'


def test_extract_pdf_attachment():
    # Test PDF extraction from multipart email
    pass
```

### Integration Tests
```python
def test_accept_workflow_end_to_end():
    """
    1. Send assignment email
    2. Receive ACCEPT reply
    3. Verify template sent
    4. Check DB status = ACCEPTED
    """
    pass
```

### Manual Testing (Felix UAT)
- [ ] Felix receives assignment email (readable, clear)
- [ ] Felix replies ACCEPT (system sends template)
- [ ] Felix fills PDF (form usable, instructions clear)
- [ ] Felix submits PDF (receives confirmation)
- [ ] Felix gets approval (badge awarded, points credited)

---

## 📖 Related Documentation

- `/docs/kb-pdf-template-spec.md` - PDF form design
- `/docs/kb-admin-dashboard-spec.md` - Manager review UI
- `/docs/kb-badge-system-spec.md` - Gamification details

---

## ✅ Success Criteria

This workflow is successful when:
1. ✅ Felix (non-technical) can contribute KB via email only
2. ✅ <5 min from ACCEPT to template received
3. ✅ <3 days from submit to approval
4. ✅ Zero failed emails (robust parsing)
5. ✅ 10+ KBs contributed in first month

---

**End of MailHog KB Workflow Specification**
