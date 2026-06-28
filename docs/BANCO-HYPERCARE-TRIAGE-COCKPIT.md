# Banco — Hypercare Triage Cockpit (spec / plan)

*2026-06-28. Angel's "brilliant idea", captured live. An AI-assisted feedback → backlog
pipeline + a cockpit, so a war-room hour of user feedback gets triaged, cleaned, scored and
queued automatically — and Angel just reviews + ships. The **secret weapon**: users never see
it; they only get a "your ticket is being addressed" notification.*

*Built on pieces we ALREADY have: 💬 feedback → `POST /pos/feedback` → Backlog board (BL numbers,
severity, screenshot, activities log) · BYO-brain `src/llm/run_llm` (Ollama local/Turbo) · vision
engine `src/services/vision.py` · cron infra on the box · 📊 Shop Pulse diagnostics.*

---

## The loop (one picture)

```
 War room (3 users on SANDBOX) ──💬──▶ Backlog ticket
   (messy title + desc + screenshot + auto metadata)
        │
        ▼  [cadence cron: Hypercare 15m / High 30m / Med 60m / Low daily — per ENV]
   AI TRIAGE (Ollama + vision):  read screenshot + text + metadata
        │   → rewrite into a CLEAN ticket (title, description, type, severity)
        │   → store as a NEW VERSION (never overwrite original)  ← dual-version audit
        │   → notify reporter: "we got it, addressing (~15m)"
        │   → notify Angel: Telegram + email
        ▼
   CONFIRM-BACK (optional): "here's how we understood it — confirm?" → user ✔ / tweak / reject-with-questions
        ▼
   COCKPIT (Angel): queue · original vs cleaned · SLA lifecycle · decide → ship (SHA)
        ▼
   SCORE: reporter gets points + the actual commit; SLA timer stops
```

## What we capture per ticket (grab everything)

Already: title, description, screenshot (data-URL), console/network breadcrumbs, browser/screen.
**Add:** the 📊 Shop Pulse snapshot at click-time — env, build SHA, sales count today, system
health, device/viewport, signed-in user. *The richer the metadata, the better the AI triage.*

## Dual-version (Angel's "verify the transcription")

Never overwrite the original. Store the AI-cleaned ticket as a **BacklogActivity**
(`actor=ai-triage`, `old_value=raw`, `new_value=cleaned`, `comment=model+confidence`). Free audit
trail + both versions side by side in the cockpit.

## SLA scorecard (lifecycle timestamps)

Per ticket, stamp: **opened → picked-up → assessed → packaged → shipped (SHA + commit)**, plus
the cadence tier it was under. Score = "closed within its SLA?" (15m / 30m / 60m). Shows how
fast we close + gives the reporter credit with the real commit. The cockpit aggregates it.

## Reporter scoring (skin in the game)

A user whose ticket becomes a shipped change earns **points** ("smart person helping build a
great product"), with the commit shown. Noise gets triaged down. Turns hypercare into a game.

## Notifications

- **To the reporter (in-app bell by their name):** on file → "BL-X opened [time], hypercare,
  ~15m"; on triage → "being addressed"; on confirm-request → "is this what you meant?"; on ship
  → "fixed in [commit] — +N points". Bell shows unread count; mark-all-read; paginated.
- **To Angel:** **Telegram** (@BigKingFisher, instant) + email the moment feedback lands.

## Cadence as a SETTING (per environment)

`Hypercare(15m) · High(30m) · Medium(60m) · Low(daily) · Off`, set **per env** (sandbox can run
Hypercare for a war-room hour while prod is Low). Default Hypercare; system may override.

## The cockpit (Angel's command center)

Log in anytime → "5 feedbacks · 2 assessed · 1 undecipherable · 2 open" + the board + original-vs-
cleaned + SLA lifecycle + points. Decide → ship (even straight to prod within the hour if online).

---

## Build phases (smallest-magic-first)

- **PoC-1 — the Triage Brain (build first).** A script: take ONE backlog ticket (messy title +
  desc + screenshot + metadata) → `run_llm` + vision → a clean ticket (title, description, type,
  severity, confidence) stored as a `BacklogActivity` (dual-version). Run on a real/seeded ticket;
  show messy-in / clean-out. *This is the wow.*
- **PoC-2 — Cron + cadence setting.** Per-env poller (Hypercare/High/Med/Low) that runs PoC-1 on
  new untriaged tickets; idempotent (tag `triaged`, no double-notify). Local Ollama.
- **PoC-3 — Cockpit + notifications + scorecard.** Dashboard (queue, dual versions, SLA lifecycle,
  points) + in-app reporter bell + confirm-back loop + Telegram/email to Angel.

## Guardrails

- **Secret weapon:** server-side only; users see notifications, never the cockpit.
- **Sandbox-first:** simulate hypercare in the sandbox (seed fake tickets, run the cron by hand).
- **Cheap brain:** local Ollama for triage (rewrite + one vision read); strip `<think>`.
- **Idempotent + auditable:** never re-triage; never overwrite the original; log every step.
- It ASSISTS, Angel DECIDES. Pairs [[banco-day-one-wishlist]] · BYO-brain `src/llm`.

---

*"This is revolutionary. Let's make it the sexiest, best thing ever. I can resolve tickets in
prod within the hour. Work with me on this, tiger." — Angel, 2026-06-28*
