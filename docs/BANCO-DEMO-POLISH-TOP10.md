# Banco — Demo Polish: Top 10 + Bonus

The demo = the **first-sale-ever** story on the empty sandbox (recorded). Ranked by what
makes the *recording* look like a real shop and land emotionally — not by engineering size.
Most of the top ones are **config/data, not builds.** ⚡ = quick win · 🔨 = real build · ⟶ = need from Felix.

| # | Thing | Why it matters on camera | Effort |
|---|-------|--------------------------|--------|
| **1** | **Real Artemis Lucerne identity** on the **receipt + dashboard** | The receipt is the money shot, and right now it says **"Artemis Store – Zurich, Bahnhofstrasse 42, 8001 Zurich"** with a fake phone/email/VAT. The real shop is **Artemis GmbH, Murbacherstrasse 37, 6003 Luzern, 041 220 22 22, contact@artemisluzern.ch, since 1999.** Wrong city = toy. Right details = real. | ⚡ data (⟶ VAT no.) |
| **2** | **Artemis logo + brand colour** on login, dashboard, receipt | Makes it *his* shop, not "HelixPOS demo". One asset, placed in 3 spots. | ⚡ (⟶ logo file) |
| **3** | **Clean branded login screen** | It's the first frame of the video. Calm, branded, "Artemis" — sets the tone. | ⚡ small CSS |
| **4** | **The opening shot: empty shop** | Dashboard at CHF 0.00 / 0 sales / drawer closed = "before anything." Already clean; maybe one Day-One framing line. | ⚡ |
| **5** | **First-sale receipt: TXN-…-0001** | The emotional beat — the *first* number, clean layout, real tagline, "thank you". Ties to #1. | ⚡ (with #1) |
| **6** | **Born-once item shows its photo** in cart + catalogue | We just fixed the cashier photo; make sure the picture renders crisp as the cover (not 📦) on camera. | ✅ done — verify |
| **7** | **Loyalty beat** — member + points earned | Your prod test already showed *"@JJ BRONZE · +75 pts"* — a lovely human moment. Feature it: a member buys, points tick up. | ✅ works — stage it |
| **8** | **Cash drawer: open float → sell → close balanced** | The shift report (float 200 → expected 215 → counted 215 → **variance 0.00 balanced**) looked beautiful in your test. It's a *trust* beat — "the money is accounted." | ✅ works — stage it |
| **9** | **The treat touch** — "CBD Gummy 🎁 on the house" | Showed in your test. A warm, brand-true moment (the CRACK community vibe). Keep it in the script. | ✅ works |
| **10** | **No stutters** | A demo can't hiccup. Fix the small UX nits — e.g. you noted *"need a refresh to make the confirm go green"* after opening the drawer. Smooth > feature-rich on camera. | 🔨 small fixes |
| **Bonus** | **The narration / story** | The thing that turns a screen-recording into a *film*: the empty shop coming alive, the first sale ever, Felix's 25 years. We have `BANCO-DAY-ONE-RUN-SHEET.md` / `-VO-SCRIPT.md` — record the voice over the clean run. | 🔨 record |

---

## The honest shape of it
Items **1–5 are mostly config + one logo file** — a single focused "make it Artemis" pass and
the demo *looks* real instead of placeholder. **6–9 already work** — they just need to be
*staged* into the run (the right order of beats), not built. **10** is small smoothing. The
**bonus** (narration) is what makes it a story, not a screen-grab.

**If we only did three:** #1 (real receipt/identity), #2 (logo), #10 (no stutters). That trio
alone takes it from "dev demo" to "real shop." The rest is gravy that's mostly already cooked.

**Deferred (your call, leaving simple):** the item-detail view shows only the *cover* photo,
not a gallery carousel — you can load several, see one. Fine for the demo; noted, not doing.
