# What we're really doing — in plain English

La Piazza lets ordinary people make real things — a voiceover, a postcard, a video,
one day a 3D model — without knowing anything about code, AI models, or servers.

How? Every job is a **recipe**: a fixed, tested set of steps. You pick a recipe, you
give it your words or your photo, and a finished file comes back. No surprises,
because we wrote and tested the steps before you ever ran them.

Three things can be swapped, and one thing can't. Knowing which is which is the
whole design.

---

## The three "Bring Your Owns"

Think of a recipe like a dish in a restaurant: `INPUT → PROCESS → OUTPUT`.

### 1. Bring Your Own Brain (BYOB) — *who thinks* — SAFE to swap

The "brain" is the AI model that does the thinking part of a recipe (writing a
script, picking words). You can bring your own — your own Ollama Turbo key, or any
model. By default we use a shared one.

**Why it's safe:** a brain is a *resource*, like electricity. A different brain
gives the same *kind* of answer. The recipe still decides what to ask it.

### 2. Bring Your Own Hardware (BYOH) — *where it runs* — SAFE to swap

The "hardware" is the machine that does the work. You can run a recipe on our
server, or on your own computer, or one day on a friend's gaming PC. The job goes
wherever there's a capable machine.

**Why it's safe:** a machine is a *resource* too. Before any job is sent, we check
the machine is capable (enough memory, the right tools). If it can't run the
recipe, it's politely turned away at the door — it never gets the job. Same output,
different machine.

> The kitchen and the cook can change. You can cook the same dish in any kitchen,
> with any qualified cook, and it still comes out right.

### 3. Bring Your Own Software (BYOS) — *what it does* — **NOT** offered, on purpose

The "software" is the actual procedure — the tools and steps that turn your input
into the output. **This is the recipe itself.** We do not let people swap it at
will, and that's a feature, not a limit.

> If every customer rewrites the recipe card, you don't have a restaurant anymore —
> you have a roomful of strangers cooking unknown things.

---

## Why the software stays fixed

**The recipes ARE our software.** That's the product. Fixing them is what lets us
promise three things nobody can promise with "bring your own software":

- **No surprises.** We tested the steps. We know what comes out.
- **It can be supported.** We can fix a recipe we wrote. We can't debug a stranger's
  broken script at 11pm.
- **It protects the people who lend hardware.** If anyone could ship their own code
  to a member's machine, we'd have built a way for strangers to run unknown programs
  on your computer. A member lends their PC to run *vetted recipes* — not a mystery
  binary. Fixed recipes are the safety contract for both sides of the exchange.

This is the same discipline behind everything else we build: write it down, test it,
version it, then ship it. You don't get reliable results from software you don't
control.

---

## But the menu still grows — through a gate, not at runtime

"Fixed software" does **not** mean "never anything new." It means new software enters
in **one** controlled place:

- **At runtime, mid-job — never.** That's the chaos we avoid.
- **Into the catalog, after testing — always.** A new recipe is one new tested entry
  in the library. Either we add it, or eventually a trusted member submits one and it
  passes a **review-and-test gate before it's published**. Nothing runs in the square
  until it's been cooked and tasted first.

It's an **app store, not sideloading**. A **signed package registry, not arbitrary
code**. The menu gets bigger every week — every dish on it has been tested.

So the honest one-liner:

> **Bring your own brain. Bring your own hardware. You don't bring your own software —
> you pick from recipes we've tested. The menu grows, but every dish has been cooked
> and tasted first. That's the guarantee.**
