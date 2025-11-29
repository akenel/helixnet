# KB-035: Ralph's Admin Pain Points - The Scaling Challenge

**Created**: 2024-12-07 (Sunday drinks, honest conversation)
**Author**: Ralph (Rafi) with Felix
**Status**: CRITICAL - Operational feedback

---

## The Honest Truth

> "Felix, my hands are full now. Working and behind the keyboard. This is not something for nothing. Sure, faster and more accurate checkouts... but where is the reporting? Who can help? This is a lot of work."

---

## What Ralph Is Dealing With

### Time Split (Current Reality)
```
Before HelixNet:           Now:
─────────────────          ─────────────────
80% Sales floor            50% Sales floor
20% Admin/stock            50% Admin/Tech/System

Ralph is becoming half IT manager.
```

### The Paper Problem

Ralph printed color copies of products and KBs. Felix's response:

> "Rafi, I want LESS paper, not more. Those color printouts cost real money. 3000 items and 20 KBs - we can't print it all."

But Ralph's notes on those printouts? That's KNOWLEDGE:
- "2 left, old USB connectors"
- "New ones have USB 3.0, same look"
- "Sell old stock at 50% next BF"
- "New barcodes for new version"

**The printouts aren't the problem. The system not capturing this info IS.**

---

## Specific Pain Points

### 1. Old Stock vs New Version
**Example**: Power adapter product
- Old version: USB 2.0 connector, 2 units left
- New version: USB 3.0, different barcode, same look
- Need to: Discount old stock 50%, create new SKU

**Current process**: Ralph writes on printout, hopes he remembers.
**Needed**: Version tracking, discount scheduling, linked SKUs.

### 2. Sylvie's Unique Items
- 50 different styles of bags
- One-offs and personalized items
- Labels change frequently
- Stock is handmade, unpredictable

**Current process**: Ralph keeps it in his head.
**Needed**: Variant management, artisan product flags, custom notes.

### 3. Stock Alerts - The Wallet Problem

> "We sold out of all those Sylvie wallets. Sylvie won't be able to replenish till January. She needs 4-6 weeks to make 100 new wallets. Missed high season."

**What went wrong**: No low stock alert. No lead time visibility.
**Cost**: Lost sales during peak season.

**Needed**:
- Min stock level (alert threshold)
- Max stock level (reorder target)
- Lead time (supplier days to deliver)
- Reorder date calculation

### 4. Missing Reports

Ralph needs to see:
- Day to day comparison
- Week to week comparison
- Month to month comparison
- What's selling, what's not
- Who sold what (already have this!)
- Stock levels vs sales velocity

**The data EXISTS. The views DON'T.**

### 5. KB Management

Current:
- Edit in text files
- No preview
- No search
- Print to read

Needed:
- Web view of all KBs
- Quick edit
- Search across KBs
- Link products to KBs

---

## Felix's Response

> "Hey no stress Rafi, no pressure. Let's talk at end of month closing. I'll ask Angel to make sure we can view month to month, day to day, week to week comparison."

> "He can do some UI reports with HTML and save you a ton of time. So you can quickly display KBs, edit them, and a full proper product page."

### Minimum Viable Features Requested:

1. **Product page improvements**
   - Min/max stock levels
   - Lead times
   - Supplier info
   - Version notes

2. **Reporting dashboard**
   - Daily/weekly/monthly views
   - Sales comparisons
   - Stock alerts

3. **KB viewer/editor**
   - Web-based
   - Search
   - Quick edit

---

## The Core Insight

> "The system has all the information. We just need the system WITH the info to help us NOW."

Data without visibility = stress.
Data with visibility = power.

Ralph has the data. He needs the dashboard.

---

## Priority Matrix

| Need | Urgency | Effort | Impact |
|------|---------|--------|--------|
| Stock alerts (min/max) | HIGH | Low | High - prevent stockouts |
| Lead time tracking | HIGH | Low | High - plan reorders |
| Daily sales view | MEDIUM | Low | Medium - quick checks |
| Month comparison | MEDIUM | Medium | High - trends |
| KB web viewer | MEDIUM | Medium | Medium - accessibility |
| Product versioning | LOW | High | Medium - edge case |

---

## Ralph's Load

> "It may be like this until we get all our processes defined. And that means even more work and more KBs."

**Translation**: Ralph is documenting as he goes, but he's also running the shop, training Leandra, managing stock, and being half IT support.

**Felix's job**: Get Angel to build the views so Ralph can WORK, not just MANAGE.

---

## Action Items for Angel

1. [ ] Add min_stock, max_stock, lead_time_days to products table
2. [ ] Create stock alert view (items below min)
3. [ ] Create daily/weekly/monthly sales comparison report
4. [ ] Create simple KB viewer (HTML, read-only first)
5. [ ] Create reorder report (stock < min, with lead times)

---

## Key Quote

> "This is not something for nothing. Sure, faster and more accurate checkouts... but where is the reporting?"

Ralph is right. A POS without visibility is just a fancy cash register.

---

*Felix raises his glass one more time.*

**Felix**: "Rafi, you've been carrying this. I see it. Angel will help. By end of month, you'll have your dashboard. Promise."

**Ralph**: "Thanks Felix. I just want to help customers, not fight spreadsheets."

**Felix**: "That's exactly what we're building toward."
