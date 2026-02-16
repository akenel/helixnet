# SESSION STATE - February 17, 2026

*Last Updated: Mon Feb 17, 2026 ~12:00am - PuntaTipa Room 101, Trapani. EP4 on YouTube. Anne onboarding at 10:30 CET.*

---

## TODAY'S PLAN (Mon Feb 17)

### 10:30 CET -- Anne Onboarding Meeting
- Anne is the new human tester for HelixNet
- Needs: test account, orientation, testing checklist
- Good opportunity to document the testing workflow properly

---

## YESTERDAY'S WINS (Sun Feb 16)

1. **CT EP4 ON YOUTUBE** -- https://youtu.be/e9bJpoSyOZU -- "The Workshop Floor" - appointments, walk-in, bay timeline, 1:38 runtime
2. **CT EP3 ON YOUTUBE** -- https://youtu.be/L9g4MBRDr6I -- "The Full Lifecycle" - 3 roles, 8 workflow steps, 4:18 runtime
3. **Wipro SAP PI/PO contract** -- RTR signed, updated CV submitted to Cholleti (EUR 320/day, 100% remote, Czechia)
4. **i18n system complete** -- Full English mode via `?lang=en` across all 14 Camper templates
5. **Video Production SOP updated** -- Tags file now mandatory in YouTube kit

---

## CAMPER & TOUR VIDEO SERIES

| EP | Title | Duration | Status | YouTube |
|----|-------|----------|--------|---------|
| 1 | First Impressions | 2:33 | FINAL | Published |
| 2 | Quote to Invoice | 3:00 | FINAL | Published |
| 3 | The Full Lifecycle | 4:18 | FINAL | [YouTube](https://youtu.be/L9g4MBRDr6I) |
| 4 | The Workshop Floor | 1:38 | FINAL | [YouTube](https://youtu.be/e9bJpoSyOZU) |

### Known Issue: Appointment Seed Data
- Sophie Dupont and Tourist walk-in appointments don't appear after `make up`
- Seeding code uses `today = date.today()` which should work
- Possibly a timing issue with container startup vs seeding execution
- EP4 worked around this with walk-in creation fallback
- **TODO:** Investigate and fix before any future appointment demos

---

## WIPRO SAP PI/PO CONTRACT

**Status:** RTR signed, CV submitted, waiting for interview
**Role:** SAP PI/PO Development Lead / Architect
**Client:** Wipro, Czechia (100% Remote)
**Rate:** EUR 320/day all-inclusive
**Recruiter:** Cholleti (WiseStep / Avance Services)
**CV:** `/home/angel/Documents/2026 KENEL CV Infos/CV_Angelo_Kenel_WIPRO.pdf`
**Availability:** Immediate, anytime with 1 day notice

**Plan:** Work 9-5 CET on Wipro contract, HelixNet in off-hours. Set boundary early for working hours.

---

## NEXT UP (Priority Order)

### 1. Anne Onboarding (TODAY 10:30 CET)
- Test account setup, orientation, testing checklist
- Document the testing workflow

### 2. Fix Appointment Seed Data
- Sophie + Tourist not appearing on appointments page
- Need to debug seeding service timing

### 3. KC Video Series Voiceovers
- EP5-EP8 have silent videos ready, need voiceover
- Pipeline proven with EP4 (Telegram voice messages, Whisper, ffmpeg)

---

## KC VIDEO SERIES

| EP | Title | Duration | Video | Voice | YouTube |
|----|-------|----------|-------|-------|---------|
| 4 | Keys to the Kingdom | 2:32 | FINAL | VOICED | [YouTube](https://youtu.be/_ap7-hgtC9o) |
| 5 | RBAC Deep Dive | 3:19 | FINAL | TODO | -- |
| 6 | Client Architecture | 2:30 | FINAL | TODO | -- |
| 7 | Authentication Flows | 2:35 | FINAL | TODO | -- |
| 8 | Multi-Tenant Platform | 2:30 | FINAL | TODO | -- |

---

## AXA INSURANCE CLAIM

**Claim:** 22.831.735/0001
**Submit docs to:** schaden@axa.ch
**Status:** Invoices submitted (EUR 2,405.50), waiting for response
**Water damage:** EUR 5,000-10,000 est., pending preventivo from C&T

---

## UFA POSTCARDS - CLIENT STATUS

| # | Client | Status |
|---|--------|--------|
| 1 | Color Clean | Delivered, needs detailed feedback |
| 2 | Pizza Planet | Delivered, done for now |
| 3 | Marghe Trapani | PDFs done, not delivered |

---

## KEY CONTACTS

| Who | Details |
|-----|---------|
| **Cholleti (Wipro recruiter)** | WiseStep / Avance Services |
| **Camper & Tour** | Sebastiano/Nino, Via F. Culcasi 4, Trapani |
| **AXA** | schaden@axa.ch, Claim 22.831.735/0001 |
| **Anne** | New tester, onboarding 10:30 CET today |

---

## VIDEO PRODUCTION LESSONS (Feb 16)

- **No `<` `>` or `->` in YouTube descriptions** -- YouTube strips angled brackets
- **Re-encode when trimming** -- `-c:v copy` skips keyframes, can miss intro cards
- **Alpine.js @click rows** -- don't click in Puppeteer, navigate by URL instead
- **Always include TAGS file** in YouTube kit -- added to SOP
- **SOP updated:** `videos/keycloak/VIDEO-PRODUCTION-SOP.md`

---

*This file is Tigs' working memory. Update it often.*
*"The shop floor shouldn't need a spreadsheet." -- CT EP4 tagline*
*"Don't fight the rate before you have the offer." -- Wipro lesson*
*"4 Episodes. 1 System. Ready for Production."*
