# Banco — Cockpit + Tags (spec)

*The first concrete piece of the metadata-graph layer from `HELIXNET-VISION.md` (the
Taxonomy/Trend layer + the cockpit). Two halves: give Pam a **cockpit** (she's flying blind
right now), and fix the **tags** so the cockpit's drill-in actually works. Both lean heavily
on what already exists — reuse, don't reinvent.*

---

## PART 1 — The Cockpit (Pam's personal dashboard)

**The gap:** a cashier can see the *total* but can't review *what she sold*, can't drill in,
sees nothing motivating. She's in the shop but out of the loop.

**The good news:** the data is already computed. The **juicy daily report**
(per-cashier-by-name, top-3 leaderboard, avg basket, items sold, busiest hour) exists — Felix
sees it, Pam doesn't. And `GET /transactions` already returns *"managers see all, cashiers see
their own."* So this is **surfacing existing data, scoped to her, dressed up** — not new
plumbing.

### What the cockpit shows
| Tile | Content | Source |
|------|---------|--------|
| **Your day** | your sales (CHF), your transactions, **your** best item today, your busiest hour | daily report, `mine` |
| **Your people** | the members you served today | transactions + customer link |
| **A little lift** | "CHF 40 past yesterday," a streak, a personal best | daily report vs yesterday |
| **Your sales (drill-in)** | a list of today's sales → tap → the items → tap an item → what it is + how it's moving | `GET /transactions?date=today` (own) |

### Make it juicy — suggestions, tips, FAQ
A cockpit doesn't just *report* — it **teaches and nudges**, so Pam is never stranded and gets a
little better at the job every shift. Three layers, kept clean (a few smart things, not clutter):

- **Suggestions (data-driven — from HER day, so they're relevant not generic):**
  - "**3 items you sold today still need tags** — tidy them up" *(closes the needs-tags loop)*
  - "You're **CHF 40 from beating yesterday**"
  - "Papers + filters sell together — **suggest the pair**" *(basket affinity)*
  - "**A walk-in spent CHF 60 today** — worth a member invite?"
- **Tips (one rotating how-to at a time — teaches the system + the trade):**
  - "No barcode? **Take a photo → make a label.**"
  - "**Open your drawer before the first cash sale.**"
  - "Found a hot item? **Tag it so it shows in the reports.**"
- **FAQ / help (in-app, collapsible — she helps herself instead of waiting on Felix):**
  - "How do I add a member?" · "Item has no barcode?" · "Customer wants a refund? → **ask a
    manager.**" · "Stuck / something broke? → **the feedback button**, or call Ralph."
  - **The content lives in the existing KB** (`kb_router` — we already have it). Tips + FAQ are
    **KB articles**, surfaced contextually on the cockpit; **Felix/Ralph curate them in the KB**,
    the cockpit just shows the relevant ones. **One knowledge base, many windows — never build a
    second help system.** (The KB is an asset we already own; the cockpit is its front door for Pam.)

**Keep it clean:** a handful of *relevant* nudges + a tidy help corner. Juicy ≠ cluttered — one
good suggestion she acts on beats ten she scrolls past. (This is the anti-stranded, dignity
layer: she's looked after, so she looks after the customer.)

### Gamify it — but gamify the RIGHT things
Make the shift a game Pam *wants* to win — but **reward care + quality, not raw sales.** A sales
leaderboard breeds hard-selling and pressure (death to a CRACK community). Reward the behaviours
that feed the flywheel, and the sales come as the byproduct.

**What to reward (the good behaviours):**
- **Drawer accuracy** — "Balanced to the franc, 7 days straight." Integrity, streaked.
- **Member care** — "Member Maker: 5 sign-ups this week." Serving regulars. *(the Relate layer)*
- **Enrichment** — "Enricher: 12 items tagged / photographed this week." *(feeds the metadata graph)*
- **Consistency** — show-up streaks, "first sale of the day."

**Mechanics (light, tasteful — not a kids' app):**
- **Personal bests** — "New best day!", biggest basket, fastest clean close. *Compete with yourself.*
- **Daily goal** — a progress bar to "beat yesterday"; hit it → a small celebration (a green
  flourish, not a slot machine).
- **Badges / streaks** — earned for the good behaviours above, shown on her cockpit.
- **Leaderboard = manager view.** Ralph sees the cross-cashier board; **a cashier sees only her
  own rank** ("you're #2 this week"), never others' numbers — respects "she sees only her own."

**Why it's more than morale:** the game makes Pam *want* to tag items, sign up members, and
balance her drawer — the exact actions that feed velocity, the community, and clean data.
**The gamification IS an engine for the flywheel,** not a sticker chart.

**Gotcha:** never gamify revenue/sales directly — it corrupts the customer relationship and
invites gaming. Reward the *care*; the money follows.

### Earn points for growing the KB — staff now, members next
The KB isn't a maybe — **it already exists, with a full workflow.** `kb_router` is tagged
*"📚 KB Contributions"*: a **cashier can already submit** a KB (`POST /kb`, any-pos-role), it goes
**pending → review → approve/reject** (manager-gated), and staff can **review** each other's
(`/kb/{id}/review`). Model: `kb_contribution_model`. The contribution engine is done.

**Gamify the contribution (staff — buildable now):**
- Points + badges for **approved** KBs ("Author") and for **reviews** ("Reviewer"). The workflow
  already records who submitted / reviewed / approved — points are mostly *counting existing events*.
- **Points on APPROVAL, not submission** — the quality gate (manager review) is what pays. Kills
  spam, rewards *useful* knowledge. Pam writes "how I handle a returned Zippo," it's approved, she
  earns, the shop's knowledge grows. She previews her own drafts too.

**Members too (the vision — same engine, extended):** open contribution to **members** —
**product write-ups, extra details, photos, videos** — earning **loyalty credits** when approved.
The CRACK community **co-authors the catalogue**: who knows the Royal Kush better than the regular
who buys it every week? Moderated by the same review gate. That's **crowd-sourced enrichment + the
Relate layer fused** — the community makes the products richer, and is rewarded for it.

**Gotchas:** points on *approval* not submission (no spam) · member content is **moderated** —
quality *and* legal (a member can't claim "cures cancer"; the review gate catches it) · **videos
are the bigger lift** (storage/MinIO + the video pipeline) — write-ups first, videos later.

### The Clipper case — product knowledge at the point of sale (why all this matters)
A real example that ties the cockpit, the KB, and the suggestions into one job. A **Clipper lighter**
comes in **small and large** — and the **replaceable flints are size-specific to match**, which is
**NOT obvious from the packaging.** Buy the wrong flint, you can't replace it. The **gas refill** needs
the **Clipper nozzle** (a standard, but some bottles refill cleaner than others). Tribal knowledge —
the kind that lives in Felix's head and walks out the door the day he's not there.

This is **two different things, with two different homes:**
- **Knowledge note (a write-up):** *"Flints are size-specific — match the lighter. Gas needs the
  Clipper nozzle; Brand-X refills cleanest."* → a **KB article attached to the product** (staff write
  it, members add to it, the review gate keeps it honest).
- **Compatibility / cross-sell link (structured):** *this lighter → its matching flint(s) → its gas.*
  A **"fits / goes-with" relationship**, not free text — because the till needs to *act* on it.

**The payoff at the counter:** Pam rings a Clipper → the cockpit **pops the note** ("small or large?
flints must match") **and suggests the right flint + the right gas.** She looks like she's worked there
twenty years, the customer doesn't go home with the wrong flint, and the basket grows by two items —
*correctly.* Suggestion engine + KB + compatibility, doing one real job.

**And it's the perfect member-KB case:** who knows the flint-size gotcha better than the regular who's
refilled his Clipper fifty times? Let members write it; staff approve it; everyone benefits.

**Build order (incremental, don't boil the ocean):** KB notes on products first (reuse the KB) →
compatibility links (structured "fits/goes-with") → the point-of-sale pop. The note alone already
saves the wrong-flint sale.

**And don't judge the lighter by its margin.** A buck-fifty lighter is one of the *most important*
items in the shop — the everyday essential people walk in for, the anchor of half the baskets, the
**razor in razor-and-blades.** By *revenue* it's nothing; by *role* it's a **traffic driver.** So the
reports and the cockpit should recognise that **role** (a "key item / everyday essential" flag), not
rank by money alone — it's the other half of the by-units-vs-by-revenue story. And the **cross-sell
writes itself:** lighter → matching flint → the right gas → a **leash** (Felix wears his on a
belt-buckle chain, slings right back) so they never lose it. A buck-fifty becomes a five-franc basket,
*and* the customer's actual problem — "I always lose my lighter" — is solved. That's the shop being
helpful, not just ringing a sale.

### Rules
- **Read-only.** No editing a completed sale (it's a financial record — *reverse, never edit*).
  Corrections are rare and handled elsewhere: the buck-fifty lighter = a giveaway/replace, the
  rare CHF-80 Zippo = the existing manager-gated refund. **Build no cashier edit/refund here.**
- **Scope (DECIDED — keep it simple):** a **cashier sees ONLY her own** — her own cash drawer,
  her own sales. A **manager (Ralph) sees all.** **No cashier "see-all" toggle, no setting** —
  revisit *only if/when* Pam is promoted to manager. The back-end **already enforces this**
  (`/transactions`: "managers see all, cashiers see their own"; daily-summary `mine`), so the
  cockpit just surfaces the already-scoped data. Nothing to gate.
- **Personal, not a ledger.** It should make her go *"that's my day"* — motivating, hers.

### Acceptance
- [ ] Pam's dashboard has a **"Today's Sales"** view: her transactions, drill-in to items.
- [ ] It shows her juicy stats (best item, busiest hour, avg basket) — her own.
- [ ] It is **read-only**; no edit/refund controls for a cashier.
- [ ] Pam sees **only her own** (own drawer + own sales). A **manager (Ralph) sees all**. No cashier see-all toggle — revisit only on promotion.
- [ ] **Data-driven suggestions** (needs-tags, beat-yesterday, basket pair, member invite) + a **rotating tip** + a **collapsible FAQ** — tips/FAQ content from the **existing KB** (`kb_router`), curated by Felix/Ralph, not a second help system.
- [ ] **Gamification rewards care/quality** (drawer accuracy, member sign-ups, enrichment, KB contributions) via streaks/badges/personal-bests + a "beat yesterday" goal — **never raw sales**; leaderboard manager-only (cashier sees own rank).
- [ ] **Points for APPROVED KB contributions** (staff, buildable now). Member contributions (write-ups/photos/videos → loyalty credits, moderated by the review gate) = the next-phase vision.

---

## PART 2 — Tags (so the drill-in actually works)

**Two real problems:**
1. **Born-once tags nothing** — every on-the-fly item lands naked.
2. **Free-format tags rot** — "CBD" / "cbd" / "C.B.D", "flower" / "flowers" / "blossom":
   three spellings, and the groups stop grouping. The drill-in breaks.

**Goal:** keep free-format (flexible — Angel wants it) *without* the spelling drift.

### The fix — suggest, then normalize
- **Autocomplete from existing tags.** Typing a tag suggests the tags that already exist, so you
  *pick* `cbd-flower` instead of inventing `CBD Flowers` fresh. New tags still allowed; gravity
  pulls everyone toward the existing set. *(This is how Gmail labels / Stack Overflow tags
  survive — suggest, don't police.)*
- **Normalize on save** — lowercase, trim, de-dupe, collapse spaces→hyphens. `"CBD "` and `"cbd"`
  become one tag automatically. Never rely on willpower.
- The product model already has the `tags` field — wire the input + the normalize step.

### Born-once stays fast
- **Don't make Pam tag mid-sale** (kills the speed). On creation, auto-assign a **baseline tag**
  (the category) and flag the item **`needs-tags`**.
- The flagged items surface in the **catalogue-health report** (REPORTS-TOP10) — the hot ones get
  their proper tags later, in calm time. *The item earns its tags when it earns the attention.*

### Structured vs free — the split that stops reports from lying
The **money dimensions** must be **structured fields (picked from a list), NOT free tags:**

| Structured (controlled — reports depend on it) | Free tags (long-tail flavor) |
|---|---|
| category, brand, **effect** (relax/sleep/energy), **THC% / CBD%**, age-restricted | "gift-idea", "festival", "staff-pick", "regulars-love-it" |

A typo in a *free* tag is a cosmetic miss. A typo in a *money dimension* is **a lie in the
numbers.** Keep those controlled; let the rest run free.

### Acceptance
- [ ] Tag input **autocompletes** from existing tags; new tags allowed.
- [ ] Tags **normalize** on save (lowercase/trim/dedupe) — `CBD` and `cbd` merge.
- [ ] Born-once auto-tags the **category** + flags **`needs-tags`** (no typing required at the till).
- [ ] `needs-tags` items appear in the catalogue-health report for later enrichment.
- [ ] The money dimensions (category/brand/effect/THC-CBD) are **structured**, not free text.

---

## The connection + build order

**Tags are the joints of the metadata graph.** The cockpit's drill-in / "research / link to my
stuff" only works if tags are consistent. So:

1. **Cockpit first** — it's mostly surfacing the report you already wrote; high value, low build.
2. **Tag autocomplete + normalize** — the discipline that makes everything downstream (drill-in,
   velocity-by-tag, trends, the per-supplier list) reliable.
3. **Born-once baseline-tag + `needs-tags`** — closes the enrichment loop.

**Gotchas:** spelling drift → autocomplete+normalize (not willpower) · tag explosion → suggest
existing + a "merge tags" tool for Felix later · don't slow the sale → tag at enrichment, not at
the till · reports lie if money-dimensions are free → keep them structured.

---

*"Good tags make a powerful cockpit for free. Invest the discipline once; the drill-in lights up
everywhere."*
