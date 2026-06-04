# La Piazza Compute Exchange (LPCX)

*The Workbench-and-Inference Marketplace. Internal. Build first, announce later.*

**One line:** La Piazza does not host AI. It hosts the **square** where the
person who needs compute meets the person with an idle machine — and settles
the trade in **credits**, not cash.

---

## 0. THE CRUX (read this first)

The whole idea lives or dies on one distinction. Get this right and everything
else snaps together:

> **Somebody's GPU always runs the model. We just don't want it to be us, and we
> don't want it to be the crown jewels.**

So there are **three separate jobs**, and people keep squishing the first two
together. Keep them apart:

```
  BRICK 1: THE BRAIN              BRICK 2: THE WORKBENCH          BRICK 3: THE SQUARE
  runs the model math            runs the apps + tools           identity, credits, trust
  ──────────────────             ─────────────────────           ────────────────────────
  • Claude API (USA)             • Frank's idle gaming GPU        • La Piazza platform
  • Ollama box (Hetzner)         • Blender / Stable Diffusion     • Keycloak  = every profile
  • Local Swiss model            • Puppeteer / PDF render         • Credit ledger (who owes who)
  • ANY model endpoint           • compile / 3D / video encode    • templates, billing, SSH certs
                                 • throwaway VM, wiped on exit     • reviews = the trust layer
  "the tokens go HERE"           "the WORK happens HERE"          "the trade settles HERE"
       (rented or BYO)                (the rented muscle)             (what WE actually build)
```

- **The Brain** does the *thinking* ("here's the code", "here's the answer").
  Pure tensor math. Lives anywhere. Plugged in via an API key. **Frank never holds
  the weights.**
- **The Workbench** does the *doing* — runs the containers that turn the Brain's
  answer into a rendered PDF, a 3D scene, an image, a compiled binary. **This is
  Frank's idle GPU.** This is literally what our box does today when it makes a
  postcard.
- **The Square** is the only thing *we* operate: who you are, what you owe, who's
  trustworthy, which template you picked. **We host the square, not the model.**

Frank lends muscle. The Brain is borrowed. We run the market. That's it.

---

## 1. THE REQUEST LIFECYCLE

```
  REQUESTER (Johnny, broke but skilled)                     PROVIDER (Frank, idle GPU)
  ────────────────────────────────────                      ──────────────────────────
            │                                                          │
            │ 1. log in to La Piazza (Keycloak)                        │ (Frank already
            │                                                          │  registered his
            ▼                                                          │  node + templates)
   ┌─────────────────────┐                                            │
   │   THE SQUARE (LP)    │  2. Johnny browses providers + templates   │
   │  ─────────────────   │ ◄──────────────────────────────────────── │
   │  • match Johnny→Frank│                                            │
   │  • check credit bal. │  3. picks template "PDF-render-v2"         │
   │  • issue SHORT-LIVED │     on Frank's node                        │
   │    SSH cert (scoped) │                                            │
   └──────────┬──────────┘                                            │
              │ 4. cert + connection details                          │
              ▼                                                        ▼
   ┌──────────────────────────────────────────────────────────────────────────┐
   │  FRANK'S WORKBENCH                                                          │
   │  ┌────────────────────────────────────────────────────────────────────┐  │
   │  │  THROWAWAY VM / container  (spun from template, wiped on exit)       │  │
   │  │   • Johnny SSHes in with the short-lived cert                       │  │
   │  │   • runs his job (render postcard PDF)                              │  │
   │  │   • job calls THE BRAIN (Claude API / Ollama) for the thinking ─────┼──┼──► BRAIN
   │  │   • GPU does the rendering muscle                                   │  │    (tokens
   │  └────────────────────────────────────────────────────────────────────┘  │     in/out)
   │   Frank's host OS is NEVER exposed. VM destroyed when Johnny leaves.        │
   └──────────────────────────────────┬─────────────────────────────────────────┘
                                       │ 5. job done, meter reads usage
                                       ▼
   ┌─────────────────────┐
   │   THE SQUARE (LP)    │  6. ledger: Johnny −50 credits, Frank +50 credits
   │  credit ledger       │  7. Johnny leaves a review → Frank's reputation grows
   └─────────────────────┘
```

**What "the tokens are sent and it comes back" actually is:**

1. Text → **tokens** (a token ≈ ¾ of a word).
2. Tokens → **the Brain**.
3. The Brain predicts the next token, then the next, one at a time (GPU sweating).
4. Tokens stream **back**, re-assembled into code/text.
5. **The Workbench runs that code** — renders the PDF, builds the image.

**Cost = (tokens in + tokens out) × GPU time.** That is the whole meter.

---

## 2. WHY SOPs ARE THE BUSINESS MODEL (not just tidiness)

Every token you send is re-read by the Brain on **every** step of its answer. So:

- Bloated 50k-token context → re-read 50k tokens per token written → **the guy
  burning a shitload of tokens.**
- Tight SOP-shaped context (~2k tokens) → same answer, **~25× cheaper.**
- **Prompt caching:** if the context is *consistent* (same SOP every time), the
  Brain remembers the setup and we don't re-charge for it. The light/regular user
  is almost free to serve → he subsidizes the system.

A template ships **with its SOP baked in.** "Pick PDF-render-v2 → here's the exact
context, the exact steps, every time." Same way, every time = cheap + reliable +
reviewable. The SOP discipline isn't housekeeping. It's the margin.

---

## 3. THE CREDIT LEDGER (the actual unlock)

People are broke but have **skills and idle hardware.** So it's not cash — it's a
**ledger.** Append-only, exactly the shape of our QA/backlog activity trail.

```sql
-- lp_compute_ledger  (sketch)
id            bigserial PK
account_id    uuid        -- Keycloak subject
kind          text        -- 'earn' | 'spend' | 'grant' | 'adjust'
amount        int         -- credits (+/-)
job_id        uuid NULL   -- the job this settled (null for grants/barter)
counterparty  uuid NULL   -- the other side of the trade
note          text        -- "rendered postcard on frank's node"
created_at    timestamptz default now()
```

- Frank lends Workbench → **+credits.**
- Johnny renders postcard → **−50 credits.**
- Johnny has no money but translates Frank's menu → **+credits** (barter).
- Nobody touched a euro. The square balanced itself.
- **New users get a starter grant** so the flywheel turns on day one.

Ledgers are tiny. Postgres on Hetzner has effectively unlimited room for this.
1,000 users of ledger rows is nothing.

---

## 4. THE TRUST LAYER (gamification — already built into La Piazza)

We already have reviews. Reputation **is** the trust layer that makes a stranger's
machine safe enough to use:

- After each job: *"seamless, easy, helpful, great template, clean SOP, in and out."*
- Provider reputation = uptime + reviews + jobs completed.
- **Tiers fall out of this automatically:** high rep → premium/realtime jobs;
  flaky → cheap async jobs only. One flag, no committee.

This is the Airbnb/Uber move: you don't trust the stranger, you trust the **score**
the square keeps on the stranger.

---

## 5. THE "SIMPLE RULE" INVARIANTS (binary defaults that kill the cons)

We don't solve hard distributed-systems problems. We **rule them out of existence**
with a default. One choice, not three.

| The scary con | The invariant (enabled by default) |
|---|---|
| Data on a stranger's machine | Every job runs in a **throwaway VM, wiped on exit.** Frank never sees inside. |
| Frank turns his PC off mid-job | Jobs are **stateless + checkpointed.** Node drops → reschedule. User never knows. |
| Model weights / IP leak | **Workbench never holds weights.** Brain is external/BYO-key. Non-issue by design. |
| No money to pay providers | **Credits, not cash.** Barter ledger + starter grants. |
| Frank is an unreliable rando | **Reputation tiers.** Score decides what jobs he's allowed. |
| Frank's host gets attacked | **Host OS never exposed.** Short-lived SSH cert scoped to the throwaway VM only. |

---

## 6. WHAT WE REUSE (this is why it's days, not years)

| Need | We already have it |
|---|---|
| Identity / login / profiles | **Keycloak** (every realm, every user, `helix_pass`) |
| Storage (ledger, templates, jobs) | **Postgres on Hetzner** — upgrade is a slider |
| Billing / subscription bones | LP billing module |
| Append-only activity trail pattern | QA bug trail + backlog activity (built 3×) |
| Model access | **Ollama key (BH_OLLAMA_KEY)** + any provider API |
| Deploy / smoke / sweep gates | `scripts/smoke-test.sh`, `tests/e2e/console-sweep.js` |
| Big-image distribution | **BitTorrent** for Docker layers / model files (save bandwidth + space) |

The genuinely **new** parts: (a) the **provider agent daemon** that registers a
node and spins throwaway VMs, (b) the **SSH certificate authority** that issues
short-lived scoped certs, (c) the **matchmaker** that pairs requester→provider.
Everything else is our existing LEGO.

---

## 7. MVP — THE 1-2 DAY VERTICAL SLICE (honest scope)

Build the thinnest end-to-end thread that actually settles a real trade. Resist
building the whole market.

**In scope (the slice):**
1. `lp_compute_ledger` table + a `/compute/credits` balance view.
2. **One** provider node = our own Hetzner box (we are Frank #1). Register it with
   one template: `pdf-render` (Puppeteer postcard, the thing we already do).
3. Requester flow: log in → see balance → "run pdf-render job" → job runs in an
   ephemeral container → ledger debits → review prompt.
4. Brain = our existing Ollama/Claude key. No change.
5. Smoke check + console sweep green. Human-verify one real postcard end to end.

**Explicitly NOT in the slice (later phases):**
- Third-party providers / real strangers' GPUs (needs the SSH-CA + agent daemon
  hardened — this is the real security work, do it deliberately, not in a rush).
- BitTorrent layer distribution.
- Marketplace browse/search, tiers, payouts to cash.
- Multi-node scheduling / checkpoint-reschedule.

> The slice proves the **economic loop** (job → ledger → review) on hardware we
> already trust. Strangers' machines come *after* the loop is proven, because that's
> where the security cost lives and it deserves its own focused build — not a
> "set it up in a day" corner-cut. If one seal is loaded, inspect all the seals
> before you let strangers in.

---

## 8. OPEN QUESTIONS (park, don't block)

- **SSH-CA scope:** short-lived certs (minutes), one VM, auto-revoke on job end.
  Needs a clean design before any non-LP node joins.
- **Credit→cash bridge:** do credits ever cash out, or stay a closed economy?
  (Closed is simpler and dodges money-transmitter regulation. Start closed.)
- **Abuse:** what stops someone renting muscle to mine crypto / do something
  illegal? → template allowlist + reputation + the throwaway VM has no persistent
  outbound by default.
- **Brain billing passthrough:** if Johnny uses our Claude key, his token cost is
  real euros to us → credits must price that in, or require BYO-key for paid Brains.

---

*Build first. Announce later. The square goes up before the speech.*
*"We host the square, not the model."*
