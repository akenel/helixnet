# HELIX COMICS — Workflow
> Scene Script → AI Prompt → Image → Folder

---

## THE SIMPLE FLOW

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   1. LEO writes scene script (.md)                          │
│         ↓                                                   │
│   2. YOU copy the AI PROMPT from the script                 │
│         ↓                                                   │
│   3. YOU paste into nano banana (AI image generator)        │
│         ↓                                                   │
│   4. YOU save image to correct folder                       │
│         ↓                                                   │
│   5. DONE — Comic panel ready                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## YOUR PART (The Coffee Sipper)

1. **Open scene script** (e.g., `scene-001-toast-button.md`)
2. **Find the AI PROMPT section** (I'll add these now)
3. **Copy the prompt**
4. **Paste into your AI tool** (Midjourney, DALL-E, Leonardo, whatever)
5. **Generate image**
6. **Save to:**
   - 4-panel strips → `/assets/comics/strips/`
   - Single panels → `/assets/comics/one-shots/`
7. **Sip coffee**

---

## FOLDER STRUCTURE

```
/assets/comics/
├── strips/                    # 4-panel finished images
│   ├── strip-001-toast.png
│   ├── strip-002-coffee.png
│   └── strip-003-september.png
├── one-shots/                 # Far Side singles
│   ├── farside-001-microservices.png
│   └── farside-001-microservices.md  (the script)
├── templates/                 # Reference docs
└── uat-scenes/                # Scene scripts (your input)
```

---

## FILE NAMING

```
Script:  scene-001-toast-button.md
Image:   strip-001-toast.png

Script:  farside-001-microservices.md
Image:   farside-001-microservices.png
```

Same name, different extension. Simple.

---

## WHAT LEO DOES

- Writes scene scripts with ASCII layouts
- Adds AI-READY PROMPTS (copy-paste ready)
- Adds captions (for you to overlay or include in prompt)
- Keeps it YAGNI

## WHAT YOU DO

- Copy prompt
- Paste into AI
- Save image
- Drink coffee
- Laugh at results

---

## THAT'S IT

No complex pipeline.
No build system.
No dependencies.

Script → Prompt → AI → Image → Folder → Done.

---

*The tiger writes. The human generates. The kids laugh.*
