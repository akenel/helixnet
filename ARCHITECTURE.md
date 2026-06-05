# La Piazza / HelixNet — The Castle Map

*The whole thing on one page: boxes, IPs, what runs where, how work flows.*
*Render: GitHub shows the Mermaid diagrams below automatically. Edit = just text.*

---

## The three machines

```mermaid
flowchart TB
  porkbun["🌐 Porkbun DNS (akenel)<br/>lapiazza.app · *.lapiazza.app"]

  subgraph LAPTOP["💻 Angel's Laptop — DEV"]
    direction TB
    dns1["helix.local (self-signed)"]
    dev["helix-platform (FastAPI)<br/>Bottega · Compute Exchange<br/>camper · isotto · pos · qa · backlog"]
    devkc["Keycloak<br/>realms: <b>lapiazza</b> · camper · pos · borrowhood"]
    devpg[("Postgres")]
    devmq["RabbitMQ + lpcx-consumer<br/>(local jobs)"]
    dev --> devkc & devpg & devmq
  end

  subgraph HETZNER["☁️ Hetzner — 46.62.138.218 (the prod box)"]
    direction TB
    caddy["Caddy (HTTPS, Let's Encrypt)"]
    subgraph prodapps[" "]
      direction TB
      bh["borrowhood<br/><b>lapiazza.app</b> (PROD marketplace)"]
      bhs["borrowhood_staging<br/>staging.lapiazza.app"]
      hp["helix-platform<br/><b>bottega.lapiazza.app</b><br/>Bottega · Compute Exchange"]
    end
    kc["Keycloak (shared)"]
    pg[("Postgres (shared)")]
    mq["RabbitMQ + lpcx-consumer"]
    caddy --> bh & bhs & hp
    hp --> kc & pg & mq
  end

  subgraph DO["🌊 DigitalOcean — 206.189.30.236 (helix-hub)"]
    worker["lpcx-worker (container)<br/>pulls jobs · runs recipe · returns result<br/>node = do-staging-0"]
  end

  porkbun -->|"A records"| caddy
  worker -->|"HTTPS pull/result<br/>X-Node-Token"| caddy
  worker -.->|"runs recipe via brain"| brain["🧠 Ollama Turbo<br/>ollama.com (shared brain)"]
  hp -.->|"shared brain"| brain
  dev -.->|"shared brain"| brain
```

---

## How a job flows (the genie loop)

```mermaid
sequenceDiagram
  participant U as You (browser)
  participant B as Broker (helix-platform @ bottega.lapiazza.app)
  participant DB as Postgres
  participant W as Worker (DO box, do-staging-0)
  participant Brain as Ollama Turbo

  U->>B: submit job (recipe + inputs + node=do-staging-0)
  B->>DB: store job (queued) — NOT enqueued locally
  W->>B: GET /worker/next?node=do-staging-0 (X-Node-Token)
  B->>DB: pick oldest queued, mark running
  B-->>W: resolved {system, prompt}  (allowlist is broker-side)
  W->>Brain: chat(system, prompt)
  Brain-->>W: output
  W->>B: POST /worker/result {output, tokens}
  B->>DB: store output · settle ledger (spend/earn) · mark done
  U->>B: "view output" → GET /jobs/{id}
  B-->>U: rendered result
```

---

## Who guards which door (Keycloak realms)

```mermaid
flowchart LR
  lp["<b>lapiazza-realm-dev</b><br/>'La Piazza'<br/>users: angel (lapiazza-user/admin)"] --> bottega["La Bottega + Compute Exchange"]
  camper["kc-camper-service-realm-dev<br/>'Camper & Tour'<br/>nino, sebastino…"] --> camperapp["Camper app · qa · backlog"]
  bhr["borrowhood realm"] --> market["lapiazza.app marketplace"]
  pos["kc-pos-realm-dev"] --> posapp["POS"]
```

---

## The cheat-sheet

| Thing | Where | Notes |
|---|---|---|
| **DEV** | laptop, `helix.local` | full stack; login works; no live remote worker |
| **PROD marketplace** | `lapiazza.app` → Hetzner | borrowhood app, real traffic — **do not break** |
| **Bottega / Compute** | `bottega.lapiazza.app` → Hetzner | helix-platform; shares the box with prod |
| **staging (marketplace)** | `staging.lapiazza.app` → Hetzner | borrowhood_staging only |
| **Worker node** | `206.189.30.236` (helix-hub) | `lpcx-worker`, node `do-staging-0`, pulls from bottega |
| **Shared brain** | `ollama.com` (Turbo) | flat-rate; workers relay to it (no local model yet) |
| **The rule** | — | a Bottega deploy is a **prod-box** deploy: gate on dev → pull+restart → verify prod 200 |

*Live flow view (jobs moving through this in real time) = the Grafana dashboard, built next.*
