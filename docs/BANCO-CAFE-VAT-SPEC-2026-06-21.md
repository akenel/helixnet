# Banco Cafe Till — Swiss VAT Spec (dine-in vs takeaway)

*Deep-research, 2026-06-21. 18 sources, 78 claims, 25 verified (24 confirmed / 1 killed), almost all from primary ESTV/FTA sources (estv.admin.ch, gate.estv.admin.ch, FTA MWST-Branchen-Info 08 "Gastgewerbe"). This is implementable. The one thing still needing a Treuhänder is flagged at the bottom.*

---

## THE HEADLINE (why this matters for Felix)

**Felix's 25-seat cafe is legally OBLIGATED to do per-line dine-in/takeaway VAT — the easy shortcut is closed to him.**

The FTA offers a flat-rate shortcut (`Pauschalregelung`, CHF 60/seat/day) so small kiosks can *avoid* tracking dine-in vs takeaway — **but it's capped at 20 seats/standing places.** A 25-seat cafe **exceeds the cap**, so Felix legally MUST use "geeignete organisatorische Massnahmen" = a programmed till that splits the rate per line. *If he doesn't, the FTA presumes the standard rate (8.1%) on everything* — i.e. he over-pays VAT on every takeaway coffee.

**Translation: the "ask dine-in or takeaway" till logic isn't a feature — it's a legal requirement Banco satisfies and no US POS even knows exists.** This is the single sharpest proof of the Swiss-correct moat.

---

## 1. THE RATES (effective 1 Jan 2024, in force through 2026)

| Rate | % | Applies to |
|------|---|-----------|
| Standard (Normalsatz) | **8.1%** | Dine-in restaurant/catering; **all alcohol**; **all tobacco**; head-shop non-food retail goods |
| Reduced (reduzierter Satz) | **2.6%** | Food/non-alcoholic drink sold **takeaway** (delivery of goods under the Foodstuffs Act) |
| Special (Sondersatz) | 3.8% | Lodging/accommodation only — **irrelevant to the cafe** |

> **Make rates CONFIGURABLE, not hardcoded.** A rise of the standard rate to 8.5% is parliamentary-proposed but not yet effective. (Banco already stores VAT rates as data — keep it that way.)

---

## 2. THE DECISION RULE (inputs → rate) — what the till computes

The legal test is the **`Konsumvorrichtung`** (consumption facility): tables, standing tables, counters/`Theken`, or any consumption surface on-site. Felix's 25-seat cafe IS a Konsumvorrichtung. So:

```
function vatRate(line):
    if line.category == ALCOHOL:            return 8.1%   # always, no exceptions
    if line.category == TOBACCO:            return 8.1%   # always (head shop!)
    if line.category in (FOOD, NONALC_DRINK):
        if line.consumption == DINE_IN:     return 8.1%   # restaurant supply
        if line.consumption == TAKEAWAY:    return 2.6%   # delivery of goods
    if line.category == RETAIL_GOODS:       return 8.1%   # head shop / grow supplies
    # default / undocumented consumption mode:
    return 8.1%                                            # FTA presumes standard rate
```

Key confirmed facts behind the rule:
- **Same item, two rates at the same counter is REAL and expected** — a coffee is 2.6% to-go and 8.1% if drunk on-site, even when handed over at the counter (not served). FTA MBI 08 §1.3.5 "Bäckerei/Konditorei/Confiserie mit Tea-Room" says this verbatim.
- **Ownership/use of the facility is irrelevant** — doesn't matter if the customer actually sits, or if there's a seat free. The facility *existing* is the trigger.
- **Heating is NOT the trigger.** A heated takeaway item is still 2.6% if no facility/serving. (Don't gate the rate on hot/cold.)
- **Alcohol AND tobacco are ALWAYS 8.1%** (Art. 25 MWSTG) — this matters doubly for a head shop: tobacco never gets the reduced rate.
- **"Ordered takeaway, then sat down" → flips to 8.1%.** Consumption context wins. (See re-ring open question below.)
- **Vending machine sales = 2.6%** (no facility) — relevant if Felix ever puts a machine in.

**Per the FTA, default to 8.1% (DINE_IN) and make the cashier actively choose TAKEAWAY** — because an undocumented sale is *presumed* standard-rated. Cheaper to be safe: the 2.6% rate must be the deliberate, recorded choice.

---

## 3. WHAT THE TILL MUST PRINT/STORE (compliance, not optional)

Legal basis: Art. 25 Abs. 3 MWSTG + Art. 55/56 MWSTV + FTA MBI 08 §1.3.2. To validly charge 2.6% on a takeaway when a facility exists, the till MUST:

1. **Issue a receipt** to the customer (always).
2. The receipt must show, per line: the **article (or at least product group)**, the **price**, AND the **VAT rate** for that line. (Coded rates allowed if a legend explains the codes — e.g. `A=8.1% B=2.6%`.)
3. **The takeaway nature must be clearly evident from the documents** — otherwise the sale is presumed a standard-rated restaurant service.
4. **Book the two turnover streams separately** in the accounts (dine-in revenue vs takeaway revenue tracked apart).

> ✅ **REFUTED claim, do NOT over-build:** you do *not* need separate cost-of-goods accounts. The obligation is to separate the two **turnover** streams, not COGS. (This claim was killed 3-0.)

A single shared till is fine — it just has to be programmed (a "Registrier-/Spartenkasse") to do the above. That's exactly what Banco is.

---

## 4. THE SHORTCUT THAT'S CLOSED + THE ACCOUNTING METHOD (Treuhänder zone)

- **`Pauschalregelung` (CHF 60/seat/day flat rate):** lets ≤20-seat shops skip dine-in/takeaway tracking. **Felix at 25 seats CANNOT use it.** → per-line split is mandatory. (Moot unless he ever cuts to ≤20 seats; the CHF-60 figure is from a 2017 doc and may have been recalculated — confirm if ever relevant.)
- **`Saldosteuersatz` (net-tax-rate method):** a *separate* accounting-method choice — settle VAT via an industry flat rate. Eligible if annual taxable turnover ≤ **CHF 5.024m** AND VAT owed ≤ **CHF 108k/yr**. Felix likely qualifies on size. **BUT:** even under Saldo, the customer-facing receipt still shows 8.1%/2.6% per line — Saldo only changes how he *remits* to the FTA, not what the till prints. Which net-tax rate(s) apply to a *combined head-shop + cafe* is a **Treuhänder decision** (may need a two-activity split).

---

## 5. RECEIPT / QR-BILL

- **Receipt:** must show VAT rate per line/group (covered in §3).
- **QR-bill (for invoices):** the Swiss QR code has **no native VAT field**. Multi-rate data goes in the optional billing-information field using **Swico S1 syntax, tag `/32/`**: a list of `rate:net` pairs, `:` separating rate from net, `;` separating entries — e.g. `/32/8.1:553.39;2.6:400.19`. **Hard constraint:** the sum of the net amounts + their computed VAT MUST reconcile to the QR-code total amount. (Banco's invoice generator must enforce this when both rates appear on one invoice.)

---

## 6. STILL NEEDS A SWISS TREUHÄNDER SIGN-OFF (don't hardcode these)

1. **Accounting method:** effective method (two-rate till) vs Saldosteuersatz — and if Saldo, which net-tax rate(s) for a combined retail + cafe operation, and whether a two-activity split is required.
2. **Re-ring workflow:** if a takeaway line rung at 2.6% becomes dine-in (customer sits), is there an FTA-accepted correction flow, or must the cashier confirm dine-in/takeaway *before* finalizing each line? (Spec recommends: **confirm before finalize**, default DINE_IN, to avoid presumed-standard-rate exposure being wrong the *other* way.)
3. **Audit substantiation:** whether the FTA wants any physical signage / distinct takeaway packaging beyond the receipt + till programming.

---

## SO WHAT — the build, in one paragraph

Banco already stores VAT as configurable data and already does multi-rate lines (POS sprint). The cafe adds: a **per-line `consumption` flag (DINE_IN | TAKEAWAY)** that the cashier sets, defaulting to DINE_IN; a **category → rate resolver** that forces ALCOHOL and TOBACCO to 8.1% regardless; a **receipt that prints the per-line rate with a code legend**; **two separated turnover streams** in the daily Z-report (dine-in vs takeaway); and a **QR-bill Swico-S1 `/32/` multi-rate emitter** with the reconciliation check. That's the whole job. It is a few days of focused work, it's legally required for Felix, and it is the demo that no Dutchie/Flowhub/Cova on Earth can match.

*Primary sources: estv.admin.ch (rates, Saldosteuersatz thresholds), FTA MWST-Branchen-Info 08 "Gastgewerbe" via gate.estv.admin.ch & swissvat.ch (the Konsumvorrichtung test, single-till programming rule, 20-seat cap), Swico S1 syntax spec + SIX QR-bill IG v2.2 (QR multi-rate field). Full URL list in the workflow result.*
