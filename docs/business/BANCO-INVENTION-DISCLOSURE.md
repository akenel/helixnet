# Banco — Invention Disclosure (draft for patent counsel)

*Prepared 2026-06-29 for Angelo (Albert-Daniel) Kenel. This is a **first-draft invention disclosure** — the document a patent attorney or agent reads to assess patentability and draft claims. It is **not** a legal opinion and was not prepared by a lawyer. Treat every "novel" below as a hypothesis to be tested by a professional prior-art search, not a conclusion.*

---

## ⚠️ READ THIS FIRST — the disclosure clock

**Public disclosure of an invention can bar patent rights. The rules differ by region:**

- **United States:** a 12-month grace period runs from the **first public disclosure** (sale, demo, video, blog, pitch). File within 12 months or lose US rights.
- **Europe (EPO) and most of the world:** **absolute novelty — no grace period.** Any public disclosure *before* the filing date can **permanently bar** a European patent.

**Banco has already been disclosed publicly** via the *Born Once* YouTube series and live demos. **Action item, time-sensitive:** before the *next* public video, demo, or pitch that shows the loop in operation, get a patent attorney's read on (a) whether the existing disclosures have already started/limited the clock, and (b) whether to file a **US provisional application** (~USD 130–300 government fee; holds a priority date for 12 months) *now* to preserve optionality. Do not treat this as urgent-but-someday. The cheapest mistake to avoid is disclosing more before deciding.

---

## 1. Inventor & field

- **Inventor:** Angelo (Albert-Daniel) Kenel.
- **Working title:** Banco — a point-of-sale (POS) / light-ERP for small merchants.
- **Field:** point-of-sale and small-business management software; AI-assisted product-feedback/support workflows; inventory and customer-record capture at point of sale.

## 2. The problem being solved

Small merchants (market vendors, cafés, single-location shops; roughly CHF/EUR 100k–5M turnover) are served badly at two points:

1. **Support after go-live.** Enterprise software gives intensive "hypercare" only as a *temporary* post-launch phase, then drops the customer into a ticket queue or a paid partner SLA. A 25-seat shop gets neither the hypercare nor an affordable substitute — its feedback dies in a black hole or a public vote board.
2. **Selling things that were never catalogued.** Existing POS assume a **catalogue and a customer exist before the sale.** A maker with 50 unlabelled handmade items, nothing written down, must either pre-build a catalogue (work she won't do) or ring a nameless "custom amount" that captures nothing reusable.

## 3. The invention — two interlocking mechanisms

### Mechanism A — Permanent, AI-mediated, self-closing "hypercare" loop (merchant-facing)

A feedback-and-resolution loop built **into the merchant product itself**, operating as a *permanent* mode (not a launch phase):

1. The merchant/operator taps an in-product feedback control during normal use.
2. An **AI agent triages the raw, messy feedback into a clean, categorized backlog ticket** (de-duplicated, classified, prioritized) on the vendor's/steward's product backlog — without the merchant learning any ticketing system.
3. The work is performed and shipped.
4. The **original reporter is notified in-product and confirms/closes their own loop** — the person who raised it is the person who closes it.
5. A **visible heal-time / SLA is surfaced in-product** ("Healed in 2h 37m"), making responsiveness a legible feature.

The combination that is asserted as non-obvious: *merchant-facing* + *AI-triaged* + *original-reporter self-close* + *visible heal-time* + *permanent operating mode*, embedded in a vertical SME POS.

### Mechanism B — Zero-perpetual, "sell-first / define-after" capture

A selling and record-creation flow that **inverts the catalogue-before-sale assumption**:

1. **Zero-perpetual inventory by design:** the till never gates a sale on a stock count; the physical presence of the item is the only check. (Not a perpetual-inventory system with tracking switched off — designed without the gate.)
2. **Product born at the sale:** the operator rings an item that does not yet exist as a catalogue record — entering a name/price and/or **photographing the item at the moment of sale** — and that capture **creates a real, reusable product record** (not a nameless custom amount).
3. **Post-sale enrichment of both product and customer:** after the transaction, the operator can enrich the just-created product record *and* build/augment the buyer's customer profile (notes, business card, photos) for later follow-up (e.g., next-season outreach).
4. Optional AI assist ("Snap & fill"): a photo of an unlabelled good drafts the product name/category/description/price for one-tap confirmation.

The combination asserted as non-obvious: *no-catalogue, no-stock-gate sale* + *product record born from an at-sale photo* + *deferred enrichment of product and customer for CRM follow-up*, as a **single designed workflow**.

### Why A and B belong together

B is *why* A is needed: a merchant who starts with nothing catalogued and defines as she goes will hit rough edges constantly — so the self-healing loop (A) is the mechanism that lets the software adapt in real time instead of via a consulting engagement. The pairing — adapt-as-you-sell software with an adapt-as-you-go support loop — is the system-level idea.

## 4. Prior art already identified (honest — counsel needs this)

A targeted (non-professional) market scan on 2026-06-29 found the **components** exist separately; the **combinations** in §3 were **not found** in any POS/SME product surveyed. Disclose all of this to counsel:

**Near prior art for Mechanism A:**
- **Linear "Intake" / "Triage Intelligence"** — AI triage of messy feedback into engineering backlog tickets. *Developer-team-facing, not merchant-facing; no original-reporter self-close; no heal-time SLA.* (Closest art for the AI-triage step.)
- **Canny, Productboard, Savio, Sleekplan, LaunchNotes** — feedback-to-roadmap with "you asked, we shipped" close-the-loop notification. *Sold to software/SaaS teams; close-the-loop is largely manual email; no AI auto-triage; no heal-time SLA; standalone, not embedded in a POS.*
- **Zendesk AI, ServiceNow Now Assist, Freshdesk Freddy, Zoho Desk Zia, Intercom Fin** — AI ticket triage for internal support teams. *Not merchant-facing product-feedback; no reporter self-close in the merchant's own operating tool.*
- **"Razorpay Self-Healing POS"** — same phrase, different thing: *device/hardware* auto-troubleshooting, not a feedback-to-backlog loop.
- Academic work exists on AI-driven self-healing SLA ticket workflows, scoped to **internal enterprise IT**, no merchant application.

**Near prior art for Mechanism B:**
- **Square** custom-amount sale (captures price only); separate "create item with optional photo" (a catalogue action, not born-at-sale); barcode/GTIN-keyed auto-item-creation (fails for unlabelled goods); Photo Studio AI (makes imagery, not records); oversell-tolerance (sale not blocked at zero stock — *tolerance, not designed zero-inventory*).
- **Shopify POS** quick/custom sales (price only; catalogue-from-ecommerce origin).
- **Loyverse** per-item "track stock" toggle (opt out of a perpetual system) + back-office item creation with image.
- **Rain** craft-store POS (no photo-to-product creation advertised).

**The gap:** no surveyed product unites these into either §3 combination. That is the basis for the novelty hypothesis — to be confirmed by a professional search.

## 5. Honest assessment of patentability (non-lawyer)

- The **individual pieces are prior art** → not patentable alone.
- A **specific novel method** (either combination, or the A+B system) *may* be patentable, but US software/business-method claims face the *Alice* (2014) "abstract idea" bar; expect a real attorney to be cautious and the process to cost ~USD 10–30k+ and take years for a granted patent.
- **First-to-market ≠ patentable.** Strong evidence that "nobody does this" supports **brand, trade-secret, and first-mover** positioning regardless of whether a patent is pursued.
- For a solo founder, the **durable moat is likely execution + relationships + trade-secret + being first-and-loud**, with a patent as optional reinforcement — not the core strategy.

## 6. Recommended next steps

1. **Stop the bleed on disclosure:** decide *before the next public reveal* whether to file. (§ warning above.)
2. **One-hour consult** with a patent attorney/agent; bring this document.
3. If proceeding: file a **US provisional** to lock a priority date cheaply while deciding on full prosecution.
4. Commission a **professional prior-art search** — the only thing that converts "unoccupied in our scan" into a real patentability opinion.
5. Regardless of patent: **keep the evidence trail** (the market-scan receipts in [BANCO-WHY-NOT-THE-BIG-GUYS.md](BANCO-WHY-NOT-THE-BIG-GUYS.md) §7) and treat the specific implementation details as **trade secret** until a filing strategy is set.

---

*Not legal advice. Prepared as an engineering/business disclosure to brief professional counsel. Evidence basis: deep-research market scans, 2026-06-29 — see BANCO-WHY-NOT-THE-BIG-GUYS.md §7 for citations.*
