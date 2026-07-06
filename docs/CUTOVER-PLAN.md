# Banco — Go-Live Cutover Plan

*Started 2026-07-06, 20:00 (Monday) — declared the **official go-live DRY RUN** the afternoon
Angel ran Banco over Layla's shoulder at Artemis, on prod, with real products and real sales.
This is the spine document for taking Banco from "works in the shop" to "the shop runs on it."*

*Companion docs: [BANCO-WORKLIST.md](BANCO-WORKLIST.md) (the ordered to-do) ·
[BANCO-DEPLOY-SOP.md](BANCO-DEPLOY-SOP.md) (how a change ships) ·
[BANCO-GO-LIVE-READINESS.md](BANCO-GO-LIVE-READINESS.md) (analysis).*

---

## 1. WHERE WE ARE (2026-07-06)

The first real over-the-shoulder run happened today. Signed in as `felix` (admin), on **prod**,
Angel added ~19 products, rang real sales, tried to enrol a member. **Nothing was a showstopper.**
What it surfaced is the whole taxonomy of what a real shop hits on day one — a small sample
(10–12 products) but *full-variety* coverage. This plan turns that field report into a path.

**Staffing reality:** Pam off (likely permanent) · Ralph on holiday · **Layla** — 8-year veteran,
called back to cover, effectively **managing** the store → she is manager-level, not cashier.

---

## 2. THE TWO DOCTRINES (the spine — everything hangs off these)

### 2.1 PRICE DOCTRINE — *the feed owns identity; the shop owns the price*

The FourTwenty catalog is excellent at **identity**: name, barcode, category, photo — spot-on,
and it impressed Layla. But its **price is the wrong shop's number** — a distributor suggested
retail this shop consistently sells *under*. Today it was higher **every single time**. The real
price is physical: a sticker on the item, a shelf-edge price, a "these grinders are all 5 bucks"
bin, or in Layla's head ("I think those go for two"). It is in **no feed**.

So the system's job is not to *know* the price — it is to make it trivial for the shop to
**assert their price and remember it forever.** Three rules:

1. **A scan-hit fills everything except price.** Price arrives flagged **"unconfirmed — check the
   sticker."** The cashier confirms or overtypes it the first time the item is ever sold. That is
   the moment the shop's real price is born.
2. **A confirmed price is sticky and sovereign.** A later FourTwenty re-sync may refresh name or
   photo but must **NEVER overwrite a shop-set price.** (The `products` table already carries
   `sync_override` + `last_sync_at` — that seam exists; it must mean *hands off the price*.)
3. **The cockpit's headline filter = "sold, still on reference price."** Real money went through,
   nobody confirmed the price → the manager's daily "go check these against the shelf" list.

**Corollary — the manual path is a front door, not a fallback.** Half the shop is sticker-priced
with no scannable code. On-the-fly (name + price + go) is a co-equal entry path, not an edge case.

### 2.2 DATA DOCTRINE — *catalog is asset; transactions are exhaust*

The catalog Angel is hand-curating now (confirmed prices, categories, 18+ flags, photos) is
**weeks of labor and a real asset** — it must be *promoted*, never thrown away. But dry-run
sales and test members are **disposable exhaust** — they must not pollute the real day-one ledger.

> **Promotion rule: carry the catalog, reset the ledger.** The cockpit cleans the catalog to a
> promotable state first; transactions/members are wiped at true go-live.

---

## 3. ENVIRONMENT LADDER — sandbox → staging → preprod → prod

Today's "prod" is really the **dry-run environment**. The plan:

| Rung | Today | At go-live |
|------|-------|-----------|
| sandbox | `helix-platform-sandbox` | unchanged (throwaway) |
| staging | `helix-platform-banco-staging` | unchanged (UAT gate) |
| **preprod** | *(does not exist yet)* | **← today's prod, "slipped" here** — keeps all curated catalog |
| **prod** | `helix-platform-banco` (dry run) | **fresh box, DR-hardened, seeded from preprod catalog** |

**The slip:** when Felix says "I like how it's loaded," today's prod is promoted to **preprod**
(all the curation survives). A **new real prod** stands up — ideally a **separate box** with a
disaster-recovery plan that's been *burnt down and rebuilt 5–6 times* until we trust it — seeded
from preprod's **catalog only** (per §2.2). It's a code + database deploy; the rails already exist.

**For now:** run prod as the dry run. Keep taking backups — they *are* the DR seed. (Tonight's
`banco_prod-premberfix-20260706` dump is the first artifact of this plan.)

---

## 4. THE ROLE MODEL

| Role | Who | Can do | Cannot |
|------|-----|--------|--------|
| **Cashier** | (Pam-type) | Sell fast. On-the-fly add = **name + price + two ticks (18+? category?)**. | No photos, no descriptions, no cost, no catalog editing. |
| **Manager** | **Layla** | Everything cashier + categorize, confirm prices, take photos, voice-describe, work the **cleanup cockpit**. | (Owner-level config.) |
| **Admin** | Felix | Everything + users, config, environments. | — |

**The cashier contract (memorize this):** *name, price, "is it 18+?", "what is it?" — done.* Keep
her out of everything that makes her hesitate. The cockpit + manager catch the rest.

---

## 5. HARDWARE KIT (one proper POS station — so a visit isn't three trips)

1. **Tablet + counter stand** — the POS terminal (runs the web app / PWA). ~10–11", good rear
   camera (Snap-&-fill photo + fallback scan), all-day battery. iPad (10th gen) or Samsung Galaxy
   Tab A9+/S-series — either runs the web POS. Rotating stand so the customer can see the total.
   *(The phone worked today — proves the responsive/PWA build holds in real hands; a tablet is the
   real all-shift ergonomics.)*
2. **Barcode scanner — DECIDED: Zebra DS8178** (`DS8178-SR7U2100PFW`, Bluetooth 2D, presentation
   cradle). HID keyboard-wedge → types the code into the scan field + Enter, zero drivers. Reads
   1D **and** QR (loyalty/campaign) — one device. Camera scan stays as the no-hardware fallback.
3. **Label printer** — thermal (Zebra ZD421 for ecosystem match, or Brother QL-820NWB budget).
   TWO jobs: (a) price/shelf stickers, and (b) **print a scannable barcode for on-the-fly /
   sticker-only items that have no code** — closes the loop with the scanner (OTF product → print
   barcode → stick it → it scans forever after). *This is the missing half of the OTF workflow.*
4. **Receipt — NOT a required box for Artemis** (counter space is tight — probably no room for a
   printer). Today the receipt is an **on-screen / printable HTML page** (with a "join La Piazza"
   QR). The card terminal prints the card slip separately. Zero-hardware path that works *now*:
   **show the receipt on the tablet**, customer keeps their pen-and-paper slip. A **"scan-to-see-
   your-order" QR receipt is a SMALL BUILD** (tokenized public order view) — not built yet; don't
   promise it as existing. (Optional later: 80mm thermal Epson TM-m30III if a shop wants paper.)
5. **Payment terminal — they already have one** (Twint + Visa/debit, standalone). For now the
   cashier reads the total off the POS and keys it into the terminal by hand — fine. **Phase-2:**
   integrate (POS → terminal sends the amount, kills keying errors) — Worldline/SumUp/myPOS APIs.
6. **Cash = manual cash box** (Angel's call — no auto-popping drawer needed).
7. **Internet — the sleeper dependency.** The POS is web-based; it needs reliable shop WiFi + a
   **mobile hotspot / SIM backup** so a dead line never stops sales. (True offline = the PWA-outbox
   roadmap item, not built yet — until then, connectivity is load-bearing.)

**App-side check:** confirm the scan screen has a focused input that accepts wedge "type + Enter"
like a camera read; build `/pos/scanner-test` (see §7).

---

## 6. THE DRY-RUN LOOP + TRAIN-THE-TRAINER (now → go-live, ~1–2 weeks)

Angel on-site, ~1 hr scan + tune per visit (parking-limited), debug + hotfix live (like today).
Charging: **training is the billable container; the feedback-driven tuning falls out of it** —
and the tuning *manufactures champions* (Layla/Ralph → "I said fix it, he did, now I love it").
Keep polish (button size, colour) bundled; keep shop-rules (discount tiers) as **config, not code**.

**Training IS the inventory load — train-the-trainer:**
1. **Angel loads ~300 solo** — billable setup (~3 hrs / 100 ≈ 10 hrs ≈ CHF 1,000 @ CHF 100/hr).
   Felix wants 500; realistically grows to 1–2k **ongoing**. 300 = the "prove it" seed.
2. **Train the two managers hands-on** — Layla + Ralph each load ~100 *as* their training
   (200 more built while learning) → the shop now has **two in-house trainers.**
3. **Managers cascade to cashiers** — test with `pam` signed in as cashier so all see the cashier
   view. Angel exits that loop. Net: 2 certified trainers + a catalog built as a by-product.

The cockpit bounds daily cleanup to **only the products that actually sold** — never audit the
whole catalog, just the day's real movement.

**Reporting — presets on what already exists (do NOT overkill).** The engine is built:
`/reports/daily-summary(.csv)`, `/reports/product-sales`, `/reports/category-sales`, and
`/transactions` already take `date_from`/`date_to`, so arbitrary ranges work today. **Year-end =
a CSV over the year** (Felix → Banana → accountant; we only ever hand a CSV). Gap = **"fast buttons"**
(Today · This month · MTD · Last month · Q1 · Last 90 days) that pre-fill the range — a small
frontend add. **Felix names the presets he needs; we build only those.**

**Settings visibility** — today: any role can READ settings, only **admin** can EDIT
(`require_admin`). So "cashier sees it read-only" already holds server-side. **Open decision:**
let *managers* edit too? Risk — a manager could raise their own discount cap; keep edit admin-only
unless Felix asks otherwise.

**Rate:** CHF 120/hr standard · **CHF 100/hr for Felix** (founder). Setup (~3 hrs / 100 items) is
absorbed for Felix as customer-acquisition; extra stores / bespoke features billed hourly.

**Parallel-run → hypercare exit.** For the first weeks the cashiers keep the 25-year pen-and-paper
slip **alongside** the POS, and at end of day reconcile **paper vs POS vs cash drawer** — they must
match. That's the trust-building bridge and the safety net. **Open decision: how long — 2 / 3 / 6
weeks — before hypercare ends and the paper stops?** (Decide with Felix; the reconcile-match record
is the evidence that it's safe to drop the paper.)

**Hardware priority (from the field):** the **gun (scanner) + label printer are a MUST** — when you
gun an on-the-fly item you want a scannable label to spit out *on the spot* (queuing labels for
Felix to print + stick later is impractical). The **receipt printer is optional** (screen / QR).

---

## 7. PUNCH LIST — prioritized (the dry-run findings)

| # | P | Item | Owner |
|---|---|------|-------|
| **P1** | 🔴 | **Price-confirm flow** — reference price arrives "unconfirmed"; cashier sets shop price; sticky vs re-sync (§2.1) | 🐯 |
| **P2** | 🔴 | **18+ toggle on quick-add** — cashier's safety tick, default OFF, + optional category | 🐯 |
| **P3** | 🔴 | **Cleanup cockpit** — "sold but unconfirmed/unset-up" manager view | 👥 |
| H1 | 🟠 | **Scanner DECIDED: Zebra DS8178** (`…PFW`, BT 2D, cradle) — order + `/pos/scanner-test` + wedge-input check | 🧍🐯 |
| H2 | 🟠 | **Tablet + rotating stand** (10–11", good camera) — the POS terminal; spec + buy | 🧍 |
| H3 | 🟠 | **Label printer** (Zebra ZD421 / Brother QL) — price stickers **+ print scannable barcodes for OTF items** | 🧍🐯 |
| H4 | 🟡 | **Receipt: paper printer vs paperless email/QR** — decide per shop | 👥 |
| H5 | 🟡 | **Reliable internet + SIM/hotspot backup** — POS is online-dependent until PWA-outbox ships | 🧍 |
| H6 | 🟢 | **Payment-terminal integration** (POS→terminal amount) — phase-2; standalone keying for now | 👥 |
| P4 | 🟠 | **Reference 18+ re-flag** — FourTwenty under-flags real tobacco (408/7272); smarter-than-regex | 🐯 |
| P5 | 🟡 | **Artemis-into-prod decision** — prod reference = 100% FourTwenty, 0 Artemis | 👥 |
| P6 | 🟡 | **Fungible-SKU / catalog curation** — don't chase every cigarette/paper variant; curated representative catalog | 👥 |
| P7 | 🟢 | **Layla → manager-level user** (identity) | 🧍 |
| P8 | 🟢 | **"0.75" decimal check** on quick-add edit (Sputnik) — reproduce before assuming | 🐯 |
| R1 | 🟡 | **Reporting "fast buttons"** (Today/Month/MTD/Last-month/Q1/Last-90) on existing date-ranged reports — Felix names the set | 🐯 |
| R2 | 🟢 | **Settings-visibility decision** — cashier read-only already holds; decide if managers may edit | 👥 |
| R3 | 🟡 | **QR "scan-to-see-your-order" receipt** — tokenized public order view (small build; the no-printer path) | 🐯 |
| R4 | 🟢 | **Parallel-run / hypercare exit** — paper+POS+cash reconciled daily; decide 2/3/6-week duration | 👥 |
| R5 | 🟢 | **`/pos/scanner-test`** page + wedge-input check — before the gun lands | 🐯 |

**✅ SHIPPED tonight, backup-gated + proven on prod:**
- `346a2a2` — member-enrol 422 on blank birthday (coerce blank date → None).
- `1851eb4` — **discount caps read live from store settings** (phantom-setting bug: prod cashier
  cap was 20 but the till enforced a hardcoded 10). Now cashier/manager caps are set in the
  admin-only Settings screen and the till obeys; admin stays 100%. Manager baseline aligned 100→25
  across envs (was the untouched default) so wiring was behaviour-neutral; Felix dials it up live.

---

*"The feed owns the name. The shop owns the price. The cockpit owns the cleanup."*
*"Carry the catalog, reset the ledger."*
*"Cashier: name, price, is-it-18+, what-is-it — done."*
