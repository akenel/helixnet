# HelixNet Keycloak Video Series

**Production method:** Puppeteer automated browser + OBS screen capture
**Scripts:** `/scripts/kc-record-ep*.js`
**Workflow:** Script drives Chrome, OBS records screen, trim with ffmpeg, voiceover later

---

## Episodes

| EP | Title | Duration | Status | Script |
|----|-------|----------|--------|--------|
| 4 | Keys to the Kingdom | 2:22 | RECORDED + TRIMMED | `kc-record-ep4.js` |
| 5 | RBAC Deep Dive | 2:37 | RECORDED + TRIMMED | `kc-record-ep5.js` |
| 6 | Client Architecture | 2:38 | RECORDED + TRIMMED | `kc-record-ep6.js` |
| 7 | Authentication Flows | 2:35 | RECORDED + TRIMMED | `kc-record-ep7.js` |
| 8 | Multi-Tenant Platform | 2:30 | RECORDED + TRIMMED | `kc-record-ep8.js` |

---

## Folder Structure

```
videos/keycloak/
├── README.md                          <- This file
├── EP4-keys-to-the-kingdom/
│   ├── KC-EP4-Keys-to-the-Kingdom.mp4 <- FINAL trimmed video (use this)
│   ├── voiceover-script.md            <- Talking points for narration
│   └── raw/
│       └── take2-good-full.mp4        <- Full OBS recording before trim
├── EP5-rbac-deep-dive/
│   ├── intro.html                     <- Title card source
│   ├── outro.html                     <- End card source
│   ├── voiceover-script.md            <- Talking points for narration
│   └── raw/                           <- OBS raw recordings
├── EP6-client-architecture/
│   ├── intro.html                     <- Title card source
│   ├── outro.html                     <- End card source
│   ├── voiceover-script.md            <- Talking points for narration
│   └── raw/                           <- OBS raw recordings
├── EP7-authentication-flows/
│   ├── intro.html                     <- Title card source
│   ├── outro.html                     <- End card source
│   ├── voiceover-script.md            <- Talking points for narration
│   └── raw/                           <- OBS raw recordings
├── EP8-multi-tenant-platform/
│   ├── intro.html                     <- Title card source
│   ├── outro.html                     <- End card source
│   ├── voiceover-script.md            <- Talking points for narration
│   └── raw/                           <- OBS raw recordings
└── archive/
    └── EP4-take1-wrong-window.mp4     <- Failed takes, old versions
```

---

## Production SOP

### Recording a New Episode

1. Write the Puppeteer script: `scripts/kc-record-epN.js`
2. Dry run headless: `scripts/kc-record-epN-test.js` (verify selectors)
3. Close all browser windows (clean desktop)
4. Open OBS, set to **Screen Capture**, hit Record
5. Tell Tigs "GO" -- script runs, Chrome opens maximized
6. Wait for "RECORDING COMPLETE" in terminal
7. Stop OBS recording
8. Trim with ffmpeg: cut pre-roll (before Chrome) and post-roll (after Chrome closes)
9. Copy trimmed file to `EP{N}-folder/KC-EP{N}-Title.mp4`
10. Move raw to `EP{N}-folder/raw/`
11. Write voiceover script

### Trimming Command

```bash
ffmpeg -y -i raw-recording.mp4 -ss START -to END -c:v libx264 -crf 18 -preset slow -c:a copy output.mp4
```

### Key Timings in Scripts

```
PAUSE.SHORT  = 2500ms  (quick view)
PAUSE.MEDIUM = 4000ms  (read content)
PAUSE.LONG   = 6000ms  (study screen)
PAUSE.XLONG  = 8000ms  (money shots)
PAUSE.TYPE   = 90ms    (per character, human speed)
```

---

## KC Admin Console Selectors (v24.0.4)

| Element | Selector |
|---------|----------|
| Realm dropdown toggle | `.pf-c-context-selector__toggle` |
| Realm list items | `.pf-c-context-selector__menu-list-item button` |
| Login username | `#username` |
| Login password | `#password` |
| Login button | `#kc-login` |
| Welcome tab | `[data-testid="welcomeTab"]` |
| Server info tab | `[data-testid="infoTab"]` |
| Navigation URL pattern | `KC_BASE/#/{realmId}/{section}` |

**Realm switching:** Use direct URL navigation, NOT dropdown clicks (unreliable).

---

## Realms

| Display Name | Realm ID | Type |
|-------------|----------|------|
| Keycloak | master | Platform admin |
| HelixPOS Development | kc-pos-realm-dev | POS system |
| HelixNet Development | kc-realm-dev | Main platform |
| 420 Wholesale - Mosey Network | fourtwenty | Cannabis wholesale |
| Artemis Headshop - Luzern | artemis | Retail headshop |
| BlowUp V2 | blowup-v2 | Headshop & cafe |

---

*Created: Feb 10, 2026 -- First video recorded at McDonald's Trapani*
*"You write a script, I press the clicker, OBS does the rest."*
