# docs/testing — structure

Keep source separate from generated output. Source is tracked; outputs are organized but git-ignored.

| Folder | What | Tracked? |
|---|---|---|
| **`test-scripts/`** | The runbooks — self-contained HTML UAT gates. **SOURCE.** | ✅ tracked |
| **`reports/`** | Exported run reports (`*.html` with screenshots + `*.txt` text twins). | 🚫 ignored |
| **`artifacts/`** | Screenshots, PDFs, page captures from testing. | 🚫 ignored |
| **`archive/`** | Superseded scripts/reports kept for reference. | 🚫 ignored |
| `*.md` (root) | Testing checklists (Anne, ISOTTO). | ✅ tracked |

## Runbook conventions
- **Naming:** registered № `LP-UAT-YYYYMMDD-NAME` + `rev.N`. Bump `rev.N` on each iteration of the same sheet.
- **Format:** per-step ✓ done-check + **PASS / FAIL / ISSUE** verdict + a note box (type or 🎤 **speak — mic on every box**) + 📋 paste/drop/pick screenshot. Stopwatch + auto-save in the browser.
- **Export:** one click downloads **two** files — the full `*.html` (with screenshots) and a lightweight `*.txt` twin (verdicts + notes, no images) that opens with a FAIL/ISSUE summary and the env stamp. Drag the `.txt` to Tigs to read fast; the `.html` is the full record.
- **The gate:** a runbook is the human-green step between staging and prod (see the deploy pipeline). Run on staging, green-light, then promote.

## Served live (phone-testable)
- `staging-bottega.lapiazza.app/static/door-release-uat.html`
- `staging-bottega.lapiazza.app/static/fresh-firsttimer-test.html`
