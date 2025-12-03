# BLQ Session Capture
## 2025-12-03 | George Clooney / Bruce Lee Epic

*"Be water, my friend"* — Bruce Lee

---

## SESSION SUMMARY

**Duration:** ~4 hours
**Method:** BLQ (Bruce Lee Quality) - Screenplay-Driven Development
**Collaboration:** Human (Director) + Claude (Production)

---

## WHAT WE BUILT

### Code & Database
| Item | Details |
|------|---------|
| Products | +26 SKUs (Zippo line, Bruce Lee Grinders, Cleaning Kits, Lighters) |
| Customers | 6 personas (Coolie, Dayo, BruceBLQ, MsLee, Poppie420, SirGessler) |
| DB Function | `search_products()` with trigram fuzzy search |
| Customer Fields | `payment_method`, `iban`, `vat_number`, `company_name` |
| UI | Status bar footer (pulse, time, version, user) |

### Knowledge Base
| KB | Title | Purpose |
|----|-------|---------|
| KB-040 | Zippo Maintenance Guide | A-Line repair, flint replacement |
| KB-041 | UNBOXING Workflow | New product documentation |
| KB-042 | Cheap Lighter Repair SOP | C-Line, ISO-flexible |

### Documentation
| Doc | Purpose |
|-----|---------|
| `docs/BLQ-DEVELOPMENT-METHOD.md` | The methodology explained |
| `uat/SCENE-BACKLOG.md` | Prioritized scene list |
| `uat/SESSION-2025-12-03-BLQ-EPIC.md` | This file |

---

## THE BLQ COMMAND LANGUAGE

```
COMMANDS:
├─ SHOWME     → Display status, options, data
├─ TELLME     → Explain, analyze, recommend
├─ BUILD      → Create code, products, KBs
├─ PUSH       → Git add + commit + push
├─ SCAN       → Health check
├─ YAGNI      → Stop overengineering
├─ PAUSE      → Stop and discuss
├─ BREAKOUT   → Exit scene, commit milestone
└─ CONTINUE   → Keep going
```

---

## THE FLOW

```
INPUT (What Pam hears/sees)
    │
    ▼
PROCESS (What Pam thinks/does)
    │  → Breathe
    │  → STATUS CHECK
    │  → PRIORITIZE
    │  → ACT
    │
    ▼
RESULT (What happens)
    │
    └─→ NEXT SCENE
```

---

## SCENES COMPLETED

### Episode 1: George Clooney / Bruce Lee Epic

| Scene | Characters | What Happened |
|-------|------------|---------------|
| 1.1 Zippo Flint JAM | George, Pam | Stuck flint, train in 30 min, products added |
| 1.2 Bruce Grinder Arrival | Pam, Felix | UNBOXING, Slot #16 vending, KB-041 |
| 1.3 Dayo Cheap Lighter | Dayo, Pam | Mini flints, C-line repair, KB-042 |
| 1.4 The Road Trip | Felix, Coolie | Rosie's leather, SylKen, Clooney Collection |
| 1.5 Ralph Takes Over | Ralph, Pam, CN | Staff handoff, mystery customer |

---

## PRODUCT TIERS ESTABLISHED

```
C-LINE (< CHF 5)     → Mini lighters, flints, papers
B-LINE (5-20)        → Clippers, Zippo accessories
A-LINE (20-100)      → Zippos, Barney Farm, Barcey, Bruce Buster
SIGNATURE (100+)     → Artemis Limited, Clooney Collection, Bruce Master
```

---

## CHARACTERS ROSTER

### Active
| Handle | Name | Role | Tier |
|--------|------|------|------|
| Coolie | George Clooney | VIP Customer | SILVER |
| Dayo | Dayo | Local Regular | BRONZE |
| BruceBLQ | Bruce Lee | Signature Partner | PLATINUM |
| MsLee | Cynthia Lee | Tea Specialist | GOLD |

### Staff
- **Pam** - Cashier, front-of-house queen
- **Felix** - Owner, deal closer
- **Ralph** - Manager, detail-oriented
- **Leandra** - New employee (planned)
- **Vera** - LAB worker, vape expert (planned)

### Suppliers/Partners
- **SylKen** - Custom engraver
- **Rosie** - Raber Leather, snake skins
- **Boris** - Vending site manager
- **Marco** - Technician from Tessin
- **KAMAKI** - Japanese broker (future)

---

## THE VISION

### Why Headshop?
- Real domain knowledge (2-3 months observing Felix & Pam)
- CRACKs are REAL people - tattoos, alternative, know products better than anyone
- POS is where rubber meets road - works for ANY system
- Small businesses (2-4 people) need this

### The Expanding Universe
```
SEASON 1: Artemis Headshop (NOW)
SEASON 2: International Deals (KAMAKI, customs, Japanese torches)
SEASON 3: The Network (Boris rave palace, Butch butcher shop, more)
```

### Thursday Demo
- Location: Near Artemis Warehouse
- Need to show: Working system + the METHOD

---

## COMMITS THIS SESSION

```
27528e3 docs: BLQ Development Method + Scene Backlog
2ad782f v3.2.1 — HR Module fixes + Documentation bundle
71ca412 feat: Add minimal status bar footer to POS templates
cf2794e v3.2.0 — UAT Epic: George Clooney / Bruce Lee Scenario
```

---

## NAMING CONVENTIONS (PAM-PROOF)

### Products
```
[CATEGORY]-[BRAND]-[VARIANT]
Examples:
  ZIPPO-CLASSIC-BLK
  GRINDER-BRUCE-FLOW
  LIGHTER-BARNEY-FARM
  CLEAN-KIT-A
```

### Customers
```
Handle: Short, memorable (@Coolie, @Dayo, @BruceBLQ)
Real name: Full name for records
```

### KBs
```
HelixPOS_KB-[NUMBER]-[slug]
Examples:
  HelixPOS_KB-040-zippo-maintenance-guide.md
  HelixPOS_KB-041-unboxing-workflow.md
```

### Commits
```
[type]: [Scene/Feature] - [Description]
Examples:
  feat: Add minimal status bar footer
  docs: BLQ Development Method
  v3.2.0 — UAT Epic: George Clooney
```

---

## WHAT'S NEXT

### Immediate (Episode 2)
- [ ] Ralph + CN scene
- [ ] Cash count / 40 rappen error
- [ ] Timesheet approval

### Thursday Prep
- [ ] Define what demo needs
- [ ] Rehearse key flows
- [ ] Prepare talking points

### Future Episodes
- [ ] Boris Vending (Pam + Vera)
- [ ] Black Friday
- [ ] Leandra Training
- [ ] KAMAKI International

---

## THE PRINCIPLE

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   BLQ = BRUCE LEE QUALITY                                    ║
║                                                               ║
║   "Be water, my friend"                                      ║
║                                                               ║
║   → Characters are FAIR testers                              ║
║   → Conflict reveals requirements                            ║
║   → Build only what the scene needs (YAGNI)                 ║
║   → Improvisation beats planning                             ║
║   → Human imagination + AI execution                         ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

*Session captured. Be water.*
