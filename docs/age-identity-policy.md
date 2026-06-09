# Age & Identity Policy — La Piazza

*Decision record, 2026-06-09. Not legal advice — the Italy/EU age-verification landscape is evolving
and a real legal review is required before public launch. This sets the lean, defensible baseline.*

## Premise
La Piazza is an **adult neighbourhood marketplace** — not a kids' app, not social media, not adult
content. Privacy-first (essential cookies only, no tracking/profiling). The age strategy follows
**data minimisation + contextual gating**: collect the least, gate only at the point of need, and
turn "we're careful about age" into a **trust feature** — the opposite of the surveillance crowd.

## The legal frame (summary)
- **GDPR digital age of consent:** EU default **16**; member states 13–16. **Italy = 14.** Below the
  consent age, processing a minor's data needs **parental consent**.
- **Commerce:** minors generally cannot form binding contracts (buy/sell/rent) without a guardian →
  transaction features lean 16+/18+.
- **Age-restricted goods/events (18+):** alcohol, some tools, adult items → an 18+ check.
- **Trend:** Italy (AGCOM, school-managed accounts) + the EU are pushing **age verification** and a
  digital-ID wallet. More gating is coming; align early.

## THE DECISION
1. **No birthdate at signup.** Data minimisation; less to leak, less to regulate.
2. **Self-declared 16+ at signup** — one required checkbox: *"I confirm I'm 16 or older."* Above
   Italy's 14 floor, covers most commerce-capacity concerns. The baseline bar.
3. **Contextual 18+ gate.** Age-restricted listings (`age_restricted`) show a confirm-18+ gate
   **at the point of interaction** (viewing/RSVP/contact/buy). The "18+" badge becomes an actual
   gate, not a sticker. The confirmation is remembered per device (localStorage), not stored as data.
4. **Hard ID verification = deferred, feature-driven.** Only if a specific feature demands it
   (e.g., selling alcohol). Could later integrate SPID / EU digital-ID for strong assurance
   **without storing birthdates**.
5. **Parental-consent path = deferred.** Only if we ever target under-16s (we don't plan to).
6. **Legal review before public launch.** Mandatory for the Italy/EU specifics.

## SWOT
- **Strengths:** privacy-first (no minor profiling — the worst risk avoided); platform-controlled
  gating; role/listing-driven (most users need nothing).
- **Weaknesses (before this change):** zero age collection; 18+ cosmetic; no commerce-capacity check.
- **Opportunities:** privacy + sensible age-assurance = a trust differentiator; early EU-alignment;
  SPID/EU-ID integration later without storing DOBs.
- **Threats:** EU/Italy tightening (fines); liability if a minor transacts/accesses 18+; Italy school
  blocking makes under-16s largely unreachable anyway; reputational risk.

## IMPLEMENTATION (this change)
- **16+ checkbox** on `/get-started` (Bottega one-motion signup): required, submit disabled until ticked.
- **18+ gate** on age-restricted item pages (`item_detail.html`): an overlay that blocks the listing
  until the visitor confirms 18+ (remembered in localStorage as `age18_confirmed`, not server-stored).
- *Deferred:* the Square/Keycloak self-registration form needs the same 16+ tick (a KC theme change);
  noted, not done here.

## NOTES
- For the Dream Weavers story: a *garage move* is not 18+ — drop the cosmetic 18+ there; use
  `age_restricted` only where it genuinely applies (this also exercises the new gate honestly).
