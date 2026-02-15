# Camper & Tour -- Monday Demo Talking Points

**Date:** Monday, February 17, 2026
**Audience:** Nino (shop manager), possibly Sebastino (owner)
**Format:** Laptop demo + discussion, 30-60 minutes
**Goal:** Is this something you want? Let's start a proper discovery.

---

## DEMO FLOW (15 minutes)

### 1. Login (30s)
- Show Keycloak SSO -- one login, all features
- "Every user gets their own account with their own permissions"
- Nino sees manager features, Simona sees counter features, mechanics see job features

### 2. Cruscotto / Dashboard (2 min)
- 4 numbers: vehicles in shop, active jobs, parts waiting, quotes pending
- Active jobs table below -- who's working on what
- "One screen replaces 20 minutes of walking around asking what's going on"
- **Nino question to expect:** "Can I see last week? Last month?" -> FUTURE: date filters + reporting

### 3. Accettazione / Check-In (2 min)
- Type a plate number -> instant vehicle history
- New plate? Click to register -> vehicle + customer in 1 minute
- "The plate number is the universal key. Everything starts here."
- **Show:** TI 123456 (MAX) -> full history appears
- **Show:** New plate -> registration form

### 4. Lavori / Job Board (2 min)
- All jobs, filterable by status
- Color-coded badges: gray/amber/red/green
- "Nino sees who needs what, right now. No whiteboard, no sticky notes."
- Click a job -> full detail

### 5. Dettaglio Lavoro / Job Detail (3 min)
- THE MONEY SHOT: MAX roof seal repair
- Show: quote amount, deposit paid, hours logged, parts ordered, PO numbers
- Mechanic notes, follow-up scheduling
- "This is a real job. This damage was real. The system tracked every step."
- **Nino question to expect:** "Can I print this?" -> FUTURE: PDF export

### 6. Clienti / Customers (2 min)
- Search by name -> full customer profile
- Total spend, visit count, vehicles owned, service history
- "Every customer, every vehicle, every euro -- tracked from day one"

### 7. Preventivi / Quotations (2 min)
- Formal quote with line items
- IVA 22% calculated automatically
- 25% deposit calculated on acceptance
- "Customer accepts the quote, deposit is calculated, job moves to approved"

### 8. Fatture / Invoices (1 min)
- Generated from completed jobs
- Deposit deducted, balance due shown
- Payment tracking (cash, card, transfer)

---

## DISCUSSION TOPICS (15-30 minutes)

### "What's Ready Now"
- Dashboard, check-in, jobs, customers, quotes, invoices, purchase orders
- Calendar, appointments, bay timeline
- 9 staff roles with different access levels
- 84 automated tests passing
- All labels in Italian

### "What's Coming Next" (show the roadmap)

| Feature | Why It Matters | Timeline |
|---------|---------------|----------|
| PDF quotes + invoices | Legal documents for customers | 1-2 weeks |
| Mobile-optimized views | Mechanics use phones in the bay | 1-2 weeks |
| Admin user management | Nino adds/removes staff without calling Angelo | 1 week |
| Backup system | Automatic daily + hourly backups | 1 week |
| Customer portal | Customers check their own job status | 2-3 weeks |
| SDI integration | Electronic invoicing (fattura elettronica) | 4-6 weeks |
| Multi-language (10+) | German/French/Dutch customers get info in their language | 3-4 weeks |
| IVA reporting | Daily/weekly/monthly/quarterly numbers for commercialista | 2-3 weeks |
| Photo uploads | Simona photographs damage, attached to job | 1-2 weeks |
| Insurance export | Full job history as one PDF for AXA | 2-3 weeks |

### "What It Takes to Install"

**Hardware:**
- Mini PC or desktop under Nino's desk (no cloud, no monthly fees)
- Connected to existing WiFi network
- Staff use tablets or phones to access the system

**Setup:**
- Angelo installs once, configures users and roles
- Angelo can remote in anytime for support and updates
- Automatic backups every hour to external storage
- Power outage? No problem -- system restarts automatically, data is safe

**Cost:**
- Hardware: one-time (mini PC ~150-300 EUR)
- Software: [YOUR PRICING MODEL HERE]
- Support: [YOUR SUPPORT MODEL HERE]

### "Questions Nino Will Ask" (be ready)

| Question | Answer |
|----------|--------|
| "Can it print?" | PDF generation coming in 2 weeks. Ctrl+P works now. |
| "What about mobile?" | Works on phone/tablet now, mobile-optimized version coming. |
| "How do I add a new worker?" | Admin panel coming. For now, Angelo does it remotely. |
| "What if the computer breaks?" | Automatic backups. We restore to a new machine in 1 hour. |
| "Can customers see their status?" | Customer portal planned. For now, you call/text them. |
| "What about electronic invoicing?" | SDI integration planned. Your accountant can still use the numbers. |
| "How much does it cost?" | [BE READY WITH THIS ANSWER] |
| "Can we try it with real data?" | Yes, we set up a test environment with your real customers. |
| "Who else uses this?" | First production installation. Built specifically for your shop. |
| "What about GDPR?" | Customer data stays on YOUR machine. Deletion available on request. |

### "The Close" (if Nino is interested)

1. **Next step:** Schedule a discovery session (2-3 hours)
   - Map Nino's actual daily workflow
   - List the 20 most common job types
   - Define which staff gets which access
   - Identify the hardware to purchase

2. **Trial period:** Install on Nino's network, seed with real customers
   - Run parallel with current method for 2 weeks
   - Staff training: 30 min per person
   - Angelo available for support during trial

3. **Go-live:** Cut over to digital-only when staff is comfortable

---

## DO NOT SAY

- "It's almost ready" (it IS ready for demo, the rest is planned)
- "We can add anything" (scope creep kills projects)
- "It's easy" (respect the complexity)
- Any specific timeline you can't keep
- Any price you haven't calculated

## DO SAY

- "This is built for YOUR shop, not a generic product"
- "The data stays on YOUR machine, not in some cloud"
- "Every number you see is real -- this is production-grade"
- "84 automated tests verify the system works correctly"
- "What matters most to you? Let's start there."

---

*"Casa e dove parcheggi." -- Home is where you park it.*
