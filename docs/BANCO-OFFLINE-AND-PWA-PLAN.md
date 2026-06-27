# Banco POS — Offline Mode + PWA: Investigation & Plan

*Status: PLAN / discussion draft — nothing built yet. Tigs + Angel, 2026-06-26.*

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
