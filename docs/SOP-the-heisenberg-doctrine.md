# SOP — The Heisenberg Doctrine: Stable Core, Flexible Extension

*Doctrine, June 10 2026. Born from a master's answer in the Legends room (Werner Heisenberg, asked
by a SAP integration consultant about reconciling data consistency with rapid innovation). It read
like SAP advice; it's actually how La Piazza is built. So we make it law.*

---

## 1. What the master said (the summary)

> **Complementarity.** Two aspects of a system — *consistency* (exactness, things staying fixed)
> and *flexibility* (the freedom to change) — **cannot both be maximized at once.** The quantitative
> shape of it:
>
> **Δconsistency × Δflexibility ≥ constant**
>
> Tighten consistency (a narrow, precise contract) and you must accept *less* agility. Open the
> system for rapid change and you must accept *looser* consistency. The "constant" is set by the
> intrinsic coupling of the parts. **Observing/measuring one disturbs the other.**

His prescription was a **two-stage process**, and *that* is the part we steal:

1. **Define a stable "core" contract** — the minimal set of fields/rules that *must* remain invariant
   for correctness (financial keys, inventory IDs). Few, frozen, measured with high precision. Narrow
   consistency window.
2. **Layer an "extension" envelope** around the core — optional, format, experimental fields. Here you
   *deliberately allow* flexibility; mismatches are reconciled later by a downstream **adapter**.

> **The one small action he gave:** take a single interface, extract the *minimal* set of fields
> absolutely required for business correctness, freeze them in a formal schema, document them as the
> *core contract* — and push everything else into a separate "extension" structure handled by an adapter.
> A concrete foothold for balancing consistency and flexibility.

---

## 2. Why this is doctrine for us

We have been *unknowingly obeying complementarity all day.* Name it, and every decision gets sharper.

| Our thing | The **stable core** (precise, frozen) | The **flexible extension** (reconciled later) |
|---|---|---|
| **Environments** | **CODE** — staging == prod, byte-identical (`scripts/env-parity.sh`) | **DATA + CONFIG** — different DBs, env vars, model targets (allowed, expected) |
| **Identity / age** | **16+ AND Terms, server-enforced**; later: birth date, verified ID (*control data*) | Self-declared until verified; the imagination-machine persona play |
| **Artifacts** | The immutable record: **serial № + watermark + owner + timestamp** | Reading-mode enrichment, edits, embeds, re-feeds to other masters |
| **Distribution** | **PROD** artifacts: precise, no watermark, **distributable** | **STAGING** artifacts: watermarked "not distributable", experimental |
| **Any new feature** | The minimal schema that *must* be correct, frozen up front | Everything else — an extension envelope, adapted later |

The lesson the master hands us: **don't try to make everything both precise and flexible — that
violates complementarity and you get neither.** Decide, per thing, which half it is.

---

## 3. The operating rule (do this, every time)

**Before building anything, name the two halves out loud:**

1. **The core** — what *must* be invariant and exactly right? (legal gates, identity control-data,
   schema keys, the deployed code, the prod artifact of record). → **Freeze it as a contract. Enforce
   it server-side. Measure it with precision. Change it rarely and deliberately.**
2. **The extension** — what *should* stay free to move? (AI outputs, experiments, staging, enrichment,
   format, the imagination). → **Let it flow. Reconcile to the core later via an adapter. Never let
   periphery churn force a change to the core.**

If you find yourself fighting to keep one thing *both* perfectly consistent *and* perfectly flexible —
**stop.** That's the complementarity wall. Split it into a core + an extension instead.

> **"Precision in one measurement costs precision in another."** — Heisenberg
> **"If one seal fails, check all the seals."** — the seal-inspection lesson (same family: find the
> invariant, then audit everything that shares its failure mode).

---

## 4. The standing checklist (folds into the deploy SOP)

- [ ] **Core named + frozen?** The must-be-correct fields are a documented contract, server-enforced.
- [ ] **Extension named?** The flexible parts are explicitly the periphery — not accidental core.
- [ ] **Adapter, not core-edit?** Periphery reconciles to the core downstream; the core didn't move to chase it.
- [ ] **Consistency boundary visible?** staging = watermarked/experimental; prod = precise/distributable.
- [ ] **Parity holds?** Code (core) identical across envs; only data/config (periphery) differs (`env-parity.sh`).

*This doctrine governs the WoW (branch → staging → human-green → merge → gated prod) and the CI gate.
The core is what the gate protects; the extension is what we let people play in. — Tig*
