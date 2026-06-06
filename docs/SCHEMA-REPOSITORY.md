# 🏰 The Castle Plan — Schema Repository (the ESR)

> *Begin with the end in mind (Syd Field). Don't make it up as we go — that's a mess.*
> We inherit the SAP PI/PO concept: a visual, classified repository of **service interfaces** (schemas) and **operations** (recipes/iFlows). This is the catalog of what it takes to build the castle.

## The End (Syd Field's last page)
A lonely, burned, AI-displaced person walks in → over a 4-week cutover, repeated → walks out with a **profile, a rebuilt body, a clearer mind, a remembered spirit, something to sell, and a community.** The castle is the machine that does that — for 300+ souls, run by one Wolf + the AI. Every schema and operation below exists to fill **one growing JSON document per person.**

## The Blueprint = the Person Schema (the end-state document every operation fills)
```
member {
  identity { name, slug, avatar, one_liner, elevator_22s, bio, tagline, skills[], categories[] }
  body     { equipment[], injuries[], goal, alcohol{drinks,amount},
             kpis{ weight, energy, mood, sleep, shoulder, pushups, burpees, squats, plank },
             journey{ week, day, workouts_done } }
  mind     { questions[], mentors_seen[], coaching_notes[] }
  spirit   { childhood, passion, dreams[], the_why }
  make     { listings[], drafts[], shares[] }
  journey  { start_date, week, cutover_plan, streak, kpi_history[] }
}
```
Every field starts as a **default/null**; the rebuild is filling the tree over time (one validated field per conversation), versioned weekly so we can watch the person get rebuilt. (See [[lp-structured-json-io]].)

## The Repository — operations classified by domain (the "Houses" of the ESR)
Each operation is a complete **iFlow**: inbound SI (`inputs[]`) → mapping (Llama + system/prompt) → outbound SI (`output_schema`) → receiver (a slice of the person schema).

| Domain (House) | Operation (recipe) | Fills | Status |
|---|---|---|---|
| 👤 **Identity** | `get-started` | member: account + profile | ✅ live |
| | `cv-to-bio` | identity.{bio,tagline,skills,categories} | ✅ schema'd |
| | `cv-generate` · `cover-letter` | CV / letter artifacts | ✅ |
| | `one-liner` / `elevator-pitch` | identity.{one_liner, elevator_22s} | ▢ planned |
| 🏋️ **Body** | `workout-plan` | body.journey (day-N, calibrated) | ✅ live |
| | `body-intake` | body.{equipment,injuries,goal,alcohol} | ▢ planned (structured) |
| | `meal-plan` | body.fuel (breakfast/snacks/OMAD) | ▢ planned |
| 🧠 **Mind** | `mentor-session` (Ask a Master) | mind.mentors_seen | ✅ live |
| | `coaching-question` (GROW) | mind.questions | ▢ planned |
| ✨ **Spirit** | `story-intake` | spirit.{childhood,passion,dreams,the_why} | ▢ planned |
| 📢 **Make** | `event-posting` · `product` | make.listings | ✅ live |
| | `music-playlist` | a playlist (+ YouTube via yt-dlp) | ✅ live |
| | `locandina` / postcard | make.shares | ✅ (BorrowHood) |
| 🧭 **Journey** | `blueprint` (30-day cutover) | journey.cutover_plan | ✅ `lp_blueprint.py` |
| | **`suggest-for-me`** (reads the whole member → proposes) | — | ▢ **THE keystone** ([[lp-ai-suggests-keystone]]) |

## The Contract (every operation obeys)
- **Inbound SI** = `inputs[]` (request schema). **Outbound SI** = `output_schema` (response schema, defaults fill gaps).
- **Mapping** = the recipe's `system`+`prompt`, executed by Llama ([[lp-brain-default-llama]]).
- **One dict entry = one iFlow.** Add operation #N = a config row, not a project. ([[lp-the-design-factory]])

## Build order (the cutover — don't wing it)
1. ✅ **Foundations:** identity (get-started, cv-to-bio schema'd), body (workout-plan), mind (Ask a Master), make (postings/playlist). The Lego base snaps together.
2. ▢ **The structured intakes** — `body-intake`, `story-intake` (fill the person schema with the calibration + the why), schema-driven.
3. ▢ **The dashboard** — the tabbed rebuild hub ([[lp-member-dashboard-tabs]]) where the schema is shown/tracked.
4. ▢ **The keystone** — `suggest-for-me` reads the filled member → proposes the next move.
5. ▢ Journey tracking — the 4-week cutover ([[lp-body-coaching-intake]]), KPI history, weekly snapshots.

---
*The cast (Houses + characters) classifies the people; this repository classifies the operations. Same discipline. Rome wasn't built in a day — but it was built to a plan.* 🏰🐺
