---
error_id: ERROR-042
title: Product Descriptions All Blank After Bulk Operation
service: helix-platform
error_domain: functional
severity: high
resolution_group: business-functional
assignee: sales-team
first_seen: 2025-11-27
last_seen: 2025-11-27
occurrence_count: 1
in_kb: true
auto_fix: false
fix_command: null
requires_human: true
requires_business_decision: true
related_errors:
  - ERROR-043
  - ERROR-044
keywords: [products, descriptions, blank, bulk, data-quality, user-error]
patterns:
  - "product.*description.*null"
  - "description.*empty.*blank"
  - "bulk update.*description"
---

## 🔍 Symptoms
- POS receipts show product names but no descriptions
- Pam reports "I can't tell customers what they bought - no descriptions!"
- Database query shows many products with `description = NULL` or `description = ''`
- **Not visible in system logs** (this is a functional/data issue, not technical error)

## 🧠 Common Causes
1. **User fat-fingered bulk edit** (70%) - Admin accidentally set all descriptions to blank
2. **CSV import with wrong column mapping** (20%) - Description column not mapped correctly
3. **Database migration issue** (5%) - Schema change dropped descriptions
4. **SQL injection or mass update error** (5%) - Script gone wrong

## 👥 Resolution Group
**Primary:** business-functional (Sales team reviews data)
**Secondary:** tech-devops (implements rollback or fix)
**Decision Maker:** Sales team lead
**Escalation Path:** Sales team → Decides rollback vs re-import vs manual fix → DevOps implements

## 🩺 Diagnosis Steps

### 1. Check how many products affected
```sql
SELECT COUNT(*) as blank_count
FROM products
WHERE description IS NULL OR description = '';
```

### 2. Check recent bulk operations
```sql
SELECT *
FROM product_audit_log
WHERE operation IN ('BULK_UPDATE', 'CSV_IMPORT')
ORDER BY timestamp DESC
LIMIT 10;
```

### 3. Check who made the change
```sql
SELECT user_id, username, operation, COUNT(*) as changes
FROM product_audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY user_id, username, operation
ORDER BY changes DESC;
```

### 4. Check CSV import logs (if recent import)
```bash
docker logs helix-platform | grep "CSV import" | tail -20
```

### 5. Review database backup timestamps
```bash
ls -lht backups/postgres/ | head -5
```

## ✅ Resolution

### Option 1: Rollback to Last Good Backup
**Best if:** Bulk operation happened recently (< 1 hour ago) and no other changes made

```bash
# 1. Identify last good backup
ls -lht backups/postgres/ | grep "before-bulk-update"

# 2. Stop database
docker stop postgres

# 3. Restore backup
./scripts/restore-postgres.sh backups/postgres/2025-11-27_09-00_before-bulk-update.sql

# 4. Restart services
make up
```

**Pros:** Clean rollback, no data loss
**Cons:** Loses any changes made after backup
**Time:** ~10 minutes

---

### Option 2: Re-import from Corrected CSV
**Best if:** Bulk import was the cause and you have corrected CSV

```bash
# 1. Sales team provides corrected CSV file
cp /path/to/corrected_products.csv /tmp/

# 2. Validate CSV (check description column)
head -5 /tmp/corrected_products.csv

# 3. Run import script (with dry-run first)
python scripts/import_products.py --file /tmp/corrected_products.csv --dry-run

# 4. Run actual import
python scripts/import_products.py --file /tmp/corrected_products.csv --update-only
```

**Pros:** Only updates descriptions, leaves other fields intact
**Cons:** Requires Sales team to provide corrected CSV
**Time:** ~30 minutes (+ Sales team time to prepare CSV)

---

### Option 3: Manual Bulk Fix via Admin UI
**Best if:** Few products affected (< 50) or need selective editing

```bash
# 1. Sales team logs into Admin UI
https://helix.local/admin/products

# 2. Bulk select affected products
# 3. Use "Bulk Edit" feature to set descriptions
# 4. Review and save
```

**Pros:** Surgical fix, Sales team controls exactly what changes
**Cons:** Slow for many products
**Time:** ~1-2 hours (depends on product count)

---

### Option 4: SQL Restore from Audit Log
**Best if:** You have audit log tracking previous values

```sql
-- Find previous description values from audit log
SELECT product_id, old_value as previous_description
FROM product_audit_log
WHERE field_name = 'description'
  AND timestamp < '2025-11-27 10:00:00'
ORDER BY timestamp DESC;

-- Restore descriptions
UPDATE products p
SET description = subq.previous_description
FROM (
    SELECT DISTINCT ON (product_id) product_id, old_value as previous_description
    FROM product_audit_log
    WHERE field_name = 'description'
      AND timestamp < '2025-11-27 10:00:00'
    ORDER BY product_id, timestamp DESC
) subq
WHERE p.id = subq.product_id
  AND (p.description IS NULL OR p.description = '');
```

**Pros:** Restores exact previous values
**Cons:** Requires audit log enabled
**Time:** ~5 minutes

## 📝 Notes

### Why No Auto-Fix?
- **Requires business decision:** Which data is "correct"?
- **Data integrity risk:** Can't automatically guess correct descriptions
- **Approval needed:** Sales team must verify fix before applying

### Root Cause Analysis (RCA)

**What happened:** Ralph (admin user) performed bulk edit operation and accidentally cleared all descriptions

**Why it happened:**
1. UI didn't show clear warning for bulk operations
2. No confirmation dialog for mass changes
3. No audit trail visible to user

**Prevention measures:**
1. Add confirmation dialog: "You are about to change 3000 products. Are you sure?"
2. Add undo feature for bulk operations (last 5 operations)
3. Implement staging area: Bulk changes go to review queue before applying
4. Add role permission: Only store manager can do bulk >100 products

### Impact Assessment
- **User Impact:** High (Pam can't describe products to customers)
- **Revenue Impact:** Medium (slower checkout, confused customers)
- **Technical Impact:** None (system works, data quality issue)
- **Urgency:** High (fix within 1-2 hours, affects current sales)

## 📜 History
- **2025-11-27 10:15** (pam): Reported issue via phone to Ralph
- **2025-11-27 10:20** (ralph): Confirmed via database query (2847 products affected)
- **2025-11-27 10:25** (angel): Determined cause (Ralph's bulk edit at 09:58)
- **2025-11-27 10:45** (sales-team): Decision: Option 1 (rollback to 09:00 backup)
- **2025-11-27 10:55** (angel): Rollback completed, 2847 descriptions restored
- **2025-11-27 11:00** (pam): Confirmed fix, receipts show descriptions again

## 🔗 References
- Product import documentation: [internal wiki]
- Bulk operations best practices: [internal wiki]
- Database backup/restore guide: `scripts/README.md`
- Audit log schema: `docs/database-schema.md`
