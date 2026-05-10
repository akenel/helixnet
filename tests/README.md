# tests/ -- HelixNet / La Piazza E2E

Playwright-driven browser tests. Real Chrome, real network, real assertions.

## Quick start

```bash
# All tests against local dev (helix.local)
npm run test:e2e:dev

# Smoke tests only, against prod (lapiazza.app) -- read-only
npm run test:e2e:prod

# Full suite against ephemeral staging (when up)
npm run test:e2e:staging

# UI mode -- watch tests run in real browser, replay on failure
npm run test:e2e:ui

# Open the last HTML report
npx playwright show-report tests/playwright-report
```

## Layout

```
tests/
├── playwright.config.ts   # 2 envs: dev + prod, staging optional
├── sanity.spec.ts         # framework heartbeat (delete once real tests land)
├── fixtures/              # personas, seed helpers (task #5)
└── scenarios/             # O2C, P2P, mixed-role (tasks #6, #7, #8)
```

## Safety rules

1. **Prod runs `@smoke` tests only** (read-only GETs). The config enforces this.
   Never tag a write/POST test with `@smoke`. The grep filter is the only thing
   keeping you from corrupting lapiazza.app data.
2. **Staging is ephemeral** -- it may be down. Tests should fail fast with a
   clear message ("staging.lapiazza.app unreachable"), not hang.
3. **Test users get `helix_pass`** across all envs (per CLAUDE.md standing rule).

## Adding tests

Until task #5 lands the persona fixtures, write tests that don't need login.
Once personas exist:

```typescript
import { test } from '@/tests/fixtures/personas';
test('alice can browse listings', async ({ alicePage }) => { ... });
```
