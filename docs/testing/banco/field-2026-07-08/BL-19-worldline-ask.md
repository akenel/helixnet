# BL-19 — the ask Felix sends Worldline (draft)

**Goal:** get Worldline to enable the **ECR / ep2 integration interface** on Felix's terminal so
Banco can send the amount to the reader and read back approved/declined — killing the manual
re-keying. This is the FIRST move; no code until Worldline confirms the interface + spec.

**Which terminal to integrate:** lead with the **AXIUM DX8000** (Android smart POS, TID `25409030`) —
it's Worldline's newer platform and the cleaner integration target. Mention the Move/5000
(TID `25145450`) as the fallback.

**Worldline contact from the terminal label:** hotline **0800 111 600** / **0848 000 601**.

---

## 📧 German (send this — Worldline CH is German-speaking)

> **Betreff: ECR-/ep2-Kassenintegration aktivieren — Terminal TID 25409030 (AXIUM DX8000)**
>
> Guten Tag
>
> Ich betreibe ein Fachgeschäft und möchte mein Worldline-Terminal direkt mit meiner
> Kassensoftware (POS) verbinden, damit der Verkaufsbetrag automatisch ans Terminal übergeben
> und das Resultat (genehmigt/abgelehnt inkl. Transaktionsreferenz) zurück in die Kasse
> geschrieben wird. Heute tippen wir den Betrag von Hand ins Terminal — das möchte ich beenden.
>
> Konkret bitte ich um:
> 1. **Aktivierung der ECR-/ep2-Integrationsschnittstelle** auf meinem Terminal
>    **AXIUM DX8000, TID 25409030** (alternativ Move/5000, TID 25145450).
> 2. Die **Protokoll-Spezifikation bzw. das SDK** für die Kassenanbindung (ep2 ECR).
> 3. Bestätigung, ob dafür **Kosten** anfallen und ob mein **Vertrag** die integrierte
>    Zahlung erlaubt.
> 4. Ihre Empfehlung, **welches der beiden Terminals** sich besser für die Integration eignet.
>
> Besten Dank für eine kurze Rückmeldung.
>
> Freundliche Grüsse
> [Felix — Firma, Adresse, Kundennummer]

---

## 📧 English (reference / for us)

> **Subject: Enable ECR/ep2 till integration — terminal TID 25409030 (AXIUM DX8000)**
>
> Hello,
>
> I run a retail shop and want to connect my Worldline terminal directly to my POS software, so
> the sale amount is passed to the terminal automatically and the result (approved/declined + a
> transaction reference) is written back into the till. Today we key the amount in by hand — I'd
> like to stop that.
>
> Specifically I'm asking for:
> 1. **Activation of the ECR/ep2 integration interface** on my terminal **AXIUM DX8000,
>    TID 25409030** (or the Move/5000, TID 25145450).
> 2. The **protocol spec / SDK** for the till connection (ep2 ECR).
> 3. Confirmation whether there's a **fee** and whether my **contract** permits integrated payments.
> 4. Your recommendation on **which of the two terminals** is the better integration target.
>
> Thank you.
> [Felix — company, address, customer number]

---

## After Worldline replies
- If they enable ECR + give the spec/SDK → Banco builds a small ep2-ECR client (send amount →
  poll/await result → record txn ref against the sale). Simulate the flow first (no hardware needed
  to build the client + a mock terminal).
- If it needs a paid contract change → that's Felix's call (cost vs. the manual-keying pain).
- Blanks to fill before sending: Felix's **company name, address, Worldline customer/contract number**.
