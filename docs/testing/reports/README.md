# Test Reports — verified runs, sorted by environment

Exported runbook reports from **real human test runs**. This is the "what did we actually
test, where, and when" log — so when a question comes up later we can answer from evidence,
not memory.

## Layout

```
reports/
├── prod/      runs against PRODUCTION  (bottega.lapiazza.app)
├── staging/   runs against staging     (staging-bottega.lapiazza.app) + earlier local-file runs
└── (dev/)     add when dev-env testing starts
```

Sort by the **env stamp inside the report** (every runbook stamps `env: <hostname>`):
`bottega.lapiazza.app` → `prod/`, `staging-bottega…` or `local-file` → `staging/`.

## Naming

```
<feature>-<YYYY-MM-DD>.txt     ← lightweight text twin (TRACKED in git)
<feature>-<YYYY-MM-DD>.html    ← full report w/ screenshots (local only, gitignored)
<feature>-<YYYY-MM-DD>-run2…   ← a second run the same day
```

## Tracked vs. local

- **`.txt` twins are committed** — small, plain text, grep-able. `git grep -i FAIL reports/`
  finds every failure we ever logged. This is the durable record.
- **`.html` reports are gitignored** — they embed screenshots and balloon the repo. They
  live here locally for reference but don't ship to GitHub.

## How to file a new report

1. Run the runbook (`docs/testing/test-scripts/*.html`, or its static copy under `src/static/`).
2. Export both the `.html` and the `.txt` twin.
3. Drop them in the right env folder, dated, per the naming above.
4. Commit (the `.txt` gets tracked automatically; the `.html` is ignored).

The runbooks themselves (the blank test scripts) live in `../test-scripts/` and are tracked
as source. This folder is their **output**.
