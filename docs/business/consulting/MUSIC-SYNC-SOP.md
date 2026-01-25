# Music Library Sync SOP
## Sunrise Chain → Google Drive
### ISO 9001 Aligned | Consistent Backup Process

---

## PURPOSE

Ensure the sunrise-chain music library is backed up to Google Drive consistently. No excuses. No "I forgot." Automated where possible, manual checklist where not.

---

## CURRENT SETUP

**Local Library:**
```
/home/angel/repos/helixnet/compose/helix-media/music/sunrise-chain/
```

**Backup Target:**
- Google Drive (via n8n workflow or rclone)
- Credential: `googleDriveOAuth2Api` (ID: NNZYG1RA9Qnau0Ki)

**Reference Workflow:**
- `/home/angel/repos/helixnet/n8n-workflows/eco-gdrive-uploads-v1.json`
- Watches folder → Renames → Logs manifest → Uploads to GDrive

---

## OPTION A: N8N AUTOMATED SYNC

### Setup
1. Copy `eco-gdrive-uploads-v1.json` workflow
2. Modify watch path to: `/home/angel/repos/helixnet/compose/helix-media/music/sunrise-chain/`
3. Set GDrive destination folder: `Music/sunrise-chain/`
4. Activate workflow

### What It Does
- Watches for new `.mp3` files
- Renames with timestamp: `YYYYMMDD_HHMMSS_track-name.mp3`
- Logs to `manifest.json`
- Uploads to Google Drive

### Verification
- Check n8n execution log daily
- Verify manifest.json has new entries
- Spot-check GDrive folder weekly

---

## OPTION B: RCLONE MANUAL/CRON SYNC

### Install (one-time)
```bash
curl https://rclone.org/install.sh | sudo bash
rclone config  # Setup Google Drive remote as "gdrive"
```

### Manual Sync Command
```bash
rclone sync /home/angel/repos/helixnet/compose/helix-media/music/sunrise-chain/ gdrive:Music/sunrise-chain/ --progress
```

### Cron Setup (daily at 3am)
```bash
crontab -e
# Add:
0 3 * * * rclone sync /home/angel/repos/helixnet/compose/helix-media/music/sunrise-chain/ gdrive:Music/sunrise-chain/ >> /var/log/music-sync.log 2>&1
```

### Verification
```bash
rclone check /home/angel/repos/helixnet/compose/helix-media/music/sunrise-chain/ gdrive:Music/sunrise-chain/
```

---

## WEEKLY CHECKLIST

- [ ] Count local tracks: `ls -1 sunrise-chain/*.mp3 | wc -l`
- [ ] Count GDrive tracks: `rclone ls gdrive:Music/sunrise-chain/ | wc -l`
- [ ] Numbers match? If not, run sync
- [ ] Check for corrupted files (play random 3)
- [ ] Update track count in SESSION-STATE.md

---

## RECOVERY

If GDrive is lost:
- Local is source of truth
- Re-run full sync
- Verify with `rclone check`

If local is lost:
- Download from GDrive: `rclone copy gdrive:Music/sunrise-chain/ ./sunrise-chain/`
- Verify integrity

---

## 5-STAR STANDARD

- Sync runs automatically (no manual intervention needed)
- Failures alert immediately (n8n notification or cron email)
- Weekly verification confirms match
- Music is NEVER lost

---

**Document Version:** 1.0
**Created:** January 25, 2026

