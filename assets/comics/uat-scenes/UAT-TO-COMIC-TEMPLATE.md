# UAT-TO-COMIC Pipeline
> Real test cases. Real comedy. Kids teach CTOs.

---

## The Formula

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   UAT SCRIPT  →  SCENE  →  LEGO PANEL  →  CAPTION          │
│                                                             │
│   "Certificate     "YUKI says    [CHARLIE     "45 days.    │
│    validation       it's fine,    pointing,    Under the   │
│    fails after      CHARLIE's     coffee cup   coffee."    │
│    45 days"         3rd eye       visible]                  │
│                     glows"                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘

The UAT is the script.
The bug is the punchline.
The kid explains what the CTO couldn't see.
```

---

## TEMPLATE: Single Panel (Far Side Style)

```markdown
## UAT-XXX: [Test Case Name]

**UAT Source:** [Link or reference to actual test case]

**The Bug:** [What actually went wrong]

**Scene:**
- WHO: [Characters in panel]
- WHAT: [Action happening]
- WHERE: [Setting]
- PROP: [Key object that tells the story]

**Visual:**
[ASCII sketch of panel layout]

**Caption:** "[Punchline - short, punchy, truth bomb]"

**Alt Text:** [For accessibility]
```

---

## TEMPLATE: 4-Panel Strip (Dilbert Style)

```markdown
## UAT-XXX: [Test Case Name]

**UAT Source:** [Link or reference]

**The Bug:** [What actually went wrong]

### Panel 1: SETUP
- WHO:
- ACTION:
- DIALOGUE: ""

### Panel 2: PROBLEM
- WHO:
- ACTION:
- DIALOGUE: ""

### Panel 3: KID WISDOM
- WHO:
- ACTION:
- DIALOGUE: ""

### Panel 4: PUNCHLINE
- WHO:
- ACTION:
- DIALOGUE: ""

**Caption:** "[The moral, the truth, the lesson]"
```

---

## EXAMPLE: UAT-001 Certificate Expiry

**UAT Source:** HELIX-UAT-2024-047 (Certificate validation)

**The Bug:** SSL certificate expired. Nobody noticed for 45 days.
              It was under a coffee cup on YUKI's desk. Literally.

### Panel 1: SETUP
- WHO: YUKI (compliance officer)
- ACTION: Checking papers, confident
- DIALOGUE: "Everything is FINE. I checked EVERYTHING."

### Panel 2: PROBLEM
- WHO: CHARLIE (third eye starting to glow)
- ACTION: Standing behind, third eye activating
- DIALOGUE: "..." (silent, just the eye glowing)

### Panel 3: KID WISDOM
- WHO: KID with magnifying glass
- ACTION: Lifting coffee cup, certificate visible underneath
- DIALOGUE: "Found it! It was under the coffee!"

### Panel 4: PUNCHLINE
- WHO: Everyone staring at coffee cup
- ACTION: YUKI facepalming, CHARLIE's eye full glow
- DIALOGUE: (none needed)

**Caption:** "45 days. It was always under the coffee."

---

## EXAMPLE: UAT-002 The Deploy Button

**UAT Source:** HELIX-UAT-2024-089 (Deployment pipeline)

**The Bug:** CTO spent 3 sprints building "AI-powered deployment orchestration"
              The deploy button was there the whole time.

### Panel 1: SETUP
- WHO: CTO at whiteboard
- ACTION: Complex diagrams, flowcharts, AI boxes
- DIALOGUE: "We need MACHINE LEARNING to OPTIMIZE the DEPLOYMENT!"

### Panel 2: PROBLEM
- WHO: CTO, smoke coming from somewhere
- ACTION: More diagrams, stress sweat
- DIALOGUE: "It's been 3 SPRINTS! Why isn't it DEPLOYING?!"

### Panel 3: KID WISDOM
- WHO: KID walking past, juice box in hand
- ACTION: Pointing at screen
- DIALOGUE: "Dad... there's a button that says 'Deploy'."

### Panel 4: PUNCHLINE
- WHO: CTO frozen, looking at actual deploy button
- ACTION: Button clearly labeled, has been there all along
- DIALOGUE: "..."

**Caption:** "3 sprints. $150,000. The button was labeled."

---

## EXAMPLE: UAT-003 The Microservices

**UAT Source:** HELIX-UAT-2024-112 (Architecture review)

**The Bug:** Team built 47 microservices.
              They needed 3.

### Single Panel (Far Side):

**Visual:**
```
┌────────────────────────────────────┐
│                                    │
│   [CTO pointing at massive wall    │
│    of connected boxes/services]    │
│                                    │
│   [KID in corner with 3 LEGO       │
│    blocks stacked simply]          │
│                                    │
│   KID: "I used three."             │
│                                    │
└────────────────────────────────────┘
```

**Caption:** "47 microservices. 3 customers."

---

## HOW TO CONVERT ANY UAT

1. **Find the absurdity** - What's the gap between effort and result?
2. **Identify the obvious** - What did everyone miss?
3. **Cast the characters**:
   - CTO = The one who overcomplicates
   - CHARLIE = The one who sees the problem
   - KID = The one who states the obvious
   - PAM = The one dancing through chaos
   - SAL = The one who quietly fixed it already
4. **Write the caption FIRST** - The punchline drives the visuals
5. **Sketch the simplest version** - 6 crayons or less

---

## CAPTION STYLE GUIDE

**DO:**
- "45 days. Under the coffee."
- "$150,000. The button was labeled."
- "47 microservices. 3 customers."
- "Sprint 47 was cancelled."
- "Freedom doesn't buffer."

**DON'T:**
- Long explanations
- Technical jargon
- Anything a 5-year-old can't repeat

**THE TEST:**
Can a kid read this caption to their CTO parent
and make them feel something?

---

## FILE NAMING

```
/uat-scenes/
  uat-001-certificate-coffee.md
  uat-002-deploy-button.md
  uat-003-microservices-three.md
  ...

/strips/
  strip-001-certificate.png
  strip-002-deploy.png
  ...

/one-shots/
  farside-001-microservices.png
  farside-002-standup.png
  ...
```

---

## NEXT: YOUR UATs

List your real UAT cases below. We'll convert them.

| UAT ID | Bug/Issue | Comedy Potential | Characters |
|--------|-----------|------------------|------------|
| | | | |
| | | | |
| | | | |

---

*Pull from REAL test cases.*
*The comedy writes itself.*
*The kids will teach the CTOs.*

