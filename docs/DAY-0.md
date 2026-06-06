# La Piazza — Day 0 🃏

*The whole game on one page. Locked 2026-06-06. Open this first.*
*Day 0 = surveyed, drawn, agreed, foundation poured, baseline at zero. Day 1 = the first cut.*

---

## 🗺️ The four parts (architecture)

```
        ┌──────────────────────────────────────────────────────────────┐
        │  🐙 GITHUB  github.com/akenel/helixnet                         │
        │  the code + every blueprint & doc  ·  main = source of truth   │
        └──────────────────────────────────────────────────────────────┘
              ▲ push                                      │ pull
              │                                           ▼
 ┌───────────────────────────┐     ┌────────────────────────────────────────────┐
 │ 💻 LAPTOP — DEV            │     │ ☁️ HETZNER  46.62.138.218  — THE MAIN BOX   │
 │    helix.local            │     │    8 GB · everything shares this one machine │
 │  • build & break here     │     │  ┌──────────────────────────────────────────┐│
 │  • TEST account           │     │  │ 🟥 PROD     lapiazza.app   (real market)  ││
 │  • Grafana, the lab       │     │  │ 🟨 STAGING  staging.lapiazza.app          ││
 └───────────────────────────┘     │  │ 🟩 BOTTEGA  bottega.lapiazza.app (the walk)││
                                    │  └──────────────────────────────────────────┘│
                                    │  + Keycloak · Postgres · RabbitMQ · Caddy     │
                                    └────────────────────────────────────────────┘
                                          ▲ pulls jobs (HTTPS, dials out)
                                          │
                              ┌───────────────────────────┐      ┌────────────────┐
                              │ 🌊 DIGITALOCEAN  helix-hub │ ───► │ 🧠 ollama.com  │
                              │    lpcx-worker (the DOer)  │      │  shared brain  │
                              │    alive · runs the jobs   │      └────────────────┘
                              └───────────────────────────┘
```

**Build on the laptop → push to GitHub → the Hetzner box runs prod + staging + bottega → the DO box pulls the jobs and thinks with ollama.**
⚠️ **The one risk in the picture:** everything real lives on the *one* Hetzner box. The architecture cut that matters most = mem-limits + a monitoring alert.

## 📋 The four plans (all committed in `docs/`)
1. 🐺 **[Angel's Blueprint](LA-PIAZZA-BLUEPRINT.md)** — the 30-day comeback (headline → portfolio → outreach → contract)
2. 🏛️ **[La Piazza's Blueprint](LA-PIAZZA-BLUEPRINT.md)** — the platform 30/60/90 (go-live: *one real comeback*)
3. 🎭 **[The Legend Journey](LA-PIAZZA-THE-LEGEND-JOURNEY.md)** — *how* the coaching works (mentors, Houses, three-strikes)
4. 🗺️ **[The Architecture](../ARCHITECTURE.md)** — the full castle map

## 🎭 Two roles → two accounts
- **Builder** → TEST account → `helix.local` (dev, the lab)
- **User** → REAL account (the SAP specialist) → `bottega.lapiazza.app` (the walk) — *login fix is a Day-1–30 cut*

## ❤️ The mission (the real people)
Patient Zero: **Angel.** Then the community he already made in Trapani — **Flora** (69, cook, apartment to rent), **Corrado** (painter, two rentals + a sailboat), **Diego** (special forces, best buddy), **Peter** (83, independent, sharp). Help them succeed → prove it works → the rope pulls the next.

## 🚨 The one disease (the BHT bottom line)
*Building instead of shipping* — Angel's blocker, the platform's risk, the architecture's sprawl, all one thing. The cure is one act: **walk the blueprint.** Resist the factory.

## ✂️ The next cut — Day 1
- 🐺 **Angel:** one LinkedIn headline. That's the whole day.
- 🏛️ **La Piazza:** assemble the Legend Journey into one walkable loop + fix the public login.

> *"The factory is built. The only enemy left is the pull back into the workshop."*
