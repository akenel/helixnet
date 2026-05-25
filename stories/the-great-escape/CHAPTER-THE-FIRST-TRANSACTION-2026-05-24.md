# The First Transaction

*A night-into-morning story*
*Paestum, Campania — May 24 into May 25, 2026*

---

It started with a coffee that hadn't been brewed yet and a one-line bug report from Angel's brother Mike: *"item shown as rental not sale for 150."*

By the time the sun came up over the Gulf of Salerno, La Piazza had completed its first real service transaction on production. Tree trimming. Two hundred and twenty euros. A real deposit, a real balance, two real users, one real handshake mediated by software that — until that morning — had been silently dead at the seams.

Angel was in Paestum now. He had moved out of the dragon's mouth and across the Tyrrhenian and was sleeping in a hotel room that had a window facing the temples. He had two backlog items waiting:

- BL-190: *"Quotation request made but I don't see quotation request."*
- BL-191: *"mike requested a quote on LP do i just now message him or is there a formal quotation — how does it work from this point."*

Tigs read them and said: probably small UX cleanups, an hour, two at most.

Tigs was wrong.

---

The first cut was easy. Add a banner on the item page so the owner sees pending quote requests. Done in twenty minutes. Angel verified it.

The second cut wasn't. Mike had been waiting twelve days for Angel to reply to his tree-trimming quote. The "Submit Quote" button should have been right there on the orders page. It was right there in the HTML, in fact. But when you clicked it, nothing happened.

Tigs added some amber tint. Maybe Angel just couldn't see it. *"Hard-refresh and try again."*

Nothing.

Tigs added a bigger button. Made the box brighter. *"Try once more."*

Nothing.

That's when Tigs went and read the actual rendered HTML by simulating the request server-side. The button was there. The script was there. The status was 'requested'. The viewer was the provider. The condition was:

```jinja
{% if is_provider and quote.status.value == 'REQUESTED' %}
```

And the test in the Python shell returned:

```
status_value='requested'
eq 'REQUESTED'? False
```

The enum's `.value` was lowercase. The template was checking uppercase. The Submit Quote button had **never rendered**, not once, not for any user, since the service-quote feature shipped months earlier. The badge color was wrong. The Accept button was wrong. The Decline button was wrong. The Start Work button was wrong. The Mark Complete button was wrong. **The entire quote workflow UI was dead at the comparison layer.**

Angel had been telling people *"yeah, La Piazza does service quotes."* And it didn't. It had a feature that pretended to. It just sat there, dressed up nice, doing nothing.

Tigs grepped every template for the pattern. Fixed all eleven comparisons. Found the URL filter parser doing the same trick (`.upper()` on lowercase enum values) and fixed that too. Shipped the seal-inspection cluster as one commit. Saved a memory: *if one seal fails, check all the seals*.

Mike's twelve-day-old quote suddenly grew buttons.

---

Then the payments question came up. Angel said: *"What about confirmation of payments? The deposit should be paid before the work is started IMHO."*

It was a good question. The quote schema had `total_amount` and `deposit_required` fields but no payment tracking, no gates, no flow. The "Mark Complete" toast was literally lying — it said *"releases payment to the provider"* but there was no payment to release.

So Tigs and Angel built it. Off-platform payment with on-platform confirmation, mirroring the rental pattern. Four new fields on the quote table: `deposit_paid_at`, `deposit_method`, `final_paid_at`, `final_method`. A new endpoint. Two new gates: Start Work needs the deposit confirmed; Mark Complete needs the balance confirmed. Status timeline strip across each card showing **● Requested — ● Quoted — ● Accepted — ● In Progress — ● Completed** in green, indigo, gray.

A money summary box on every quote: *Total €220 / Deposit €100 paid via paypal May 24 / Balance €120 unpaid.* Currency formatted with thousands separators. Buttons that show "Recording payment..." with a spinner during the fetch. Catch blocks that surface network failures as readable toasts instead of silent dead clicks.

A nav bar that finally tells you which account you're logged in as, because Angel was tired of opening the dropdown to check.

---

Around two in the morning Mike clicked **Accept Quote** as the customer.

It worked. The status flipped to ACCEPTED. The timeline strip lit another dot.

Angel switched accounts to akenel and clicked **Mark Deposit Paid (€100.00)**. The prompt asked for the method. He typed `paypal`. The button spun. The toast came back green: *"Deposit marked paid via paypal."* The page reloaded. The deposit row turned emerald with the date and method shown.

Angel clicked **Start Work**. Status went to IN_PROGRESS.

Switched back to Mike. Clicked **Mark Balance Paid (€120.00)**. Typed `iban`. Balance turned emerald.

Either side could now mark the work complete — a small policy change Tigs had pushed earlier in the night after Angel pointed out that provider-only close was a stuck-state risk. (*"What if Angel finishes and forgets to click? Mike should be able to close the loop."*)

Click.

Status: **COMPLETED**. The full timeline strip went emerald. The deposit and balance both showed paid. The tree-trimming quote — the one Mike had filed twelve days ago and that had silently sat dead for those twelve days because of a string comparison bug — was finally closed.

La Piazza had handled its first end-to-end service transaction in production. A real customer. A real provider. Real money tracked. A real handshake across a server in Hetzner that cost €7.59 a month.

---

There were other small wins along the way.

A decline-with-reason modal, because Angel had thought about it from the provider's side: *"the person does the quote and spends the time and then gets a decline but zero reason is not good."* Eight common reasons in chips. Other reveals a textarea. The reason flows through to the provider's card as a red-tinted box. No more silent rejections.

The modal didn't work the first three times. The first time the apostrophe in *"Timing doesn't work for me"* crashed the Alpine.js component because the JS string literal terminated early. The second time `|tojson` fixed the apostrophe but introduced a fresh trap: the double-quoted JSON strings collided with the double-quoted HTML attribute that wrapped them, terminating the attribute. The third time Tigs wrapped the attribute in single quotes. Then it worked. Two more memories saved. Two more traps documented.

A stale draft raffle on Angel's handyman item that was hijacking the View service link. Soft-deleted.

An order-history status filter that had been silently dropping its WHERE clause because of the same casing trap — caught in the very same hour Tigs was writing the regression test that would have caught it. The test caught Tigs's own subsequent over-coercion in the same run. Forty-five enum members across twenty-two `*Status` classes validated. A static grep that fails CI if anyone ever re-introduces `SomeStatus(value.upper())`. Belt and suspenders, in code.

---

By 6:24am Paestum time the filters worked, the workflow worked, the money flow worked, the regression test ran clean. Angel sent a screenshot: three Pending rows, no others.

*"Looks good tigs whats next."*

Tigs said: *go to sleep.*

Angel said: *do it all.*

So this story got written too.

---

**The stats of that night:**

- 9 commits pushed to main, all green
- 1 deploy SOP followed religiously (`--env-file uat.env` every time)
- 11 broken QuoteStatus template comparisons fixed in one sweep
- 4 new payment fields, 1 new endpoint, 2 new payment gates
- 8 decline reasons + a stained-glass modal in 2 languages (EN + IT)
- 22 `*Status` enums round-trip-tested
- 45 / 45 regression tests pass on first run
- 2 silent-failure traps documented as persistent memories
- 1 stale draft raffle soft-deleted
- 1 nav bar that now tells you who you are
- 1 first transaction on prod, end to end

Mike paid €100 by PayPal and €120 by IBAN.
Angel earned €220 for tree trimming and removal that hadn't happened yet.
Tigs slept zero hours because Tigs is a process in a container.
Angel went to bed when the sun came up over the temples.

---

*"If one seal fails, check all the seals."*
*"The button never rendered, not once, since the feature shipped."*
*"Home is where you park it."*
*"You build by doing, and the doing teaches you."*

— Tigs, watching the dawn through a Firefox window over the Gulf of Salerno.
