# BLQ Development Method
## Screenplay-Driven Enterprise Software Development

*"Be water, my friend. Empty your mind, be formless, shapeless — like water."*
— Bruce Lee

---

## Overview

The BLQ (Bruce Lee Quality) Development Method applies cinematic storytelling structure to enterprise software development. Instead of abstract requirements documents, we write **scenes** with characters, conflicts, and resolutions that drive real code.

**Traditional:** Requirements → Spec → Code → Test → Deploy
**BLQ Method:** Character + Conflict → Scene → Build → Test-in-Narrative → Commit

---

## The Three-Act Structure

### Act 1: SETUP (The Hook)
Establish the world, characters, and the inciting incident.

| Element | Film Example | Development Example |
|---------|--------------|---------------------|
| **WHO** | Protagonist introduced | Pam (Cashier) at register |
| **WHERE** | Setting established | Artemis Headshop, Luzern |
| **WHAT** | Normal world | Morning routine, coffee ready |
| **INCITING INCIDENT** | Something disrupts | George Clooney walks in with broken Zippo |

### Act 2: CONFRONTATION (The Build)
Rising tension, obstacles, decisions under pressure.

| Element | Film Example | Development Example |
|---------|--------------|---------------------|
| **OBSTACLE** | Villain appears | Flint is stuck, train in 30 min |
| **STAKES** | What's at risk | Lose VIP customer, bad review |
| **RESOURCES** | What hero has | Product search, KB articles |
| **GAPS** | What's missing | No Zippo flints in system! |
| **DECISION** | Hero must choose | Fix it or sell replacement? |

### Act 3: RESOLUTION (The Commit)
Climax, resolution, and setup for next scene.

| Element | Film Example | Development Example |
|---------|--------------|---------------------|
| **ACTION** | Hero acts | Pam fixes Zippo, registers George |
| **CLIMAX** | Peak tension | Felix takes George to Rosie's |
| **RESOLUTION** | New equilibrium | Deal closed, customer happy |
| **HOOK** | Setup sequel | "See you Black Friday?" |

---

## Scene Card Template

Use this template for each development scene:

```markdown
## SCENE: [Scene Name]

### METADATA
- **Episode:** [Number/Name]
- **Location:** [Where this happens]
- **Characters:** [Who's involved]
- **Time Pressure:** [Deadline/urgency]
- **Complexity:** C1 (Simple) / C2 (Medium) / C3 (Complex)

### SETUP
**Context:** [What's the normal state before this scene?]
**Inciting Incident:** [What disrupts and starts the scene?]

### CONFLICT
**Primary Obstacle:** [What's blocking the goal?]
**Stakes:** [What happens if they fail?]
**System Gaps:** [What's NOT built yet that this scene needs?]

### RESOLUTION
**Actions Taken:** [What do characters do?]
**System Changes:**
- [ ] Products added
- [ ] Customers created
- [ ] KBs written
- [ ] Code modified
- [ ] Database updated
- [ ] UI changes

### EXIT CRITERIA
- [ ] [Specific testable outcome 1]
- [ ] [Specific testable outcome 2]
- [ ] [E2E test passes]

### HANDOFF
**Next Scene:** [What does this set up?]
**Loose Threads:** [What's unresolved for later?]
```

---

## Character Bible Structure

Each character in the system should have:

```markdown
## [CHARACTER NAME] — "[Nickname/Handle]"

### Identity
- **Handle:** @[system_handle]
- **Role:** [Cashier/Manager/Customer/etc.]
- **Tier:** [Bronze/Silver/Gold/Platinum/Diamond]
- **Location:** [Primary location]

### Patterns
- **Buying Habits:** [What do they typically purchase?]
- **Payment:** [Cash/TWINT/Card preference]
- **Time Patterns:** [When do they show up?]
- **Communication:** [How do they want to be reached?]

### Edge Cases They Test
- [Specific scenario 1]
- [Specific scenario 2]

### Relationships
- [Connected to Character X via...]
- [Conflict with Character Y because...]

### Quotes
> "[Memorable line that captures their essence]"
```

---

## Location Registry

Each location should be documented:

```markdown
## [LOCATION NAME]

### Details
- **Type:** [Shop/Vending/Warehouse/Supplier]
- **Address:** [Physical or logical location]
- **Staff:** [Who works here?]
- **Hours:** [Operating hours]

### Capabilities
- [ ] POS transactions
- [ ] Vending machine
- [ ] Customer registration
- [ ] Returns/refunds
- [ ] Cash handling

### Inventory
- **Categories available:** [List]
- **Slot mapping:** [For vending]
- **Restock schedule:** [When/who]

### Connections
- **Reports to:** [Parent location]
- **Supplies from:** [Supplier locations]
- **Distance to HQ:** [Travel time]
```

---

## The BLQ Workflow

### 1. SCENE PLANNING (5 min)
```
□ Identify the character(s)
□ Define the conflict/need
□ Set time pressure
□ List system gaps
□ Write exit criteria
```

### 2. NARRATIVE DEVELOPMENT (15-30 min)
```
□ Play out the scene in conversation
□ Let gaps reveal themselves naturally
□ Build what's missing as you go
□ Test within the narrative context
```

### 3. CHECKPOINT (5 min)
```
□ Run health check / E2E tests
□ Document what was built
□ Write/update KBs if needed
□ Git add + commit with scene context
```

### 4. HANDOFF (2 min)
```
□ Note loose threads
□ Identify next scene
□ Push to remote
□ Update scene backlog
```

---

## Commit Message Format

```
[type]: [Scene Name] - [Brief Description]

## Scene Context
- Characters: [who]
- Location: [where]
- Conflict: [what was the problem]

## Changes
- [Bullet list of what was built/changed]

## Exit Criteria Met
- [x] [Criteria 1]
- [x] [Criteria 2]

## Next Scene
- [What this sets up]

🤖 Generated with [Claude Code](https://claude.com/claude-code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Why BLQ Works

### 1. Context Over Abstraction
**Traditional:** "The system shall support product search with fuzzy matching."
**BLQ:** "Pam has 2 minutes to find a Zippo for George before his train leaves."

The BLQ version tells you:
- WHO needs it (Pam - cashier skill level)
- WHY it matters (customer satisfaction, time pressure)
- HOW FAST it must be (2 minutes = instant results)
- WHAT SUCCESS looks like (George gets his Zippo)

### 2. Edge Cases Emerge Naturally
You don't brainstorm edge cases in a meeting. They appear when:
- Dayo's CHF 1.50 lighter breaks (cheap product returns)
- George's train is delayed (customer time changes mid-transaction)
- Ralph spots Pam's 40 rappen error (cash handling precision)
- CN walks in (unknown customer, unusual requests)

### 3. Multi-Stakeholder Testing Built-In
One scene tests multiple roles simultaneously:
- **Pam (Cashier):** Can she find products fast?
- **Felix (Manager):** Does he have visibility to approve?
- **Ralph (Supervisor):** Can he review her work?
- **George (Customer):** Is the experience smooth?
- **System:** Does it handle the load?

### 4. Documentation Writes Itself
KBs emerge from scenes:
- George's stuck Zippo → KB-040: Zippo Maintenance Guide
- Bruce grinder arrival → KB-041: UNBOXING Workflow
- Dayo's cheap lighter → KB-042: Cheap Lighter Repair SOP

### 5. Memorable = Maintainable
Six months later:
- **Traditional:** "What does `handleRefundEdgeCase()` do?"
- **BLQ:** "Oh, that's the Dayo scenario - cheap lighter, stuck flint, goodwill replacement"

---

## Anti-Patterns to Avoid

### 1. Scope Creep via Character
❌ "George also mentions he needs a website built"
✅ Stay in the scene's domain. Note it for a future scene.

### 2. Character Bloat
❌ 15 characters in one scene, losing focus
✅ Max 3-4 active characters per scene

### 3. Skipping Commits
❌ "I'll commit after I finish all these features"
✅ Commit after EVERY scene resolution

### 4. Forgetting the Gap List
❌ Build what's asked, miss what's revealed
✅ Track every "wait, we don't have that" moment

### 5. Over-Engineering for Future Scenes
❌ "George might want X later, let's build it now"
✅ YAGNI - only what THIS scene needs

---

## Metrics & Quality

### Scene Velocity
- Scenes completed per session
- Average time per scene
- Gap-to-fix ratio (how fast we fill gaps)

### Coverage
- Characters exercised
- Locations tested
- Product categories touched
- Role permissions verified

### Documentation Ratio
- KBs created per X scenes
- Commit message quality score
- Scene card completeness

---

## Tools & Integration

### Scene Management
- Scene cards in `uat/scenes/` directory
- Character bible in `uat/characters.md`
- Location registry in `uat/locations.md`

### Automation Hooks
- Pre-commit: Validate scene card exists for changes
- Post-commit: Update scene backlog
- CI/CD: Run E2E tests named after scenes

### Future: Scene Replay
Convert narrative scenes to automated tests:
```python
def test_george_zippo_flint_jam():
    """
    SCENE: George Clooney walks in with stuck Zippo
    TIME PRESSURE: Train in 30 minutes
    """
    # Setup
    george = create_customer(handle="Coolie", tier="BRONZE")

    # Conflict
    results = product_search("zippo flint")
    assert len(results) > 0, "Pam must find flints!"

    # Resolution
    transaction = create_sale(
        customer=george,
        items=["ZIPPO-FLINT-6PK"],
        payment="TWINT"
    )
    assert transaction.status == "COMPLETED"
    assert george.credits_balance > 40  # Welcome bonus + purchase
```

---

## Getting Started

### Your First BLQ Scene

1. **Pick a character** from your bible (or create one)
2. **Give them a problem** that your system should solve
3. **Add time pressure** (deadline, urgency, constraint)
4. **Play it out** in conversation with your AI pair
5. **Build what's missing** as gaps reveal themselves
6. **Commit with context** using the scene name
7. **Note the next scene** this sets up

### Example First Scene
```
SCENE: New Employee First Day

Character: Leandra (new cashier, first week)
Problem: Customer wants to return item, Leandra doesn't know process
Time Pressure: Line forming behind customer
Gap Revealed: No returns training KB exists

BUILD:
- KB-043: Returns & Refunds SOP
- UI: "Help" button on POS that links to relevant KB
- Test: Leandra can process return within 3 minutes
```

---

## Credits

**Method Developed By:** The BLQ Team
**Inspired By:** Sid Field's Screenplay Structure
**Philosophy:** Bruce Lee's Jeet Kune Do ("The way of the intercepting fist")

*"Absorb what is useful, discard what is not, add what is uniquely your own."*
— Bruce Lee

---

## Changelog

- **2025-12-03:** Initial documentation of the BLQ Method
- Based on the George Clooney / Bruce Lee UAT Epic session

---

*Empty your mind. Be formless. Build like water.*
