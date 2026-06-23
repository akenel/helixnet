# BORN ONCE — Series Bible (v0.1, working draft)

*A series of ~2-minute films about Banco, a Swiss-made till built for the counter, not the
warehouse. Not a feature tour — a small show about a real shop. Syd Field structure, every time:
hook → turn → resolution. Theme: **a thing is known once, then forever** — so the humans get to
stay human.*

---

## THE WORLD
**Artemis** — a Swiss head shop (Felix's). The counter is the stage. The till is **Banco.**
The status bar shows the environment (SBX / STG / PRD) — that little badge is a character too.

## THE CAST — three people, and the roles ARE the drama
| Who | Role | Archetype | Powers (the drama) |
|-----|------|-----------|--------------------|
| **Pam** | Cashier | *The new kid / our hands* — the everyperson at the counter | Sell, scan, find-by-picture. **Can't** create/edit products, change prices, void big things. The system has her back so she can't break it — or get blamed. |
| **Ralph** | Manager | *The floor boss / the fixer* — the one Pam calls over | Create + fix products, override prices, open/close any drawer, see all sales. Steps in where Pam hits a wall. |
| **Felix** | Owner / Admin | *The road* — never on the floor | Sees **everything**, from his phone, anywhere. The shop in his pocket. |

**The RBAC line is the conflict engine.** Someone tries something, it goes through — or it
*doesn't*, and they get stuck, and that wall turns out to be a feature. (The Phantom Sale was
literally a cashier hitting a manager-only door.)

## THE CUSTOMERS — the second ladder
| Who | Archetype | Their role |
|-----|-----------|-----------|
| **Larry** & **Sally** | The regulars | They buy the cream, come back, and *write how it worked* — earning points/credit. Their word of mouth is the shop's best salesman. |

**Two ladders, one currency:** staff climb one ladder (sales, drawers, roles); customers climb
another (purchases, feedback, points) — both running on the same Banco spine. Larry and Sally are
how the *community* enters the show.

## ARCHITECTURE TRUTH (so the stories stay honest)
The **Artemis-Luzern website** is the rich source — gorgeous photos, full specs, the story. Banco
is the **till**. They are **separate systems; no direct integration.** The honest answer is NOT to
duplicate the website into Banco (two systems drift — *if one seal fails…*). Instead:
**website = content · Banco = the sale + the feedback loop · a tap-through links them.** Banco's
catalogue gets richer *at the counter* (a better photo, the key specs), and the customer's review
flows back. Link, don't copy.
*(Reality check: a CustomerModel + credits ledger already exist in the code but aren't wired to the
sale yet — so we tell the points/feedback loop as the vision we're building, truthfully.)*

## THE STAR PROP — the cream
**HempSana SALBE** — a CHF 45 insect-bite cream that actually *works.* Real product, real papers,
real customer feedback ("it's not cheap, and it works"). Repeat buyers. The recurring hero object.
**Supporting shelf:** 2–4 cheap look-alikes (a CBD shampoo, a generic tube) — the "five tubes, one's
40, one's 12" tension, and enough SKUs for velocity / multi-item stories. Real or faked with
bathroom barcodes — doesn't matter; keep it simple.

---

## THE BORN-ONCE LIFECYCLE (the spine of the whole show)
A product's life, and why each role exists:
**Born rough** (Pam, on the fly — the sale never stops) → **Proven** (Larry & Sally buy it) →
**Made proper** (Ralph enriches it — the manager's role) → **Watched** (Felix, from the road).
Cashier births it · manager raises it · owner oversees it. The RBAC is a relay team, not red tape.

## SEASON STRUCTURE
- **Season 1 — "The Cream":** ONE product (HempSana SALBE) followed through its entire life. Every
  episode is a chapter in one tube's biography. Discipline: one hero, start to finish.
- **Season 2 — "The Shelf":** the other 4–5 creams open up — velocity races, the five-tubes
  tension, multi-item drawers, competition. The world widens once the one is fully told.

## SEASON 1 — the cream's biography (ordered)
| # | Title | Chapter of the life | Lead | Teaches | Status |
|---|-------|---------------------|------|---------|--------|
| 01 | Stop Counting | *(prologue — the philosophy)* | — | the till learns the shop | **LIVE** |
| 02 | The Phantom Sale | it almost vanished | Pam | born once must *stay* (integrity) | **LIVE** |
| 03 | The Forty-Franc Cream | **born** — on the fly | Pam | sell by sight — the picture catalogue | **LIVE** |
| 04 | Make It Proper | **raised up** | Pam → Felix → **Ralph** | the born-once lifecycle + RBAC relay; effort follows velocity | **LIVE** |
| 05 | The Delivery | **restocked** | Ralph / Pam | receiving = log the *event*, not the count; packaging knows the cost | **LIVE** |
| 06 | Felix on the Road | **watched** | **Felix** | remote owner — the shop in your pocket (the status bar) | premise |
| 07 | The Drawer That Wouldn't Close | **counted out** | Pam | accountability without accusation (cash shift) | scripted |
| 08 | Word of Mouth ("It Works") | **remembered** | cream + Larry & Sally | feedback → reputation → points (two ladders, one currency) | premise |

## THE DELIVERY — receiving the Banco way ("don't count what you receive")
A box of cream arrives. Old way: count every tube (20? 50?), reconcile, argue. **Banco way: record
that it *came in.*** No quantity. The **packaging knows the cost** (built-in box→singles math), and
the shop infers the rest from packaging + sales velocity. Zero Perpetual Inventory all the way to
the loading dock — log the *event*, not the *number.* (Real: BL-91 receiving dropped quantity by
design; a delivery-slip qty is "how many labels to print," never a stock count.)

## CORE PRINCIPLE — "Effort follows velocity"
You don't enrich 7,000 dead SKUs. The shop tells you what's worth polishing — *in sales.* A rough
on-the-fly entry that sells twice in a day has **earned** its photos, specs, cost, and reorder. The
long tail stays rough on purpose. This is Zero Perpetual Inventory grown up: the catalogue is
*earned*, not built. (#05 is the flagship of this idea.)

**#05 "Make It Proper" — the beat sheet:**
1. Pam borns the cream on the fly (rough — name, price, quick photo).
2. Larry & Sally buy it — two in a day. Velocity.
3. Felix, from the road, sees it on the dashboard → texts Ralph **a URL** (the product on
   artemis-luzern.ch). Self-explanatory.
4. **Ralph makes it proper** — opens the website (no integration, so he copies it across by hand):
   the real photos, the specs, the story. **AND** the cost (→ margin) and a reorder quantity (→
   never runs out).
5. **The approval gate** — Ralph's real job isn't paste, it's *verify*: the barcode Pam **scanned**
   may not match the website's product. A human confirms "yes, this is that" before the shop trusts
   it. (*If one seal fails, check all the seals.*)
6. Next shift, Pam opens the cream — beautiful, complete. It graduated.

**Feature seed (real roadmap):** a manager "make proper / approve" queue — on-the-fly hits that
gain velocity surface for enrichment + a barcode-match approval. The product model already carries
cost / image / min-max-stock / reorder, so this is wiring, not inventing. The SMS stays Felix's own
phone; Banco just surfaces the flag.

## THE MACHINE (our new workflow)
Angel reads the teleprompter (one continuous take, ~2 min) → Tigs drives every screen with
Puppeteer + builds the whole film (~10 min). **New film every ~20 minutes.** Angel tells the
story; Tigs does the clicks and the post. We agree on the premise first, then roll.

*Bible is a living doc — redirect anything. Last updated 2026-06-23.*
