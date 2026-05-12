# LP CLI — Architecture Design

**Author:** Angel + Tigs
**Date opened:** 2026-05-13 (night-shift design session)
**Last revised:** 2026-05-13 — design pivot: YAML is source of truth, env is generated output
**Status:** ★ DESIGN — not yet implemented. Review + redline before any code.

---

## ★ DESIGN PIVOT (2026-05-13, late night session)

**Original design:** the tool edits `borrowhood.env` in place. The env file is BOTH source of truth and runtime config.

**Pivoted design:** the env file is a **generated output**, not a source of truth. The source is a YAML file (per environment) that lives OFF the git repo. The tool reads YAML → generates env file → deploys.

**Why the pivot is better:**

- Single source of truth (the YAML). No drift between human-edited file and runtime config.
- Architecturally impossible to commit secrets to git (env files are generated artifacts, gitignored; YAML lives outside the repo entirely).
- Per-environment files (`prod.yaml`, `staging.yaml`, future `preprod.yaml`, `uat.yaml`) are the same shape — same tool handles all.
- Rollback is symmetric: `prod.previous.yaml` always exists as the last working version. One-command revert.
- Diff-able and dry-runnable: edit YAML, run `lp-rotate apply --dry-run`, see what would change.

The Resource + Provider + Test abstractions below stay the same. What changes is how state is read and applied — YAML in, env file out, then deploy.

---

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

## The YAML schema — REVISED (post-pivot)

**Location: NOT in the git repo.** Lives at `/opt/helixnet/secrets/<env>.yaml` on the Hetzner server, chmod 700 on the directory, chmod 600 on each file, owned by root.

**One YAML per environment.** `prod.yaml` holds prod secrets. `staging.yaml` holds staging secrets. Same schema, different values.

**Rollback pair:** before any apply, the current file is snapshotted to `<env>.previous.yaml`. To roll back: `cp prod.previous.yaml prod.yaml && lp-rotate apply --env prod`.

**The schema (example: `/opt/helixnet/secrets/prod.yaml`):**

```yaml
# /opt/helixnet/secrets/prod.yaml
# La Piazza prod environment -- secrets source of truth
# Permissions: chmod 600, owned by root
# Backup: replicated to KeePass attachment monthly
version: 1
env_name: prod
generated_env_file: /opt/helixnet/hetzner/lapiazza.env  # OUTPUT path
app_container: borrowhood                                # to restart after apply
hetzner_host: 46.62.138.218
compose_files: ["hetzner/docker-compose.uat.yml"]
compose_env_file: hetzner/uat.env

secrets:
  - id: flask-secret-key
    env_var: BH_SECRET_KEY
    value: <the actual value, plain text>
    rotation:
      sources: [generate, paste]
      generator: openssl_rand_base64_32
      test: app_healthz
      severity: critical
      side_effects: "Invalidates all logged-in user sessions"

  - id: db-password
    env_var: BH_DATABASE_URL
    composite:                      # the URL is built from parts
      template: "postgresql+asyncpg://{user}:{password}@postgres:5432/{database}"
      parts:
        user: lapiazza_app
        password: <the actual hex value>
        database: borrowhood
    rotation:
      sources: [generate, paste]
      generator: openssl_rand_hex_32           # URL-safe
      apply_extra: [alter_user]                # ALSO run ALTER USER in Postgres
      db_admin_role: helix_user                # who to use for ALTER USER
      test: asyncpg_connect_docker_network
      severity: critical

  - id: kc-client-secret
    env_var: BH_KC_CLIENT_SECRET
    value: <the actual value>
    rotation:
      sources: [paste]                          # provider-issued only
      paste_url: https://lapiazza.app/admin/master/console/#/borrowhood/clients
      paste_instructions: "KC admin UI -> Clients -> borrowhood-web -> Credentials -> Regenerate"
      test: oidc_discovery_200
      test_url: https://lapiazza.app/realms/borrowhood/.well-known/openid-configuration
      severity: high

  # ... 6 more secret entries (paypal, resend, telegram, ollama, github, google)

# Future resource types -- co-exist in the same file:
# ai_models:
#   - id: bh-ollama-model
#     env_var: BH_OLLAMA_MODEL
#     value: gemma3:12b
#     options: [gemma3:12b, gemma3:27b, llama3.1:70b]
#     test: ollama_inference_roundtrip
#
# routes:
#   - id: caddy-route-staging
#     ...
```

**Key point:** the YAML contains BOTH the secret values AND the metadata for how to rotate them. It's a self-describing file. The tool reads it, generates the env file:

```
# /opt/helixnet/hetzner/lapiazza.env  -- GENERATED, do not hand-edit
# Generated from: /opt/helixnet/secrets/prod.yaml at 2026-05-13T08:14:22Z
# To change: edit the YAML and run `lp-rotate apply --env prod`

BH_SECRET_KEY=<from yaml>
BH_DATABASE_URL=postgresql+asyncpg://lapiazza_app:<password from yaml>@postgres:5432/borrowhood
BH_KC_CLIENT_SECRET=<from yaml>
# ... etc
```

A header comment in the generated file makes it obvious that hand-editing is wrong — the next `apply` would overwrite hand-edits silently.

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

## Directory structure — REVISED (post-pivot)

```
# OFF-REPO (on Hetzner server only, chmod 700, root):
/opt/helixnet/secrets/
├── prod.yaml                          ← prod source of truth (per env, ONE file)
├── prod.previous.yaml                 ← last working version (rollback target)
├── staging.yaml                       
├── staging.previous.yaml
└── (future) preprod.yaml, uat.yaml, regression.yaml

# IN-REPO (the tool itself):
helixnet/
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
│       └── ssh.py                      ← Hetzner SSH wrapper (shell-out, no paramiko)
└── docs/
    ├── design/
    │   └── lp-cli-architecture.md     ← this file
    └── runbooks/
        └── secret-rotation.md          ← user-facing how-to (existing)

# GENERATED (on Hetzner server, NOT in git):
/opt/helixnet/hetzner/
├── lapiazza.env                       ← generated from prod.yaml
└── lapiazza-staging.env               ← generated from staging.yaml
```

**Rule: nothing in `/opt/helixnet/secrets/` ever touches the git repo. Nothing in the git repo ever contains real secret values.** The repo holds: the tool, the schemas, the documentation. Nothing else.

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

## Open questions — RESOLVED (2026-05-13 design session)

1. ~~**SSH wrapper**: paramiko vs shell-out~~ → **SHELL OUT** to `ssh`. Pure simplicity. Revisit only if we ever need connection pooling.
2. ~~**YAML or Python config?**~~ → **YAML** (off-repo, per environment).
3. ~~**Env var overrides on top of YAML**~~ → **NO**. Two sources of truth = drift bug. The YAML is the only truth.
4. ~~**Dry-run mode**~~ → **YES**. `lp-rotate apply --env prod --dry-run` prints the diff between current and YAML-derived, doesn't apply.
5. ~~**Logging + audit log**~~ → **YES both**. Python `logging` to stderr + JSONL audit to `~/.lp-rotation-log.jsonl`.
6. ~~**pytest unit tests for safety-critical recipes**~~ → **YES**. edit_env, alter_user, asyncpg_docker_network, generate_env_from_yaml all get tests.

## New open questions (post-pivot)

A. **Encryption at rest for the YAML files?** v1 is plain text at chmod 600 root-only on server. v2 candidates: `sops` with `age` keys, or KeePass attachment. **My lean: defer to v2.** Plain at 600 is no worse than current env files; the architectural win (no git-leak path) is already in place.

B. **Should the YAML diff against the deployed env be shown on every apply?** Yes — that's the dry-run output and the pre-apply confirmation. ~30 LOC.

C. **Two-stage rotation: prod.staged.yaml for "prepared but not applied"?** Could let Angel edit and review the change over hours/days before applying. Or just keep it simple: edit `prod.yaml` directly, the dry-run shows the diff, you commit when ready. **My lean: simple direct edit + dry-run is enough for v1.** Two-stage adds complexity without proportional gain.

D. **Backup cadence to KeePass?** Manual for v1 (Angel exports the YAML to KeePass attachment periodically). v2 could include `lp-rotate backup --to-keepass` if there's an API.

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
