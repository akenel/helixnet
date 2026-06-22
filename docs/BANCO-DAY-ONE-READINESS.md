# Banco — Day-One demo readiness ("tested upside down and backwards")

*Run this on the **desktop** first (fast, no camera), then on the **phone** in the sandbox.
Every row green before you film. A red row = a stumble caught off-camera.*

Sandbox: `https://sandbox-banco.lapiazza.app` · reset between runs:
`ssh root@46.62.138.218 'cd /opt/helixnet && make sandbox-reset'`

---

## Beat-by-beat: what must work under each beat

| Beat | The moment | What must actually work | 🖥️ desk | 📱 phone |
|------|-----------|--------------------------|:---:|:---:|
| 0 | Empty shop | Dashboard + Shop Pulse render cleanly at **zero data** (no NaN/undefined/errored widgets) | ☐ | ☐ |
| 1 | Unscannable cream | Camera opens (HTTPS); a no-read **routes to no-barcode born-once**, doesn't dead-end | ☐ | ☐ |
| 2 | Born once | "New item, no barcode" → **creates a REAL product** (name + price), not a `[CATALOG]` line | ☐ | ☐ |
| 3 | Make a label | Internal code generated + **dropped in the label queue** | ☐ | ☐ |
| 4 | Photo in hand | Photo captured, **saved**, and shows on the product + in catalogue | ☐ | ☐ |
| 5 | First sale | Checkout → cash → **1-page receipt** with shop name + VAT, number `…-0001` | ☐ | ☐ |
| 6 | Gizeh papers | Same born-once, quick | ☐ | ☐ |
| 7 | Found instantly | **Search "black cup" / "Gizeh" by NAME → it's there** (the born-once fix); labelled code scans | ☐ | ☐ |
| 8 | Catalogue built itself | Catalogue page = the **picture wall** (photos saved + render) | ☐ | ☐ |
| 9 | Close the day | Drawer count + variance → **Z-report** (CHF, VAT) → **print queued labels** (WeasyPrint) | ☐ | ☐ |

**Dependency clusters (where a single fix unblocks several beats):**
- **Born-once no-barcode fix** → beats 1, 2, 6, 7 *(in progress — the demo-blocker)*
- **Photo save/storage** (image intake → MinIO?) → beats 4, 8
- **Label module** (internal code → queue → WeasyPrint N-up) → beats 3, 9
- **store_settings seeded** (shop name + VAT) → beat 5
- **Empty-state polish** → beats 0, 8
- **Search returns born-once items by name** → beat 7

---

## The hidden seals (non-obvious things that stumble demos)

- [ ] **Empty-state audit.** Day One starts at zero — the #1 place demos break. Walk EVERY
      screen empty (dashboard, catalogue, search, Z-report, Pulse): does it say "0 sales,
      let's begin" or does it show `undefined` / a blank widget / an error?
- [ ] **Photo *actually persists*.** Take a photo → reload the product → photo still there
      (not just held in the browser). Confirm where it's stored and that the sandbox has it.
- [ ] **Label *actually prints*.** "Make a label" → close day → the N-up PDF renders and a
      printed code **scans back** on the phone. (If the label module isn't done, Beat 3 can
      show "queued" but Beat 9 won't print — know which before filming.)
- [ ] **Latency / feel.** Sandbox is on the resource-pinched Hetzner box. Is save-and-next
      snappy? Camera decode fast? A 3-second hang reads as "broken" on camera.
- [ ] **The login ritual.** Fresh tab → Log Out → Log In before each take (clears cart +
      the "already logged in" SSO state). Don't let that friction land on camera.
- [ ] **Receipt #0001.** After a reset, the first sale's number restarts (looks brand-new,
      not second-hand).
- [ ] **Security (light).** Sandbox is a public URL with demo creds — fine because it's
      empty + throwaway, but `make sandbox-down` when not filming so it's not a forgotten
      open box.

---

## Sign-off
- [ ] All 10 beats green on **desktop**
- [ ] All 10 beats green on **phone** (the Fairphone 1% — camera + photo + label scan-back)
- [ ] One clean **full run** start→finish with no stumble → *then* press record
