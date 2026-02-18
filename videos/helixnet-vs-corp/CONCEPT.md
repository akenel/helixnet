# "One Afternoon vs 16 Weeks" -- Video + LinkedIn Concept

## THE HOOK

SAP implementation: EUR 200,000. 16 weeks. 12 consultants. PowerPoint decks.
HelixNet UAT: EUR 7.59/month. One afternoon. Two people (one of them is an AI).

This isn't a speed flex. It's a systems problem.
The corps aren't slow because they're dumb. They're slow because they built
permission structures that eat time alive.

---

## YOUTUBE VIDEO

**Title options (pick one):**
- "We built what SAP charges EUR 200k for -- in one afternoon"
- "Why enterprise IT takes 16 weeks to do what we did before dinner"
- "EUR 7.59 vs EUR 200,000 -- the real cost of corporate IT"

**Format:** Talking head + screen demo (7-10 minutes)

**Structure:**

  INTRO (0:00 - 1:00)
  "Let me show you something we did yesterday."
  Show the Anne testing URL live in browser. HTTPS. Login. Works.
  "That took us one afternoon. A corp would take 16 weeks and EUR 200k.
  Here's why -- and why it matters for every Swiss SME paying SAP invoices."

  ACT 1 -- WHAT WE BUILT (1:00 - 3:00)
  Screen demo: show the stack
  - 6 services, one compose file
  - Hetzner console, EUR 7.59/mo server
  - Keycloak login, RBAC roles, the whole flow
  "This is a production-grade identity + microservice platform.
  Same thing SAP charges you EUR 50k/year to license."

  ACT 2 -- THE COMPARISON (3:00 - 6:00)
  Show the table. Read each row. Let it land.

  Phase              | Corp              | Us
  -------------------|-------------------|-------------------
  Requirements       | 2 weeks, 4 mtgs   | "Hetzner, let's go"
  Architecture       | Review board      | Done in chat
  Server             | Infra ticket      | 30 sec on console
  Docker             | Infra backlog     | one curl command
  TLS cert           | Security team     | one openssl command
  UAT live           | 8-16 weeks        | One afternoon
  Cost               | EUR 50-200k       | EUR 7.59/mo

  "The difference isn't intelligence. It's decision latency.
  Corps spend 90% of their time asking permission.
  We spend 90% of our time building."

  THE REAL KICKER:
  "When our TLS cert broke -- SNI doesn't work on IP addresses, by the way --
  there was no war room. No post-mortem scheduled for next Tuesday.
  We fixed it in the next message. That's not speed. That's ownership."

  ACT 3 -- THE POINT (6:00 - 8:30)
  "Swiss SMEs are paying SAP EUR 50-200k per year for systems that
  take 6 months to change a form field. That's not a feature. That's a trap.
  HelixNet is built for the 5-50 person company that needs real tools
  without the enterprise ransom. FastAPI. Keycloak. Docker. Open source.
  You own it. No license. No lock-in."

  OUTRO (8:30 - 10:00)
  "If you're a Swiss SME asking why your IT costs more than your rent --
  let's talk. Link in the description."
  [Show HelixNet outro card]

---

## LINKEDIN POST

**Post (copy-paste ready):**

---

We built a production UAT environment yesterday.

HTTPS. OAuth2 login. Role-based access control. 6 microservices.
Running 24/7 on a dedicated server.

Cost: EUR 7.59/month.
Time: one afternoon.

Here's what a corp takes for the same thing:

  Requirements gathering:  2 weeks, 4 meetings
  Architecture approval:   3 weeks, review board
  Server provisioning:     1-2 weeks, infra ticket
  Docker setup:            1 week, infra backlog
  TLS certificate:         2 weeks, security team
  UAT environment live:    8-16 weeks total
  Budget:                  EUR 50,000-200,000

The difference isn't intelligence or tools.

It's decision latency.

Corps spend 90% of their time asking permission.
We spend 90% of our time building.

When something broke (TLS/SNI on IP addresses),
there was no war room. No post-mortem next Tuesday.
We fixed it in the next message.

That's the difference between enterprise IT and lean engineering.

Swiss SMEs are paying SAP EUR 50-200k/year for systems
that take 6 months to change a form field.

There's a better way.

[link to YouTube video]

#HelixNet #SAP #Swiss #SME #FastAPI #Keycloak #DevOps #EnterpriseIT

---

## HOW TO PRODUCE THE VIDEO

**Option A: Talking head + screen share (fastest, this week)**
- Angel on camera OR voice only (no camera needed)
- Screen recording of: Hetzner console, Docker compose up, browser login
- Use existing KC recording pipeline (OBS screen capture)
- Voiceover: record as Telegram voice messages, process through ffmpeg pipeline
- Total production: 3-4 hours

**Option B: Animated explainer (more polished, next week)**
- HTML slides with the comparison table (Puppeteer screenshots)
- Voiceover over slides
- No camera needed -- just the data and the voice

**Recommendation: Option A first.**
Get it out. The content is the value, not the production quality.
A shaky real demo beats a polished nothing every time.

---

## THE POSITIONING

This video does three things:

1. Attracts Swiss SME owners who are sick of paying SAP
2. Signals to developers: HelixNet is serious, real, production-grade
3. Makes the Wipro/SAP crowd uncomfortable (good -- that's the point)

The number that makes SAP people squirm: EUR 7.59/mo.
Not because it's cheap. Because it works.

---

*Draft: Feb 17, 2026*
