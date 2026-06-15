# La Piazza — The Cleopatra Reception Architecture

*Prior-art research synthesis, 2026-06-15. The decide-from document for the Cleo
reception line (#111–#117). TL;DR: almost every piece of our design is a named,
20–60-year-proven pattern. We're not inventing — we're assembling.*

---

## 1. You are not reinventing the wheel

Every box in our architecture has a real name.

| Our piece | It's just… | One-liner |
|---|---|---|
| "The card" — one profile, many readers, one writer | **MDM Golden Record** (Informatica/Reltio/Profisee) | A consolidated, de-duplicated, trusted record of one entity everyone references. 30 yrs of vocabulary: steward, survivorship, source authority. |
| Cleo is the only one who writes the card | **Data Steward + single write-authority** (DAMA-DMBOK) | The designated gatekeeper; consumers read, never write. Textbook. |
| Masters read the card, never edit it | **System of Record vs System of Reference** | Chat = SoR (facts originate, Cleo's domain). Card = curated read model masters consult. Masters never parse raw chat. |
| Chat log → Cleo derives the card → masters get a snapshot | **CQRS-lite / read-model projection** | Append-only events, one write path, many read projections. Free auditability ("why does the card say divorced?"). |
| Conflicting facts (card says married, user says divorced) | **Survivorship / match-merge rules** | Authority (explicit > inferred), recency (newer life-fact wins), completeness (fill blanks). A *policy*, not last-write-wins. |
| Card builds over time, thin→generic, rich→tailored | **Progressive Profiling** (HubSpot/Marketo) | The proven antidote to form-fatigue. 1–3 fields at a time, reward = better experience. Our incentive loop, with published numbers (+42% submissions). |
| Cleo's gentle-elicitation manner | **Motivational Interviewing — OARS** | Open questions, Affirmations, Reflections, Summaries. The clinical version of "smooth, not forceful." Our recap = the "S". |
| "Can I ask a couple personal things? Skip any." | **Ask-Permission + Elicit-Provide-Elicit** (MI) | Hands control to the user before sensitive blocks AND before routing. |
| One ask, never re-ask a skip | **Rolling with resistance** (MI) | Decline = change approach, not push harder. |
| Hard questions go last | **Trauma-informed sequencing** + **slot-filling** | Rapport → screen → sensitive. Track filled vs empty slots; ask only the gap. |
| Cleo → master, carrying context | **Warm transfer / warm handoff** + **Orchestrator-Worker handoff** | "Never make them repeat themselves; explain *why*." The Reception Packet IS a warm transfer. |
| Cleo coordinates, masters are isolated specialists | **Orchestrator/Lead + Workers** | Cleo = stateful **Supervisor** (control returns to her) with a **router** sub-step for the pick. |
| Card-as-shared-state masters read | **Blackboard architecture** (Hearsay-II, 1976) | Agents coordinate through shared state — plus single-writer on top. |
| How Cleo writes facts without bloat/contradiction | **Mem0 pipeline: extract → dedupe → insert/update/discard** | Background fact extraction. Don't blind-append. |
| Matching card → House + master + reason | **Content-based recommender + Skill-Based Routing** | Match required attributes to specialist attributes, weighted. Language = hard filter; RIASEC = soft weight. |
| Thin card → generic + nudge | **Cold-start fallback + confidence-gated routing (reject option)** | New user = high reducible uncertainty = "ask one more thing." Abstain from a confident wrong route. |
| Cleo computes the ONE next step, not a menu | **Next-Best-Action** (Pega/Bain) | One shot, one kill. (Our UFA Wolf Philosophy already.) |
| Card-completeness → quality loop, the scorecard | **Customer Health Score** + **LinkedIn All-Star meter** + **Endowed Progress Effect** | Composite readiness number; pre-filled bar; frame as unlock. |
| Nudges ("you haven't loaded a CV") | **Lifecycle marketing (behavioral triggers)**, not drip | Fire on behavior/stage, not a calendar. |
| Signal → Cleo acts | **Customer Success Playbooks (CTA → Playbook)** = our recipes | Named: thin-card play, CV-but-no-listing play, lapsed-user play. |
| Sensitive fields (age, divorce, disability) | **Strengths-based / asset-based framing** + **Normalizing statement** | Deficits stored as assets-not-yet-named; "lots of folks here are starting over." |
| The "steer but never force" doctrine | **Libertarian paternalism / Nudge** (Thaler & Sunstein) | The academic foundation of our anti-rejection soul. |
| The resources dimension of the card | **Sustainable Livelihoods Five Capitals** (DFID) + **ABCD** | Built *for* low-capital vulnerable people. Capital is 1 of 5 assets, explicitly optional. The missing spine. |
| Tagging skills so masters can reason | **KSAO** + **O*NET** + **RIASEC** + **ESCO** | Person spine = O*NET; skill atoms = KSAO; EU multilingual codes = ESCO. |
| Locking reception scope & role boundary | **SIPOC + Service Blueprint (line of visibility)** | One-time artifacts. Card-writes live *backstage, under Cleo.* |
| Improving the flow without scripting Cleo | **DMAIC** loop + **Poka-yoke** the backstage, not the conversation | Mistake-proof the structured steps; keep the voice flexible. |

**Angel's ESR frame extends to the data layer:** the card is the **golden record**,
Cleo is the **steward**, the Reception Packet is the **typed delegation contract**
(the mapping object) that travels on handoff.

---

## 2. What the pros do that we DON'T yet (ranked by leverage)

1. **Per-field provenance + confidence + timestamp.** Every card field carries
   `value | source(stated|inferred) | confidence | last_updated`. The *mechanism*
   that makes "held with dignity" real: Cleo holds a `stated` fact firmly, but
   says "I think you mentioned X — right?" for an `inferred` one. Enables
   survivorship + audit. **Do this first.**
2. **A real survivorship policy.** A misparse (#89 "Born"→name) must never silently
   overwrite a stated fact. Rule: *explicit > inferred; newer life-fact wins for
   mutable fields; never silently overwrite a sensitive field — confirm.*
3. **extract → dedupe → insert/update/discard write pipeline (Mem0).** Semantic-
   overlap check before committing. Async so card-writing adds zero chat latency.
4. **Active-learning elicitation, weighted DOWN for sensitivity.** Ask the most
   informative *low-sensitivity* gap first; let sensitive fields emerge with trust.
5. **Confidence-gated routing with a reject option.** Below threshold → generic
   help + one clarifying question, or "two Houses to peek at" — not a forced pick.
   Higher bar before firmly routing a *vulnerable* user (asymmetric cost).
6. **Field-level access control + card-slicing into the packet.** The leatherwork
   master never reads the divorce field. Dignity = an enforceable permission.
7. **Define ONE activation event + North Star:** "first useful master output the
   user keeps/shares." Nudges target getting stalled users *to that moment*.
8. **Behavioral-trigger nudges with frequency caps**, not scheduled drips.
9. **Typed Reception Packet:** objective + card-slice + output-type + boundaries
   ("don't re-ask these"). Stops masters re-interrogating.
10. **One-time SIPOC + Service Blueprint** to lock the Cleo-vs-masters boundary.

---

## 3. Where we DIVERGE on purpose (the anti-rejection soul)

- **Reject Lean Canvas, embrace Five Capitals.** Lean Canvas drops Key Resources;
  our whole audience IS their resources-at-hand. We need the box it omits.
- **Health score → readiness bar (empowerment, not surveillance).** Same math,
  opposite framing. **No red "40% incomplete."** Only "the more Cleo knows, the
  sharper your masters get." Never gate core help behind 100%.
- **No collaborative filtering / no authority-based expert ranking.** No volume;
  both amplify popularity bias against a curated, dignity-first cast. Stay content-based.
- **Don't transfer full conversation on handoff.** Hand a *curated* packet. Full
  history leaks sensitive raw fields and burns tokens.
- **Active learning weighted by sensitivity, not pure info-gain.** Info-greedy
  would interrogate the vulnerable first. We invert that.
- **Borrow triage's asymmetric-cost logic, reject its clinical coldness.** Vulnerable
  signal → default to the warm path (stay with Cleo). No urgency tiers.
- **Poka-yoke the backstage, NOT Cleo's voice.** Mistake-proof card writes / grounding
  guards / no-fabrication (#92, #121). Keep the conversation flexible.
- **Skippability is in the SENTENCE, not just the UI.** "Totally fine to skip" must
  be *said*.
- **AI self-disclosure only about the SYSTEM, never invented feelings** (we've been
  bitten by fabrication). "One honest profile, no resale" — never a fake personal life.

---

## 4. Card schema v2

Two spines + a soul skin. **Every field is a typed slot carrying
`value, source(stated|inferred), confidence, last_updated, sensitivity_tier(1–3),
why_we_ask`.** Tier 1 = safe/energizing (ask early). Tier 3 = sensitive (deferred,
optional, normalized, never re-asked).

**A. PERSON spine** — O*NET + KSAO + RIASEC
- `language` + `level` *(tier 1 — **HARD filter** for routing)*
- `interests_riasec` — Holland 2–3 letter code *(tier 1, soft routing weight)*
- `skills[]` — tagged K/S/A/O internally; ESCO id later *(tier 1)*
- `knowledge[]`, `experience[]` *(tier 1–2)*
- `work_values` / `work_styles` *(tier 2)*
- `goals[]` + `why_they_came` *(tier 1 — the energizing opener)*

**B. CAPACITY spine** — Five Capitals (DFID), the missing dimension, asset-framed
- **Human:** time available, energy, health/stamina *(tier 1–2)*
- **Social:** helpers, network, suppliers, who-they-know *(tier 1)*
- **Physical:** tools owned, materials, workspace, production capacity *(tier 1 — "what can you do today")*
- **Financial:** capital/credit/savings *(tier 3 — asked last, lightly, optional; one of five, never a prerequisite)*
- **Natural:** local materials/place *(tier 2)*

**C. HOUSEHOLD & SITUATION** — strengths/constraint-framed, all tier 3, normalized
- `marital_status` incl. "freshly divorced" — *stored only as it bears on constraints*
- `dependents` / `ties` — kids, alimony, can't-leave-town *(planning inputs)*
- `accessibility` — ADHD, disability *(asset/constraint framing)*
- `age` *(tier 3, normalized, dignity)*
- `gender` *(tier 3, optional)*
- `employment_status` — reframed: "time + energy available + what you want to build," never "unemployed"

**D. LOCATION**
- `location` + `mobility_constraint` (can/can't leave town) *(tier 1–2 — "I'll only suggest things you can do from here")*

**E. META (governance layer)**
- `completeness_by_section` (drives the readiness bar + next-slot-to-ask)
- `freshness` (last full recap — our E2 recap = the freshness mechanism)
- `private_fields[]` (the tier-3 set Cleo redacts out of any master packet)

**Rule:** an empty field is stored as **"asset not yet named"** (ABCD), never
"missing X." A thin card = an incomplete inventory, not a deficient person.

---

## 5. The plan — ordered small slices

1. **Card v2 schema with per-field provenance** (`value/source/confidence/timestamp/tier/why_we_ask`). *Foundation; first.*
2. **Single-writer enforcement in code** — masters get a read-only projection; card mutation only through Cleo's one write path (not prompt convention).
3. **Card-slicing + private-tier redaction** — the master-facing slice drops tier-3.
4. **Mem0-style write pipeline** — extract → dedupe → insert/update/discard, async, survivorship rules.
5. **Slot-filling intake driven by OARS** — filled/empty slots; one warm question/turn; normalizing preamble + `why_we_ask` on tier-3; one-ask-then-roll.
6. **Content-based matcher (R3)** — card vs each master's tagged specialty; language hard filter, RIASEC soft; human-readable reason.
7. **Confidence gate (reject option)** — below threshold → generic + one question OR two Houses; higher bar for vulnerable signals.
8. **Typed Reception Packet (warm handoff)** — objective + card-slice + output-type + boundaries; Cleo says *why*.
9. **Readiness bar** — pre-filled, unlock-framed, no red state, never gates help.
10. **Activation event + North Star** — "first kept/shared master output"; instrument it.
11. **NBA nudge engine** — signal→playbook table (thin-card, CV-but-no-listing, lapsed-user), at-most-one/session, frequency cap.
12. **One-time SIPOC + Service Blueprint** — lock the line of visibility.
13. **Poka-yoke the backstage** — schema validation + grounding/no-fabrication guards (#89/#90/#92/#121) wired into smoke + console-sweep (DMAIC "Control").

---

## 6. Pitfalls to dodge

- **Last-write-wins** (no survivorship) — an offhand remark overwrites a stated sensitive fact.
- **A master writing the card "just this once"** — collapses single-source-of-truth. Enforce read-only at the *data layer*, not by prompt.
- **Masters parsing raw chat** instead of the card — duplicates Cleo, breaks role separation.
- **Asserting inferred facts as certain** — violates the soul. Confidence + confirm.
- **Front-loading a long intake / forcing sensitive fields** — vulnerable users bounce.
- **Nudge-shaming a thin card** — turns the incentive loop into a guilt loop.
- **Re-asking a skipped question** in-session — kills trust.
- **A red "% complete" meter** — reads as a verdict. Unlock-framing only.
- **Fabricated AI self-disclosure** to force reciprocity.
- **Transferring full chat history on handoff** — leaks sensitive fields, burns tokens.
- **RIASEC standing in for capacity** — high interest + zero tools/time still can't ship.
- **Collaborative filtering / authority ranking too early** — no volume; popularity bias.
- **Over-engineering** — no full probabilistic match-merge, no event-sourcing framework, no ML-NBA, no ESCO import yet. One authenticated user per card = adopt *concepts*, skip heavy machinery.
- **Optimizing completeness instead of the aha output.**
- **Hard-scripting Cleo's voice** in the name of process rigor.

---

**The decision in one breath:** The card is an **MDM golden record with per-field
provenance**; **Cleo is the sole data steward** applying **survivorship rules**;
masters read a **sliced, read-only System of Reference** and never touch raw chat;
fed by **progressive profiling** delivered through **Motivational Interviewing**,
routed by a **content-based skill-based-router with a cold-start reject-option
fallback**, handed off via a **typed warm transfer**, kept alive by
**Next-Best-Action behavioral nudges** — all governed by **libertarian paternalism**
and the **Five Capitals** asset lens so a broke, freshly-divorced leather-bag maker
in Trapani feels *received*, not processed.
