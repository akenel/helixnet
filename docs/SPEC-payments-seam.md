# SPEC — Payments provider seam (🌍-1: "Move the money")

*Status: DRAFT · 2026-07-18 · Tier-1 best-in-the-world sprint · not built.*
*Ties: [BANCO-WORKLIST.md](BANCO-WORKLIST.md) 🌍-1, [BANCO-COMPETITIVE-SCOREBOARD.html](BANCO-COMPETITIVE-SCOREBOARD.html),
memory `banco-payments-provider-seam`, `banco-fiskaly-integration-brief`, `banco-fiscalized-markets-italy-germany`.*

---

## Why

HelixPOS rings a sale beautifully but does **not settle the card** — the shop still needs a separate terminal to
actually charge. This is the single highest-leverage gap between "best POS for Felix" and "best, period"
(the scoreboard's Tier 1). This spec closes it.

## The decision (locked 2026-07-18)

**ONE payment seam, TWO adapters, provider-is-data per store.** Same shape as `_store_currency(db)` (never assume
CHF) and BYO-brain model targets (the model is data a recipe names). The store's `payment_provider` is a settings
value; the POS core never knows which terminal is on the counter.

- **Build SumUp FIRST** — its **Cloud API is web-native** (HTTPS + webhook, perfect for FastAPI) and it has a
  **Virtual Solo sandbox** so we build and prove the whole flow **today, zero hardware, zero waiting on a sales rep.**
- **Get fully prepared for Worldline in parallel** — it's Felix's *existing* acquirer. If his terminal is a current
  **ep2** model, HelixPOS drives it via Worldline **TIM** (Till Integration Module) over LAN/WiFi — he keeps his
  acquirer, keeps his rates, **zero new hardware.** The Worldline adapter slots into the *same seam*.

Net: shop #2-on-SumUp and Felix-on-Worldline run identical POS code. "SumUp or Worldline?" → "yes — whichever the
store carries."

---

## 1. The seam interface

One provider Protocol; adapters implement it. Async, Pydantic result types. Lives in `src/payments/`.

```python
# src/payments/base.py
class PaymentIntent(BaseModel):
    intent_id: str            # our id (idempotency key), stored on the sale
    provider: str             # "sumup" | "worldline"
    amount: Decimal           # quantized to cents FIRST (money-cent-precision rule)
    currency: str             # from _store_currency(db) — never hardcode
    reference: str            # our transaction/sale reference shown on the slip

class PaymentResult(BaseModel):
    intent_id: str
    status: Literal["approved", "declined", "aborted", "timeout", "error"]
    provider_txn_id: str | None   # acquirer's own id (for reconciliation / refund)
    card_scheme: str | None       # visa/mc/… for the receipt
    raw: dict                     # full provider payload, persisted for audit

class PaymentProvider(Protocol):
    async def initiate_payment(self, intent: PaymentIntent) -> str: ...   # returns provider checkout/session id
    async def poll_status(self, intent_id: str) -> PaymentResult: ...     # fallback when no webhook
    async def cancel(self, intent_id: str) -> None: ...
    # webhooks handled by a provider-specific verified endpoint (see §5)
```

Resolver (mirrors `_store_currency`):

```python
# src/payments/__init__.py
async def get_payment_provider(db) -> PaymentProvider | None:
    name = await _store_payment_provider(db)   # reads store_settings.payment_provider
    if name == "sumup":     return SumUpCloudAdapter(await _sumup_config(db))
    if name == "worldline": return WorldlineTimAdapter(await _worldline_config(db))
    return None            # "manual" / not configured → today's cash-only behaviour, no regression
```

**Money rule:** quantize `amount` to cents *before* building the intent, and compare at cent precision on
reconciliation (memory `banco-money-cent-precision`). **Currency rule:** `intent.currency = await _store_currency(db)`.

---

## 2. Data model additions

- `store_settings`: `payment_provider VARCHAR(16) DEFAULT 'manual'` (`manual|sumup|worldline`). *(Schema-drift note:
  `create_all` never ALTERs — add via manual `ALTER TABLE` on each env, per `schema-create-all-alembic-drift`.)*
- New `payments` table — one row per payment attempt, FK to the transaction/sale:
  `id, transaction_id, provider, intent_id (unique, idempotency), amount_cents, currency, status,
  provider_txn_id, card_scheme, created_at, settled_at, raw JSONB`.
  A sale can have >1 attempt (declined → retry); the **approved** row is the settlement of record.
- Config/credentials do **NOT** live in the DB in plaintext — they go through the secrets tool (§6).

---

## 3. Adapter A — SumUp Cloud (build first)

Flow (all HTTPS from our FastAPI backend; no native app, no SDK embed):

1. **Pair the Solo once** (setup, per store): generate a pairing code on the Solo → `POST Create Reader` with the
   code → reader enrolled to the merchant account. Store `reader_id` in `_sumup_config`.
2. **Charge:** `POST Create Checkout` (merchant code + `reader_id` + amount + currency). Reader must be **online**;
   a **60-second** window to start payment. Returns a checkout/session id → save as `intent.intent_id`.
3. **Result:** SumUp calls our **webhook** (`/api/v1/pos/payments/sumup/webhook`, signature-verified) with the final
   status in real time. `poll_status` is the fallback if the webhook is late/missed.
4. **Auth:** API key (`sk_live_…` / `sk_test_…`) or OAuth2 + Affiliate Key. Test keys are `sk_test_`.

**Sandbox:** `Virtual Solo` + a sandbox merchant → build and prove the full round-trip with **no physical reader**
(caveat: no PIN simulation, no offline). **This is milestone 1 and it needs nothing but a free dev account.**

Fees at time of writing (verify at contract): **CH ~1.1–1.3%** in-person; **IT ~0.95%** domestic consumer /
~1.99% business·intl·Amex. Hardware: Solo ~99 (standalone SIM+WiFi), Air/Solo Lite ~34–49 (needs phone). No monthly.

## 4. Adapter B — Worldline TIM (prep now, build when Felix's terminal is confirmed)

- **TIM** = Worldline's interface to drive **ep2** terminals from POS software over **LAN/WiFi**, OS-independent.
  (Modern alternative: Worldline **Terminal API** — Nexo Retailer v5.1, JSON.) The adapter is a thin local-network
  client speaking TIM to the terminal on the counter.
- **What makes a terminal "ready" (the open question Angel is checking):** the terminal must be **ep2 + ECR-provisioned**
  — Worldline flips it into till-integration mode and issues the **TIM integration package**. Most current CH models
  (Yomani, Yoximo, Valina, Desk/Move series) support it; a standalone "manual" terminal needs Worldline to enable the
  ECR profile — **usually a config on their side, not new hardware.**
- **First action (Angel):** get Felix's terminal **model number** + whether it already talks to any till. That single
  fact decides: ep2+ECR → we integrate; standalone-only → one call to Worldline to enable ECR.
- `_worldline_config`: terminal IP/port, terminal id, TIM endpoint. No card data ever touches HelixPOS (PCI scope stays
  on the terminal) — we send amount, we get an approve/decline.

---

## 5. Checkout integration (where it plugs in)

At cart-finalize in `pos_router` (the existing "complete sale" path):

1. `provider = await get_payment_provider(db)`. If `None` → today's behaviour unchanged (cash/manual), **no regression**.
2. Build `PaymentIntent` (quantized amount, `_store_currency`, sale reference) → `initiate_payment`.
3. Till shows a "waiting for card…" state (HelixDirtyGuard-friendly — don't let a stray Escape kill an in-flight charge).
4. On **approved** (webhook or poll): persist the `payments` row, complete the transaction, print/emit the receipt.
   On **declined/aborted/timeout**: keep the cart, let the cashier retry or fall back to cash. Never double-charge —
   `intent_id` is the idempotency key.
5. Refund/void = a later slice (needs `provider_txn_id`); out of scope for MVP but the field is stored from day one.

## 6. Secrets & config

All credentials via `set-banco-secret.py` (never in DB plaintext, never dumped to chat). Per env / per store:
`SUMUP_API_KEY`, `SUMUP_MERCHANT_CODE`, `SUMUP_AFFILIATE_KEY`, `SUMUP_READER_ID`; `WORLDLINE_TERMINAL_IP`,
`WORLDLINE_TERMINAL_ID`. Sandbox uses `sk_test_` keys so nothing real is charged during the build.

## 7. 🇮🇹 Fiscal coupling — Italy makes 🌍-1 and 🌍-2 one job

Since **1 Jan 2026** Italian law *requires* the POS wired to the *registratore telematico* (RT) with automatic
transmission of *corrispettivi* to the Agenzia delle Entrate. **In Italy you cannot ship payments without the RT link.**
So the seam must, in an IT store, emit a fiscal receipt on `approved` — this is the join point to 🌍-2
(fiscal certification, `banco-fiskaly-integration-brief`). CH has no such coupling today; a CH store can ship
payments alone. Design the `on_approved` hook so the fiscal emit is a pluggable step, off in CH, on in IT.

---

## 8. Build order (milestones)

1. **M1 — SumUp sandbox round-trip.** Seam + SumUp adapter + Virtual Solo. Prove `initiate → webhook approved` end
   to end with a sandbox merchant. *No hardware, no store change.* ← start here.
2. **M2 — SumUp on a real Solo, sandbox store first** (sandbox-first: never prod). One live low-value test charge.
3. **M3 — Checkout wiring + `payments` table + waiting-for-card UI**, ladder sandbox→staging→prod, backup-gated.
4. **M4 — Worldline TIM adapter** against Felix's confirmed ep2 terminal (blocked on his model number + ECR activation).
5. **M5 — Refund/void + reconciliation report** (cent-precision match of `payments` vs settlement).
6. **M6 — IT fiscal `on_approved` emit** (joins 🌍-2).

## 9. Open questions (Angel)

- **Felix's Worldline terminal model** — the M4 unblock. (Get the model number.)
- SumUp merchant account: open a **sandbox** dev account now (free) for M1; the real CH/IT merchant contract comes at M2/M3.
- Acquirer confirm at contract: exact CH + IT fee tiers, settlement timing, and whether the Solo is the right SKU vs
  the printer-integrated Terminal for Felix's counter.

## 10. Test plan

- **Automated:** the seam resolver + adapter logic are unit-testable with a mocked provider (SumUp sandbox has no
  pytest hook — like BL-101, the live sandbox round-trip is the proof, not a unit test). Webhook signature verification
  gets a real unit test.
- **Human-green:** a real card on a real Solo in the **sandbox store** (machine-green ≠ human-green). Then the gate
  ladder for the prod wiring, backup-gated as always.
