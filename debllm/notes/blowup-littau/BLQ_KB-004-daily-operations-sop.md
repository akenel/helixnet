# BLQ KB-004: Daily Operations SOP

**Owner:** Andy Warhol
**Created:** 2025-11-30
**ISO Reference:** ISO 9001:2015 - 8.1 Operational Planning and Control

---

## One-Man-Army Daily Routine

> *"Bruce Lee style - efficient, focused, no wasted motion"*

---

## Morning (07:00 - 12:00)

### 07:00 - Wake Up & Check
```
[ ] Check phone for overnight orders
[ ] Quick email scan (urgent only)
[ ] Mental prep for the day
```

### 07:15 - HelixNet Daily Backup (Automatic)
```bash
# Cron job runs automatically at 07:15
# Backs up: products, transactions, customers, batches
# Location: /backups/helixnet/daily/

# Verify backup ran:
ls -la /backups/helixnet/daily/$(date +%Y%m%d)*
```

### 07:30 - Production Planning
```
[ ] Check inventory levels in HelixNet
[ ] Review orders needing fulfillment
[ ] Plan production batch if inventory low
[ ] Gather raw materials for today's work
```

### 08:00 - Lab Work (Production Days)
```
If production needed:
[ ] Sanitize workspace
[ ] Weigh/measure raw materials
[ ] Follow batch production record (KB-003)
[ ] Mix, centrifuge, test
[ ] Fill, cap, label, box
[ ] Update batch record
[ ] Release batch in system
```

---

## Afternoon (12:00 - 17:30)

### 12:00 - Order Fulfillment
```
For each order:
[ ] Pick products from inventory
[ ] Record batch numbers on packing slip
[ ] Triple check: right product, right quantity
[ ] Pack with love (tissue, thank you card)
[ ] Seal and label shipping box
[ ] Generate shipping label
[ ] Update order status: SHIPPED
```

### 14:00 - UPS Pickup
```
[ ] All packages ready at door
[ ] Hand to UPS driver
[ ] Get scan confirmation
[ ] Wave goodbye (sun sparkle optional)
```

### 15:00 - Inventory Reconciliation
```
In HelixNet POS:
[ ] Check stock levels match physical
[ ] Flag any discrepancies
[ ] Reorder if below reorder point
[ ] Update any damaged/sample deductions
```

### 16:00 - Customer Service
```
[ ] Respond to emails (1-hour max)
[ ] Process returns/exchanges
[ ] Handle inquiries about products
[ ] Update customer notes in system
```

### 17:00 - Next Day Prep
```
[ ] Review tomorrow's orders
[ ] Stage products for morning
[ ] Check packaging supplies
[ ] Update production schedule if needed
```

### 17:30 - End of Day Closeout
```
In HelixNet POS:
[ ] Run daily sales report
[ ] Verify cash drawer (if applicable)
[ ] Complete shift closeout
[ ] Final backup verification

# Manual backup command (if needed):
make backup-postgres
```

---

## Weekly Tasks

### Monday - Supplier Day
```
[ ] Review raw material inventory
[ ] Place orders with suppliers:
    - Peru Organics (carrier oil)
    - 420/FourTwenty (bottles, boxes)
    - CBD supplier (isolate)
    - Printer (labels)
[ ] Update expected delivery dates
[ ] Reconcile supplier invoices
```

### Wednesday - Production Day
```
[ ] Major production batch
[ ] Full batch record completion
[ ] QC testing
[ ] Inventory update
```

### Friday - Review Day
```
[ ] Weekly sales report
[ ] Backup verification (all 5 days)
[ ] KB review - any updates needed?
[ ] Plan next week's production
[ ] Bank reconciliation
```

---

## Monthly Tasks

### First Week
```
[ ] Full physical inventory count
[ ] Compare to HelixNet records
[ ] Adjust discrepancies with notes
[ ] Generate monthly inventory report
```

### Second Week
```
[ ] Supplier performance review
[ ] Price comparison check
[ ] Quality review of recent batches
```

### Third Week
```
[ ] Financial review
[ ] Margin analysis by product
[ ] Cash flow check
[ ] Tax payment prep (if quarterly)
```

### Fourth Week
```
[ ] KB documentation review
[ ] Process improvement notes
[ ] New product R&D time
[ ] Next month planning
```

---

## Backup Procedures

### Automatic Daily Backup (07:15)
```bash
# Add to crontab:
15 7 * * * /home/angel/repos/helixnet/scripts/backup-daily.sh

# Backup script includes:
# - PostgreSQL database dump
# - Product images
# - Transaction logs
# - Configuration files
```

### Manual Backup Commands
```bash
# Full backup
make backup-all

# Database only
make backup-postgres

# Verify backup
make backup-list

# Restore (if needed)
make restore-postgres BACKUP_FILE=backup_20251130.sql
```

### Backup Retention
```
Daily backups:   Keep 7 days
Weekly backups:  Keep 4 weeks
Monthly backups: Keep 12 months
```

### Offsite Backup (Weekly)
```
Every Friday:
[ ] Copy weekly backup to external drive
[ ] Store in fireproof safe
[ ] Or: sync to cloud storage
```

---

## Emergency Procedures

### System Down
```
1. Don't panic
2. Check: docker compose ps
3. Restart: make up
4. If still down: make down && make up
5. If data issue: make restore-postgres
6. Document what happened
```

### Order Issue
```
1. Stop and breathe
2. Contact customer immediately
3. Offer solution (replacement/refund)
4. Document in customer notes
5. Update process to prevent repeat
```

### Product Quality Issue
```
1. Stop all sales of affected batch
2. Mark batch as HOLD in system
3. Investigate root cause
4. Follow recall procedure if needed (KB-003)
5. Document everything
```

---

## Daily Checklist (Print & Use)

```
DATE: _______________

MORNING
[ ] 07:15 - Backup verified
[ ] 07:30 - Production planned
[ ] 08:00 - Lab work (if needed)

AFTERNOON
[ ] 12:00 - Orders fulfilled
[ ] 14:00 - UPS pickup complete
[ ] 15:00 - Inventory reconciled
[ ] 16:00 - Emails answered
[ ] 17:00 - Tomorrow prepped
[ ] 17:30 - Closeout complete

NOTES:
_________________________________
_________________________________
_________________________________

ISSUES/FOLLOW-UP:
_________________________________
_________________________________
```

---

## Related KBs

- BLQ_KB-001: Vision & Launch Epic
- BLQ_KB-002: Product Catalog & SKU System
- BLQ_KB-003: Batch & Lot Tracking
- BLQ_KB-005: Cutover Checklist (Dev → Prod)
