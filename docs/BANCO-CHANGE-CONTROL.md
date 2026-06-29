# Banco — Change Control & Sign-off (the "train" pipeline)

*Spec. 2026-06-29. A lightweight, shop-owned way to take a fix from "reported" to "live on the
real till" — with an evidence-backed sign-off at every gate, owned by the shop's own team, not
by Angel-in-a-chat. Grew out of the Hypercare loop. Dogfooded as a Felix feedback ticket.*

*Pairs with: BANCO-HYPERCARE-TRIAGE-COCKPIT.md · the `scripts/ops/deploy-banco.py` rail (BL-024).*

---

## THE ONE-LINE

Every change rides a **train** through gates — *dev → sandbox → staging/UAT → prod* — and **a human
signs off at each gate, with proof.** The proof is structured (who, when, pass/fail per check) and
rendered as an **immutable PDF certificate** stuck to the ticket. Keep it **one-tap simple** or it
becomes the Jira we killed.

## WHY (the problem it solves)

Today the "go" and the sign-offs happen in Angel's chat — Angel is the bottleneck for every fix.
This lifts the gates **into the app**, so the **shop's own team** (Felix + Ralph + Pam) drives
approve → test → sign off → promote. Angel (or a steward, or eventually an AI coder) is pulled in
**only to write the code.** Everything else the shop owns.

> The honest "missing middle": the app orchestrates the gates; it does **not** write the fix. The
> code step is still a human handoff. This makes the team *request-responsible for everything except
> the coding* — a big win, not full autonomy.

## THE TEAM (resolution group)

A per-shop **POS team** — e.g. Felix (manager/admin), Ralph (manager), Pam (cashier). Felix can:
- see **who's on the team, who's active, and their role** (who has a valid tester role on sandbox / staging);
- **assign** a ticket's test to someone (or take it himself);
- **reassign** ("Ralph's busy → Pam, you take staging" / bounce back to Felix).

Assignment = an `assigned_to` + a notification. Nothing heavier.

## THE GATES (the train)

1. **Report** → 💬 → auto-triaged into a clean ticket (existing Hypercare).
2. **Plan / Approve** → a plain-language fix plan; manager taps **👍 Approve** / 💬 Comment.
3. **Build (dev)** → a human writes the code (sandbox-first). *(Not automated.)*
4. **Sandbox gate** → "on sandbox at HH:MM, build `<sha>`, ready for your check" → **test + sign off.**
5. **Staging / UAT gate** → train rolls → "on staging at `<sha>`" → **assigned tester** tests + signs off.
6. **Prod** → safe deploy → **hypercare sign-off**: everyone involved is asked to confirm it's live & good.

At each gate the decision is: **push forward** / **send back to fix & redo** / **scrap it** (drop the
changes, leave it as it was). Comments allowed; the manager can edit/move/finalize.

## SIGN-OFF MECHANICS

A gate sign-off is **completing the test sheet** — not a blind "yep":
- **Mandatory fields:** tester **name** (required), **date/time** (auto-filled), **assigned-to**.
- **The checks:** the pre-filled, Lego-language checklist for *this* ticket (we already generate these),
  PASS/FAIL per item + notes, tips inline. Tab through it.
- **Quick-pass override** (for low-severity only): sometimes it's a glance, not a 30-min test. Allow a
  **two-tap** "✓ Reviewed — looks good, pass" + **name** + a confirm tick. It is **logged as an override**
  ("passed on review, full checklist not run, by <name>") so the shortcut is *visible*, not hidden.
  Override is **blocked for high-severity** tickets (see below) — those demand the real test.

## SEVERITY 1–10 (drives priority AND ceremony)

Every ticket carries a seriousness score (AI proposes, manager adjusts):
- **1–3 (trivial / cosmetic):** quick-pass override allowed; single sign-off; low priority.
- **4–7 (normal):** full checklist at each gate; standard train.
- **8–10 (foundational / all-hands, e.g. BL-024):** full test mandatory (no override), all involved
  sign off, top priority. *"All hands on deck."*

So the score tells everyone **what's urgent** *and* **how much rigor** the change needs.

## EVIDENCE — log = vault, PDF = certificate, hash = proof

The catch inside the catch: **a PDF is not actually tamper-proof** (any editor can change one). So:
- **The append-only activity log is the source of truth** — name, time, ✓/✗ per check, notes written
  to the log (already tamper-evident, and *structured* so the system can read the result).
- **The PDF is the certificate** — rendered *from* the log, attached to the ticket, the human "train ticket."
- **Hash-stamp the PDF** with a fingerprint of the results, so a doctored PDF won't match the log → the
  certificate is *provably* authentic. That's "can never be changed" — for real.
- Bonus: because results are structured (not a flat picture), the system can **scan the output** and
  recommend push / fix-redo / scrap. A PDF blob alone can't drive that.

## THE RAILS (so promotion is safe)

Owner-triggered deploys need bulletproof mechanics, regardless of how many people signed:
- **`deploy-banco.py`** (BL-024, shipped): checkout → **stamp the real SHA** → restart → health-wait.
- Promotion = **backup → deploy → smoke → auto-rollback on fail.** Sandbox-promote first; **prod-promote last.**
- Sign-offs gate the *decision*; the rails guarantee the *mechanism*.

## GUARDRAILS (don't break what's good)

1. **One-tap, or it's Jira.** Mandatory fields must feel like *finishing the test*, not paperwork. The
   PDF is a byproduct of doing the work, never a form to fill.
2. **No "all must sign" deadlock.** Ask everyone involved; let the **manager finalize** so a sick day
   doesn't freeze prod.
3. **Pam never sees the machinery.** Reporter view stays the simple loop. All gates/sign-offs live in the
   role-gated manager/owner Cockpit.

## PHASING

- **P1 — Board + approve + checklist:** Cockpit "Needs your call" lane; plain-language plan → Approve/Comment;
  after a human builds + deploys to sandbox, auto-generated checklist → **Felix drives the gates** (deploy
  still human). Removes most of Angel's bottleneck. *Severity score + quick-pass override land here.*
- **P2 — Gates + sign-off evidence:** staging/UAT gate, assign/reassign, the log→PDF certificate + hash,
  prod hypercare sign-off.
- **P3 — Safe one-tap auto-promote:** wire Approve/Promote to the rails (backup→deploy→smoke→rollback),
  sandbox first, **prod last.**

## OPEN QUESTIONS

- Prod sign-off: "all involved confirm" vs "manager finalizes after asking" (lean: ask-all, manager-finalizes).
- Where the tester role lives (reuse pos-cashier/manager, or a dedicated `tester` flag per env?).
- PDF generation on the device vs server (server = consistent; reuse the Puppeteer pipeline).

## STATUS

**Spec only — not built.** Requested *through Hypercare itself* as a Felix feedback ticket (dogfood).
First real brick already shipped: `deploy-banco.py` (BL-024). Build P1 next, sandbox-first.
