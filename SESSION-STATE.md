# SESSION STATE - February 12, 2026

*Last Updated: Wed Feb 12, 2026 ~7:45am - At Gym 4U, waiting for 8am open. EP4 on YouTube.*

---

## TODAY'S WINS (Wed Feb 12)

1. **EP4 ON YOUTUBE** -- https://youtu.be/_ap7-hgtC9o -- Thumbnail, description, SRT subtitles, timestamps all done. First public episode.

### Yesterday (Tue Feb 11)
1. **EP4 VOICED** -- First episode with voiceover. Recorded 9 scenes at McDonald's with Jabra headset, Tigs stitched + normalized + merged. New voiceover pipeline proven.
2. **AXA email sent** -- Invoices (EUR 2,405.50) sent to schaden@axa.ch + water damage flagged with 3 questions.
3. **Color Clean cards delivered** -- Owner meeting done in person. Approval form template built.
4. **Pizza Planet cards delivered** -- Free beer + panino + 4 monster slices = 7 EUR.
5. **Phone fixed** -- Fairphone 3+ force restart (Power 10s).

---

## KC VIDEO SERIES - EP4 VOICED, EP5-EP8 SILENT

**Voiceover Pipeline (NEW - Feb 11):**
Record each scene as separate Telegram voice message (.ogg) → Whisper transcribe → ffmpeg trim/normalize/concat/speed-fit → merge into silent video

| EP | Title | Duration | Video | Voice | File | YouTube |
|----|-------|----------|-------|-------|------|---------|
| 4 | Keys to the Kingdom | 2:32 | FINAL | VOICED | `EP4.../KC-EP4-Keys-to-the-Kingdom-WITH-VOICE.mp4` | [YouTube](https://youtu.be/_ap7-hgtC9o) |
| 5 | RBAC Deep Dive | 3:19 | FINAL | TODO | `EP5.../KC-EP5-RBAC-Deep-Dive-FINAL.mp4` | -- |
| 6 | Client Architecture | 2:30 | FINAL | TODO | `EP6.../KC-EP6-Client-Architecture-FINAL.mp4` | -- |
| 7 | Authentication Flows | 2:35 | FINAL | TODO | `EP7.../KC-EP7-Authentication-Flows-FINAL.mp4` | -- |
| 8 | Multi-Tenant Platform | 2:30 | FINAL | TODO | `EP8.../KC-EP8-Multi-Tenant-Platform-FINAL.mp4` | -- |

**Voiceover technical notes:**
- Source: Opus 48kHz mono (.ogg from Telegram voice messages)
- CRITICAL: Force `-ar 48000` at every ffmpeg step (loudnorm silently upsamples to 192kHz = lion growl)
- Speed adjust: atempo ~1.1x to fit content window (barely noticeable)
- Fades: 0.5s in at voice start, 3s out before outro

**Teleprompter PDFs:** `EP4.../voiceover-script-TELEPROMPTER.pdf` (built but not needed -- scene-by-scene recording is better)

**YouTube assets:** `~/Videos/HelixNet-YouTube/Keycloak Episodes/` (thumbnails, descriptions, SRTs)

**MP4s:** Local only (GDrive when on solid WiFi, not hotspot)

---

## AXA INSURANCE CLAIM

**Claim:** 22.831.735/0001
**Submit docs to:** schaden@axa.ch (with claim number in subject)
**Adjuster:** Iwan Zgraggen (forwarded case, no longer primary)

### Timeline
- **Feb 9:** Iwan forwarded case to English-speaking colleague
- **Feb 11 morning:** Iwan confirmed -- send everything to schaden@axa.ch directly
- **Feb 11 ~9:50am:** Email SENT to schaden@axa.ch with both invoices + water damage questions

### Costs to Claim
| Item | Amount | Status |
|------|--------|--------|
| Camper & Tour (stove + smoke clean) | EUR 1,010 | PAID, invoice submitted |
| PuntaTipa Hotel (13 nights B&B) | EUR 1,395.50 | PAID, invoice submitted |
| Water damage (roof/seals) | EUR 5,000-10,000 est. | Pending preventivo from C&T |
| **Total submitted** | **EUR 2,405.50** | |

### Waiting For (from AXA)
1. Confirmation of invoice receipt
2. Same claim or new claim for water damage?
3. Do they send an assessor to Sicily?
4. New case worker introduction

---

## UFA POSTCARDS - CLIENT STATUS

| # | Client | Cards | Meeting | Next Step |
|---|--------|-------|---------|-----------|
| 1 | **Color Clean** | Delivered (4UP + tent card) | 5pm done, walked through in person | Get her detailed feedback, fill approval form properly, better photos |
| 2 | **Pizza Planet** | Delivered | Free beer + positive reception | Done for now, reprint when photos improve |
| 3 | **Marghe Trapani** | PDFs done | Not yet delivered | Show owner, get approval |
| 4 | ~~Piccolo Bistratto~~ | Not started | Bad vibes | PARKED -- maybe never |

### Color Clean CRM Notes
- **Owner name:** Still unknown (need to get at next visit)
- **Phone:** 320 054 0352 (only number on business card -- check if landline exists)
- **Hours:** MISSING from postcards -- need to confirm every day + lunch break
- **Payment methods:** Unknown -- ask (Google Pay, Satispay, cash, card?)
- **Approval form:** `postcards/colorclean/colorclean-APPROVAL-FORM.pdf` (ready to print/show)
- **Proof PDF:** `postcards/colorclean/colorclean-PROOF.pdf` (portrait + landscape samples)
- **The deal:** She gets free design + printing. He gets fabric expertise + wash testing for merch R&D.
- **ISOTTO triangle:** Angel (design) → ISOTTO (print/merch) → Color Clean (fabric testing) → sell to everyone
- **Merch idea:** Test t-shirts with different print methods, she washes 5x, see what survives. Cotton only, no synthetic.

### Business Philosophy
- Only work with people you LIKE
- Non-competing businesses in same category/area
- Bad vibes = exit (Piccolo Bistratto lesson)
- Approval form template is standard intake for all new clients

---

## CAMPER & TOUR STATUS

- **Camera radio adapter:** Install TODAY (Wed Feb 12) -- they promised
- **Be there at 9am** for the install
- **When installed:** Maybe remove back window to assess roof + write preventivo for AXA
- **Cremers:** Angel buying coffee cremers for the guys tomorrow morning
- **Kevin:** Gets his own JYSK bathrobe whenever, hot springs Saturday

---

## PENDING ACTIONS

### Done Wed Feb 12
- [x] EP4 uploaded to YouTube (https://youtu.be/_ap7-hgtC9o)
- [x] EP4 thumbnail created (1280x720, key icon + title)
- [x] EP4 YouTube description + tags written
- [x] EP4 SRT subtitles ready for upload

### Still TODO Wed Feb 12
- [ ] Upload SRT subtitles to YouTube (Subtitles > Add > English > Upload SRT)
- [ ] Set EP4 thumbnail on YouTube (upload KC-EP4-Keys-to-the-Kingdom-THUMBNAIL.png)
- [ ] 9am Camper & Tour -- camera install
- [ ] Ask C&T about preventivo for roof/water damage (for AXA)
- [ ] Buy cremers for coffee at C&T
- [ ] Clear Telegram cache on Fairphone (prevent next fuzz)
- [ ] Get JYSK bathrobe (for self, before Saturday)
- [ ] Color Clean: return with printed approval form, get her name + hours + details
- [ ] ISOTTO: check in person, print status
- [ ] Record voiceover EP5 (same scene-by-scene method)

### Later
- [ ] Record voiceover EP6, EP7, EP8
- [ ] Marghe Trapani: deliver cards, get approval
- [ ] Cheap test print before next ISOTTO run
- [ ] Wait for AXA response to schaden@axa.ch email
- [ ] Wait for Rajiv/Vyoma response

---

## KEY CONTACTS

| Who | Details |
|-----|---------|
| **Camper & Tour** | Sebastiano/Nino, Via F. Culcasi 4, Trapani, +39 328 684 4546 |
| **AXA** | schaden@axa.ch, Claim 22.831.735/0001 |
| **Color Clean** | Via Virgilio 105/107, 320 054 0352, colorclean.tp@gmail.com |
| **Pizza Planet** | Ciccio, Via Asmara 35 Bonagia, 0923 592609 |
| **ISOTTO Sport** | Print partner, +39 349 972 9418 |
| **Kevin Galilee** | Hot springs Saturday, needs XXL bathrobe from JYSK |
| **Gym 4U** | Via Benedetto Valenza 31, Trapani. Mon/Wed/Fri 7am-10pm, Tue/Thu/Sat 8am-10pm, Sun CLOSED |
| **Marghe Trapani** | Via Garibaldi 52, 352 088 2833 |

---

## FINANCIAL OVERVIEW

- **Pension:** ~11 months away (birthday ~Jan 2027)
- **RAV:** Closed Jan 31, 2026
- **Today's spend:** ~10 EUR (Color Clean + Pizza Planet prints) + 7 EUR (Pizza Planet dinner)
- **UFA budget:** ~50 EUR initial for test runs
- **AXA submitted:** EUR 2,405.50 (stove + hotel)
- **AXA pending:** EUR 5,000-10,000 (roof/water damage)

---

*This file is Tigs' working memory. Update it often.*
*"The lion growl was a 192kHz sample rate bug. The fix was -ar 48000." -- McDonald's Trapani, Feb 11*
*"Pizza Planet card drop = free beer. That's ROI on day one." -- 7 EUR dinner, try that in Switzerland*
*"She's not your customer. She's your R&D department." -- Color Clean fabric testing strategy*
*"I only work with people I like." -- The UFA client filter*
*"First public episode. From McDonald's parking lot to YouTube." -- Gym 4U, Feb 12, 7:45am*
