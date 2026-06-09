# SOP — Interactive Task Sheets (the standard hand-off format)

*Angel's standing preference (2026-06-09). Whenever Tigs hands Angel a task to do — record a video,
run a workout, cook a meal, test a flow, evaluate options — deliver it as an **interactive HTML
work-sheet**, not a wall of text. Works on mobile AND desktop. It's the workout-sheet DNA, generalised.*

## The shape (every task sheet has these)
1. **Step-by-step, one step at a time** — click-by-click / beat-by-beat. Rarely parallel; we're not
   multitaskers. Each step is its own card.
2. **A checkbox per step** — tick it off, it turns green, a running "X / N done" counter.
3. **An editable field where it helps** — e.g., the suggested script line in a textarea Angel can
   reword in his own voice. Pre-filled with Tigs' draft; his to change.
4. **A comment/notes box on every step** — his work-area: "too long here," a phone number, a memo, an
   idea. Like a line in his diary.
5. **An overall notes box** at the bottom — the catch-all diary box.
6. **Video tips / example links where useful** — like the workout how-to clips ("here's how to do a
   push-up"). Show, don't just tell. An embedded video or a link per step when it lifts the task.
7. **Saves on the device** (localStorage) — close it, come back, it's all there.
8. **"Copy my notes back to Tigs"** — one button that bundles his checks + edits + notes into text he
   pastes into the chat. That's the feedback loop.

## The loop (drafts → working form)
Draft 1 (Tigs) → Angel works it + copies notes back → **draft 2** (Tigs adjusts) → draft 3 → … until
it's a working form Angel can interactively use. Never assume draft 1 is final; always leave the box
open for him to type, save, and return.

## Why
Same as any real task — video, workout, cooking, deploy: **one step at a time, check it off, leave
room to scribble.** It makes Angel's life easy AND gives Tigs the exact feedback to improve. Pair with
the workout-sheet rules (native inputs, no-JS-required fallback, Print→PDF).

## Exemplars
- `docs/business/marketing/ep01-directors-cut.html` — video + timed beats + editable lines + notes + copy-back.
- `docs/business/marketing/music-site-finder.html` — options + eval boxes + ratings + copy-back.
- `docs/blueprint/*workout*` — the original (checkboxes + ratings + YouTube how-tos + comment boxes).
