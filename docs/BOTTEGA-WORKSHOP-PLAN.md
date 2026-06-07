# Bottega — The Dark Workshop (Build Plan)

> *La Piazza is the bright square where you show your work. Bottega is the dark workshop
> behind it where the work gets done.* A mirror of the marketplace — member identity,
> history, notifications, messages, teams — but built for **making**, not browsing.

**Lean and mean now:** one Bottega environment (`bottega.lapiazza.app`, its own La Piazza
realm). Staging-Bottega → prod-Bottega is a *later* luxury — noted, not built. Every block
ships gated-on-dev, reversible, prod stays 200.

---

## The Spine — one event stream

Everything in the workshop is an **event** on one table (`bottega_sessions`, already live —
we extend, not multiply). History, archive, notifications, feedback, recipe-runs all write
here. **One spine = one Grafana source = less to maintain.**

```
bottega_sessions (the spine)
  username · slug(kind) · title · inputs(JSON) · output(JSON) · tags · version · parent_id · created_at
  kinds: blueprint-archive · recipe-run · profile-built · avatar-changed ·
         account-created · notification · message · feedback
```

Why one table: the member's *history*, their *archive*, their *notifications* and their
*Grafana charts* are all just queries over this stream with different filters. Build the
spine once; everything else is a view.

---

## Blocks

| # | Block | What | State |
|---|-------|------|-------|
| **A** | **Blueprint Archive + clue-scan** | Onboarding input (CV *or* description) archived with scanned clues — emails, phones, links, skills, categories. | ✅ **DONE / live** |
| **B** | **Member History** | The whole stream as a sortable, **searchable** timeline. "My Blueprint" becomes the history hub. Events logged: account-created, profile-built, avatar-changed, session-saved, recipe-run, archive. | next |
| **C** | **Notifications** | Bell + unread count + feed. Welcome, credits granted, job done, system. Written as `notification` events. | planned |
| **D** | **Messages** | System→member first (Tigs talks to you), member↔member later. `message` events. | planned |
| **E** | **Grafana — the works** | Off the spine + ledger: platform (signups/day, active members, recipes run, top recipes, credit flow) and per-member activity. Reuses `scripts/lp_grafana_setup.py`. | planned |
| **F** | **Teams** | Keycloak groups → shared Bottega/resources, team roster. Mirror of La Piazza groups. | planned |
| **G** | **Backlog / Feedback in Bottega** | A feedback/issue widget *inside* the workshop that files into the existing Backlog (BL) module — log issues, fixes, track changes. The seatback feature, built in. | ✅ **DONE** — floating widget in the shared nav (logged-in members only) → `POST /api/v1/compute/bottega/feedback` → real `BacklogItemModel` on `/backlog` (bug→`bug_fix`, idea/other→`business_ops`, tagged `bottega,feedback,*`). No new table — files into the existing spine. |

---

## Sequencing (be water)

1. **A ✅** — the spine + first event (archive).
2. **B** — make the spine *visible*: history view, search + sort. (Highest value next: the member sees their journey, and it's the surface C/D/G hang off.)
3. **C + D** — notifications + messages (same spine, new event kinds + a bell/inbox UI).
4. **G** — feedback widget → BL (small, leans on the existing backlog module).
5. **E** — Grafana once there's a stream worth charting.
6. **F** — Teams (biggest; needs KC groups + shared-resource model). Last.

---

## Principles
- **One spine, many views** — don't fork a table per feature.
- **Reversible + gated** — dev first (smoke + console-sweep), pull+restart, verify prod 200.
- **Lean now** — no staging-Bottega yet; no premature K8s; one box handles it.
- **No shortcuts** — full libraries, real fixes, BL the rest. *If one seal fails, check all the seals.*
- **The clues are gold** — names, emails, numbers, skills, connections feed the coaching/Legend Journey later.

---
*Started 2026-06-06. Block A live. Riding shotgun: Angel. Driving: Tigs. "Be water, my friend."*
