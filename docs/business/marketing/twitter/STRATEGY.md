# La Piazza on X (Twitter) — Marketing Strategy

*Created May 25, 2026. Owner: Angel. Account email: artemisthinking@gmail.com (fresh, never used as an X login).*

---

## The honest premise (read this first)

Someone told Angel to "market La Piazza on Twitter." Half right.

**X will NOT fill the marketplace with Trapani locals.** Italian neighbors lending drills,
books, and tools live on WhatsApp, Facebook groups, and Instagram. Italy is a weak X market
for hyper-local community stuff. Spending energy chasing Trapani users on X is pushing a rope.

**X IS excellent for the layer underneath La Piazza: the build-in-public story.**

> A Swiss-Canadian dev builds a zero-fee, six-in-one neighborhood marketplace from a camper
> van in Sicily — bilingual, self-hosted, no VC, no algorithm, every euro stays with the neighbor.

That story reaches the people who actually convert into money right now:
- **Indie hackers / #buildinpublic** crowd — attention, follows, social proof
- **Potential "HelixNet as a Service" clients** — Swiss SMEs, founders who want the stack
- **Contract / freelance leads** — SAP PI/PO, FastAPI, Keycloak, Docker (the Wipro-tier work)
- **Future La Piazza partner towns** — other operators who want a Piazza in *their* square

So: **X is a top-of-funnel brand + lead engine for Angel-the-builder, not a user-acquisition
channel for La Piazza-the-marketplace.** We market the journey; the journey sells everything else.

---

## Audience (in priority order)

1. **#buildinpublic / indie hackers** — relate to the solo-builder grind, zero-fee ethos, self-hosting
2. **FastAPI / Python / self-hosted / homelab devs** — the stack is the hook (Keycloak, Caddy, Docker, Hetzner €7/mo)
3. **Anti-big-tech / "own your data" / co-op / degrowth** — "no algorithm, no fees, no ransom" resonates
4. **Recruiters & founders** — the contract pipeline; they lurk, they DM
5. **Sicily / Trapani / expat-in-Italy** — soft local color, not the primary funnel

## Positioning pillars (what every post should ladder up to)

- **Zero fees, forever.** "We don't take a cut. Every euro stays with the neighbor."
- **Six apps in one.** Items, makers, events, raffles, help board, bottega — one login.
- **Built from a camper van.** Real constraints, real place, no office, no funding.
- **Self-hosted & open.** Public repo, €7/mo box, no Silicon Valley landlord.
- **Local-first, human-first.** Verified profiles, no anonymous accounts, no algorithm.

## Voice

The Great Escape voice — plain, a little poetic, never corporate. Short sentences. Real
numbers. Show the work. Occasional Sicilian/Italian phrase ("Casa è dove parcheggi.",
"Prendi & Presta"). No emojis unless they earn their place. No engagement-bait threads that
don't deliver. Foo Fighters don't lie about the work being done.

---

## Content mix (weekly rhythm — aim 1 post/day, 5–7/week to start)

| Day | Pillar | Format |
|---|---|---|
| Mon | Build log — what shipped last week | screenshot + 1-liner |
| Tue | The "why" — zero fees / no algorithm ethos | short take or quote |
| Wed | Tech / stack detail (FastAPI, Keycloak, Hetzner cost) | code/diagram + lesson |
| Thu | Sicily texture — camper, Trapani, a real moment | photo + story |
| Fri | Feature spotlight — one of the six apps | screen recording / GIF |
| Sat | Engage — reply to 5 #buildinpublic / FastAPI accounts | replies, not posts |
| Sun | Reflection / numbers / weekly recap thread | thread |

**Ratio guide:** ~60% build-in-public, ~20% ethos/opinion, ~20% Sicily/human color.

## Growth tactics (no bots, no buying)

- **Reply > post.** Most early reach comes from thoughtful replies to bigger accounts in
  #buildinpublic, FastAPI, self-hosting, r/selfhosted-adjacent folks. Budget 10 min/day.
- **Ship in public.** Every deploy is a post. The smoke-test, the €7 Hetzner box, the
  bilingual toggle — devs love concrete detail.
- **One pinned thread** that tells the whole story (see PROFILE.md). It's the landing page.
- **Cross-post the YouTube videos** (Keycloak series, Camper demo) — native upload clips, not links.
- **Link discipline.** X throttles outbound links. Put the link in a reply or the profile,
  not the main post, for reach-sensitive posts.
- **Hashtags, sparingly:** `#buildinpublic` `#FastAPI` `#selfhosted` `#indiehackers`. 1–2 max.

## What NOT to do

- Don't pretend it's a polished startup. The camper van *is* the moat.
- Don't post "Sign up for La Piazza!" to a global audience who can't use a Trapani app. CTA is
  *follow the build* / *want one in your town?* / *want this stack?* — not local signups.
- Don't buy followers, don't engage-bait, don't auto-DM. Burns the fresh account's trust score.
- Don't go silent for 3 weeks then dump 10 posts. Consistency beats intensity (same as the SOPs).

## Metrics that matter

- **Leading:** posts/week shipped, replies/week, profile clicks, link clicks to repo/lapiazza.app
- **Lagging:** follows from devs/recruiters, DMs that turn into a call, repo stars, contract leads
- **Vanity (ignore):** raw follower count, likes without clicks

## The funnel, end to end

```
X build-in-public posts
   → profile click → pinned story thread
      → repo (github.com/akenel/helixnet)  OR  lapiazza.app demo
         → DM / email → "HelixNet as a Service" call  OR  contract lead  OR  partner town
```

X's job is the first arrow. Everything else is already built.

---

## Setup checklist (do once)

- [ ] Create X account with artemisthinking@gmail.com
- [ ] Handle: see PROFILE.md options (check availability in order)
- [ ] Bio, location, link, banner, avatar — all from PROFILE.md
- [ ] Pin the story thread (PROFILE.md)
- [ ] Apply for X API access at developer.x.com (Free tier: write-only, ~1.5k posts/mo — enough to post)
- [ ] Drop API keys into `.env` (see `scripts/lp_tweet.py` header) — never commit them
- [ ] Queue first 2 weeks from `tweets-batch-01.md`

*"We market the journey. The journey sells everything else."*
