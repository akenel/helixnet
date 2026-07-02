# Head-Shop CRM — Postcard Outreach List (CH)

*Purpose: turn 20 Google-Maps head-shop listings into a call/postcard sheet.
The postcard only NEEDS the address. The manager name is the bonus that makes it land.*

Connects to the Banco head-shop GTM (memory: `banco-headshop-vertical-mosey-gtm`).
These postcards ARE the warm-outreach channel into the head-shop vertical.

---

## The Schema (`headshop-leads.csv`)

Three tiers of fields, ordered from "already have it" to "needs a phone call":

**Tier 0 — Seed (from the Google Maps paste, done):**
`id, name, chain, category, city, rating, reviews, phone`

**Tier 1 — Enrichment (automated, cheap, high yield):**
`street_address, postal_code, website, email, legal_entity, manager_name, manager_role`
plus provenance: `source_address, source_manager`

**Tier 2 — CRM / outreach (human, the phone-call layer):**
`contact_status (todo|enriched|called|emailed|reached), contact_person, postcard_sent, notes, last_updated`

`chain` groups multi-location owners (Werners = K4/K5/Limmatquai/Zug → ONE decision-maker,
four postcards). That column is also the multi-tenant seam for Banco later.

---

## Difficulty — the honest read (proven on 3 shops, 2026-07-01)

| Field | Difficulty | Best source | Expected yield |
|---|---|---|---|
| Street address + postal | **Easy** | search.ch, local.ch, own website | ~100% |
| Website | Easy | web search | ~90% |
| Email | Easy–Medium | Impressum / Kontakt page (Swiss law requires it) | ~75% |
| Legal entity (GmbH/AG) | Easy | Zefix / Moneyhouse | ~100% for registered cos |
| **Manager name** | **Medium** | **Zefix / Moneyhouse (free, for GmbH/AG)** | ~60% free; rest by phone |

The address — the thing you actually need — is the EASY 90%. The manager name is the
hard 10%, and Switzerland hands you a shortcut: the commercial register.

---

## The Swiss shortcuts (this is the tip that matters)

1. **Zefix** (`zefix.ch`) — the federal commercial-register search. FREE public REST API.
   Every `GmbH`/`AG` lists its officers (Geschäftsführer / signatories) BY NAME.
   That's how "Emanuel Fischer, Stayhigh GmbH" appeared with zero phone calls.
2. **Moneyhouse** (`moneyhouse.ch`) — same register data, friendlier surface, shows role +
   signatory authority. Good for the LLM to read.
3. **search.ch / local.ch** — Swiss phone books. Exact street address + hours, reliably.
4. **Impressum law** — Swiss sites must publish a legal imprint with a contact. That page
   is where email (and often the owner's name) lives.

Sole proprietorships (Einzelfirma) under CHF 100k turnover aren't always in the register →
those are the ones the phone call is FOR. That's why the CRM has a call layer.

---

## Recommendation — DON'T build the scraper yet

For **20 shops**: enrich them in-session with web search (like the 3 demo rows). One
afternoon, no infrastructure. You get addresses today and can print postcards this week.

Build the automated recipe **only at scale** (the "hundreds of CH head-shops" in the GTM
memory). When that day comes, reuse the Artemis enrichment pattern (`run_llm`, BYO-brain):

```
for each shop:
  address  <- search.ch / local.ch  (or Google Places API)
  website  <- web search
  email    <- fetch site, LLM reads Impressum/Kontakt
  entity+manager <- Zefix API by name+canton  ->  LLM merges officers
  emit record with per-field confidence + source
```

The NEW parts vs Artemis are just two data taps: **Zefix (free)** and optionally **Google
Places (cheap, for address at volume)**. Everything else is the recipe you already have.

## Next actions

1. Enrich the remaining 17 rows in-session (I can do this now — ~15 searches).
2. Confirm managers by phone for the non-GmbH shops (the CRM call layer).
3. Print postcards from `street_address` as soon as Tier 1 is filled — don't wait on managers.
