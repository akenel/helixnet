# HelixNet — The Vision (North Star)

*This is not a build spec. It's the star the build specs hang under. When a feature decision
is unclear, come back here: does it serve the spine, feed the flywheel, or honour the
mission? If not, it waits.*

Written 2026-06-23, Base Camp One, from a camper van. Built by one operator + an AI, in
nine months. That's the proof, not the pitch.

---

## 1. The spine — Capture → Enrich → Relate

Every product, every customer, moves through three layers. They have different jobs,
different speeds, and different owners — and confusing them is how systems get bloated.

| Layer | What | Speed | Owner | Depth |
|-------|------|-------|-------|-------|
| **Capture** | born once: name, price, photo, category. The sale NEVER blocks. | instant | cashier | shallow, universal |
| **Enrich** | the item's *story* — better photos, an unboxing video, spec sheet, reviews | async | manager | deep, **selective** |
| **Relate** | the *relationship* — membership, coupons, feedback, community, trends | ongoing | the business | compounding |

Capture is universal and shallow — *everything* gets it, in seconds. Enrich is selective and
deep — *only what earns it.* Relate is where the moat lives. The cashier lives in Capture;
the manager visits Enrich; the **business** lives in Relate.

## 2. The reframe — zero data, rich metadata *graph*

Zero perpetual inventory means we throw away the lie (stock counts) and keep almost no
*data*. But we keep a rich **metadata graph**: `products ↔ sales ↔ customers ↔ suppliers ↔
trends`. **The asset is the connections, not the inventory.** The metadata sorts into seven
layers, each earning its keep:

1. **Identity** — name, brand, barcode, photo *(capture-time)*
2. **Economic** — cost + price → **margin** *(turns raw velocity into margin-weighted velocity)*
3. **Supply** — supplier, lead time, last-received *(powers the reorder / shopping list)*
4. **Velocity** — units/day, momentum, dead-stock *(**derived free** from the sales log — never typed)*
5. **Taxonomy / Trend** — CBD/THC/vape/accessory, effect, THC% *(this is what the **tags** are for — trend analysis, benchmarking)*
6. **Compliance** — age-restricted, THC<1%, VAT rate *(the Swiss moat a US POS doesn't model)*
7. **Relationship** — who bought it, member vs walk-in, basket affinity *(the community layer)*

**Rule:** invest metadata effort where it compounds, not everywhere equally.

## 3. Demand-driven enrichment — the loop that runs itself

Enrichment depth = a function of **velocity × margin × novelty.** Papers earn nothing; the
liquid-nitrogen bong earns the video. And the system **nominates its own hot items:** the
velocity report flags *"selling fast, no description, one blurry photo → enrich this."* The
data raises its hand; the cashier never has to remember. Capture and Enrich close their own
loop, and effort lands exactly where it pays.

## 4. The flywheel — why the data compounds

```
Capture seeds the catalog
   → sales generate velocity (free)
      → velocity says what to Enrich
         → enrichment + relationship make hot items sell more
            → relationships generate preference / feedback / trend data
               → which sharpens the catalog + recommendations
                  → which serves the next customer better
                     → more sales  ↺
```

One shop: the catalog gets smarter as it's used. **More than one shop:** the flywheel spins
at the **industry level** — trends, benchmarks, "what's hot across every head shop in
Switzerland." That network effect is what makes HelixNet bigger than any one shop. It isn't a
feature you build; it's a **property that emerges** if the spine is right.

## 5. The relationship engine — "you don't know who walks in"

It could be George Clooney and the cashier wouldn't know. So serve **everyone** like royalty
— because you genuinely don't know, *and* because the data from treating them well is the
asset. The POS is **not a cash register; it's the front door of a relationship.** The sale is
touch #1: receipt → membership invite → coupon → "tell us your ideas" → feedback → community.
The CRACK community — *"two ladders, one currency"* — is the moat no US POS will ever have,
because it requires **caring**, and caring doesn't ship in a SaaS box.

## 6. Banco × La Piazza — the community bridge

*The Relate layer's missing diagram — what turns "members" from a loyalty card into a community
with legends in it.*

**Two surfaces, one person, one currency.** Banco is the **shop** (till, counter, in-store
loyalty, products). La Piazza is the **community** (reviews, upvotes, favourites, Q&A, the
reputation ladder) — **already built.** You don't rebuild the community inside Banco; you bridge
to the one you own.

**Three wires:**
1. **Shared identity** — the CRACK who buys in-store *is* a La Piazza login (the `borrowhood`-realm
   consolidation). Same person, both surfaces. **This is the keystone — nothing community-side
   works until it lands.**
2. **One currency, two ladders** — credits earned **both** ways: buying (loyalty, *local* to a
   shop) and participating (reviews/answers/upvotes = *reputation*, global across the network).
   Bronze → diamond. A **legend** buys, knows, *and* shares.
3. **Products ↔ discussions** — a product earns a **public page on demand** (a "postcard": photo,
   the KB knowledge, reviews, a QR) — *not* pushed, **minted when it's worth talking about.** The
   community content flows back as product knowledge + social proof.

**The loop:** buy in the shop → log into the community → review/answer/upvote what you bought →
earn credits + reputation → climb to legend → your knowledge makes the shop smarter and the next
customer happier → more community, more sales.

**The prize:** the community lives on La Piazza, so it isn't Artemis-only. **One community, many
shops** (each a Banco node); a CRACK who walks through *any* head shop joins the *same* community.
**Local loyalty per shop, global reputation across the network.** That's an international CRACK
community, not a loyalty card.

*Mechanics — identity capture without forcing email (social login), the on-demand public page,
Keycloak SSO across both — are their own spec, built after the realm consolidation lands.*

## 7. Engine & skins — HelixNet is the platform

**HelixNet is an engine. Banco is a skin.** La Piazza (the square), Bottega (the workshop),
ISOTTO/UFA (print + merch) — same engine, different skins. Each new vertical needs a **domain
steward** (someone who lives the trade) + a first customer. Forty years across many fields
means the operator can *be* — or *recognise and recruit* — that steward. The leverage thesis:
merge into adjacent value from skills you already have.

**The discipline (the keel):** the platform is the **reward** for nailing one vertical
*completely*, not the *starting move.* Win Felix — utterly — and you haven't built a head-shop
POS; you've built the **proof the engine can be skinned**, with a reference customer and a
flywheel already turning. *Then* the world. One shop, all the way, first.

## 8. The mission — honest, with a keel

It is a real industry: gritty, smart, generous people the system has treated like criminals,
and there *is* a big future. Honour that — it's why this matters more than another web app.
But the **defensible** version of the mission doesn't depend on winning a medical argument:

> You don't have to be right that CBD cures cancer to win. You have to be right that this is a
> **real, growing, underserved industry of real operators who deserve good tools** — and that
> is *unambiguously* true.

Be the **picks and shovels** for the gold rush. The miners can argue about the gold; you sell
every one of them the best shovel in the valley, and you win whether or not the medical story
plays out. That's the keel. The dream sails on it.

---

*"If one seal fails, check all the seals. If the engine works for one shop, it can work for
the trade. Win the shop first."*
