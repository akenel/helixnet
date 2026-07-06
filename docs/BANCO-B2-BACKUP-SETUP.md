# Banco Offsite Backup — Backblaze B2 (immutable, ransomware-proof)

**Status:** code SHIPPED (2026-07-05), waiting on Angel's Backblaze account/keys to go live.
**Owner of the remaining steps:** 🧍 Angel (external signup — I can't create the account).

---

## Why B2, on top of Google Drive

Banco backups already land in **three** places: the box (`/opt/backups/banco`, encrypted,
30 days), the laptop, and Google Drive (`ecolution-gdrive:HelixNet-DB-Backups/banco`, via
`banco_offsite_pull.py`). All good — **except** every one of those copies can be *deleted*
by whoever holds the credential. If the box is ever compromised (ransomware, a bad actor,
a fat-fingered `rm -rf`), the local copies die with it, and a stolen token could reach the
cloud copy too.

**Backblaze B2 with Object-Lock closes that hole.** Each uploaded backup is made
**immutable** for a lock window — during that window *nobody* can overwrite or delete it,
not even with the key that wrote it. The box uploads with a **write-only** key that can
only ADD files. So a fully-compromised box can keep making recovery points but **cannot
erase the ones already offsite.** That is the one copy an attacker can't take from you.

The blobs are already GPG/AES256 ciphertext, so B2 only ever holds opaque bytes — recovery
still needs the passphrase in `/root/.banco-backup-key` (which you also keep in KeePass).

---

## What you do (one time, ~10 minutes)

### 1. Make a Backblaze account
Sign up at <https://www.backblaze.com/b2/sign-up.html>. B2 gives **10 GB free** — our
backups are ~1.3 MB each, so 90 days of them is a rounding error. No card needed for free tier.

### 2. Create the bucket — **Object Lock ON at creation** ⚠️
B2 Console → **Buckets** → **Create a Bucket**:
- **Name:** `ecolution-banco-backups` (must be globally unique — add a suffix if taken)
- **Files are:** **Private**
- **Object Lock:** **ENABLE** ← the one irreversible choice. **It cannot be turned on later.**
  If you forget it, delete the bucket and make a new one with the box checked.
- Default Encryption: on (SSE-B2) is fine — belt on top of our own GPG.

### 3. Create the box's key — **write-only**
B2 Console → **Application Keys** → **Add a New Application Key**:
- **Name:** `banco-box-writeonly`
- **Allow access to Bucket(s):** the bucket above (scope it — not "all")
- **Type of Access:** **Write Only** (if the UI only offers Read/Write, uncheck read;
  the capability we need is just `writeFiles`)
- **Do NOT** grant deleteFiles / listAllBucketNames.
- Copy the **keyID** and **applicationKey** — the applicationKey is shown **once**.

### 4. Tell me the keys — **never in chat**
Two safe ways (pick one):
- **You run it:** `ssh root@46.62.138.218`, then create `/root/.banco-b2.env` (below), `chmod 600`.
- **I prompt you:** I run a `getpass` helper; you paste into the hidden prompt; it writes the
  file on the box. The key never appears in the transcript.

`/root/.banco-b2.env` (root-only, on the box):
```
B2_KEY_ID=<keyID from step 3>
B2_APP_KEY=<applicationKey from step 3>
B2_BUCKET=ecolution-banco-backups
B2_PREFIX=banco/
B2_LOCK_DAYS=14        # each backup immutable for 14 days
B2_KEEP_DAYS=90        # lifecycle auto-deletes ~90 days after upload
B2_LOCK_MODE=governance
```

### 5. (Setup, one time) turn on retention + lifecycle
For the *setup* call only, we need an admin key (write-only can't configure the bucket).
Easiest: your account's **master Application Key** (B2 Console → App Keys → the master key at
top), used **once from the laptop** and never stored on the box:
```
B2_KEY_ID=<master keyID> B2_APP_KEY=<master appKey> B2_BUCKET=ecolution-banco-backups \
  python3 scripts/ops/banco_b2_setup.py --env-file /dev/null
```
Expected: `✅ ... backups IMMUTABLE for 14 days (governance), auto-deleted ~90d ...`
(Or set the same in the B2 Console: bucket → **File Lock** → default retention 14 days, and
**Lifecycle Settings** → keep last version 90 days.)

---

## What happens after that (automatic)

`banco_backup.sh` step 4 calls `banco_b2_push.py "$FILE"` after every encrypted dump →
the blob ships to B2, immutable. A local ledger (`/opt/backups/banco/.b2-synced`) means the
write-only key never needs list rights and the nightly job never re-ships the whole pile.
Until `/root/.banco-b2.env` exists, step 4 is a clean no-op (nightly stays green).

**Verify a push landed:** in the B2 Console the object shows a padlock / retention date; or
`python3 scripts/ops/banco_b2_push.py /opt/backups/banco/<newest>.sql.gz.gpg` prints
`✅ banco/<name> … immutable offsite`.

## Restore drill (the backup is a rumor until you restore it)
Download a blob from B2 → `gpg --decrypt --passphrase-file /root/.banco-backup-key <blob> |
gunzip | psql -U helix_user -d <throwaway_db>`. The box's nightly script already proves the
decrypt+restore round-trip locally; this proves the *offsite* copy the same way.

---

## Files
- `scripts/ops/banco_b2_setup.py` — one-time Object-Lock + lifecycle (stdlib B2 API).
- `scripts/ops/banco_b2_push.py` — per-backup immutable upload (stdlib B2 API, write-only key).
- `scripts/ops/banco_backup.sh` — step 4 hook (non-fatal).
- Ported from `freehold/ops/{backup,b2-immutable}.py`.
