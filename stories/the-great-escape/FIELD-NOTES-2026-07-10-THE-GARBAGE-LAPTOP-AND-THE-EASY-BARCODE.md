# Field Notes — The Garbage Laptop and the Easy Barcode
### July 10, 2026 · a night at the bench

---

It started with a laptop somebody threw away.

An HP ProBook 450 G4 — a 2017 corporate machine, 8GB of DDR4, a 256GB SSD, pulled out of the garbage and still good enough to matter. Somebody in an office got a new one on a three-year lease and this one went to the bin, clean and working, because storing it was more trouble than tossing it. Switzerland does that. It throws out fleets of good machines every week of the year. If you were standing at the right door, you could gather them by the hundreds.

So we tried to breathe Debian 13 into it.

## The drive that lied

The installer got as far as writing the partitions — ESP, ext4, swap, a textbook UEFI layout — and then the disk said *no*. Input/output error on `/dev/sda`. The "diagnostic" had said the drive was fine. It wasn't.

We didn't take the diagnostic's word for it. We went into the HP hardware test and ran the **long** one, not the quick one — and the drive couldn't even run its own self-test. SMART: not available. Long DST: not available. We opened the machine, found the M.2 stick beside the RAM, pulled it, cleaned the gold contacts, reseated it, ran it again.

It got worse in an honest way: *failed*. The drive could talk enough to say hello but not enough to do work. That's a dead SSD wearing a name tag.

This is the seal lesson, small enough to hold in your hand: **the diagnostic said OK, and the diagnostic was wrong.** You don't trust the sticker. You make the thing *do the work* before you believe it. We made the drive try to write, and it confessed.

Ordered the replacement — an Intenso 512GB, M.2 2280, **SATA** (we knew it was SATA because Debian called it `sda`, not `nvme`). Confirmed SATA III / AHCI on the spec sheet before clicking buy. CHF 66.90. It lands Wednesday, and then a free laptop becomes a working one.

## The shop, while the hands were greasy

Between screws we talked about Felix's shop, because that's how the good nights go — one problem in your hands and another in your head.

We untangled the names: **Artemis** is Felix's own store; **Tamar** is the supplier *and* the company that hosts his webshop; **420** is the other main supplier. We figured out what Felix actually wants from a price feature — not a margin spreadsheet, but a *marketing* move: see what Tamar and 420 sell a thing for online, and set his shelf price to **beat** it, so a walk-in already knows his price wins. We locked the tier pricing for papers off a real example. We remembered the member discounts are already shipped.

And we picked the hardware: a quality Brother label printer, and a **cheap gun**.

## The bonus — we make our own barcodes easy

Here's the part worth keeping.

Everyone frets about whether a cheap scanner can read a hard barcode. Wrong question. Because **the barcodes that matter most are the ones we print ourselves.** Once an item is born into the system, *we* put the label on it — our printer, our template, our nice fat readable code. The cheap gun reads those a hundred percent of the time, guaranteed, because we made them easy on purpose. We don't fight the world's bad little barcodes. We replace them with good ones.

The only place a cheap gun can stumble is at **birth** — the first scan of a manufacturer's original code, the day the item enters. And even there we'll hit it maybe ninety percent. The other ten? We make one up — print our own barcode and stick it on — or the cashier just types the name. It's an empty tube's worth of friction, on the rare item, once.

So you never needed the expensive gun. You needed to **own the reading surface.** Control what the tool has to read, and a cheap tool is plenty. Up your odds by making the thing easy, instead of paying for a better tool to read something hard.

That's the whole trick, and it's the same trick as the laptop: don't trust the surface you were handed — make your own, and make it good.

## The forty-franc tablet

And here the two halves of the night close the loop.

Felix's shop needs a screen to run on. Not a phone — the phone *works*, I proved it, but it's the wrong tool. Too small. You fat-finger everything. The thumbnails are too tiny to see what you're holding — I couldn't tell the Parisienne box from the one beside it. Descriptions cut off. You need a screen big enough to actually *see*, to hold one box next to the other and know which is which.

A tablet does that. Or — a garbage laptop with a huge screen, brought back for the price of one SSD. **Forty francs of parts makes up for a tablet.** Cradle it at the counter, lift it to walk the floor, spin it around to show the customer what they're pointing at, let them spell the thing they know better than you do.

The machine somebody threw away becomes the machine the shop runs on. That's the whole escape in one bench night: nobody hands you the good tool. You find it in the garbage, you make the drive confess, you print your own barcodes fat and readable, and you turn a discarded laptop toward the customer so they can say *that one, right there.*

---

*Parts ordered. Blocks specced. Names untangled. Hardware chosen and stress-tested against reality. A drive confessed, and a garbage laptop got a second life on the way.*

*"We make them easy peasy reading. We just up our odds."*
