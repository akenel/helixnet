# LP CLI — Architecture Design

**Author:** Angel + Tigs
**Date opened:** 2026-05-13 (night-shift design session)
**Status:** ★ DESIGN — not yet implemented. Review + redline before any code.

---

## TL;DR

Build a declarative, idiot-proof CLI for managing La Piazza's operational state. **The secrets rotation tool is the first concrete build** — but the architecture must generalize so the same pattern eventually handles AI model swaps, payment provider switches, URL routing changes, feature flags, anything the platform exposes that needs to change at runtime.

Pattern: **Resource + Provider + Test, driven by YAML.**

```
   declarative YAML ──→ CLI (interactive, paranoid) ──→ apply changes ──→ verify
                                  │
                                  └──→ eventually wrapped as REST API
                                       (same logic, different surface)
```

---

## Why this isn't overkill (the "build small, expand later" argument)

The secret-rotation pain that birthed this design (2026-05-12):

1. Human-error rotation: TWO password values were generated for the SAME user — one in `ALTER USER`, another in the env file. Mismatch crashed prod.
2. Tests gave false positives because of `pg_hba.conf` localhost trust.
3. Container restart timing wasn't coordinated with state changes.
4. No audit trail of "what was rotated, when, by whom."

A **declarative, scripted, paranoid CLI** prevents ALL of these. Same pattern, applied to other ops, prevents the equivalent errors.

**Building for the first secret = building for the 50th secret. Same code, more YAML.**

---

## The 3 abstractions

### 1. **Resource**

A thing that can be managed declaratively. Examples:

- `secret` — a credential stored in env/config/Postgres (DB password, API key)
- `ai_model` — which AI model the app uses (Ollama gemma3 / Gemini Flash / etc.)
- `route` — a Caddy reverse-proxy route or app URL mapping
- `feature_flag` — boolean toggles
- `quota` — rate-limit settings

For tonight's milestone, we ONLY implement `secret`. The architecture must not preclude the others.

### 2. **Provider**

The code that knows how to read, write, test, and rotate a specific resource type. Each resource type has one provider class.

```python
class SecretProvider:
    def current(name) -> str         # read current value
    def apply(name, new_value)       # set new value (env edit + maybe DB ALTER + maybe restart)
    def test(name) -> bool           # verify the new value works
    def history(name) -> list        # rotation log entries for this secret
```

```python
class AIModelProvider:           # future
    def current() -> str             # what model is active
    def apply(model_id)              # swap to a different model
    def test() -> bool               # do a tiny inference round-trip
```

Adding a new resource type = writing a new provider class. The CLI layer doesn't change.

### 3. **Test**

A small function that confirms the resource is in the expected state. Decoupled from the Provider so multiple resources can share the same test.

```python
def test_asyncpg_connect_docker_network(env_file: Path) -> bool
def test_oidc_discovery_returns_200(realm_url: str) -> bool
def test_telegram_bot_getme(token: str) -> bool
def test_paypal_sandbox_oauth(client_id: str, secret: str) -> bool
```

For tonight's design, we enumerate the tests needed by the 9 secrets.

---

## The YAML schema

The single source of truth for what can be rotated. Lives in `config/lp-secrets-manifest.yaml`.

```yaml
# config/lp-secrets-manifest.yaml
version: 1

defaults:
  env: prod
  hetzner_host: 46.62.138.218
  compose_dir: /opt/helixnet
  compose_files: ["hetzner/docker-compose.uat.yml"]
  compose_env_file: hetzner/uat.env

secrets:

  - id: lp-prod-flask-secret-key
    name: Flask SECRET_KEY (prod)
    env_var: BH_SECRET_KEY
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [generate, paste]
    generator: openssl_rand_base64_32
    apply:
      - edit_env
      - restart_container
    restart: [borrowhood]
    test: app_healthz
    severity: critical
    side_effects: "Invalidates all logged-in user sessions"

  - id: lp-prod-db-password
    name: Postgres DB Password (prod)
    env_var: BH_DATABASE_URL
    env_var_part: password  # special: embedded in a URL
    env_file: hetzner/borrowhood.env
    type: db_password
    sources: [generate, paste]
    generator: openssl_rand_hex_32       # hex = URL-safe
    db_role: lapiazza_app
    db_admin_role: helix_user
    db_name: borrowhood
    apply:
      - edit_env                          # update URL in env file
      - pretest_asyncpg_docker_network    # CHECK before changing Postgres
      - alter_user                        # ALTER USER ... WITH PASSWORD
      - restart_container
    restart: [borrowhood]
    test: asyncpg_connect_docker_network
    severity: critical
    side_effects: "~30 second prod restart window"

  - id: lp-prod-kc-client-secret
    name: Keycloak borrowhood-web Client Secret (prod)
    env_var: BH_KC_CLIENT_SECRET
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]                      # provider-issued only
    paste_url: https://lapiazza.app/admin/master/console/#/borrowhood/clients
    paste_instructions: |
      KC admin UI -> Clients -> borrowhood-web -> Credentials -> Regenerate
    apply:
      - edit_env
      - restart_container
    restart: [borrowhood]
    test: oidc_discovery_200_at https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration
    severity: high

  - id: lp-prod-paypal-secret
    name: PayPal Sandbox Client Secret (prod)
    env_var: BH_PAYPAL_CLIENT_SECRET
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]
    paste_url: https://developer.paypal.com/dashboard/applications/sandbox
    paste_instructions: My Apps -> app -> Show/Regenerate Secret
    apply: [edit_env, restart_container]
    restart: [borrowhood]
    test: paypal_sandbox_oauth_token
    severity: low

  - id: lp-prod-resend-key
    name: Resend Email API Key (prod)
    env_var: BH_RESEND_API_KEY
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]
    paste_url: https://resend.com/api-keys
    apply: [edit_env, restart_container]
    restart: [borrowhood]
    test: resend_api_me
    severity: medium

  - id: lp-prod-telegram-token
    name: Telegram Bot Token (prod)
    env_var: BH_TELEGRAM_BOT_TOKEN
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]
    paste_instructions: |
      In Telegram app: @BotFather -> /mybots -> select bot -> API Token -> Revoke current token
    apply: [edit_env, restart_container]
    restart: [borrowhood]
    test: telegram_getme
    severity: high

  - id: lp-prod-ollama-key
    name: Ollama Cloud API Key (prod)
    env_var: BH_OLLAMA_KEY
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]
    paste_url: https://ollama.com/settings/keys
    apply: [edit_env, restart_container]
    restart: [borrowhood]
    test: ollama_models_list
    severity: medium

  - id: lp-prod-kc-github-secret
    name: Keycloak GitHub OAuth Client Secret (prod)
    env_var: KC_GITHUB_CLIENT_SECRET
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]
    paste_url: https://github.com/settings/developers
    paste_instructions: |
      OAuth Apps -> La Piazza -> Generate new client secret.
      Then KC admin UI: Identity Providers -> github -> update Client Secret.
    apply: [edit_env, restart_container, kc_admin_update_idp]
    restart: [borrowhood]
    test: oidc_discovery_200_at https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration
    severity: low

  - id: lp-prod-kc-google-secret
    name: Keycloak Google OAuth Client Secret (prod)
    env_var: KC_GOOGLE_CLIENT_SECRET
    env_file: hetzner/borrowhood.env
    type: env_value
    sources: [paste]
    paste_url: https://console.cloud.google.com/apis/credentials
    apply: [edit_env, restart_container, kc_admin_update_idp]
    restart: [borrowhood]
    test: oidc_discovery_200_at https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration
    severity: low

# Future resource types (NOT IMPLEMENTED in v1):
#
# ai_models:
#   - id: lp-prod-ai-model
#     env_var: BH_OLLAMA_MODEL
#     current: gemma3:12b
#     options: [gemma3:12b, gemma3:27b, llama3.1:70b]
#     test: ollama_inference_roundtrip
#
# routes:
#   - id: lp-prod-route-media
#     ...
```

---

## CLI surface

The tool is invoked as a single Python module. **Three modes:**

### 1. Fully interactive (default)

```
$ python -m lp_rotate

  La Piazza Operations CLI
  ───────────────────────
  
  Environment? (prod/staging) > prod
  
  Resource type?
    1) secret
    (only secret implemented in v1)
  > 1
  
  Which secret? (showing 9 prod secrets)
    1) Flask SECRET_KEY                  [last rotated: never]
    2) Postgres DB Password              [last rotated: 2026-05-12 (incomplete)]
    3) Keycloak Client Secret            [last rotated: never]
    ...
  > 2
  
  Source?
    g) Generate locally (openssl rand -hex 32)
    p) Paste from KeePass (hidden input)
  > g
  
  Generated 64-char hex. SHOWING ONCE for KeePass:
  
      0224abcd...2cc53
  
  ⚠ PASTE INTO KEEPASS ENTRY "LP Prod -- Postgres DB Password" NOW.
    Press Enter when saved.
  
  Pre-checks:
    ✓ env file readable
    ✓ Postgres container running
    ✓ Backup taken: /opt/backup-rotations/borrowhood.env.20260513-...
  
  Pre-test (BEFORE state change):
    ▸ Editing env file with new password...     done
    ▸ asyncpg connect via docker network...     AUTH_FAIL (expected pre-ALTER)
  
  Apply:
    ▸ ALTER USER lapiazza_app WITH PASSWORD ... done
    ▸ asyncpg connect retest...                 OK
    ▸ Restart borrowhood container...           done (28s)
    ▸ HTTP health: https://lapiazza.app/ ...    200
  
  Audit log:
    /home/angel/.lp-rotation-log.jsonl  <- one new entry
  
  ✓ ROTATION COMPLETE.
```

### 2. Single-secret mode

```
$ python -m lp_rotate --secret lp-prod-paypal-secret --source paste
```

Skips the interactive menus. Still prompts for the value (hidden) and runs the same paranoid flow.

### 3. List / status modes

```
$ python -m lp_rotate --list
  prod secrets (9):
    lp-prod-flask-secret-key          BH_SECRET_KEY             [never rotated]
    lp-prod-db-password               BH_DATABASE_URL           [2026-05-12 incomplete]
    lp-prod-kc-client-secret          BH_KC_CLIENT_SECRET       [never rotated]
    ...

$ python -m lp_rotate --status
  prod secrets summary:
    overdue (>365d): 0
    incomplete:      1  (db-password)
    never rotated:   8
    
$ python -m lp_rotate --diff prod staging
  Diff between prod and staging secret manifests:
    + lp-staging-* mirror entries exist for all 9 prod secrets
    - 0 prod-only secrets
    - 0 staging-only secrets
```

---

## Directory structure

```
helixnet/
├── config/
│   ├── lp-secrets-manifest.yaml      ← all rotatable secrets
│   └── (future) lp-models-manifest.yaml, lp-routes-manifest.yaml
├── scripts/
│   ├── lp_rotate.py                   ← entry point (Typer CLI)
│   └── lp/                            ← package
│       ├── __init__.py
│       ├── cli.py                     ← Typer commands
│       ├── manifest.py                ← YAML loader + Pydantic validation
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── base.py                ← abstract Provider class
│       │   ├── secret_provider.py     ← v1 implementation
│       │   └── (future) ai_model_provider.py
│       ├── recipes/                    ← per-step apply functions
│       │   ├── __init__.py
│       │   ├── edit_env.py             ← env file editor (in-place)
│       │   ├── restart_container.py    ← docker compose restart
│       │   ├── alter_user.py           ← Postgres ALTER USER
│       │   ├── kc_admin_update_idp.py  ← KC admin REST API
│       │   └── ...
│       ├── tests/                      ← per-test verify functions
│       │   ├── __init__.py
│       │   ├── asyncpg_docker_network.py
│       │   ├── oidc_discovery.py
│       │   ├── telegram_getme.py
│       │   ├── paypal_sandbox_oauth.py
│       │   ├── resend_api_me.py
│       │   └── ollama_models_list.py
│       ├── generators.py               ← openssl_rand_hex_32 etc.
│       ├── audit.py                    ← rotation log writer
│       └── ssh.py                      ← Hetzner SSH wrapper
└── docs/
    ├── design/
    │   └── lp-cli-architecture.md     ← this file
    └── runbooks/
        └── secret-rotation.md          ← user-facing how-to (existing)
```

---

## Dependencies (Python only — no bash for new code per rule #11)

```
typer[all] >= 0.12      # CLI framework, prompts, colored output
pydantic >= 2.7         # YAML schema validation
PyYAML >= 6             # YAML parser
asyncpg >= 0.29         # DB password test
httpx >= 0.27           # OIDC / Telegram / PayPal / Resend / Ollama tests
paramiko OR fabric     # SSH to Hetzner (or just shell out to ssh -- decide later)
keyring [optional]      # for caching secrets from KeePass in OS keyring (future)
```

Total: ~6 small libraries. Standard FastAPI-adjacent stack.

---

## Audit log format

`~/.lp-rotation-log.jsonl` — one JSON object per line:

```json
{"ts":"2026-05-13T08:14:22Z","env":"prod","secret_id":"lp-prod-db-password","actor":"angel","source":"paste","apply_steps":["edit_env","pretest","alter_user","restart"],"test_result":"PASS","outcome":"complete","backup":"/opt/backup-rotations/borrowhood.env.20260513-081421","duration_s":42}
{"ts":"2026-05-13T08:25:11Z","env":"prod","secret_id":"lp-prod-flask-secret-key","actor":"angel","source":"generate","apply_steps":["edit_env","restart"],"test_result":"PASS","outcome":"complete","duration_s":35}
```

Queries:
- "When did we last rotate the DB password?" → `grep db-password ~/.lp-rotation-log.jsonl | tail -1`
- "Anything failed lately?" → `grep '"outcome":"failed"' ~/.lp-rotation-log.jsonl`
- "How many rotations this year?" → `grep 2026 ~/.lp-rotation-log.jsonl | wc -l`

---

## Safety mechanisms (the paranoia layer)

Encoded in code, not in operator discipline:

1. **Backup before any change** — every apply step that touches state takes a timestamped backup first
2. **Pre-test BEFORE state change** — if asyncpg can already connect, no ALTER needed (idempotent). If it FAILS with AUTH_FAIL, that's expected pre-ALTER. Anything else aborts.
3. **Re-test AFTER state change** — must pass before considering the rotation complete
4. **Auto-rollback on failure** — if any step fails, restore the backup, restart with old creds, report failure clearly
5. **`read -s` style hidden input** — passwords never echo to terminal
6. **Compare-paste enforcement** — when source is `paste`, prompt TWICE and `strcmp` the inputs. Mismatch = abort with no state changed.
7. **Single source of truth** — KeePass instructions printed at right moments. Tool doesn't try to store the value itself.
8. **Audit log every action** — even failures. The log is append-only.

---

## v1 milestone: what gets built first

Only what's needed to rotate the 9 prod secrets we already know about:

1. ✅ CLI entry point + Typer commands (`lp_rotate.py`)
2. ✅ Manifest loader + Pydantic validation
3. ✅ SecretProvider (the v1 resource type)
4. ✅ Recipes: `edit_env`, `restart_container`, `alter_user`
5. ✅ Tests: `asyncpg_docker_network`, `oidc_discovery`, `telegram_getme`, `paypal_sandbox_oauth`, `resend_api_me`, `ollama_models_list`, `app_healthz`
6. ✅ Generators: `openssl_rand_hex_32`, `openssl_rand_base64_32`
7. ✅ Audit log writer
8. ✅ Manifest YAML for the 9 prod secrets

**Out of scope for v1** (deferred to v2+):
- AIModelProvider
- RouteProvider
- REST API wrapper
- KC admin IDP secret update (the `kc_admin_update_idp` recipe — for v1, the tool tells the user to update KC manually and prompts to confirm)
- Multi-env diff
- Encrypted audit log
- Concurrency/locking (only one rotation at a time — for v1 we trust solo operator discipline)

---

## v2+ — how the same architecture grows

Adding `ai_model` as a resource:

1. Add `lp-models-manifest.yaml` with entries like `BH_OLLAMA_MODEL: gemma3:12b → llama3.1:70b options`
2. Write `AIModelProvider` class with `apply()` = edit env + restart, `test()` = inference round-trip
3. Update CLI menu: "Resource type? 1) secret 2) ai_model"
4. Done. ~50 LOC.

Adding `route` as a resource:

1. Add `lp-routes-manifest.yaml` with Caddy block definitions
2. Write `RouteProvider`: `apply()` = edit Caddyfile + reload Caddy, `test()` = curl new hostname
3. Update CLI menu

REST API wrapper (eventually):

1. Wrap the same Provider classes in FastAPI routes
2. POST /api/v1/secrets/lp-prod-paypal-secret/rotate with {source: "paste", value: "..."}
3. Same audit log, same safety mechanisms
4. Auth: KC-protected route with admin role

---

## Open questions for redline

1. **SSH wrapper**: paramiko library OR shell out to `ssh root@host`? Paramiko = pure Python but more deps. Shell out = simpler but loses some type safety. **My lean: shell out for v1**, paramiko later if we want connection pooling.

2. **YAML or Python config?** The YAML is human-readable but has no IDE autocomplete or type safety. Pure-Python config (a `manifest.py` returning Pydantic models) gives both. **My lean: YAML for v1** because non-Python operators (future Anne, future Flora) can read/edit it.

3. **Where do environment overrides go?** Some values (e.g., `hetzner_host`) might want to come from env vars rather than the YAML. **My lean: YAML defaults + env var override** (e.g., `LP_HETZNER_HOST=...` overrides the YAML value).

4. **Should the tool also support DRY RUN mode?** `--dry-run` = print what WOULD happen, don't change state. **My lean: yes**. ~10 LOC, great for first-time use.

5. **Logging**: Python `logging` module to stderr + the JSONL audit log to file. **My lean: yes both**.

6. **Tests**: Should the v1 build include pytest unit tests for the recipes? **My lean: yes for the safety-critical ones** (edit_env, alter_user, asyncpg_docker_network). Mock the network calls; test the file-edit logic.

---

## Estimated build effort (NOT tonight)

| Component | LOC | Effort |
|---|---:|---|
| CLI + Typer + interactive prompts | ~150 | 2h |
| Manifest loader + Pydantic models | ~80 | 1h |
| SecretProvider + recipes | ~120 | 2h |
| Tests (6 test functions) | ~150 | 2h |
| Audit log | ~30 | 0.5h |
| pytest unit tests | ~150 | 2h |
| **Total v1 build** | **~680** | **~10h** |

Doable in one focused session. **NOT tonight.** Tonight is design only.

---

## Next steps (after this design is signed off)

1. **Angel reviews this doc, redlines anything off**
2. **We agree on the 6 open questions**
3. **Tigs writes the manifest YAML for the 9 prod secrets** (validation of the schema)
4. **Tigs builds v1 in one focused session** (10h = one good day or two evenings)
5. **First real use**: finish the prod DB password rotation that's currently incomplete
6. **Then**: knock out the other 7 prod secrets in a single clean session

Andiamo. Be water — fill the gaps, no shortcuts, water that builds the bridge for every future rotation.
