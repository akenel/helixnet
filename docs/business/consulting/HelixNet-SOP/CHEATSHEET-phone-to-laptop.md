# Phone-to-Laptop Cheat Sheet
### FP3 USB + ADB Pipeline

---

## THE OLD WAY (Telegram Round-Trip)

Phone > Telegram Saved Messages > Desktop App > Save to Downloads

**Problems:** Compresses photos, 2GB video limit, one-by-one, slow.

---

## THE NEW WAY (USB Cable)

### You Do:

1. Plug USB cable into phone + laptop
2. Say "Tigs, pull the new stuff"

### Tigs Does:

1. `adb pull` -- grabs photos, videos, voice memos (full quality)
2. Sorts into `/home/angel/Pictures/FP3-backup-YYYY-MM-DD/`
3. Cleans phone if storage > 70%
4. Reports what came in

---

## IF THE PHONE ASKS

| Screen | Tap |
|--------|-----|
| "Allow USB debugging?" | **Allow** (check "Always allow") |
| "USB mode?" | **File Transfer / MTP** |

---

## IF ADB DOESN'T CONNECT

1. Unplug cable, wait 5 sec, replug
2. Check phone screen for the "Allow" popup
3. If nothing: Settings > System > Developer Options > USB Debugging = ON

### How to unlock Developer Options (one-time):
Settings > About Phone > tap **Build Number** 7 times

---

## WHAT TRANSFERS (AND WHAT DOESN'T)

| Content | Transfers | Where |
|---------|-----------|-------|
| Photos (DCIM) | Full resolution JPG | `photos/` |
| Videos (DCIM) | Full resolution MP4 | `videos/` |
| Voice memos | OGG/M4A | `voice/` |
| Telegram downloads | Already on laptop | `~/Downloads/Telegram Desktop/` |
| App data, contacts | NO -- needs Google backup | -- |

---

## FIELD WORK PROTOCOL

1. **Shoot everything** -- photos, videos, voice memos. Don't hold back.
2. **Come home, plug in** -- Tigs pulls and sorts.
3. **Review together** -- Tigs shows what came in, you pick what to use.
4. **Phone stays light** -- delete after backup, keep it under 50%.

---

*One cable. Full quality. No Telegram tax.*
