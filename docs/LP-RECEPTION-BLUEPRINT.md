# La Piazza — Reception: SIPOC + Service Blueprint

*The one-page map of "a person walks in the door." Draft for Angel to mark up —
NOT finished. Pairs with `docs/LP-RECEPTION-ARCHITECTURE.md` (the why + prior art)
and `memory/lp-anti-rejection-origin.md` (the acceptance test).*

**Acceptance test for every box below:** *would this have helped the Angel who
walked into that coaching room — psyched, prepared, ready?* If a step would make him
feel processed / blamed / talked-down-to, it's wrong.

**The one role rule (the line we're drawing):** Cleo WRITES the card — backstage.
Masters READ a sliced copy — frontstage. Nobody crosses the line. The card is the
golden record; Cleo is its steward; the Reception Packet is the typed contract that
travels on handoff.

---

## Part 1 — SIPOC (the process at arm's length)

*Suppliers → Inputs → Process → Outputs → Customers. What feeds reception, the few
big steps, and what it must produce.*

### Suppliers (who/what provides the raw material)
- **The user** — the one source of truth for their own life.
- **Keycloak** — identity + login state (regular vs first-timer vs anon).
- **CV / self-description** — whatever they bring (or nothing).
- **Existing card** — for returning visitors (the prior golden record).
- **Master roster + House catalog** — the cast we can route to.
- **Recipe / output-type shelf** — what the workshop can actually produce.
- **The brain** — Ollama Turbo (extraction, matching nuance, warm phrasing).

### Inputs
- Raw signup: email + 16/18 age check.
- Language choice (the one hard field).
- CV text OR a plain "tell us what you do" sentence.
- Chat utterances (the running conversation).
- Login/visitor state + the prior card (if any).

### Process (the few big steps — detail in the blueprint below)
1. **R0 prep-scan** — read the latest card fresh; never go in cold.
2. **Greet by visitor-mode** — first-timer / regular / independent.
3. **Intake** — progressive profiling via OARS; build/enrich the card with provenance.
4. **Readiness** — grade the must-dos (tiered: language hard, house produce, rest soft).
5. **Match** — card → House + master + *reason*; confidence-gated (abstain if unsure).
6. **Warm handoff** — assemble the typed Reception Packet (sliced, tier-3 redacted);
   the master takes the desk (`current_host`).
7. **(First-timer fork)** — offer the house tour vs straight into the profile.

### Outputs (what reception must produce)
- **The card** — golden record, every field provenanced.
- **The Reception Packet** — objective + card-slice + output-type + boundaries.
- **`current_host` set** — you always leave with a host.
- **A seeded thread** with the matched master (continuity).
- **One concrete next step / first artifact** — never "figure it out yourself."
- **Favorites / readiness** — updated.

### Customers (who consumes the output)
- **The user** (primary) — feels *received*, leaves with a host + a next step.
- **The receiving master** — gets the packet, doesn't re-interrogate.
- **Future masters / the user's future self** — read the same card.
- **The Today board** — seeded with first tasks.

---

## Part 2 — Service Blueprint (the layered swim-lanes)

*The new-visitor journey, top to bottom: what they see, what Cleo shows, the line of
visibility, what happens backstage, and the systems underneath. `═══` lines are the
boundaries that enforce the role rule.*

```
JOURNEY →        ARRIVE          SAY WHAT         A FEW GENTLE        SEE THEIR        MEET A           START
                                 YOU DO           QUESTIONS          CARD             MASTER          WORKING
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ PHYSICAL        get-started     Cleo chat        Cleo chat          card panel       intro + master   master chat
│ EVIDENCE        page / door     box              (one Q at a time)  (readiness bar)  hand-off card    + 1st output
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CUSTOMER        lands (logged   types/speaks     answers / skips    glances: "yes    "nice to meet    asks, gets a
│ ACTIONS         in or anon)     "I make leather  freely             that's me" /     you"             tailored answer
│                                 bags"            (no pressure)      edits            (or "stay w/ Cleo")
├═════════════════════════════════════════════════════════════════════ FRONTSTAGE (visible — Cleo's voice + UI) ═┤
│ FRONTSTAGE      mode-aware      warm reflect     OARS: open Q +     recap: "here's   warm transfer:   master opens
│ (Cleo /         greeting:       (MI): "a leather Affirm + one ask;  what I've got"   "here's Leonardo, KNOWING them
│  host)          first-timer →   maker, lovely"   normalizing pre-   + readiness bar  EN+IT, here's    (reads the
│                 "expecting you" then EPE          amble on tier-3   (unlock-framed,  WHY I picked     packet, never
│                 regular → your                    + why_we_ask;      NO red %)        him" → passes    re-asks)
│                 master greets                     skip = roll, no                     the chat box
│                 indep → step back                 re-ask
├═════════════════════════════════════════════════════ LINE OF VISIBILITY (user never sees below) ═══════════════┤
│ BACKSTAGE       prep-scan:      extract facts    extract→dedupe→    completeness     matcher: score   thread seeded;
│ (Cleo's         read latest     from utterance   survivorship       scoring per      card vs masters  master reads
│  machinery —    card +          (NOT the master) write to card      section;         (lang=hard       SLICED packet
│  WRITE here)    freshness;      → provisional    w/ provenance      must-do          filter, RIASEC   (tier-3
│                 classify mode   (inferred,       (explicit>inferred;readiness        =soft); confid-  redacted);
│                                 low-confidence)  confirm sensitive) grade (tiered)    ence gate +      current_host
│                                                                                       reason string    = master
├═══════════════════════════════════════════════ LINE OF INTERNAL INTERACTION ══════════════════════════════════┤
│ SUPPORT         Keycloak        the brain        the brain +        session spine    House/master     session spine
│ PROCESSES       (identity,      (extraction)     write pipeline     (bottega_        roster + output- (threads);
│                 visitor mode)                    + session spine    sessions)        type registry    grounding /
│                                                                                                        no-fabricate
│                                                                                                        guards (poka-yoke)
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3 — Where the anti-coach rules live (the markup targets)

| The coach's failure | Where we fix it in this blueprint |
|---|---|
| Didn't read the CV | **R0 prep-scan** (backstage, every turn) + masters read the packet, KNOWING you |
| "Figure it out yourself" | **Output: one concrete next step** is mandatory; the master's 1st reply is tailored |
| Grade-three conveyor belt | **Match by card**, not a script; **standing host** = continuity, not a new stranger |
| Abstract / non-applicable | Outputs are **real artifacts** (recipes / output-types), not advice-shaped air |
| 5–6 teachers, no memory | **`current_host`** + the card carry you; you never re-introduce yourself |
| Humiliating / blamed | **tier-3 dignity** (skippable, normalized, never re-asked) + **no red % meter** |
| The German course (clear, leveled) | **readiness bar = "next rung"** framing; OARS recap = "you're here, now this" |

---

## Part 4 — Decisions (locked 2026-06-15)

*The thread tying all six: **never blank, never a grade, never dumped.** Every answer
is the anti-coach.*

1. **House tour — neither as a cold fork.** Cleo gets ONE thing first (language + a
   one-line "what do you do"); the card starts the instant they speak; THEN she offers
   the tour, now *tailored* ("want to see what other makers here are doing?"). A cold
   tour is the conveyor belt; a tour that already knows one thing is a welcome. *(Easy.)*
2. **Independent mode — always a silent card, never nothing.** The user who waves her
   off still gets his card quietly kept from what he does, so he's not blank on return.
   Silent ≠ forgetful; she just doesn't talk while he works. *(Easy.)*
3. **Readiness — words, no number (not even green).** Any % is a grade, and grades
   judge. Instead, a one-line nudge: "add your location and I can point you to things
   nearby." A hint, not a scoreboard. The German-course "next rung." *(Easy.)*
4. **Confidence gate — one more good question, then offer two.** No wild guess, no
   interrogation. Foggy on the House → one sharp question → still foggy → "I'm torn
   between these two, want a peek at each?" Bounded patience (the 2–3-try rule). *(Medium.)*
5. **Capital — last, smallest, skippable, gates nothing.** She never asks "do you have
   money"; she asks what you've got to work with, and money is one optional corner.
   Skipping costs zero. *(Easy.)*
6. **First next-step — Cleo hands off with a sticky-note already written.** Never
   walked to a master and left at a blank page. Cleo drafts the starter task at handoff
   (seeds the Today board); the master refines it. The opposite of "figure it out
   yourself." *(Medium.)*

---

## Part 5 — Cleo's chat UI (the input tool), in bricks

*The chat IS the tool; the better the tool, the richer the card, the sharper the
masters. Built in order so it never overwhelms.*

- **Brick 1 (start here): a paperclip for documents.** Same machine as the door's CV
  upload, now *inside the chat*. Drop a diploma, a certificate, another CV, a tool
  list → Cleo reads the text and enriches the card. Reuses what we have; low risk.
  **On drop, Cleo reacts in the moment (decided):** "ooh, a diploma — let me look…
  nice, added your honours in chemistry." Reacting shows she actually read it (the one
  thing the coach didn't do). *(Cheap.)*
- **Brick 2: "here's my leather bag, what do you think?"** Photos of the user's *work*.
  Bigger brick — understanding a picture needs a **vision model**, not Cleo's text
  brain. Cleo *files* the photo on the card; a **master** (a craft/design eye)
  critiques it. Stays in lane. *(Needs a vision brain.)*
- **Brick 3 (later): the power-chat.** Persistent context across visits (mostly there
  via the thread spine), "new chat" = a new thread, and slash-commands (`/compact`,
  `/workflow`) as the power-user polish on top — the last brick, once 1 & 2 earn their keep.
