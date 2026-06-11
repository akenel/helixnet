# La Piazza — Planned Maintenance Notice

**Window:** Nightly, **20:00–22:00 CEST** (daily). Tonight's work may finish sooner.
**Date drafted:** 2026-06-11
**Why tonight:** ship the Concierge grounding + stability fixes (the dup-record 500, fiction-grounding, mobile mic, language-following chips).

---

## Short (Telegram / chat / status)

> 🔧 **Heads-up:** La Piazza does light maintenance nightly between **20:00–22:00 CEST**. The site may
> briefly blink during that window while we ship fixes. Tonight we're rolling out Concierge
> improvements. Back to normal shortly — thanks for your patience. 🐺

## Shorter (one-line in-app banner)

> ⚙️ Scheduled maintenance 20:00–22:00 CEST — La Piazza may be briefly unavailable while we ship updates.

## Social (LinkedIn / X — build-in-public flavour)

> Shipping tonight: La Piazza's Concierge (Cleopatra) gets sharper — she stays grounded, the
> profile she builds stays honest, and the mic behaves on mobile. Quick maintenance window
> 20:00–22:00 CEST. Building in public, one fix at a time. 🐺 #buildinpublic

---

## Notes
- "Daily 20:00–22:00 CEST" = a standing nightly window so deploys never surprise a live visitor.
- Prod is currently ~31 files + a schema delta behind `main` — tonight's deploy is a **prod catch-up**,
  not a one-file poke (see resume note). Smoke after, roll back on any red.
- TODO (optional, not built): a config/env-driven site banner so this notice can be toggled on/off
  without a code deploy each night.
