# SESSION STATE - February 11, 2026

*Last Updated: Tue Feb 11, 2026 ~1:00am - EP4 + EP5 + EP6 + EP7 recorded at McDonald's Trapani*

---

## KC VIDEO SERIES - EP4 + EP5 + EP6 + EP7 DONE

**Method:** Puppeteer (non-headless) + OBS Screen Capture + ffmpeg post-production
**SOP:** `videos/keycloak/VIDEO-PRODUCTION-SOP.md`
**Location:** McDonald's Trapani, invented the pipeline over McFlurries

| EP | Title | Duration | Status | File |
|----|-------|----------|--------|------|
| 4 | Keys to the Kingdom | 2:32 | FINAL (intro+content+outro) | `EP4-keys-to-the-kingdom/KC-EP4-Keys-to-the-Kingdom-FINAL.mp4` |
| 5 | RBAC Deep Dive | 3:19 | FINAL (intro+content+outro) | `EP5-rbac-deep-dive/KC-EP5-RBAC-Deep-Dive-FINAL.mp4` |
| 6 | Client Architecture | 2:30 | FINAL (intro+content+outro) | `EP6-client-architecture/KC-EP6-Client-Architecture-FINAL.mp4` |
| 7 | Authentication Flows | 2:35 | FINAL (intro+content+outro) | `EP7-authentication-flows/KC-EP7-Authentication-Flows-FINAL.mp4` |
| 8 | Multi-Tenant Platform | TBD | Planned | - |

**EP4 content:** Login, master dashboard, realm dropdown (6 realms), POS users, role mapping, clients, realm tour
**EP5 content:** 5 custom RBAC roles, role details (admin/cashier/manager), users in role, 4 user role mappings (Pam/Ralph/Michael/Felix), client scopes (10 OIDC), auth flows (7), realm settings
**EP6 content:** 3 OIDC clients (web/mobile/service), public vs confidential, redirect URIs, custom scheme callback, client secret + credentials, service account roles, per-client scopes vs realm scopes
**EP7 content:** 7 built-in auth flows (browser/direct grant/registration/reset credentials/first broker login/docker auth/clients), execution steps with requirement levels, 11 required actions, 5 policy types

**MP4s:** Local only (GDrive, not git). Voiceover to be added later.

**Pipeline:** Script -> Dry run (headless) -> OBS Record -> ffmpeg trim+strip audio -> Puppeteer screenshot intro/outro -> ffmpeg stitch -> FINAL

---

## AXA INSURANCE CLAIM

**Claim:** 22.831.735/0001
**Adjuster:** Iwan Zgraggen (forwarded case -- new English-speaking case worker TBD)

### Timeline
- **Late Jan/Early Feb:** Van at Camper & Tour for stove repair, Angel at PuntaTipa Hotel
- **During smoke cleanup:** Technicians cleaned every millimeter, saw ceiling bubbles, said nothing
- **Thu Feb 5:** Stove DONE, left hotel, living in van again
- **Fri Feb 6:** Returned for backup camera, insisted on window inspection, water damage discovered
- **Sat Feb 8 2:02am:** Email SENT to Iwan Zgraggen - stove complete + hotel expenses + new water damage
- **Mon Feb 9 ~10:30am:** Iwan replied -- case forwarded to English-speaking colleague, photos + email attached to file
- **Mon Feb 9 ~10:45am:** Reply SENT to Iwan -- asked for new case worker name/email/timeline, flagged both fire + water damage

### Costs to Claim
| Item | Amount | Status |
|------|--------|--------|
| Camper & Tour (stove + smoke clean) | EUR 1,010 | PAID |
| PuntaTipa Hotel (13 nights B&B) | EUR 1,395.50 | PAID, invoice collected |
| Water damage (roof/seals) | EUR 5,000-10,000 est. | Pending assessment |
| **Total so far** | **EUR 2,405.50 + TBD** | |

### Waiting For (from AXA)
1. New case worker to introduce themselves (name, email, phone)
2. Where to submit receipts (hotel invoice + stove repair)
3. Same claim or new claim for water damage?
4. Do they need an inspector to come to Sicily?

---

## SYLVIE

- Back in Switzerland, no internet at home, no phone
- Went to KFN, paid the bill - should have internet back Monday
- Looking for internet cafe to send messages
- She knows about roof damage (already slipped out) - no stress
- Major dental surgery coming (all teeth removed, implants)
- Sent Batch 2 of Mattenweg bills (11 bills, all PAID by Angel on Feb 9)

---

## HELIXNET VIDEOS - ALL 3 LIVE (YouTube)

| # | Title | Link |
|---|-------|------|
| 1 | The Stack | https://youtu.be/P2k63CXZwBg |
| 2 | HTTPS in Development | https://youtu.be/9E2tBu1wIkM |
| 3 | Health Checks & Self-Healing | https://youtu.be/V4QbXM1_fLQ |

**Playlist:** https://www.youtube.com/playlist?list=PLrRlgzUrqK1-rz6EhQIn65h-mJb409cNA

---

## DHARMA LIFE / VYOMA

- **Message sent** to Rajiv & Venky with all 3 video links
- **Waiting for:** Vyoma platform access (Rajiv to respond on WhatsApp)
- **Goal:** PoC connecting Vyoma SOP-to-workflow tool with HelixNet
- **Meeting needed:** Rajiv, Venky, Karthick - pending Rajiv response
- **Venki:** +971 56 999 9181 (Telegram)

---

## UFA POSTCARDS

| # | Client | Status | Next Step |
|---|--------|--------|-----------|
| 1 | **Pizza Planet** | **PDFs DONE (real photos + address confirmed)** | Show Ciccio, print at ISOTTO |
| 2 | **Marghe Trapani** | **PDFs DONE** | Show owner, get approval, print at ISOTTO |
| 3 | **Color Clean** | **PDFs DONE** | Show owner (TOP PRIORITY client), cheap test print first, then ISOTTO |
| 4 | Piccolo Bistratto | Pipeline | Create card + back side, 8 pics needed |

### Print Strategy
1. Cheap test print at digital photo shop first (verify colors, QR, alignment)
2. Once verified, ISOTTO for real color postcard batch
3. Color Clean = top priority real customer

---

## CAMPER & TOUR STATUS

- **Camera radio adapter part:** Expected Tue or Wed (checked Mon morning)
- **Nino will contact via Telegram** when part arrives
- **When part arrives:** Install camera + remove back window to assess roof damage + write preventivo
- **Loaner camper:** Camper & Tour will provide small camper during repairs
- **Gym 4U:** 30-day membership renewed -- shower/toilet/training backup

---

## PENDING ACTIONS

### Done Tue Feb 10 / Wed Feb 11
- [x] KC EP4 recorded, trimmed, stitched (Keys to the Kingdom - 2:32)
- [x] KC EP5 recorded, trimmed, stitched (RBAC Deep Dive - 3:19)
- [x] KC EP6 recorded, trimmed, stitched (Client Architecture - 2:30)
- [x] Video Production SOP written and committed
- [x] Video pipeline invented (Puppeteer + OBS + ffmpeg)
- [x] TZLA Whisper transcript analyzed (Zish/Visionary Life Hacks)
- [x] EP4 folder structure created with intro/outro HTML + voiceover script
- [x] EP5 folder structure created with intro/outro HTML + voiceover script
- [x] EP6 folder structure created with intro/outro HTML + voiceover script
- [x] 3 episodes in one night (8:21 total runtime)
- [x] KC EP7 recorded, trimmed, stitched (Authentication Flows - 2:35)
- [x] 4 episodes in one night (10:56 total runtime)

### Wednesday+
- [ ] Upload hotel invoice to Google Drive (digital backup)
- [ ] Wait for AXA new case worker introduction
- [ ] Wait for Nino (Telegram -- camera part)
- [ ] Wait for Rajiv/Vyoma response
- [ ] Show Color Clean owner her cards (when passing Via Virgilio)
- [ ] Cheap test print at digital photo shop (Color Clean first)
- [ ] ISOTTO color print run (Color Clean + Pizza Planet + Marghe)
- [ ] Piccolo Bistratto: design card, prepare 8 images
- [ ] EP4+EP5+EP6+EP7 MP4s to Google Drive
- [ ] Record voiceover for EP4, EP5, EP6, and EP7
- [x] EP7 Authentication Flows -- DONE
- [ ] EP8 Multi-Tenant Platform (next KC video)

---

## KEY CONTACTS

| Who | Details |
|-----|---------|
| **Camper & Tour** | Sebastiano/Nino, Via F. Culcasi 4, Trapani, +39 328 684 4546 |
| **AXA** | Iwan Zgraggen (forwarded), Claim 22.831.735/0001, new case worker TBD |
| **Vyoma/Dharma** | Venki +971 56 999 9181 (Telegram) |
| **Marghe Trapani** | Via Garibaldi 52, Trapani, 352 088 2833, Google review posted |
| **Color Clean** | Via Virgilio 105/107, Trapani, 320 054 0352, www.colorclean.it, PDFs updated |
| **Pizza Planet** | Ciccio, Via Asmara 35 Bonagia (TP), 0923 592609, PDFs done + address confirmed |
| **ISOTTO Sport** | Print partner, +39 349 972 9418 |
| **Gym 4U** | 30-day membership active (renewed Feb 9) |
| **PuntaTipa Hotel** | Alessia, Lungomare Dante Alighieri 70, 0923 948459 |

---

## FINANCIAL OVERVIEW

- **Pension:** ~11 months away (birthday ~Jan 2027)
- **RAV:** Closed Jan 31, 2026
- **Living:** Surviving on savings, building UFA postcard business in Sicily
- **Stove repair (Camper & Tour):** EUR 1,010 (PAID, claiming from AXA)
- **Hotel (PuntaTipa):** EUR 1,395.50 (PAID, claiming from AXA)
- **Total claimed so far:** EUR 2,405.50
- **Roof repair:** EUR 5,000-10,000 (estimate pending, insurance claim)
- **Mattenweg bills (Batch 2):** CHF 2,126.50 + EUR 93.50 -- ALL PAID Feb 9

---

*This file is Tigs' working memory. Update it often.*
*"You write a script, I press the clicker, OBS does the rest." -- McDonald's Trapani, Feb 10, 2026*
*"Three episodes in one night. That's not a pipeline, that's a factory." -- Rio Figiori parking spot, Feb 11, 2026*
*"Four episodes. Still going. Quality is fantastic." -- 1am, still at McDonald's*
