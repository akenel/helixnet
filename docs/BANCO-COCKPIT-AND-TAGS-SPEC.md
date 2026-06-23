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

### Rules
- **Read-only.** No editing a completed sale (it's a financial record — *reverse, never edit*).
  Corrections are rare and handled elsewhere: the buck-fifty lighter = a giveaway/replace, the
  rare CHF-80 Zippo = the existing manager-gated refund. **Build no cashier edit/refund here.**
- **Scope = her own by default.** The endpoint already does this. **"See the whole shop /
  everyone's sales + the day's takings" is a Felix decision, not the silent default** — fine in
  a small trusted CRACK shop, a leak/trust risk in a bigger one. Make it a setting or a manager
  view, not reflex.
- **Personal, not a ledger.** It should make her go *"that's my day"* — motivating, hers.

### Acceptance
- [ ] Pam's dashboard has a **"Today's Sales"** view: her transactions, drill-in to items.
- [ ] It shows her juicy stats (best item, busiest hour, avg basket) — her own.
- [ ] It is **read-only**; no edit/refund controls for a cashier.
- [ ] By default she sees **only her own**; store-wide is gated/optional.

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
