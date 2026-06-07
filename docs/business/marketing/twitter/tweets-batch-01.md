# La Piazza — Tweet Batch 01 (first ~2 weeks)

*Copy-paste ready, or feed to `scripts/lp_tweet.py`. Each `## ---` block is one post.*
*Voice: plain, concrete, no engagement-bait. 1–2 hashtags max. Links go in a reply, not the main post.*

---

## --- pillar: build log
La Piazza ships its 47th feature this week: live raffles where every cent stays in the neighborhood.

No house cut. The pot goes to a real person down the street.

Built from a camper van in Sicily, on a €7/mo server. #buildinpublic

## --- pillar: ethos
Every marketplace you use takes a cut. 10%. 20%. 30%.

La Piazza takes zero. Forever.

If the drill rental is €5, the neighbor gets €5. We're not the landlord of your street.

## --- pillar: tech
The whole La Piazza stack runs on one Hetzner box: €7.59/mo.

FastAPI + Keycloak + Postgres + Redis + RabbitMQ + Caddy, all Docker Compose.

You don't need a Series A to build something real. You need one good box. #selfhosted

## --- pillar: sicily
Office update: it's a camper van called MAX, parked in Trapani.

The roof leaked for years and rotted end to end. Found it because I insisted on a ladder.

Lesson that applies to code too: when one seal fails, check all the seals.

## --- pillar: feature
La Piazza isn't one app. It's six, one login:

· Items — borrow, lend, sell
· Makers — hire the artisan next door
· Events — workshops, language exchange
· Raffles — win for a few €
· Help Board — ask the street
· Bottega — a page for your craft

## --- pillar: ethos
"No ads. No algorithm. No monthly ransom."

That's the rule for the music player I self-host. Turns out it's the rule for the whole platform.

You're a neighbor here, not a data point.

## --- pillar: build log
Shipped a bilingual toggle (🇮🇹/🇬🇧) across all of La Piazza today.

Not a "we'll localize later" toggle. It's actually used — by people in Trapani who don't speak English and tourists who don't speak Italian.

Prendi & Presta. Borrow & Lend.

## --- pillar: tech
Hard-won lesson this week:

`class Status(str, Enum): REQUESTED = "requested"`

`.name` is "REQUESTED". `.value` is "requested".

A UI workflow was dead for months because a template compared the wrong one. Curl the rendered HTML — never trust the eyeball alone. #FastAPI

## --- pillar: ethos
The drill you need is in a garage 200 meters away.

The person who can fix your bike runs a shop on your corner.

Your neighborhood already has everything. La Piazza just connects it — and takes nothing.

## --- pillar: sicily
Built a postcard business on the side while building the app.

25 cents to print a card, sell the experience for €5–15. Wax seal, local herbs, vendor mails it for the tourist.

Software pays slow. Postcards pay today. The escape needs both.

## --- pillar: feature
The Help Board on La Piazza: ask your neighborhood anything.

"Anyone got a ladder?" "Who fixes espresso machines?" "Lost cat, gray, near the port."

Answers usually within the hour. Because it's real neighbors, not strangers.

## --- pillar: build log
Every deploy to La Piazza goes through a 25-check smoke test that runs in 5 seconds.

I added it after a bug shipped to prod and a tester found it before I did. Embarrassing once. Never again.

CI without alerts is theater. #buildinpublic

## --- pillar: tech
Why Keycloak instead of rolling my own auth?

Because auth is where solo builders go to die. RS256 JWTs, OIDC, multi-realm, social login — all solved, all free, all self-hosted.

Build your product, not your login page. #selfhosted

## --- pillar: ethos
I left Switzerland — the dragon's mouth — to build this on the road.

No office. No funding. No investor telling me to "increase take rate."

The take rate is zero. That's not a strategy I'll grow out of. It's the point.

## --- pillar: feature
Open a Bottega on La Piazza: a public page for your craft.

Your trade, your services, your story, your reviews. Verified, not anonymous.

The corner shop, but it also exists at 2am when the tourist is googling "who fixes sandals in Trapani."

## --- pillar: weekly recap (thread)
Week in the camper van, building La Piazza 🧵

· Shipped live raffles (zero house cut)
· Bilingual toggle across the whole app
· 25-check smoke test on every deploy
· Found a 3-year roof leak in the van (separate saga)

Slow is smooth. Smooth is fast. Next 👇

## --- pillar: build log
La Piazza runs in 4 environments with a locked naming convention: dev → staging → uat → prod.

Rule I never break: nothing hits prod without explicit staging sign-off. Even "low-risk" changes.

The "low-risk" ones are exactly the ones that take you down. #buildinpublic

## --- pillar: ethos
Six apps. One piazza. Zero fees.

That's the whole pitch. A digital town square that behaves like a real one — you know your neighbors, every euro stays local, and nobody's mining your attention.

Made in Sicily, from a camper van.

## --- pillar: tech
The repo is public: github.com/akenel/helixnet

FastAPI platform, Keycloak OIDC, Caddy, the works — and La Piazza built on top.

Want this stack for your own town or project? It's all there. Steal it. (reply for the link)

## --- pillar: sicily
"Casa è dove parcheggi." — Home is where you park it.

Wrote that on a postcard for a camper rental shop in Trapani. They approved it on the spot.

Turns out it's also my product roadmap.
