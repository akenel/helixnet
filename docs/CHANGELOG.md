# 🧩 HelixNet Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]
### 🚧 Work in Progress
- Setting up API orchestration layer (FastAPI)
- Preparing the message broker tuning (RabbitMQ + Redis)
- CI/CD automation for HelixNet stack


### @Becks | Nov-2025 
You’ve got two parallel fronts to manage:
1️⃣ **Auth foundation** (real tokens, users, and role enforcement)
2️⃣ **UX layer** (dashboard, job submit, and secure flow between them)

Let’s break this into a *precise sprint plan* so Helix “goes green” across Swagger, Keycloak, and the HTML mock dashboard.

---

## ⚙️ WEEKLY SPRINT: *“The Realm of Fire” (Auth & Access Sprint)*

> Goal: Replace mock tokens with real Keycloak JWT bearer tokens
> and protect the app’s frontend routes + Swagger UI endpoints.
> Finish with real logins, real users, and real RBAC flows.

---

### 🧩 Phase 1 — Swagger + FastAPI Bearer Auth ✅

**Objective:** Make the API auth work first before touching the HTML templates.

**Tasks:**

1. **Connect FastAPI to Keycloak OpenID config**

   * Add an auth dependency in `app/deps.py` using Keycloak’s JWKS endpoint.
   * Example:

     ```python
     from fastapi import Depends, HTTPException, status
     from fastapi.security import HTTPBearer
     import jwt, requests

     oauth2_scheme = HTTPBearer()

     KEYCLOAK_URL = "https://keycloak.localhost/realms/helix-realm"
     JWKS = requests.get(f"{KEYCLOAK_URL}/protocol/openid-connect/certs").json()

     def verify_token(token: str = Depends(oauth2_scheme)):
         try:
             unverified = jwt.decode(token.credentials, options={"verify_signature": False})
             kid = unverified["kid"]
             key = next(k for k in JWKS["keys"] if k["kid"] == kid)
             jwt.decode(token.credentials, key, algorithms=["RS256"], audience="account")
         except Exception as e:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
         return unverified
     ```
   * Attach to routes like:

     ```python
     @app.get("/jobs", dependencies=[Depends(verify_token)])
     ```

2. **Swagger “Authorize” Button**

   * In `FastAPI()` add:

     ```python
     openapi_url="/openapi.json",
     docs_url="/docs",
     redoc_url=None,
     ```
   * Set up an OAuth2 scheme:

     ```python
     from fastapi.openapi.utils import get_openapi

     app.openapi_schema = get_openapi(
         title="Helix API",
         version="0.0.1",
         description="Async orchestration API powered by Helix",
         routes=app.routes,
     )
     app.openapi_schema["components"]["securitySchemes"] = {
         "OAuth2": {
             "type": "oauth2",
             "flows": {
                 "authorizationCode": {
                     "authorizationUrl": f"{KEYCLOAK_URL}/protocol/openid-connect/auth",
                     "tokenUrl": f"{KEYCLOAK_URL}/protocol/openid-connect/token",
                     "scopes": {},
                 }
             },
         }
     }
     app.openapi_schema["security"] = [{"OAuth2": []}]
     ```

   ✅ Result:
   Swagger UI’s “Authorize” → redirects to Keycloak → gets a token → can call `/jobs`.

---

### 🧠 Phase 2 — HTML Frontend + Keycloak Integration

**Objective:** Make your two HTML templates (dashboard + submit_form) use Keycloak’s tokens for session-based access.

**Tasks:**

1. Use **Keycloak JS Adapter** for frontend login.

   * Add this in `base.html` before the closing `</body>`:

     ```html
     <script src="https://cdn.jsdelivr.net/npm/keycloak-js@latest/dist/keycloak.min.js"></script>
     <script>
       const keycloak = new Keycloak({
         url: "https://keycloak.localhost/",
         realm: "helix-realm",
         clientId: "helix-ui",
       });

       keycloak.init({ onLoad: "check-sso", pkceMethod: "S256" }).then(authenticated => {
         if (!authenticated) {
           window.location.href = "/dashboard"; // generic welcome
         } else {
           sessionStorage.setItem("token", keycloak.token);
           document.body.classList.add("logged-in");
         }
       });

       function logout() {
         keycloak.logout();
       }
     </script>
     ```

2. In `submit_form.html`, protect access:

   ```html
   <script>
     if (!sessionStorage.getItem("token")) {
       window.location.href = "/dashboard";
     }
   </script>
   ```

3. Add a “Login” / “Logout” button to `dashboard.html` header:

   ```html
   <button onclick="keycloak.login()" class="bg-indigo-600 text-white px-4 py-2 rounded-lg">Login</button>
   <button onclick="logout()" class="bg-red-600 text-white px-4 py-2 rounded-lg hidden" id="logoutBtn">Logout</button>

   <script>
     if (sessionStorage.getItem("token")) {
       document.getElementById("logoutBtn").classList.remove("hidden");
     }
   </script>
   ```

✅ Result:

* Not logged in → redirected to dashboard welcome.
* Logged in → token saved → can access `/submit_form`.

---

### 🧰 Phase 3 — Dev & Testing Utilities

**Goal:** Make your life easier testing Keycloak + Mailhog + Swagger.

**Tasks:**

1. Add fake users in realm:

   * `helix_admin` → role: `admin`
   * `helix_user` → role: `user`
   * `helix_viewer` → role: `readonly`
2. Mailhog running → can reset password via email.
3. Add a `scripts/helix-auth-test.sh`:

   ```bash
   curl -X POST \
     -d "client_id=helix-ui" \
     -d "username=helix_user" \
     -d "password=helix_pass" \
     -d "grant_type=password" \
     https://keycloak.localhost/realms/helix-realm/protocol/openid-connect/token | jq .
   ```

✅ Result:

* You can test tokens directly in terminal and via Swagger.
* You can see emails in Mailhog for reset and activation.

---

### 🧭 Phase 4 — Dashboard Logic Polishing

**Goal:** Make `/dashboard` RBAC-aware.

Add logic in your FastAPI router:

```python
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request, token: dict = Depends(verify_token)):
    roles = token.get("realm_access", {}).get("roles", [])
    context = {"user_roles": roles}
    return templates.TemplateResponse("dashboard.html", context)
```

Then in HTML:

```html
{% if 'admin' in user_roles %}
   <p>👑 Welcome, Admin! Manage all jobs.</p>
{% elif 'user' in user_roles %}
   <p>🧑‍💻 Welcome, Operator! Submit jobs below.</p>
{% else %}
   <p>👀 You’re in read-only mode.</p>
{% endif %}
```

✅ Result:
Dynamic dashboard text based on RBAC roles.

---

### 🗓️ Sprint Milestones

| Day | Focus                               | Deliverable                                  |
| --- | ----------------------------------- | -------------------------------------------- |
| Mon | FastAPI ↔ Keycloak JWT verification | `/jobs` protected via token                  |
| Tue | Swagger UI authorize flow           | Working OAuth2 login                         |
| Wed | Frontend: login + redirect          | `/dashboard` + `/submit_form` access control |
| Thu | Curl + Mailhog tests                | Password reset flow validated                |
| Fri | Cleanup & commit                    | v0.1.1 Auth milestone tagged                 |

---

### ⚡ Next Sprint Preview (Week 2)
Excellent! This is a fantastic foundation. You've moved from a concept to concrete, actionable plans for promotion, logistics, and content creation. The rhythm you've outlined is very sustainable and aligns perfectly with the "build in public" ethos.

Let's get that first week sketched out so you can start executing immediately. 
Also provided a few strategic tips based on outlined workflow.

Here is a detailed plan for first week, following the calendar.

---

### 🚀 Week 1 Detailed Plan (Let's say starting Monday, Dec 1)

**🎯 Theme for the Week: "Helix Bootstrap & CSV Automation"**
*This is a great starting point because it's fundamental, visual, and has clear real-world applications.*

#### **Day 1 – Raw Recording (Monday)**
*   **PR/Topic Choice:** **"Initial Helix Stack Setup with Docker Compose & Basic CSV Parser Module"**
*   **Recording Focus:**
    1.  **The "Why":** Start on camera. "Welcome back. This week, we're bootstrapping a Helix instance from scratch. The goal is to have a basic CSV data ingestion flow working by the end."
    2.  **The Setup:** Show the blank directory. Run `docker compose up` for the core stack (Postgres, MinIO, n8n). Talk about what each service does as it starts.
    3.  **The Hiccup (Embrace it!):** Maybe a port conflict happens. Show yourself diagnosing it (`netstat` or `lsof`), explaining the problem, and changing the port in the `compose.yml`. This is gold for authenticity.
    4.  **The Build:** Create a simple Python script (`modules/csv_parser/process.py`) that reads a sample CSV file (e.g., `contacts.csv` with name, email) and prints the data.
    5.  **The Integration:** Show how to call this script from a simple n8n workflow (using the `Execute Command` node). Trigger it and show the output in the n8n logs.
*   **OBS Setup:** Make sure your code editor is full-screen, with a small camera overlay in the corner. Use a microphone for good audio.

#### **Day 2 – Repo Update (Tuesday)**
*   **Push Changes:** Commit and push the `docker-compose.yml` file and the new `modules/csv_parser/` directory.
*   **Update README:** Add a "Quick Start" section to the main README.md:
    ```markdown
    ## Quick Start

    1.  Clone this repo: `git clone https://github.com/yourusername/helix-stack.git`
    2.  Navigate to the directory: `cd helix-stack`
    3.  Start the stack: `docker compose up -d`
    4.  Access n8n at: `http://localhost:5678`
    5.  See the `docs/week-1-csv-parser.md` for your first automation.
    ```
*   **Create Cheat Sheet:** Create `docs/week-1-csv-parser.md`:
    *   **Title:** Helix Cheat Sheet #1: Bootstrap and CSV Parsing
    *   **Contents:**
        *   Objective: Get the stack running and process a CSV file.
        *   Docker Commands: `up`, `down`, `logs`
        *   Code Snippet: The basic Python CSV reading code.
        *   n8n Node Used: `Execute Command` node.
        *   Common Issues: Port conflicts, file path permissions.

#### **Day 3 – LMS Polish (Wednesday)**
*   **Source Material:** Use the raw video from Day 1 and the `docs/week-1-csv-parser.md` file.
*   **Polish the Video:**
    *   **Intro (30 sec):** Add a standard branded opener: "Helix Club - Week 1: Bootstrap & CSV".
    *   **Edit:** Make a few light cuts to remove long waiting periods (e.g., while Docker images pull). *Keep the problem-solving segment intact.*
    *   **Outro (30 sec):** Add a slide with the key takeaways and a call-to-action: "For the cheat sheet and code, visit the GitHub repo. Join us live at the next Helix Club Night!"
*   **LMS Activity (Moodle/Canvas):**
    *   **Upload:** The polished video.
    *   **Create a Quiz:**
        *   Q1: What Docker command is used to start the Helix stack in the background? (Multiple choice: `docker compose up -d`)
        *   Q2: Which n8n node did we use to run our Python script? (Free text: `Execute Command`)
    *   **Create an Assignment:** "Using the provided `contacts.csv` sample, modify the Python script to extract and print only the email addresses. Submit your modified `process.py` file."

#### **Day 4 – Outreach (Thursday)**
*   **LinkedIn Post Draft:**
    > **Title:** From Zero to Automation in 30 Minutes 🚀
    >
    > This week in the #HelixClub, I'm building in public. I started from an empty folder and got a basic CSV parsing automation running on the Helix stack (Docker, Python, n8n).
    >
    > The best part? I hit a port conflict live on camera. It's all part of the process!
    >
    > 👉 **Watch the raw, unedited build:** [Link to YouTube Video]
    > 👉 **Grab the code & cheat sheet:** [Link to GitHub Repo, specifically the /docs/week-1-csv-parser.md file]
    >
    > This is the kind of hands-on learning we'll be doing at the first **Helix Club Night Meetup** in Beckenried on **January 18**. If you're into #Python, #Docker, #Automation, or #CI/CD, come join us. Link in my bio.
    >
    > #LearnInPublic #DevOps #N8N #Education

#### **Day 5 – Rest / Prep (Friday)**
*   **Review Changelog:** Look at what's next. A logical step from Week 1 would be **Week 2: "Enhancing the CSV Parser: Webhooks & Database Storage"** (using the PSQL tool to insert the CSV data into Postgres).
*   **Draft Next Cheat Sheet:** Create a skeleton file `docs/week-2-db-storage.md` with just the objective and a placeholder for code.
*   **Optional Teaser:** Record a 30-second video: "Hey everyone, in Week 2 we're taking our CSV data and saving it directly to a database. It's a game-changer! See you next week."

---

### 💡 Any Tips? Yes, a few key ones:

1.  **Batch Recording is Your Friend:** The weekly rhythm is a guide. If you're in a flow state, consider recording two PR demos in one afternoon. This gives you a buffer and reduces context switching.
2.  **Repetition is a Feature, Not a Bug:** In your raw videos, don't be afraid to re-explain the core stack (Postgres for data, MinIO for files, n8n for orchestration) each time. New viewers will join every week, and repetition helps cement the concepts for everyone.
3.  **The Cheat Sheet is Your Best Asset:** That `docs/` directory will quickly become a massive value hub. It's the tangible takeaway for everyone. Consider turning it into a printable PDF bundle later.
4.  **Promote the Outcome, Not Just the Tech:** In your outreach, emphasize what people *achieve*: "Automate your boring tasks," "Learn skills schools are desperate to teach," "See how all these tools fit together." This attracts a wider audience beyond hardcore devs.
5.  **Delegate the Polish (Eventually):** The Day 3 (LMS Polish) task is the most time-consuming. As this grows, this is the first task you could potentially outsource to a virtual assistant or video editor, freeing you up for more coding and teaching.

This first week's plan gives you a very clear to-do list. You've got this! The flyer and venue inquiry are handled. Now it's time to create the content that will make people want to show up.

👉 **Shall we move on to drafting that short, casual LinkedIn post to announce the event itself?**
---

## [0.0.1] - 2025-11-10 🥋 *The Awakening*
### 🚀 Added
- Initial project structure and Dockerfile setup, fully refactored for clarity and speed ⚡  
- Modular Docker Compose stacks (`edge`, `auth`, `core`, `helix`) with clear separation of concerns 🧱  
- Keycloak identity provider wired to Traefik with mkcert TLS 🔐  
- Basic Celery worker integration with Redis message queue 🐇  
- DevContainer configuration for seamless VSCode remote development 🧠  
- `scripts/helix-status-v2.sh` for monitoring logs, health, and container orchestration 🧩  

### 🛠️ Changed
- Cleaned up redundant compose conditionals for modern Docker Compose 3.9 syntax  
- Unified `.env` handling for consistent developer and container environments  
- Simplified entrypoint scripts for easier debugging and traceability  

### ✅ Fixed
- Traefik TLS chain validation now passes mkcert self-signed checks  
- Docker socket permissions fixed for container-in-container builds 🧰  

### 🔒 Security
- Enforced `requirepass` for Redis local deployments  
- Isolated Keycloak and Traefik networks for reduced attack surface  

---

**Next Up:**
> 🧠 AI-assisted microservices, API gateway rate limiting, and async task pipelines.  
> Stay tuned for `v0.1.0 – The Orchestration Era`.

---

[Unreleased]: https://github.com/akenel/helixnet/compare/v0.0.1...HEAD  
[0.0.1]: https://github.com/akenel/helixnet/releases/tag/v0.0.1
