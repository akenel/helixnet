# Banco POS — In-App Feedback → Backlog Board · Human Test Sheet

**Feature:** A 💬 Feedback button on every till screen. A cashier reports a bug/idea
live; it files as a real item on the **same `/backlog` board** the La Piazza button feeds.
**Env to test:** https://staging-banco.lapiazza.app
**Login:** felix / helix_pass
**Status:** machine-green on local + staging (5 API + 2 E2E). **NOT on prod yet — needs your PASS.**

---

## What got built (the tie-in)

- Ported La Piazza's exact 💬 feedback card into the POS shared layout (`pos/base.html`)
  → it shows on **every** POS screen once logged in, sitting just above the status bar.
- POS logs in against a *different* Keycloak realm than the La Piazza feedback endpoint,
  so a **POS-native `POST /api/v1/pos/feedback`** writes the **same `BacklogItemModel`** —
  tagged `banco,feedback,pos,{kind}`, attributed to the cashier. Same board, same BL numbers.
- 🐛 Bug → filed as a **bug_fix** item; 💡 Idea / 💬 Other → **business_ops**.
- **📸 Screenshot** — a "Capture this screen" button grabs the screen *behind* the card
  (html2canvas), downscaled to a small JPEG, shown as a thumbnail you can remove/recapture.
- **🖥️ Auto-collected context** — every report silently carries which screen, where they
  came from, browser/UA, viewport, screen size, pixel ratio, locale, timezone, online,
  client time, POS build. Folded into the item description so it's right there on the board.
- The screenshot shows **on the backlog board** (item detail → 📸 Screenshot, click = full size).

---

## Click-to-test

### 1 · The button shows when logged in
- [ ] Log in (felix). A red **💬 Feedback** button sits bottom-right, above the System OK bar.
- [ ] Move around: New Sale, Catalog, Reports, Close Shift. The button is on **every** screen.
- [ ] (Pre-login, on the Staff Login page, the button is **hidden** — correct.)

### 2 · File a bug with a screenshot
- [ ] Click 💬 Feedback. A card opens: 🐛 Bug / 💡 Idea / 💬 Other (Bug preselected) + title + details.
- [ ] Note the small grey **"Auto-attached: /pos/… · platform · viewport"** line — that's the context.
- [ ] Click **📸 Capture this screen** → after a moment a **thumbnail** appears (button → "Recapture").
      The ✕ on the thumbnail removes it; Recapture replaces it.
- [ ] Type a title (e.g. "Receipt printer skipped a line") + detail → **Send**.
- [ ] You see **"Filed as BL-XXX 📸 — thank you! 🐺"** (the 📸 confirms the shot went) and it closes.
- [ ] **BL-XXX is a link** → opens the `/backlog` board in a new tab.

### 3 · It landed on the board — with the screenshot + context
> View the board at **https://staging-banco.lapiazza.app/backlog** (log in as a QA/manager user).
- [ ] The new **BL-XXX** is there: your title, type **Bug**, filed by **felix**.
- [ ] Open it → the description shows a **🖥️ Context (auto-collected)** block: Screen, Browser,
      Viewport, etc. — exactly where they were and what they were running.
- [ ] A **📸 Screenshot** section shows the captured image. **Click it → opens full size** in a new tab.
- [ ] File a **💡 Idea** without a screenshot → shows as a normal item (Business Ops), no 📸 section.

### 4 · Guards
- [ ] Open the card, type just "x" (1 char) → **Send** → red "Give it a short title (3+ characters)".
      Nothing is filed.
- [ ] Cancel / click outside the card → it closes cleanly, no dead-end.

### 5 · No session damage (the thing that bit us before)
- [ ] After filing feedback you're **still logged in** — no bounce to the Keycloak login screen,
      cart/where-you-were is intact.

---

## ★ Verdict
- [ ] **PASS** — ship to prod (`banco.lapiazza.app`).
- [ ] Notes / nits: ________________________________________________

> On PASS I deploy the same two files to prod, smoke it, and confirm.
> Any feedback you file on staging is a **real** row on the shared board — tell me and
> I'll clear test rows, or just title them "TEST" so they're easy to spot.
