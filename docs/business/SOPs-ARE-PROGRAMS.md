# SOPs Are Programs

*The New Way to Write Software in the Age of AI*

**Author:** Angel Kenel + Tigs
**Date:** January 31, 2026
**Location:** PuntaTipa Room 101, Trapani, Sicily

---

## The Realization

On January 31, 2026, after two months of building a postcard production pipeline, a hotel consulting framework, and an AI-assisted development workflow from a laptop in Sicily, Angel said:

> "Our SOPs are the new way to write LLM programs."

He's right. And this document explains why.

---

## The Old Model

For 60 years, programming meant writing instructions in a language a machine could execute deterministically.

```
input → code → deterministic output
```

You wrote Python. You wrote Java. You wrote SQL. The machine did exactly what you said. No more, no less. If the output was wrong, the code was wrong. Every time.

The skill was syntax, logic, and architecture. The tools were IDEs, compilers, and debuggers. The output was predictable. The ceiling was what you could type.

---

## The New Model

Large Language Models changed the execution layer. The machine now has judgment. It can interpret, adapt, and reason. But it still needs instructions.

The instructions just aren't code anymore. They're SOPs.

```
context + SOP + tool → consistent output with judgment
```

An SOP tells the LLM:
- **What** the goal is (Purpose)
- **Who** it applies to (Scope)
- **How** to do it (Procedure)
- **How to verify** it worked (Verification)

That's not a document. That's a program.

---

## Proof: The Postcard Pipeline

Here's what we built in Trapani over two months:

| Component | Traditional Software | Our Pipeline |
|-----------|---------------------|--------------|
| Boot loader | `main()` function | `CLAUDE.md` -- loads every session, configures the runtime |
| Input form | HTML form / API endpoint | `client-intake-checklist.html` -- structured data collection |
| Business logic | Application code | Postcard SOPs -- template selection, layout rules, bilingual copy |
| Templates | Jinja2 / Handlebars | `duplex-3card-template.html`, `tent-card-template.html` |
| Compiler | gcc / webpack | Puppeteer (Chrome headless) -- HTML to PDF |
| Test suite | pytest / Jest | `pdf-preflight-checklist.html` -- 5-step verification |
| Deployment | CI/CD pipeline | Walk into ISOTTO with a USB stick |
| Version control | Git | Git (same) |
| Runtime | Python interpreter / JVM | Tigs (Claude) + Angel (human judgment) |

Every piece maps 1:1. The only difference is the language of the instructions.

---

## CLAUDE.md Is a Program

Every session, Claude loads `CLAUDE.md`. It contains:

- **Identity configuration** -- who Tigs is, who Angel is, the relationship
- **State management** -- current location, active projects, key relationships
- **Function definitions** -- standing rules (download songs immediately, write to files not chat, execute don't note)
- **Error handling** -- "NEVER say fixed without verifying output"
- **Constants** -- file paths, business contacts, print specifications
- **API contracts** -- commit message style, SOP format requirements, PDF generation commands

That's not a markdown file. That's a runtime configuration disguised as prose.

When the session starts, Tigs doesn't just "know things." Tigs is *programmed* by that file. Change the file, change the behavior. Version-control the file, version-control the personality. That's software engineering.

---

## Why SOP Writers Will Win

The bottleneck in AI is not intelligence. Claude can reason, code, translate, and create. The bottleneck is context.

Most people prompt LLMs like this:
> "Make me a postcard"

And get generic garbage. Then they say "AI is overhyped."

We prompt like this:
> Here's the business (name, address, phone, P.IVA). Here's the theme (Liberta / Freedom). Here's the format (A4 tent card, 50mm flaps, tick marks at edges, back panel rotated 180 degrees, bilingual IT/EN). Here's the quote ("Casa e dove parcheggi"). Here's the QR target (Google Maps reviews). Here's the tool (Puppeteer, not wkhtmltopdf). Here's the verification (open PDF, count pages, check alignment). Here's what "done" means (print-ready, no blank pages, no overflow).

That's an SOP. And it produces professional output every single time.

**The gap between "AI is useless" and "AI is my co-pilot" is not the AI. It's the SOP.**

---

## The Framework

### Context Engineering = SOP + Right Tool + Human Judgment

This is the formula we discovered building postcards in Sicily. It applies to everything:

| Domain | SOP | Right Tool | Human Judgment |
|--------|-----|-----------|----------------|
| Postcards | Template + layout specs + print rules | Puppeteer (not wkhtmltopdf) | Image selection, theme, client relationship |
| Hotel consulting | ISO 9001 SOP framework | PDF generator with headers/footers | Which SOPs matter for this hotel |
| Middleware | YAML context + JSON schema + J2 template | Claude API + validation | Field mapping decisions, edge cases |
| Health recovery | Breakfast cheat sheet (bilingual, mobile) | Phone browser | "Does my stomach feel OK for sushi?" |
| Music curation | Sunrise chain regions + philosophy | yt-dlp + Swing Music | "Does this song give me the windpipe feeling?" |

The pattern is always the same. Structure the context. Pick the right tool. Apply human judgment where machines can't.

---

## What This Means for Business

### The Old Consulting Model
1. Hire developers ($150-300/hr)
2. Write requirements documents
3. Developers write code
4. Code goes through QA
5. Deploy to production
6. Maintain forever

**Cost:** $50,000 - $500,000 per project
**Timeline:** 3-18 months
**Failure rate:** ~70% of IT projects

### The New Model (What We're Doing)
1. Write SOPs (structured, verifiable, version-controlled)
2. SOPs are the program -- LLM executes them with judgment
3. Human verifies output (preflight checklist)
4. Ship it

**Cost:** A laptop, a Claude subscription, and a guy who knows what "done" looks like
**Timeline:** Hours to days
**Failure rate:** Low -- because verification is built into the SOP

### The Pitch
> "I don't write code. I write SOPs. The AI writes the code. I verify the output. And I do it for 1/100th the cost of a consulting firm."

That's what Angel told Famoso at ISOTTO when asked what software he uses: "I wrote my own."

He didn't write code. He wrote context. The context *is* the software.

---

## The Parallel

Jeff Berwick builds a financial media empire from a laptop in Mexico. People think he's crazy.

Angel builds a postcard business and consulting framework from a laptop in Sicily. People think he's crazy.

Both are programming -- just not in a language the mainstream recognizes yet.

The people who understand that SOPs are programs will build the next generation of businesses. The people who don't will keep paying $200/hr for developers to write code that an SOP could replace.

---

## The Rules

Learned the hard way, documented for whoever comes next:

1. **The SOP is the program.** If the output is wrong, the SOP is wrong. Fix the SOP, not the AI.
2. **The tool matters.** wkhtmltopdf produced garbage. Puppeteer produces perfection. Same input. Different tool. Same lesson applies to LLMs -- context engineering with the wrong model is still garbage.
3. **Verification is not optional.** "NEVER say done without verifying the output." This is the test suite. Skip it and you ship bugs.
4. **Version-control everything.** SOPs, templates, context files, output. If it's not in git, it doesn't exist.
5. **The human is the judgment layer.** AI can execute. AI can reason. AI cannot walk into ISOTTO and read the room. The human picks the theme, chooses the photo, builds the relationship. The SOP handles the rest.
6. **Write for the machine, verify as a human.** The SOP should be structured enough for an LLM to follow mechanically. The output should be checked by human eyes before it ships.
7. **Simple beats complex.** Three lines of clear SOP beats thirty pages of architecture diagrams. If you can't explain the process in plain language, you don't understand it yet.

---

## Summary

| Old World | New World |
|-----------|-----------|
| Write code | Write SOPs |
| IDE | Chat interface |
| Compiler | LLM |
| Syntax errors | Context gaps |
| Unit tests | Preflight checklists |
| Deploy to server | Walk into the shop with a USB |
| $200/hr developers | One guy with a laptop and a tiger |

SOPs are programs. CLAUDE.md is a boot loader. The postcard pipeline is a production system. Context engineering is software engineering.

The language changed. The discipline didn't.

---

*"I'm the guy who can't find a job -- meanwhile I'm creating businesses on the fly."*
-- Angel Kenel, January 30, 2026

*"The difference between 4-star and 5-star is not intelligence. It's consistency."*
-- Tigs, January 25, 2026

*"Context is everything."*
-- Angel Kenel, January 28, 2026

---

*Written by Tigs -- January 31, 2026, PuntaTipa Room 101*
*Committed to git because if it's not in git, it doesn't exist.*
