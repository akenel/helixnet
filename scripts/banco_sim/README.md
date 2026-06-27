# Banco daily smoke

End-to-end "shake it all around" check against a live env: simulates a full two-till
retail day via the REAL API, verifies the money reconciles, and fuzzes the inputs.

```bash
# daily regression alarm against sandbox (zero it first)
python scripts/banco_sim/banco_daily_smoke.py --env sandbox --reset
echo $?   # 0 = all green; 1 = a check failed or a 5xx crash
```

What it does:
1. Auth `felix` (admin) + `pam` (cashier) — the only users in `kc-sandbox`.
2. Seed 12 products + 4 customers; open both drawers.
3. Ring 18 varied sales (cash/twint/visa/debit, dine-in/takeaway VAT, discount,
   giveaway), paid in/out, a manager refund, close both drawers, file timesheets.
4. **Verify**: VAT std+reduced == total, turnover split == sales, payments sum ==
   sales, two-cashier split. (Reconciliation, not just "200 OK".)
5. **Monkey/fuzz**: negative qty, qty over cap, bad enums, ghost ids, cashier-refund,
   empty-cart checkout, SQLi — all must be graceful 4xx, **zero 5xx**.

A daily run is "today" (no backdating) — it's a regression alarm, not a demo.
For a realistic *past-day* demo (e.g. "last Thursday 08:00–20:00" to eyeball),
run the day then backdate `created_at/completed_at/opened_at/closed_at` in
`banco_sandbox` by row order — see memory `banco-sandbox-day-simulation`.

Scheduling options (pick one): cron on the Hetzner box; a GitHub Action on a
schedule hitting sandbox; or a Claude `/schedule` routine. All should alert on a
non-zero exit.
