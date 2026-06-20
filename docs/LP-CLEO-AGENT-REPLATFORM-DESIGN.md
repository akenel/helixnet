# La Piazza — Cleo Agent-Loop Re-Platform — Design Sketch

**Status:** DRAFT for Angel review · 2026-06-20
**Companion:** `tests/agent/tool_probe.py` (GO result, commit `3affa81`) · memory `lp-cleo-agent-loop-go`

---

## 0. Why

Scripted conversation flow can't encode taste — convergence resisted every prompt tweak (whack-a-mole,
±2 judge noise). The gating probe proved the BYO brain **drives a tool loop reliably** (8/8 converged,
0 premature, stayed on rails under injection). So: **don't scrap Cleo — re-skeleton her.** Keep the soul
(queen's voice, polyglot, dignity) and the guards and the card and the masters; swap the brittle
scripted flow for an agent loop where all of that becomes **tools + context**.

The reframe that makes this work: **floor = programmable, ceiling = judgment.** The brain gets judgment;
a deterministic cage gets the non-negotiables. Convergence stops being a vibe and becomes a tool decision.

---

## 1. The shape (one picture)

```
                        ┌──────────── THE DIGNITY CAGE (deterministic guards) ───────────┐
                        │                                                                │
   GUEST  <──SPOKEN──>  │   ┌─────────────┐        ┌───────── SILENT tools ──────────┐  │
   (human)              │   │   BRAIN     │ <────>  │ update_card · update_brick      │  │
     ▲                  │   │  persona +  │ tool    │ run_recipe · match_master       │  │
     │  ask_guest /     │   │  judgment   │ calls   └─────────────────────────────────┘  │
     └─ deliver  ───────│   └─────────────┘                                              │
                        │         ▲  reads (never via a tool)                            │
                        │         │                                                      │
                        │   CONTEXT: card · active bricks · recipe deck · master board · │
                        │            transcript · persona + guards                       │
                        └────────────────────────────────────────────────────────────────┘
```

The brain is **free inside the cage**. The cage makes the floor unbreakable no matter what the brain does.

---

## 2. The key split: SILENT vs SPOKEN tools

This is the architectural heart, and it's exactly your "she runs the recipe in the back end, sees the
result, *then* tells you."

| Kind | Tools | Behaviour |
|------|-------|-----------|
| **SILENT** (back-of-house) | `update_card`, `update_brick`, `run_recipe`, `match_master` | change state, return the result **to Cleo**, loop continues. The guest sees nothing yet. |
| **SPOKEN** (front-of-house) | `ask_guest`, `deliver` | surface to the **human**, PAUSE the loop, wait for the reply. |

So a single guest turn can be: `update_brick → run_recipe → deliver` (save, run, present) — several silent
moves, one spoken. That's the "output becomes input" cycle you described, made literal.

---

## 3. Context, not tools (the hard-won lesson)

Exposing a no-op `read_card` tool trapped the brain in a read-loop (33–50% → 100% once removed). So
**reading is KNOWING — it's context, never a tool.** Given to Cleo every turn:

- the **Core card** (who they are),
- the **active bricks** (domain sub-profiles in play),
- the **recipe deck** — each recipe's name + its outcome + the slots it needs,
- the **master board** (for handoff),
- the **transcript**, and her **persona + guards**.

Tools are reserved for things that **change the world**.

---

## 4. The tool set — each one a Service Interface

(Your SAP/ESR frame: every tool = a contract. Input → process → output, with a guard.)

| Tool | Kind | Input contract | Output | Guard |
|------|------|----------------|--------|-------|
| `ask_guest` | spoken | `question` | guest's reply | ask ≤1× per missing slot; never re-ask the card |
| `deliver` | spoken | `message` (a concrete move or handoff) | shown to guest | must be a real move/handoff, not a framework |
| `update_card` | silent | `fields` | merged card | tier-3 privacy wall; lists capped (built) |
| `update_brick` | silent | `domain`, `fields` | merged brick | only slots the brick defines |
| `run_recipe` | silent | `name`, `inputs` | recipe output | inputs must satisfy the recipe's required slots |
| `match_master` | silent | (the card) | grounded master + first step | never dead-ends (built: retry→fuzzy→relevance) |

`match_master` and the card-merge/cap are **already built** — they become tools, not new code.

---

## 5. The profile = a composable baseplate

Not one flat RIASEC card. A **green baseplate (one human)** with snap-on bricks:

- 🟦 **Core Identity card** = the *face* (today's card: name, origin, language, life-stage, RIASEC lens,
  aptitudes). Don't bloat it.
- 🟨 **Relationship brick** = trust, history, standing host, memory across visits. *Highest value, highest
  privacy risk — phase it LAST, behind the tier-3 wall.*
- 🟥 **Domain bricks** = **recipe-owned**. The recipe's input contract *is* the brick's schema (Fitness
  brick = goal/days/equipment/injuries — defined by the workout recipe). **Two-way:** the recipe READS the
  brick and WRITES results back → the profile compounds with every recipe used. That compounding is the moat.

**Rule:** no brick until a recipe needs it (YAGNI). Bricks are bounded + tiered, never free-text — so
recipes can read them deterministically and the privacy wall still holds.

---

## 6. The dignity cage (the floor, as a wrapper)

Deterministic checks the brain **cannot** violate, enforced around the loop (not inside the prompt):

- greeted-once · tier-3 sensitive hidden · language held · lists capped (built) ·
- never-dead-end on handoff (built) · master grounded to board (built) · recipe inputs validated.

The brain has total freedom of *judgment* inside; the cage guarantees La Piazza never humiliates, never
loses the card, never hands off to no one. **This is the whole bet: programmable floor, free ceiling.**

---

## 7. Convergence — solved by construction

`readiness = required slots full`. `run_recipe` is the goal state. The loop converges because running the
recipe (or handing off) is the only exit. Add the one nudge the probe asked for: **"ask at most once per
missing slot; don't re-offer."** Proven: `premature_run = 0` across the hard multi-turn test.

---

## 8. Migration — don't rip out the beating heart

| Phase | What | Risk control |
|-------|------|--------------|
| 0 | Probe (DONE) | — |
| 1 | Loop engine + tool registry as a NEW module (`src/compute/agent/`), parallel to scripted Cleo | prod Cleo untouched |
| 2 | Wire ONE real recipe (Fitness → workout) end-to-end through the loop, behind a flag, on staging | flag off in prod |
| 3 | Port the dignity cage as the wrapper; run the **existing eval harness** (`tests/reception`) against loop-Cleo | reuse, don't rebuild |
| 4 | Expand tools (more recipes, the `match_master` handoff), staging soak | scripted Cleo = fallback |
| 5 | Flag-flip on staging → human-green → prod | trunk-based, staging-before-prod |

Scripted Cleo stays as the fallback until loop-Cleo **beats it on the eval + your hand-test.** Nothing is
deleted until the replacement is proven.

---

## 9. Risks & open questions (for review)

1. **Tool-count scaling.** Probe had 3 tools; real Cleo ~6–8. Weaker models degrade as the menu grows —
   must re-probe at full tool count before betting Phase 4.
2. **Context bloat.** Inlining the recipe deck + master board could swell the prompt. If it does, the *read*
   stays context but we add a **`find_recipe(intent)` / `find_master(need)`** search tool (an action that
   *narrows*, not a read). Defer until it bites.
3. **Latency & cost.** A multi-step loop = several brain calls per guest turn. Mitigate: batch silent tools,
   cap steps, keep `json_mode`. Watch the Hetzner pinch.
4. **Brain variance.** Generalize the never-dead-end pattern (retry + fallback) to *every* tool call, so one
   malformed turn never breaks the loop.

---

## 10. Proposed first build (Phase 1)

A standalone `src/compute/agent/` package: the loop runner + a tool registry (each tool a small class with
`name`, `schema`, `run()`, `kind=silent|spoken`, `guard`). First wired recipe = **Fitness → workout**
(your pick — cleanest two-way brick). Behind an `LPCX_AGENT_CLEO` flag. Then point the **existing eval
harness** at it and compare to scripted Cleo.

**Nothing ships to prod in Phase 1.** It's a parallel engine we can measure against the real thing.

---

### Decisions that need Angel's eyes
1. **Silent/Spoken split** (§2) — is "do several back-of-house moves, then speak once" the right feel?
2. **Recipe-owned bricks** (§5) — the recipe's input contract *is* the brick. Agree, or do you want a
   central brick registry instead?
3. **Cage vs prompt for guards** (§6) — enforce the floor in code around the loop (my rec), vs trusting the
   persona prompt.
4. **Phase-1 scope** (§10) — fitness-only behind a flag, or wire two recipes to test tool-count scaling sooner?
