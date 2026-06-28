# Banco — Hypercare Test Samples (sandbox war-room fodder)

*2026-06-28. Real, known issues/ideas — NOT made-up nonsense. File these as Pam or Felix on
the **sandbox** (https://sandbox-banco.lapiazza.app) via the 💬 button to exercise the whole
loop: file → AI triages → bell → "did we get it right?" → (fix) → done → confirm.*

**How to use:** sign in (pam/helix_pass or felix/helix_pass), open the screen named in “where”,
tap 💬, and type the **“what to type”** text *exactly as written* (messy on purpose — the AI cleans
it). Then watch it appear, triaged, on `/pos/hypercare` (Felix) and in your bell + `/pos/my-tickets`.

Each row is REAL: the “what we actually know” column is the answer we'd act on when we fix it.

---

## 🟢 Quick wins — file these first (we can actually FIX them fast → demo the full done-loop)

| # | Who | Where | What to type (messy, like a real user) | Type | What we actually know (the fix) |
|---|-----|-------|----------------------------------------|------|---------------------------------|
| 1 | Pam | Catalog (phone) | `the little chat circle covers the last item when i scroll cant tap it` | bug | The floating 💬 FAB overlaps the bottom of mobile lists. Add bottom padding / nudge the FAB. **~10 min.** |
| 2 | Pam | Cart / Checkout | `i typed 100 fags by mistake and it let me it was like 8000 chf gave me a fright` | bug | No max-quantity guard exists. Add a sane per-line cap + confirm above N. **~20 min.** |
| 3 | Felix | Customers | `i can see a customer but i cant click in to see what they bought over time` | idea | The `/customers/{id}/summary` endpoint already EXISTS — only the UI screen is missing. **Wire the view.** |
| 4 | Pam | New Sale | `when someone buys 6 waters i scan each one 6 times can i just put a number` | idea | Add a quantity stepper / “×N” on a line instead of re-scanning. **Medium.** |

## 🟡 Real bugs / rough edges

| # | Who | Where | What to type | Type | What we actually know |
|---|-----|-------|--------------|------|------------------------|
| 5 | Pam | Receipt | `the bottom of the reciept with the tax bit gets cut off on the small printer` | bug | Thermal print layout clips the VAT footer. Real print-CSS issue (we have a fiscal sample to match). |
| 6 | Pam | New Sale | `i keep forgetting to flip to takeaway and then the tax is wrong, can it remember` | idea | Dine-in/takeaway toggle doesn't persist → wrong VAT (8.1 vs 2.6). Make it sticky + louder. |
| 7 | Felix | Closeout | `end of night sometimes the close button looks greyed and i cant tap it` | bug | Closeout button disabled-state / tap target at end of day. Reproduce + fix the guard. |

## 🔵 Owner ideas / nice-to-haves (bigger — good for the “go for it?” decision demo)

| # | Who | Where | What to type | Type | What we actually know |
|---|-----|-------|--------------|------|------------------------|
| 8 | Felix | Reports | `can the categories on the sales report be a little bar chart not just numbers` | idea | Category bar chart on Product Sales (you asked for this before). Data's already there. |
| 9 | Felix | Reports | `i want to download the days sales to excel for my accountant not just on screen` | idea | XLSX export — not built (would use openpyxl). CSV exists today; Excel is the ask. |
| 10 | Felix | Catalog | `the whole thing is in english my part time girl only reads german can we switch` | idea | English-only (`lang="en"`, no i18n). German is a real go-live ask. Big — but real. |

### 🎁 Spares (in the back pocket)
- **Felix · Pricing:** `could i do a buy 5 get the 6th cheaper deal for regulars` → tiered pricing (not supported today; “seems difficult” — honest “not yet”).
- **Felix · any screen:** `if the wifi blips for a sec mid sale do i lose it? happened once and i panicked` → offline outbox (known P2 go-live blocker).
- **Pam · Scan:** `some loose herbs have no barcode, scanning a printed sheet would be faster than searching` → BL-97 house scan sheet.

---

## The loop you're testing (what works NOW vs what's next)

**Works now (file these and watch):**
1. File via 💬 → ticket created.
2. AI triages (auto on the cadence cron, or Felix taps **Run AI triage now** on `/pos/hypercare`).
3. Reporter's **bell** rings: “🛠️ We're on it”.
4. Reporter opens **/pos/my-tickets** → journey stepper + **“Did we get it right?”** → confirms or adds a note.

**Next increment (so the demo is whole):** the **“it's fixed — please confirm”** half.
When we move a ticket to Done, the reporter gets a *second* notification (“✅ Fixed — please check
& confirm”), and Pam/Felix logs in, checks it, and **closes their own ticket**. That closes the
full circle you described. *(Building this next.)*

> Pick 2–3 quick wins (#1, #2, #3) to file first — those are ones we can actually turn around fast,
> so you see file → triage → bell → confirm → fix → done → confirm end to end.
