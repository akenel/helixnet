# SOP — Add a Legend (a new master to The Legends wall)

*June 10 2026. Born from adding Sherlock Holmes live. A Legend is a master you can ask anything — the
imagination machine's mentors. This is how a new one earns a place on the wall.*

> **THIS SOP IS A RECIPE — `mint-a-legend`** (Angel: "my SOP is basically another one of our recipes").
> The factory builds its own cast. Procedure-as-code ([[lp-the-design-factory]]): one dict entry, input a
> name → the machine does the rest. The manual steps below (§5) are what the recipe AUTOMATES.
>
> **Recipe flow:** `name` → **research** the figure (web + Ollama) → **dedupe-check** the wall (fuzzy match —
> don't add a master who's already there) → **vet**: a verdict with **pros/cons** of picking them + **suggest
> better/related** masters → **draft** metadata (first-person bio, tagline, workshop, **assign a House**) →
> **propose** for approval → on approve, **insert**. Pure recipe = the proposal; the insert is the commit action.

---

## 1. The rule (who qualifies)

**A Legend must be a DOCUMENTED figure** — so the recipe can research a *real* profile, not fabricate one.
**Historical OR fictional — both welcome** (it's an imagination machine):

- **Historical person** — Heisenberg, Einstein, Lovelace, Sun Tzu.
- **Iconic fictional character** with a deep public canon — Sherlock, **Spider-Man, Superman**, etc. The
  "crazy nonsense" is *good* — but it still needs a researchable canon (who they are, their voice, their code).

The test: *is there enough public record to write a true-to-canon bio, a signature line, and capture their
voice?* Yes → qualifies. Inventing from nothing → that's the **user-minted** tier (§roadmap), not the curated cast.

**The recipe must vet before it adds:**
- **Dedupe** — already on the wall? (fuzzy match on name/canonical) → skip + say so.
- **Pros/cons** — is this master *useful* to ask? what House do they fit? any overlap with an existing one?
- **Suggest** — "you picked X; consider Y/Z who cover this better or add a missing angle."

> **Roadmap (not this SOP):** later, **users mint their own legends** — themselves, a past version of
> themselves, or a *fusion* of two ("Vince + a brain fart"). That's the imagination machine going personal.
> This SOP is the foundation that makes that safe + consistent.

---

## 2. What a Legend IS (the data model)

A Legend is a **persona row in the Square cast** — `bh_user` in the BorrowHood (Square) DB. It's read live
by `src/services/square_bridge.py::list_legends()` (`SELECT display_name, workshop_name, tagline, bio …
FROM bh_user`) and housed by the cached map (`bottega_sessions` slug `legend-houses`, [[lp-own-realm-next-block]]).
No Keycloak login — a persona you *ask*, not log in as. Appears immediately (the cast is read live, no cache).

---

## 3. The metadata to fill (research → write in their voice)

| Field | What | Example (Sherlock) |
|---|---|---|
| `display_name` | Their name | `Sherlock Holmes` |
| `slug` | kebab-case | `sherlock-holmes` |
| `email` | placeholder | `sherlock.holmes@legends.lapiazza.app` |
| `workshop_name` | their domain as a "studio/lab/study" | `The Baker Street Study` |
| `tagline` | **their signature line** (one quote) | *"When you have eliminated the impossible…"* |
| `bio` | **FIRST PERSON**, researched: origin, achievements, **method/ethos** — *speak as them* | *"Consulting detective of 221B… I invented the science of deduction…"* |
| `badge_tier` | `LEGEND` | |
| `account_status` | `ACTIVE` | |
| flags/enums | `can_vouch_raffles`, `offers_*`, `notify_*` → copy from an existing legend (guaranteed-valid) | |

**Research step (the "scrape"):** gather the figure's real facts — born where/when, key achievements, their
*method* of thinking, a signature quote. Write the **bio in first person** (the master speaks to the asker)
and make the **tagline their real signature line**. Don't fabricate facts; the voice is the styling, the
facts are true. *(Future automation: `lp_add_legend.py` — web-research + Ollama drafts the bio/tagline/house,
human reviews before insert.)*

---

## 4. Assign a House (one of ten)

| House | Domain |
|---|---|
| The Forge | engineers, inventors, makers |
| The Atelier | artists, designers, architects, filmmakers |
| The Lyceum | scientists, mathematicians, philosophers, **logicians** |
| The Strategoi | strategists, leaders, warriors |
| The Scriptorium | writers, poets, storytellers |
| The Agora | merchants, entrepreneurs, commerce |
| The Hearth | everyday masters: cooks, gardeners, craftspeople (**DEFAULT**) |
| The Observatory | explorers, navigators, astronomers |
| The Conservatory | musicians, composers, performers |
| The Sanctuary | healers, teachers, spiritual guides |

New legends fall to **The Hearth** (default) until housed. Assign properly via the `legend-houses` map, or
run `scripts/lp_house_classify.py` to AI-classify. *(Sherlock → **The Lyceum** — deduction is applied logic.)*

---

## 5. The procedure (safe DB insert — [[feedback-no-inline-python-c-through-ssh]])

NEVER inline SQL through ssh quoting. Write a `.sql` file, `docker cp` it in, `psql -f`. **Copy the enum/flag
columns from an existing legend** (so they're guaranteed valid) and **dollar-quote** the bio/tagline (apostrophes):

```sql
INSERT INTO bh_user (id, keycloak_id, email, display_name, slug, account_status, badge_tier,
  can_vouch_raffles, offers_delivery, offers_pickup, offers_training, offers_custom_orders,
  offers_repair, no_show_count, notify_telegram, notify_email, workshop_name, tagline, bio)
SELECT gen_random_uuid(), gen_random_uuid(), 'NAME@legends.lapiazza.app', 'Full Name', 'full-name',
  account_status, badge_tier, false,false,false,false,false,false, 0, false,false,
  $b$Workshop Name$b$, $b$Their signature quote$b$, $b$First-person researched bio…$b$
FROM bh_user WHERE display_name = 'Albert Einstein' LIMIT 1
ON CONFLICT DO NOTHING;
```
```bash
URL=$(docker exec borrowhood_staging printenv BH_DATABASE_URL); PW=$(echo "$URL" | sed -E "s|.*://[^:]+:([^@]+)@.*|\1|")
docker cp /tmp/legend.sql postgres:/tmp/legend.sql
docker exec -e PGPASSWORD="$PW" postgres psql -U lapiazza_staging_app -d borrowhood_staging -f /tmp/legend.sql
```

**Staging first** ([[feedback-staging-before-prod]]). To put a legend on PROD, run the same against the prod
`borrowhood` DB/user — but only after the figure is reviewed.

---

## 6. Verify (don't claim done without it)

- [ ] **In the cast:** `SELECT display_name, badge_tier FROM bh_user WHERE display_name='…';` → one row, `LEGEND`.
- [ ] **In the UI:** they appear in The Legends gallery (under their House, or The Hearth if unhoused).
- [ ] **They answer:** pick them → ask a question → the mentor-session returns gold in their voice.
- [ ] **House correct?** Re-house if they landed in the default by accident.

---

## 7. Quality bar

- Bio is **true + first-person + in their voice** — a reader should *hear* them.
- Tagline is their **real** signature line, not invented.
- The answer they give should sound like *them*, applied to the asker's problem ("the answer is in the
  question", [[lesson-answer-is-in-the-question]]).

*Example of record: Sherlock Holmes, added 2026-06-10 (staging) — The Baker Street Study, The Lyceum.*
