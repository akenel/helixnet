# Banco POS — Offline Mode + PWA: Investigation & Plan

*Status: PLAN / discussion draft. Tigs + Angel, 2026-06-26.*

> **⛔ DECISION 2026-06-29 — OFFLINE SALES (P2.2 / P2.3) ARE DROPPED.** We built P2.2 (IndexedDB
> outbox + provisional receipt + auto-sync) and tested it on the phone (TEST-P22). Angel's call
> after the run: **don't do offline sales.** The use case is tiny (a cashier in a shop has a data
> plan / hotspot / can fix the wifi), and the cost is huge (provisional receipts, fiscal numbering,
> sync edge cases, a Treuhänder sign-off). The real failure mode is a **confused cashier ringing a
> sale that silently won't go through** — and that's solved by a **big, honest "no internet — sales
> paused, use mobile data/hotspot" banner + a clear block** (cart kept safe). That shipped instead.
> **P0 (PWA) and P1 (read-offline catalog) stay** (harmless, already live). **P2.1 (atomic /sales)
> stays** — it made online checkout better and is on prod. Only the offline *write* is abandoned.
> Don't re-open P2.2/P2.3 without a real, named customer demand. The outbox branch was deleted.

> "So that we're never down, and we're always running, and it's always smooth
> operation. Because we are smooth operators." — Angel

---

## 0. The one-paragraph answer

**They are two different things, and PWA comes first.** A **PWA** (Progressive Web
App) is the *packaging and feel* — installable, full-screen, app-on-the-home-screen,
"never scroll right," loads instantly. **Offline mode** is the *data resilience* — the
till keeps ringing sales with no network and uploads them later. The **service worker**
(a background script the browser runs) is the shared foundation both sit on: a PWA
introduces it; offline mode does the heavy lifting on top of it. So we ship the PWA
first (fast, low-risk, big daily-feel win), then layer offline on in stages.

---

## 1. What Angel asked for (mapped to standard terms)

| Angel's words | Standard industry term | What it is |
|---|---|---|
| "fits on one screen, more solid, never scroll right" | **PWA / standalone display + app shell** | Installed app with no browser chrome, responsive single-screen layout |
| "use it offline to a certain extent… continue for a certain amount" | **Offline-first / store-and-forward** | App works without network for a bounded window |
| "upload the changes through a changelog or something" | **Outbox pattern** (a.k.a. offline queue / sync log) | Sales are saved locally as queued intents, replayed to the server on reconnect |
| (implied) "don't ring the same sale twice on sync" | **Idempotency key** | Each sale carries a client-made UUID so the server adopts it exactly once |
| (implied) "show the sale done instantly" | **Optimistic UI** | UI confirms locally; server reconciles after |

*(Flagging coined-vs-standard per house rule: all five right-column terms are real
industry-standard vocabulary — safe to use in a pitch. "Outbox pattern" is the precise
name for the "changelog" idea.)*

---

## 2. How the POS is built today (the honest grounding)

We checked. Banco POS is a **hybrid**, which is *good* for this:

- **Server-rendered Jinja page shells** (`src/templates/pos/*.html`) — one HTML page per
  screen (checkout, scan, catalog, …).
- **Enhanced client-side with Alpine.js** + a shared `API` helper in `base.html`. The
  data operations are already **JSON API calls**, not form posts.
- **Auth = JWT in `sessionStorage`** (`pos_token` + `pos_refresh` + `pos_token_exp`),
  with silent refresh via `/pos/refresh`. Already client-managed.
- **The cart already lives client-side** (`sessionStorage['pos_cart']`). ✅ Big head start.
- **The scanner is already client-side** (vendored `html5-qrcode` / `PosScanner`). ✅
- **Zero-perpetual-inventory** (sell-to-seed): a sale is *never* blocked by a stock count
  and never moves one. ✅ This removes the scariest offline problem (overselling logic).

### What's against us (real, fixable)

1. **CDN dependencies** — Tailwind, Alpine, html2canvas load from `cdn.*`. Offline can't
   reach a CDN, so these must be **vendored locally** first. (Bonus: `cdn.tailwindcss.com`
   is the in-browser JIT build, explicitly *not for production* — we should vendor a real
   built Tailwind anyway. Ties to house rule #9.)
2. **Checkout is a 3-round-trip, server-authoritative flow:** POST create transaction →
   POST each line item → POST checkout. The server computes the authoritative totals,
   **VAT**, member discount and assigns the transaction id. Offline we have no server to
   call and no server id. This is the core thing the plan has to re-shape.

---

## 3. The two layers, defined

### Layer A — PWA (the vehicle)
A `manifest.webmanifest` + a service worker + icons turns the POS into an installable,
standalone app: home-screen icon, no address bar, full-screen, instant load from cache,
"add to home screen" on the tablet. **La Piazza already does exactly this** — we reuse
its proven pattern (`BorrowHood/src/static/manifest.json` + `sw.js`, registered in
`base.html`). Note La Piazza's SW is *PWA-only* (`/api/` = network-only) — it makes the
app feel solid but does **not** do offline writes. That's the line we cross in Layer B.

### Layer B — Offline-first (the engine)
Three new pieces on top of the service worker:
1. **Local catalog cache (IndexedDB):** mirror the products needed to look up / scan /
   price an item offline (name, price, barcode, age-restriction flag, VAT class).
2. **Outbox (IndexedDB):** when offline (or always, then sync), a completed sale is
   written as a local record with a **client-generated UUID**, and a **provisional
   receipt** prints immediately.
3. **Sync worker:** on reconnect, replay each outbox entry to the server (idempotent),
   let the **server compute the authoritative totals/VAT/loyalty at replay time**, then
   mark it synced and reconcile the receipt number. A "⏳ N sales pending sync" badge
   keeps it honest and visible.

---

## 4. The hard part is money & compliance, not the tech

For a Swiss head shop the risks live here — call them out now:

- **VAT** (dine-in 8.1% / takeaway 2.6%; alcohol+tobacco always 8.1%) is computed
  server-side today. Offline we either (a) duplicate the VAT logic client-side, or
  (b) print a **provisional** receipt offline and let the server stamp the **final** VAT
  breakdown on sync. **(b) is safer** — one source of truth stays the server.
- **Receipt numbering / fiscal:** offline can't pull the next official receipt number.
  Options: provisional local number → final on sync, or reserve a numbered block per
  device. Needs a Treuhänder nod before it touches real books.
- **Age-gating (18+):** the age flag rides in the cached catalog, so the cashier can
  still be prompted offline — must keep the gate enforced client-side, logged, audited.
- **Cash drawer / shift:** offline sales attach to the open shift and reconcile on sync;
  closeout must wait for the outbox to drain (or flag pending).
- **Security (the lost-tablet problem):** offline means a cached token + cached catalog
  on the device. Mitigate with an **offline PIN**, a **bounded offline window** (e.g.
  24h then it must re-auth online), and device binding. A stolen unlocked tablet must not
  be able to ring unlimited offline sales forever.
- **Clock skew:** offline timestamps come from the device clock — sync must trust server
  time for ordering and accept the device time only as "rung at."

---

## 5. The plan (phased — each phase ships on its own)

### Phase 0 — PWA shell  *(quick win, low risk, do first)*
- Reuse La Piazza's `manifest.webmanifest` + service-worker pattern; Banco/wolf icons.
- **Vendor the CDN deps locally** (Tailwind built CSS, Alpine, html2canvas) — required
  for offline *and* correct for production.
- Service worker: **cache-first** for static assets + app shell, **network-first** for
  pages; `/api/` stays network-only for now (no behaviour change to sales yet).
- **Single-screen layout audit:** `display: standalone`, no horizontal scroll, fixed
  bottom action bar, viewport-fit — the "never scroll right, fits one screen" feel.
- Register SW in `pos/base.html`; "Add to Home Screen" on the tablet.
- **Outcome:** installable, full-screen, instant-loading POS that survives a flaky
  connection on *reads*. No offline sales yet — but the daily feel Angel wants, today.

### Phase 1 — Read-offline (catalog cache)
- Mirror the catalog into IndexedDB; scan + search + price-lookup work with no network.
- Service worker serves the app shell offline; an **online/offline indicator** in the bar.
- **Outcome:** the cashier can find any item and see its price/age flag offline.

### Phase 2 — Write-offline (the outbox — Angel's "changelog")
- **Refactor checkout to ONE atomic endpoint** that takes the whole cart + a client UUID
  (this is better *online* too — kills the fragile 3-round-trip partial-failure window).
- Offline: write the sale to the outbox, print a **provisional receipt**, show "pending".
- **Sync worker** replays the outbox on reconnect; server re-prices authoritatively and
  is **idempotent** on the UUID (replaying twice = one sale). "⏳ N pending" badge.
- **Outcome:** the till never stops. Sales ring offline and reconcile automatically.

### Phase 3 — Hardening & compliance
- Provisional→final receipt/VAT numbering; offline PIN + bounded window + device binding;
- closeout-blocks-on-pending; conflict/duplicate dashboards; Treuhänder review of the
  offline receipt flow before it touches Felix's real books.

---

## 6. Key architectural decisions (recommended)

1. **Outbox + server-authoritative replay**, *not* client-side money math. The server
   stays the one source of truth for totals/VAT/loyalty; the client only captures intent.
2. **Atomic "create sale" endpoint + client UUID idempotency key.** Refactor once; it
   simplifies online *and* enables offline. Highest-leverage single change.
3. **Provisional vs final receipt.** Offline prints provisional; sync finalizes. Don't
   fake an official fiscal number offline.
4. **Bounded offline window + PIN.** Resilience without turning a lost tablet into a
   liability.
5. **Reuse La Piazza's PWA pattern** — don't reinvent the manifest/SW.

---

## 7. Effort & risk

| Phase | Effort | Risk | Daily-feel payoff |
|---|---|---|---|
| P0 PWA shell | S–M | Low | **High** (immediate) |
| P1 Read-offline | M | Low–Med | Medium |
| P2 Write-offline outbox | L | **Med–High** (money/compliance) | **High** |
| P3 Hardening | M | Med | Trust/safety |

---

## 8. Open decisions for Angel

1. **How far do we go?** PWA-only (feel + read resilience) is a small, safe win. Full
   offline-transactional (P2) is the "never down" dream but carries the money/compliance
   weight. Recommendation: **ship P0 now**, then decide P1/P2 after you feel it.
2. **Primary device?** Tablet, phone, or desktop browser first? (Shapes the layout audit.)
3. **Acceptable offline window?** e.g. "a full trading day (24h) then must re-auth."
4. **Treuhänder gate:** confirm the provisional-receipt approach is acceptable before P2
   touches real books.

---

## 9. Recommended first step

**Build Phase 0 now.** It's mostly assembly of a pattern we already own, it delivers the
"solid, one-screen, app-like" feel Angel wants on day one, it makes the app load instantly
on flaky Wi-Fi, and it lays the service-worker foundation every later phase needs — all
with zero change to how sales actually work (so zero money risk). Then we drive P1/P2 with
eyes open.

---

# 10. SPEC REVIEW — grounded against shipped code (2026-06-29)

*Re-read the whole plan against what's actually in the tree today. The headline: this plan
is further along than it reads — **P0 and P1 are already shipped.** We are standing exactly
on the P2 doorstep, which is where the money/compliance weight begins.*

## 10.1 Where we actually are (verified in code)

| Phase | Plan status | **Reality today** |
|---|---|---|
| P0 — PWA shell | "do first" | ✅ **DONE.** `sw.js` (CACHE v20, cache-first shell / network-first pages / `/api/` network-only), `manifest.webmanifest`, icons, **CDN deps vendored** (`/static/vendor/`: tailwind built CSS, alpine, html2canvas, html5-qrcode + fonts). Update-nudge shipped. |
| P1 — Read-offline | future | ✅ **DONE.** `src/static/pos/catalog-cache.js` — dependency-free IndexedDB mirror (`CatalogCache.sync/findByBarcode/search/meta`); scan + search + price work with no network. Online/offline indicator present (`navigator.onLine` in scan/checkout/base). |
| P2 — Write-offline outbox | future | ⛔ **NOT built.** Offline checkout is currently **friendly-blocked**: `checkout.html:534` → toast *"You're offline — keep scanning. This sale will finish when you're back online."* The sale is held, not lost — but it cannot finish offline. |
| P3 — Hardening | future | ⛔ Not started. |

So the daily-feel + read-resilience Angel asked for is **live now**. The remaining gap is
the hard one by design: **finishing a sale with no server.**

## 10.2 What the atomic endpoint must absorb (the honest weight)

Checkout today is the 3-round-trip the plan named (`checkout.html:571/585/608`):
`POST /transactions` → `POST /transactions/{id}/items` (per line) → `POST /transactions/{id}/checkout`.
Collapsing it into one server-authoritative call means one endpoint has to carry **everything
the three do today** — all of it stays server-side (one source of truth):

1. **Server-authoritative price snapshot** — catalog price wins; client `unit_price` is ignored for catalog items (anti-tamper, `pos_router:2015`). Custom lines supply their own price+name.
2. **Per-line VAT snapshot** — `line_vat(prod_class, consumption, line_total)`: alcohol/tobacco always 8.1 %, cafe food/drink dine-in 8.1 % / takeaway 2.6 %; rate **snapshotted** so a later rate change never rewrites the receipt.
3. **Promo-restricted guard** — no discount on tobacco/alcohol (law, blocks cashier *and* manager).
4. **Role discount ceiling** — cashier 10 % / manager 25 % / admin ∞, enforced server-side.
5. **Cash drawer gate** — a CASH sale needs an OPEN shift or **409** ("open your drawer first"); card/TWINT exempt.
6. **Cent-precision tender check** — quantize both sides (the `.17` float bug, `2215`).
7. **VAT rollup** — `split_vat(...)` sums per-line VAT for a mixed cart; cart-wide discount prorated.
8. **Member tier discount + CRM** — tier % off, credits earned (1/CHF), lifetime/basket/tier recalculated.
9. **Receipt + transaction number** — ⚠ today `transaction_number` is a **count-based sequence** with a literal `TODO: Make this atomic` (`1784`). Two cashiers ringing at the same instant can collide. This is **already** a latent bug online, and it's load-bearing for the fiscal **gapless-numbering** requirement — the atomic endpoint is the natural place to fix it (DB sequence / per-device block).

## 10.3 P2, sub-incremented (each ships on its own)

**P2.1 — Atomic, idempotent `create-sale` endpoint.** `POST /pos/sales` takes the whole cart
+ payment + customer + a **client-generated UUID** in ONE request, does create+lines+checkout
in ONE DB transaction (no partial-failure window), and is **idempotent on the UUID** (replaying
the same UUID returns the same sale, never double-rings). Switch the online till to use it.
**Zero offline behaviour change yet** — but this is the keystone, and it's *strictly better
online* (kills the fragile 3-round-trip). Reuses every rule in §10.2 verbatim. ← **THE FIRST BUILD.**

**P2.2 — Outbox + provisional receipt.** Offline, write the sale to an IndexedDB outbox, print
a **provisional** receipt (clearly marked, no official fiscal number), show "pending". Online
path can route through the outbox too (write→sync immediately) for one code path.

**P2.3 — Sync worker.** On reconnect, replay each outbox entry to the P2.1 endpoint (idempotent),
let the **server** compute authoritative totals/VAT/credits at replay time, reconcile the
official receipt number back onto the provisional, mark synced. **"⏳ N pending sync"** badge.

Then **P3** hardening: provisional→final numbering, offline PIN + bounded window + device
binding, **closeout-blocks-on-pending**, duplicate/conflict view.

## 10.4 The one real risk in P2.1: a schema migration

Idempotency needs a **`client_uuid` column on `transactions`** (nullable, **unique index**).
That's a migration — and per memory `schema-create-all-alembic-drift`, `create_all` makes new
*tables* but **never ALTERs** existing ones, and the alembic chain has bitten us before
(new columns silently missing per-env). **Mitigation, non-negotiable:** write a real alembic
migration AND *prove* the column exists on sandbox→staging→prod after deploy (a one-line
`information_schema` probe per env) before the endpoint goes hot. No assuming. This is the
seal-inspection rule applied to schema.

## 10.5 Money/compliance gates that still hold

The plan's §4 stands unchanged and **gates P2.2 onward, not P2.1**:
- **Provisional vs final receipt** — never fake an official fiscal number offline. Needs the
  **Treuhänder nod** — which is the *same* P1 fiscal sign-off already in flight (the cover note
  in `docs/business/banco-fiscal/`). One ask covers both: "is a provisional-offline →
  finalized-on-sync receipt acceptable?"
- Offline PIN + bounded window (lost-tablet), closeout-blocks-on-pending, clock-skew (trust
  server time for ordering). All P3.

## 10.6 Recommendation

Build **P2.1 now** — the atomic idempotent endpoint. It's the highest-leverage single change
(better online *today*, foundation for offline), it carries **zero offline/compliance weight
yet** (the till behaves identically; offline is still friendly-blocked until P2.2), and its
only real risk — the migration — is one we know how to de-risk (real alembic + per-env proof).
Dogfood it test-first the Perfect-Ticket way: unit-test the idempotency + the money rules
before wiring the till. Then P2.2/P2.3 with the Treuhänder answer in hand.
