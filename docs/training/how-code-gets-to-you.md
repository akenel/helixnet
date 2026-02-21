# How Code Gets To You: The HelixNet Pipeline

*A guide for Anne -- from keyboard to your screen in Kenya*

---

## The Big Picture

Every time you report a bug, something amazing happens. Your bug report travels from your phone in Kenya to a server in Germany, gets picked up by a developer in Sicily, fixed by a Tiger in a laptop, and the fix travels back to you -- sometimes in minutes.

This document explains exactly how that works. No magic. Just files moving through pipes.

---

## The 3 Places Code Lives

Think of it like a kitchen, a recipe book, and a restaurant:

| Place | What It Is | Where It Lives | Who Uses It |
|-------|-----------|---------------|-------------|
| **The Workshop** (Angel's Laptop) | Where code is written and edited | `/home/angel/repos/helixnet/` in Trapani, Sicily | Angel + Tigs (the AI co-pilot) |
| **The Warehouse** (GitHub) | Where every version of every file is stored | `github.com/akenel/helixnet` on the internet | Everyone can see the history |
| **The Store** (Hetzner Server) | Where the live application runs | `46.62.138.218` in Nuremberg, Germany | You, Anne! This is what you test |

**Your bug reports go to the Store. The fix starts at the Workshop. GitHub connects them.**

---

## The Journey of a Bug Fix

Let's follow BUG-009 (Invoice Details button not working) from your report to the fix appearing on your screen:

### Step 1: You Report the Bug

You open the QA Dashboard at `https://46.62.138.218/testing`, click "Report Bug", describe what happened. That bug gets saved in the **database** on the Hetzner server.

### Step 2: Angel + Tigs See It

Angel checks the bug list. He sees your report: "Invoice Details button not working." He tells Tigs: "Fix this."

### Step 3: Tigs Investigates

Tigs reads the code files on Angel's laptop. Finds the problem: when you click "Details", the modal opens and closes so fast you can't see it (a timing bug in the JavaScript).

### Step 4: Tigs Edits the Code

Tigs changes **one file** on Angel's laptop:
```
src/templates/camper/invoices.html
```
Changes the `viewInvoice()` function from instant (broken) to async (working).

At this point, ONLY Angel's laptop has the fix. You can't see it yet.

### Step 5: Git Commit + Push

```
git add invoices.html
git commit -m "fix: BUG-009 invoice Details button not working"
git push
```

This does three things:
1. **git add** -- "Hey Git, track this file"
2. **git commit** -- "Take a snapshot of this change with a message"
3. **git push** -- "Send this snapshot to GitHub"

Now GitHub has the fix. Your server still doesn't.

### Step 6: Deploy to Hetzner

```
ssh root@46.62.138.218          (connect to the server)
cd /opt/helixnet                (go to the code folder)
git pull                        (download the latest from GitHub)
docker compose up --build       (rebuild and restart the application)
```

**git pull** downloads the fix from GitHub to the server.
**docker compose** rebuilds the application with the new code.

### Step 7: You See the Fix

Next time you refresh the page, the new code is running. Click "Details" on an invoice -- the modal opens and stays open. Bug fixed.

---

## What is Git?

Git is a **time machine for files**. Every time someone makes a change, Git takes a snapshot called a **commit**. Each commit has:

- A unique ID (like `1fe510a`) -- the **SHA** (you'll see these in the bug tracker now!)
- A message explaining what changed
- Who made the change
- When they made it

You can go back to ANY previous snapshot. Nothing is ever truly lost.

**GitHub** is just a website that stores Git repositories (collections of snapshots) in the cloud so multiple people can work together.

---

## What is Docker?

Code files by themselves are just text. They can't DO anything. It's like having a recipe but no kitchen.

**Docker** is the kitchen. It reads the code files and builds a **container** -- a complete running application with everything it needs:
- Python (the programming language)
- FastAPI (the web framework)
- All the libraries and dependencies

When we run `docker compose up --build`, Docker:
1. Throws away the old container
2. Reads the new code
3. Builds a fresh container
4. Starts it up

The whole process takes about 30 seconds. That's why fixes can go live so fast.

---

## What is the Database?

The database is SEPARATE from the code. Think of it like this:

- **Code** = the building (walls, doors, windows, layout)
- **Database** = everything INSIDE the building (furniture, files, records)

When we rebuild the application (docker compose), we rebuild the BUILDING. The furniture (your data -- bugs, test results, customers) stays exactly where it is.

Sometimes we need to add a new room to the building. That's called a **migration**:
```
ALTER TABLE qa_bug_reports ADD COLUMN assigned_to VARCHAR(100);
```
This says: "Add a new shelf called 'assigned_to' to the bug reports storage."

Your existing bug reports are untouched. They just get a new empty shelf they can use.

---

## The Complete Pipeline

```
    YOU (Kenya)                    ANGEL + TIGS (Sicily)
    ============                   ====================

    Report Bug on                  See your bug report
    QA Dashboard          <----    Read the code
         |                         Find the problem
         |                         Fix it on laptop
         |                              |
         |                         git commit + push
         |                              |
         |                              v
         |                     GITHUB (Internet)
         |                     Stores every version
         |                              |
         |                         git pull on server
         |                         docker rebuild
         |                              |
         v                              v
    HETZNER SERVER (Germany)
    =========================
    Running Application  <----  New code deployed
    Database (your data)        Your data stays safe

    Refresh page
    Fix is live!
```

---

## Your Role in This

You are not "just testing." You are the **quality gate**. Nothing goes to production without passing through you.

When you file a bug:
1. It gets a number (BUG-001, BUG-002...)
2. It gets assigned to a developer
3. The developer fixes it and attaches the commit SHA
4. It gets reassigned to YOU for verification
5. YOU decide if it's really fixed
6. Only when YOU mark it "Verified" is it truly done

**The developer says "fixed." The tester says "verified." Those are two different things.** The tester has the final word.

---

## Key Terms Cheat Sheet

| Term | What It Means | Analogy |
|------|--------------|---------|
| **Repository (repo)** | A folder of code tracked by Git | A recipe book |
| **Commit** | A saved snapshot of changes | A dated entry in the book |
| **SHA** | The unique ID of a commit (e.g. `1fe510a`) | A page number |
| **Push** | Send commits from laptop to GitHub | Mail the recipe to the warehouse |
| **Pull** | Download commits from GitHub to server | Warehouse delivers to the store |
| **Deploy** | Make new code live on the server | Open the store with new products |
| **Docker** | Turns code files into a running app | The kitchen that follows recipes |
| **Container** | A running instance of the app | The meal being served |
| **Database** | Where data is stored (bugs, customers...) | The filing cabinet |
| **Migration** | Changing the database structure | Adding a new drawer to the cabinet |
| **API** | How the frontend talks to the backend | The waiter between you and the kitchen |
| **Frontend** | What you see (HTML, buttons, forms) | The restaurant dining room |
| **Backend** | What runs on the server (Python, FastAPI) | The kitchen |

---

## Questions You Might Have

**Q: Can I break anything by testing?**
A: No. Testing is reading and clicking. You cannot damage the system. That's the whole point -- we WANT you to try to break things so we can fix them before real customers find the problems.

**Q: What if I find the same bug twice?**
A: Report it again. Maybe the first fix didn't work. That's valuable information.

**Q: How do I know if a bug is really fixed?**
A: Check the bug in the QA Dashboard. If it says "Fixed" with a git SHA, the code change is deployed. Test it yourself. If it works, mark it "Verified." If it doesn't, change it back to "Open" and add a comment.

**Q: What does the git SHA mean?**
A: It's the ID of the exact code change that fixed the bug. For example, `1fe510a` -- you can think of it as a receipt number. It proves WHAT was changed and WHEN.

---

*Written by Angel and Tigs, February 21, 2026*
*For Anne -- the quality gate of HelixNet*
*"The developer says fixed. The tester says verified. The tester has the final word."*
