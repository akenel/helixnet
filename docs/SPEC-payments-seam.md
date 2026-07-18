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

> **⚠️ AMENDED 2026-07-18 (same day) — WORLDLINE-FIRST.** SumUp does **not support TWINT** — the dominant Swiss
> mobile payment (~5.5M active users); a Swiss counter without it bleeds sales, so SumUp is unfit as the CH
> primary. Its onboarding also walls the sandbox behind full company+IBAN KYC (couldn't reach a test key without
> registering a real business). **Worldline is now the first adapter**: it does **TWINT + PostFinance Card + all
> cards** on Felix's *existing* ep2 terminal via TIM, keeping his acquirer and rates, zero new hardware. **SumUp
> is PARKED** — revisit only for a future non-CH shop where TWINT is irrelevant. The seam design is unchanged;
> that's the whole point — swapping which adapter is first costs nothing. The SumUp/SDK detail below stays valid
> as reference for that parked path.

**ONE payment seam, TWO adapters, provider-is-data per store.** Same shape as `_store_currency(db)` (never assume
CHF) and BYO-brain model targets (the model is data a recipe names). The store's `payment_provider` is a settings
value; the POS core never knows which terminal is on the counter.

- **Build WORLDLINE first** *(per the amendment above)* — Felix's *existing* acquirer, and it does **TWINT** (the
  non-negotiable Swiss payment method). If his terminal is a current **ep2** model, HelixPOS drives it via Worldline
  **TIM** (Till Integration Module) over LAN/WiFi — he keeps his acquirer, keeps his rates, **zero new hardware.**
- **SumUp PARKED** — its Cloud API is genuinely web-native (HTTPS + webhook + async SDK, all documented below) and
  its Virtual Solo sandbox is nice, BUT **no TWINT** makes it unfit as the CH primary and its sandbox is KYC-walled.
  Keep the SumUp/SDK detail below as the ready-made recipe for a future non-CH shop; the seam swaps adapters for free.

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

**Use the official SumUp Python SDK — it IS our adapter, and it's our exact stack.** `pip install sumup`
ships an **async client (`AsyncSumup`, httpx-powered) + Pydantic request models** — FastAPI-native, no
hand-rolled HTTP. The Cloud API adapter is a thin wrapper:
- `await client.readers.list(merchant_code)` → find the paired Solo (`reader.device.model == "solo"`).
- `await client.readers.create_checkout(merchant_code, reader_id, CreateReaderCheckoutBody(total_amount=…))`
  → **this call IS `initiate_payment`.** `total_amount` takes `currency` + `minor_unit=2` + `value` (integer
  **cents**) → we pass our already-quantized cents straight in (money-cent-precision rule, zero float drift).
  Returns `checkout.data.client_transaction_id` → save as `intent.intent_id`.
- Key format: `sup_sk_…` (newer than the older `sk_test_`/`sk_live_` docs; test vs live is the same split).
- ⚠️ **New pip dependency** → follow the openpyxl pattern: add `sumup` to requirements AND bake into the
  container (deploy = restart-not-rebuild won't pull a new dep on its own).

Flow (all via the SDK's async client from our FastAPI backend; no native app, no SDK embed):

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

## 8. Build order (milestones) — WORLDLINE-FIRST (amended 2026-07-18)

1. ✅ **M1 — Provider-agnostic seam — BUILT 2026-07-18 (`8e7fe326`).** `src/payments/` (base protocol +
   `to_minor_units` cent-precision + resolver `get_payment_provider`/`capture_on_terminal_if_configured`),
   `PaymentModel` (`payments` table), `store_settings.payment_provider` (NOT NULL DEFAULT 'manual', additive
   ALTER), hook wired into BOTH sale paths (checkout_transaction + create_sale) as a strict no-op today
   (adapter registry empty → resolves None → zero regression). 13 tests; full suite 2034 pass / 3 known-flaky.
   NOT deployed (invisible no-op — nothing to demo until an adapter lands). The "waiting for card" UI is
   deferred to M2 (nothing to wait for without a provider).
2. **M2 — Worldline TIM adapter.** Drive Felix's **existing ep2 terminal** (TWINT + cards) via TIM. *Blocked on:*
   his terminal **model number** + confirming TWINT is activated + Worldline enabling the **ECR/TIM package**.
3. **M3 — Human-green on the sandbox store, then the gate ladder** sandbox→staging→prod, backup-gated. One live
   low-value TWINT + card test charge on Felix's counter.
4. **M4 — Refund/void + reconciliation report** (cent-precision match of `payments` vs Worldline settlement).
5. **M5 — IT fiscal `on_approved` emit** (joins 🌍-2) — only when a non-CH/IT shop needs it.
6. **(Parked) SumUp adapter** — the §3 recipe, built only for a future non-CH shop where TWINT is irrelevant.

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
