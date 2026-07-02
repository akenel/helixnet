# ✉ Postino — the postcard CRM

*"The postcard is the handshake."*

Postino is Angel's lead-tracking cockpit for postcard campaigns. It is **not** Banco,
La Piazza, or Bottega — it's a standalone CRM. Clients (Isotto, Camper & Tour, …) live
inside it as **campaigns**; the CRM itself belongs to no single client.

## Run it (one command)

```bash
crm/start.sh
```

First run builds its own `.venv` and installs deps. Then open **http://localhost:8900**
on the laptop, or the phone URL it prints (same wifi). Change the port with `PORT=9001 crm/start.sh`.

## What's inside

- **Board** — a pipeline: To Contact → Contacted → Postcard Sent → Replied → Won.
  Cards sorted by qualify score; badges for tier (A/B) and manager.
- **All Leads** — filterable table (tier, persona, stage, city).
- **Lead detail** — edit every field, log each touch (call/email/postcard/visit/note),
  move the pipeline stage. Logging a postcard auto-stamps the date and advances the stage.
- **Add** — new leads by hand.
- **Export** — download the whole book as CSV any time (your backup).

## Data

- One SQLite file: `crm/postino.db` (gitignored — it's your private book).
- Seeded on first launch from `docs/business/headshop-crm/headshop-leads.csv`
  (the 20 qualified Swiss head-shops). Re-seeding is idempotent.
- The qualification rubric lives in `docs/business/headshop-crm/QUALIFICATION.md`.

## The pipeline stages

`to_contact → contacted → postcard_sent → replied → won` (plus `lost`, `dropped`).

## Roadmap (not built yet)

- Enrichment recipe hook (`run_llm`) to auto-qualify 100+ shops into new leads.
- Print postcards/labels for a stage straight from the board (reuse the Puppeteer pipeline).
- Multiple campaigns in the UI (model already supports it).
