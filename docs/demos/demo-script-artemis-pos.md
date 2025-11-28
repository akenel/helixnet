# HelixPOS Demo Script - Artemis Headshop

**Duration:** 5 minutes
**Audience:** Felix (Artemis), Raluca (StudioJadu), potential headshop owners
**Presenter:** angel
**Demo Environment:** HelixNet Sandbox (http://localhost:8000/pos)

---

## 🎯 Demo Objectives

1. Show VAT-correct implementation (Accenture €20M mistake avoided)
2. Demonstrate headshop-specific workflows (age verify, CBD compliance)
3. Highlight upsell combos (sales techniques built-in)
4. Prove email KB contribution (non-technical Felix can contribute)
5. Compare free vs paid tiers (business model clarity)

---

## 📋 Pre-Demo Checklist

- [ ] HelixNet running (`make up`)
- [ ] 20 Artemis products seeded (`python src/services/artemis_product_seeding.py`)
- [ ] Browser at http://localhost:8000/pos/scan
- [ ] Sample ID ready (passport, Swiss ID)
- [ ] MailHog UI open (http://localhost:8025)
- [ ] Banana accounting export folder empty (demo fresh export)

---

## 🎬 Demo Script

### INTRO (30 seconds)

> "Good afternoon Felix, Raluca. Today I'm showing you HelixPOS - a Point of Sale system built specifically for headshops. Unlike generic POS systems like Odoo or Square, HelixPOS knows your business.
>
> This demo shows a typical customer transaction at Artemis Headshop. We'll see:
> - Swiss VAT compliance (to the penny)
> - Age verification (Swiss law)
> - Sales techniques (upselling built-in)
> - Knowledge base contribution (Felix's 25 years)
>
> Let's begin."

---

### SCENE 1: Age Verification (45 seconds)

**Screen:** Age Verify (http://localhost:8000/pos/scan)

**Presenter Actions:**
1. Customer walks in → "Welcome to Artemis!"
2. Click "Start New Sale"
3. **Age Verify Screen appears FIRST**

**Narration:**
> "Swiss law requires ID check for all customers, even if they look 40. This isn't optional - it's built into the workflow. You CANNOT browse products until ID is verified."

**Demo:**
```
┌────────────────────────────────────────┐
│ 🔒 AGE VERIFICATION REQUIRED           │
│                                        │
│ Swiss Law: 18+ for tobacco/CBD sales  │
│                                        │
│ [Scan ID]  [Manual Entry]              │
│                                        │
│ Acceptable IDs:                        │
│ ✓ Swiss ID Card                        │
│ ✓ Passport (any country)               │
│ ✓ EU ID Card                           │
│ ✓ Swiss Driving License                │
└────────────────────────────────────────┘
```

**Actions:**
1. Click "Manual Entry"
2. Enter: DOB = 1990-05-15 (35 years old)
3. Country: Switzerland
4. ID Type: Swiss ID
5. Click "Verify"

**Result:**
```
✅ AGE VERIFIED
Customer: 35 years old (born 1990-05-15)
```

**Narration:**
> "Age verified. Now we can browse products. Notice the system logged this - for audits, we can prove we checked ID."

---

### SCENE 2: Product Browsing (60 seconds)

**Screen:** Product Catalog (categories visible)

**Narration:**
> "These products are Felix's actual inventory - 25 years of headshop expertise. Notice the categories match how Felix organizes his shop."

**Demo - Category View:**
```
┌────────────────────────────────────────┐
│ ARTEMIS HEADSHOP                       │
│                                        │
│ Categories:                            │
│                                        │
│ 🪴 CBD Products (25% of sales)         │
│ 💨 Smoking Accessories (60% of sales)  │
│ 🌡️  Vaporizers (10% of sales)          │
│ 👕 Merchandise (5% of sales)           │
└────────────────────────────────────────┘
```

**Actions:**
1. Click "CBD Products"
2. Show CBD Flowers (Lemon Haze, OG Kush)

**Narration:**
> "Every CBD product shows: THC limit (<1%), CBD content, batch number, lab certificate. This is Swiss compliance built-in."

**Product Card Example:**
```
┌────────────────────────────────────────┐
│ CBD Flowers - Lemon Haze (5g)          │
│                                        │
│ CHF 45.00 (incl. 8.1% VAT)             │
│                                        │
│ 🧪 THC: 0.8% (legal <1%)              │
│ 🌿 CBD: 12.0%                          │
│ 📄 Batch: HAZE-2025-Q4-001            │
│ ✅ Lab Cert: View PDF                  │
│                                        │
│ [Add to Cart]                          │
└────────────────────────────────────────┘
```

**Actions:**
1. Click "Add to Cart" → CBD Flowers Lemon Haze

---

### SCENE 3: Upselling (90 seconds)

**Screen:** Product added, upsell suggestions appear

**Narration:**
> "Here's where Felix's 25 years of knowledge kicks in. The system KNOWS what goes together."

**Upsell Pop-up:**
```
┌────────────────────────────────────────┐
│ 💡 CUSTOMERS WHO BOUGHT THIS ALSO:     │
│                                        │
│ ✓ RAW King Size Papers (CHF 2.50)     │
│   "Recommended for CBD flowers"        │
│   [Add]                                │
│                                        │
│ ✓ Space Case Grinder (CHF 65.00)      │
│   "Premium grinder, titanium-coated"   │
│   [Add]                                │
│                                        │
│ ✓ DynaVap Vaporizer (CHF 80.00)       │
│   "Healthier alternative to smoking"   │
│   [Add]                                │
│                                        │
│ [Skip]  [Add All]                      │
└────────────────────────────────────────┘
```

**Actions:**
1. Click "Add" for RAW Papers
2. Click "Add" for Space Case Grinder
3. Click "Skip" (don't add vaporizer)

**Narration:**
> "These aren't random suggestions. Felix's KB (HelixPOS_KB-001) defines these combos. New staff see the same recommendations Felix would make."

**Cart Now:**
```
┌────────────────────────────────────────┐
│ 🛒 CART (3 items)                      │
│                                        │
│ 1. CBD Flowers Lemon Haze     45.00   │
│ 2. RAW King Size Papers         2.50   │
│ 3. Space Case Grinder          65.00   │
│                                        │
│ Subtotal:                     112.50   │
│                                        │
│ [Continue Shopping]  [Checkout]        │
└────────────────────────────────────────┘
```

**Actions:**
1. Click "Checkout"

---

### SCENE 4: Discount & Freebies (60 seconds)

**Screen:** Checkout with discount options

**Narration:**
> "Felix offers loyalty discounts (5% for regulars). Watch how VAT is calculated - AFTER discount, not before. This is where Accenture failed."

**Checkout Screen:**
```
┌────────────────────────────────────────┐
│ CHECKOUT                               │
│                                        │
│ Customer Type:                         │
│ ⭕ New  ⚫ Local (5% off)  ⭕ Tourist  │
│                                        │
│ Freebie Eligible? (>CHF 100)          │
│ ☑ Yes - Add Clipper Lighter (CHF 2)   │
│                                        │
│ Payment Method:                        │
│ ⚫ Cash  ⭕ Card  ⭕ Twint               │
└────────────────────────────────────────┘
```

**Actions:**
1. Select "Local (5% off)"
2. Check "Add Clipper Lighter freebie"
3. Select "Cash"
4. Click "Calculate Total"

**VAT Calculation (Live):**
```
┌────────────────────────────────────────┐
│ CALCULATION BREAKDOWN                  │
│                                        │
│ Items Subtotal:           CHF 112.50   │
│ Discount (5%):            CHF  -5.63   │
│ ──────────────────────────────────     │
│ Subtotal (after disc):    CHF 106.87   │
│                                        │
│ Freebie:                  CHF   0.00   │
│ (Clipper Lighter - promotional)        │
│                                        │
│ VAT (8.1%):               CHF   8.66   │
│ ──────────────────────────────────     │
│ TOTAL:                    CHF 115.53   │
│                                        │
│ [Print Receipt]  [Complete Sale]       │
└────────────────────────────────────────┘
```

**Narration (CRITICAL POINT):**
> "See this? VAT calculated AFTER discount. Not before. Accenture's €20M mistake was calculating VAT before discount - illegal in Switzerland. HelixNet gets this right from day 1."

**Comparison Table (Show on screen):**
```
WRONG (Accenture):             CORRECT (HelixNet):
Items: CHF 112.50              Items: CHF 112.50
VAT (8.1%): CHF 9.11           Discount: CHF -5.63
Discount: CHF -5.63            Subtotal: CHF 106.87
Total: CHF 115.98  ❌           VAT (8.1%): CHF 8.66
                               Total: CHF 115.53  ✅

Difference: CHF 0.45 (per transaction)
Over 10,000 transactions/year: CHF 4,500 error
Audit penalty: CHF 20,000+ fine
```

**Actions:**
1. Click "Complete Sale"

---

### SCENE 5: Receipt (45 seconds)

**Screen:** Receipt preview

**Narration:**
> "Swiss tax law requires receipts show VAT breakdown. Here's the proof Felix can show auditors."

**Receipt:**
```
┌────────────────────────────────────────┐
│      ARTEMIS HEADSHOP                  │
│      Bern, Switzerland                 │
│      UID: CHE-123.456.789              │
│                                        │
│ Receipt: R-001                         │
│ Date: 2025-11-27 15:30:00              │
│ Cashier: angel                         │
│                                        │
│ ──────────────────────────────────     │
│                                        │
│ CBD Flowers Lemon Haze                 │
│ 1 × CHF 45.00            CHF   45.00   │
│                                        │
│ RAW King Size Papers                   │
│ 1 × CHF 2.50             CHF    2.50   │
│                                        │
│ Space Case Grinder                     │
│ 1 × CHF 65.00            CHF   65.00   │
│                                        │
│ ──────────────────────────────────     │
│ Subtotal:                CHF  112.50   │
│ Discount (5% Local):     CHF   -5.63   │
│ ──────────────────────────────────     │
│ Net Total:               CHF  106.87   │
│                                        │
│ VAT 8.1%:                CHF    8.66   │
│ ──────────────────────────────────     │
│ TOTAL:                   CHF  115.53   │
│                                        │
│ ──────────────────────────────────     │
│ PROMOTIONAL ITEM (no charge):          │
│ • Clipper Lighter (CHF 2.00 value)     │
│                                        │
│ ──────────────────────────────────     │
│ Payment: Cash            CHF  120.00   │
│ Change:                  CHF    4.47   │
│                                        │
│ Thank you for shopping at Artemis!     │
│ www.artemis-headshop.ch                │
│                                        │
│ VAT Breakdown (for audit):             │
│ Net Amount:    CHF 106.87              │
│ VAT 8.1%:      CHF   8.66              │
│ Gross Amount:  CHF 115.53              │
└────────────────────────────────────────┘
```

**Narration:**
> "Notice the freebie is listed separately - tracked for inventory but zero charge. Swiss tax law requires this transparency."

---

### SCENE 6: Banana Export (30 seconds)

**Screen:** Admin dashboard → Banana Integration

**Narration:**
> "Felix uses Banana for accounting. HelixNet exports every transaction - ready to import."

**Banana Export File (CSV):**
```
Date,Receipt,Customer,Net,VAT8.1,Gross,Payment
2025-11-27,R-001,Anonymous,106.87,8.66,115.53,Cash
```

**Actions:**
1. Click "Export to Banana"
2. Download CSV
3. Show file in Finder (or file manager)

**Narration:**
> "Every transaction, every VAT calculation - exportable for audits. 10-year retention, Swiss Federal Tax Administration compliant."

---

### SCENE 7: KB Contribution (60 seconds)

**Screen:** Switch to MailHog (http://localhost:8025)

**Narration:**
> "Now the secret sauce - Felix's 25-year knowledge. How do we capture it? Email."

**MailHog Demo:**
```
Inbox:
┌────────────────────────────────────────┐
│ From: kb-admin@helixnet.local          │
│ To: felix@artemis-headshop.ch          │
│ Subject: [KB-042] ASSIGNED: Storz...   │
│                                        │
│ Felix, you've been assigned:           │
│                                        │
│ KB-042: Storz & Bickel Volcano         │
│ Points: 5 (sales + product knowledge)  │
│                                        │
│ Reply with: ACCEPT                     │
└────────────────────────────────────────┘
```

**Actions:**
1. Click email, show content
2. Click "Reply"
3. Type: "ACCEPT"
4. Send

**Narration:**
> "Felix replies with one word: ACCEPT. That's it. No git, no CLI, no technical knowledge required."

**Next Email (Auto-sent):**
```
┌────────────────────────────────────────┐
│ From: kb-admin@helixnet.local          │
│ To: felix@artemis-headshop.ch          │
│ Subject: [KB-042] TEMPLATE: Fill PDF   │
│                                        │
│ Attached: KB-042-template.pdf          │
│                                        │
│ Instructions:                          │
│ 1. Open PDF                            │
│ 2. Fill sections                       │
│ 3. Reply with PDF attached             │
└────────────────────────────────────────┘
```

**Narration:**
> "Felix gets a PDF. He fills it out - like any office document. Replies with attachment. Done. HelixNet approves it, publishes to KB, and ALL headshops benefit."

---

### SCENE 8: Business Model (60 seconds)

**Screen:** Pricing table (slide or webpage)

**Narration:**
> "Let's talk money. Two tiers: Free and Paid."

**Pricing Table:**
```
┌─────────────────────────────────────────┐
│ FREE TIER (Felix's Pilot)               │
├─────────────────────────────────────────┤
│ ✅ Core POS (scan, checkout, receipt)   │
│ ✅ Age verification                      │
│ ✅ VAT compliance                        │
│ ✅ PDF receipts                          │
│ ✅ HelixKB access (200+ notes)           │
│ ✅ Sandbox forever (train staff)         │
│                                         │
│ Price: CHF 0 (OSS, yours forever)       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ PAID TIER (Production Ready)            │
├─────────────────────────────────────────┤
│ ✅ Everything in Free                    │
│ ✅ Banana export (CHF accounting)        │
│ ✅ File adapters (XLS, CSV)              │
│ ✅ Email support (48h response)          │
│ ✅ Custom receipt branding               │
│ ✅ Multi-location support                │
│                                         │
│ Price: CHF 40/hr professional install    │
│        + CHF 50/month (optional support) │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ENTERPRISE (ERP Integration)             │
├─────────────────────────────────────────┤
│ ✅ Everything in Paid                    │
│ ✅ SAP Business One adapter              │
│ ✅ Custom integrations                   │
│ ✅ Priority support                      │
│                                         │
│ Price: Custom (starts CHF 500 setup)     │
└─────────────────────────────────────────┘
```

**Narration:**
> "Felix's use case? FREE tier works perfectly. He needs PDF receipts and basic POS - no ERP, no complex integrations. Day 1: CHF 0. Week 1: Test in sandbox. Go-live: Still CHF 0.
>
> Want Banana export? CHF 40/hr one-time setup. That's it.
>
> Compare this to Odoo: CHF 200+/month forever. Square: 2.75% per transaction + CHF 50/month. HelixNet: CHF 0/month base, pay only for what you need."

---

### SCENE 9: Community Growth (45 seconds)

**Screen:** Contributor Leaderboard (mock or real)

**Narration:**
> "Here's the network effect. Felix contributes 12 KBs. Mosey (Italy, 20 shops) contributes 30 KBs. New shop owner in Spain reads 200+ KBs on day 1. They contribute back."

**Leaderboard:**
```
┌────────────────────────────────────────┐
│ 🏆 HelixKB Contributors (Headshops)    │
├────────────────────────────────────────┤
│ 🥇 1. Mosey (Italy) - 30 KBs (Gold)    │
│ 🥈 2. Felix (Switzerland) - 12 (Silver)│
│ 🥉 3. Paolo (Spain) - 8 KBs (Bronze)   │
│    4. Maria (Germany) - 5 KBs          │
│    5. Jean (France) - 3 KBs            │
│                                        │
│ Total: 200+ KBs in 4 languages         │
│ Growing: +10 KBs/month                 │
└────────────────────────────────────────┘
```

**Narration:**
> "Badges unlock rewards:
> - Silver (5 KBs): Free file adapter (CHF 50 value)
> - Gold (15 KBs): CHF 200 credit
> - Platinum (50 KBs): Lifetime free upgrades + revenue share
>
> Felix refers Mosey → 50% profit share on Mosey's first year. That's the network effect."

---

### CLOSING (30 seconds)

**Narration:**
> "To summarize what you just saw:
>
> 1. **VAT-correct** - Accenture's €20M mistake avoided
> 2. **Compliance built-in** - Age verify, CBD tracking, Swiss law
> 3. **Felix's knowledge** - 25 years, email-based contribution
> 4. **Free forever** - OSS, no monthly fees
> 5. **Network effect** - 200+ KBs, growing community
>
> Questions?"

---

## 🎤 Anticipated Questions & Answers

### Q1: "What if I don't want to contribute KBs?"
**A:** No problem. You still get all 200+ KBs from the community (read-only). Contributing earns badges/rewards, but it's optional.

### Q2: "Can I customize the receipt?"
**A:** Yes. FREE tier: basic template. PAID tier: Custom branding (logo, colors, footer).

### Q3: "What about credit card processing?"
**A:** HelixNet integrates with Stripe, SumUp, or Twint. You choose your payment processor (we don't take a cut).

### Q4: "How do I get support?"
**A:** FREE tier: Community forum. PAID tier: Email support (48h response). ENTERPRISE: Phone support.

### Q5: "What if I want Felix's KB but not the whole community?"
**A:** Felix can mark KBs as "Artemis-only" (private). Most KBs are public (network effect), but sensitive data stays private.

### Q6: "Can I use this for coffee shops?"
**A:** Yes, but HelixNet is optimized for headshops (age verify, CBD compliance, THC tracking). Coffee shops work, but you'd lose some features. Better fit: Use HelixNet as base, customize for your industry.

### Q7: "What's the catch? Why free?"
**A:** Business model:
> - FREE tier = Customer acquisition
> - PAID tier = Professional install + support (CHF 40/hr)
> - ENTERPRISE = Custom adapters (CHF 500+)
> - Revenue share = 50% on referrals
> Network effect grows KB value → more shops join → more KBs → cycle continues.

### Q8: "How do I migrate from my current POS?"
**A:** We offer migration services (CHF 40/hr):
> 1. Export data from old POS (products, customers)
> 2. Import to HelixNet (we write adapter)
> 3. Parallel run (1 week, both systems)
> 4. Cutover (weekend, minimize downtime)
> Total time: 2-3 weeks (depending on data quality)

---

## 📊 Demo Metrics (Post-Demo Survey)

**Target Audience Response:**
- [ ] "I understand the VAT compliance" (80%+ yes)
- [ ] "I can contribute KBs via email" (90%+ yes)
- [ ] "Free tier meets my needs" (60%+ yes for small shops)
- [ ] "I'd refer another shop" (50%+ yes)

**Conversion Goals:**
- Felix: Pilot sign-up (Week 1 FREE)
- Raluca: Feature request list (tattoo shop customization)
- Other leads: Email capture for launch announcement

---

## 🛠️ Post-Demo Actions

### Immediate (Same Day):
1. Email demo attendees with sandbox link
2. Create Felix's HelixNet account (pilot access)
3. Send KB-001 (Felix's Headshop 101) for review

### Week 1:
1. Felix tests in sandbox (provide 20 products pre-seeded)
2. Collect feedback (what's missing, what's confusing)
3. Fix critical bugs (if any)

### Week 2-3:
1. Felix go-live planning (new location timeline)
2. Mosey outreach (Italian/Spanish headshops)
3. KB contribution workflow testing (real email flow)

### Month 1:
1. Felix live in production (new location)
2. Case study: "Artemis Headshop - 25 Years, Now Digital"
3. Launch announcement: "HelixNet for Headshops - Open Beta"

---

## 📸 Demo Screenshots (For Documentation)

1. Age verify screen
2. Product catalog (CBD section)
3. Upsell suggestions (combo builder)
4. VAT calculation breakdown (CRITICAL - show Accenture comparison)
5. Receipt preview (Swiss compliant)
6. Banana export (CSV file)
7. MailHog inbox (KB assignment email)
8. Pricing table (Free vs Paid)
9. Contributor leaderboard (community growth)

---

## 🎯 Success Criteria

This demo is successful if:
1. ✅ Felix says "I want to test this in sandbox"
2. ✅ Attendees understand VAT compliance (can explain Accenture mistake)
3. ✅ At least 1 referral email (Mosey or other shop)
4. ✅ Zero technical questions about KB contribution (email workflow clear)
5. ✅ Free tier value proposition clear (not "why so cheap?" but "this makes sense")

---

**End of Demo Script**

**Next Steps:**
1. Rehearse demo (3x before live presentation)
2. Record demo (video for website/marketing)
3. Felix review (ensure product catalog accurate)
4. Raluca review (studio shop customization notes)

---

**Generated:** 2025-11-27
**Author:** angel
**HelixNet Version:** v2.2.0-debllm + Artemis POS Sprint
