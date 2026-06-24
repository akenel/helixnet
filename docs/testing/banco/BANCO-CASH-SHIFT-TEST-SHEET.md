# Banco POS — Per-Cashier Cash Shift (My Drawer) · Human Test Sheet

**Feature:** Each cashier owns their own drawer. Open with a counted float → ring sales (tied
to you) → record any non-sale cash → close by counting out. The system shows expected vs counted,
flags variance beyond **±CHF 0.20**, and the open→close time is your shift hours.
**Env to test:** https://staging-banco.lapiazza.app
**Logins (all helix_pass):** felix (admin), pam (cashier), ralph (manager)
**Status:** machine-green local + staging (61 API incl. 11 cash-shift + 11 math, 16 E2E).
**NOT on prod — this is your final eyeball before we push (or fix).**

---

## The flow we built (POC)

- **Dashboard** → "My Drawer" card shows your drawer status; "My Sales Today" shows *your* sales
  (a manager/Felix sees the store total instead).
- **My Drawer** (`/pos/shift`): Open → Active (status + cash in/out + close) → Report.
- Only **cash** is counted in the drawer; card/Twint are reported but banked separately.

---

## Click-to-test

### 1 · Open your drawer
- [ ] Log in as **pam**. Dashboard → tap **My Drawer** (or the "Open Shift" card).
- [ ] You see the **denomination grid**. Enter your float, e.g. **1× CHF 100 + 1× CHF 0.50**.
      The "Opening float" total updates live to **CHF 100.50**.
- [ ] Tap **Open Drawer with CHF 100.50**. The screen flips to **● OPEN** status.
- [ ] Status shows: opening float 100.50, my cash sales 0.00, **Expected in drawer 100.50**.

### 2 · Ring a sale (it lands on your drawer)
- [ ] Go to **New Sale**, ring up something, pay **cash**, finish.
- [ ] Back on **My Drawer** (tap Refresh if needed): **My cash sales** went up, and **Expected in
      drawer** = float + your cash sales. A card/Twint sale shows under "card (not in drawer)".

### 3 · Cash in / out (so it still balances)
- [ ] In the **Cash in / out** box: pick **Paid OUT**, amount e.g. **5.00**, reason "milk" → Record.
- [ ] Expected in drawer drops by 5.00. (Paid IN works the same, upward.)

### 4 · Close — count the drawer
- [ ] In **Close drawer**, count what's physically there on the grid.
- [ ] **Match it** (count = expected): the light turns **green — "Within tolerance"**.
- [ ] Or be **off by more than 20 rappen**: it goes **red — "Outside tolerance"**, and the
      **Close button stays disabled until you add a note**. (Off by ≤20 rappen = still green.)
- [ ] Tap **Close Drawer & File Report**.

### 5 · The report (Pam's one-pager for Felix)
- [ ] You get a one-page **Shift Report**: float, cash sales, paid in/out, **expected vs counted,
      variance** (green if balanced, red if flagged), card total, transactions, and **hours**.
- [ ] **Daily Sales Log** at the bottom: **every transaction you rang this shift**, each with its
      **line items** (qty × name, unit price, line total; free treats marked 🎁), and a header
      "N transactions · M items". This is the "I sold exactly these items" list Pam hands in.
- [ ] **🖨️ Print** gives a clean one-pager (totals **and** the itemized log). **Open New Drawer** starts fresh.
- [ ] (Two shifts in one day is fine — open/close a second time and you get a second report.)

### 6 · It's per-cashier (the whole point)
- [ ] Open a drawer as **pam**, then in another browser log in as **ralph** and open his own.
- [ ] Ring a sale as one of them → it shows on **that** cashier's drawer only, not the other's.
- [ ] On the dashboard, **pam** sees **"My Sales Today"** (her own); **ralph/felix** see the store total.

---

## ★ Verdict
- [ ] **PASS** — push to prod.
- [ ] **Needs fixes:** ______________________________________________

> Notes for this POC (we'll tune after): the float is counted in fresh each open; tolerance is a
> flat CHF 0.20; the old store-wide **Z-Report / Banana CSV** still lives under the manager's
> "Store Z-Report" card. Anything you test on staging writes to the real shared DB — tell me and
> I'll clear test shifts.
