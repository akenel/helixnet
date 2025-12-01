# HelixNET Sourcing System (Bestellungen)

**Status:** Planning
**Priority:** Q1 2025 (Post-Pam Go-Live)
**Owner:** Felix
**Target:** v3.0.0

---

## The Problem (IRL)

Felix has a pen & paper + XLS system for tracking product sourcing:
- Products that need suppliers
- Investigation status
- Known supplier codes
- Resolution tracking (crossed out with Caran pen when done)

**Current Pain:**
- Manual XLS on laptop
- No tracking of who researched what
- No quality ratings
- No lead time visibility
- No HelixNETWORK integration

---

## Felix's Current Workflow

```
┌──────────┬─────────────────────────────┬─────────────┬───────────┐
│ Date     │ Product                     │ Felix Admin │ Lieferant │
├──────────┼─────────────────────────────┼─────────────┼───────────┤
│ 16.04.21 │ Grow a Million Spiel        │ N/A         │ [BLANK]   │
│ 23.11.24 │ Metal Pipe Kurz             │ ?           │ 420       │
│ 16.10.25 │ Volcano Maintenance Set     │ [BLANK]     │ [BLANK]   │
│ 7.8.24   │ Canna Purple Fuel           │ [BLANK]     │ >Hem<     │
└──────────┴─────────────────────────────┴─────────────┴───────────┘

Legend:
- [BLANK] = Searching/investigating
- N/A = Not applicable
- ? = Unknown/pending
- >Hem< = Resolved with supplier Hemag Nova
- ✗ (crossed out) = Ordered/done
```

---

## Known Suppliers (Lieferanten)

| Code | Supplier Name | Category | Notes |
|------|---------------|----------|-------|
| 420  | BR Break Shop | Pipes, accessories | |
| WR   | Wellauer | General | |
| ND   | Near Dark | | |
| Hem  | Hemag Nova | CBD, hemp | |
| (TBD)| 8-12 more | | Felix to provide full list |

---

## Proposed Solution: Sourcing KB System

### 1. Supplier Registry
```
suppliers:
  - code: "420"
    name: "BR Break Shop"
    country: "CH"
    lead_time_days: 3-5
    quality_rating: A
    categories: [pipes, accessories]
    contacts: []
    notes: ""
```

### 2. Sourcing Request (KB-like)
```
sourcing_request:
  - id: SR-2024-001
    product: "Volcano Maintenance Set"
    requested_by: "Pam"
    requested_date: "2024-10-16"
    assigned_to: "Felix"
    status: "investigating"  # new, investigating, sourced, ordered, closed
    supplier: null
    notes: []
    resolution: null
```

### 3. Investigation Workflow
```
Status Flow:
NEW → INVESTIGATING → SOURCED → ORDERED → CLOSED
                   ↓
              NOT_AVAILABLE (with date)
```

### 4. Quality/ABC Rating System
```
A = ISO certified, preferred, reliable
B = Good quality, acceptable
C = Budget option, use with caution
```

### 5. HelixNETWORK Integration
- Contact tracking (John, Siggy, Joey)
- Event notes (Spannabis meetups)
- Cross-network sourcing options
- Country/customs considerations

### 6. MRP-lite
- Minimum stock levels
- Reorder quantities (2 box min, 5-pack, etc.)
- Lead time alerts
- Expected sales velocity

---

## UI Concepts

### Felix Dashboard - Sourcing Tab
```
┌─────────────────────────────────────────────────────────────┐
│ 📦 SOURCING REQUESTS                        [+ New Request] │
├─────────────────────────────────────────────────────────────┤
│ 🔍 3 Investigating │ ✓ 12 Sourced │ 📦 5 Ordered           │
├─────────────────────────────────────────────────────────────┤
│ SR-001 │ Volcano Set     │ 🔍 Investigating │ Felix │ 45d  │
│ SR-002 │ Metal Pipe Kurz │ ✓ 420           │ Done  │      │
│ SR-003 │ Canna Purple    │ ✓ >Hem<         │ Done  │      │
└─────────────────────────────────────────────────────────────┘
```

### Supplier Detail
```
┌─────────────────────────────────────────────────────────────┐
│ 420 - BR Break Shop                              Rating: A  │
├─────────────────────────────────────────────────────────────┤
│ Country: CH        │ Lead Time: 3-5 days                    │
│ Categories: Pipes, Accessories                              │
│ Products Sourced: 47                                        │
│ Last Order: 2024-11-15                                      │
├─────────────────────────────────────────────────────────────┤
│ Notes:                                                      │
│ - Good for bulk orders                                      │
│ - Contact: Hans (hans@breakshop.ch)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Model (Draft)

```python
class Supplier(Base):
    id: UUID
    code: str  # "420", "WR", "Hem"
    name: str
    country: str
    lead_time_days_min: int
    lead_time_days_max: int
    quality_rating: str  # A, B, C
    categories: List[str]
    contacts: JSON
    notes: str
    is_active: bool

class SourcingRequest(Base):
    id: UUID
    product_name: str
    product_sku: str | None  # Link to existing product
    requested_by: str
    requested_date: date
    assigned_to: str | None
    status: str  # new, investigating, sourced, not_available, ordered, closed
    supplier_id: UUID | None
    resolution_date: date | None
    resolution_notes: str | None
    min_order_qty: int | None
    expected_price: Decimal | None

class SourcingNote(Base):
    id: UUID
    request_id: UUID
    author: str
    created_at: datetime
    content: str
    source: str  # "research", "spannabis", "helixnetwork", "call"
```

---

## Implementation Phases

### Phase 1: Supplier Registry (1 week)
- [ ] Supplier model + CRUD API
- [ ] Import Felix's supplier list
- [ ] Basic UI in Felix dashboard

### Phase 2: Sourcing Requests (1 week)
- [ ] SourcingRequest model
- [ ] Status workflow
- [ ] Notes/history tracking
- [ ] UI for creating/managing requests

### Phase 3: Integration (1 week)
- [ ] Link to products
- [ ] MRP-lite (min stock alerts)
- [ ] HelixNETWORK contact integration

### Phase 4: Polish (1 week)
- [ ] ABC rating system
- [ ] Reports/analytics
- [ ] Export to XLS (for Felix backup comfort)

---

## Dependencies

- Pam go-live first (Jan 1)
- Felix's full supplier list (XLS import)
- HelixNETWORK contact data

---

## Questions for Felix

1. Full list of 10-12 suppliers with codes?
2. Current XLS format for import?
3. Who else can create sourcing requests? (Pam, Ralph?)
4. Approval workflow needed?
5. Budget thresholds for auto-approve?

---

*"Be water, my friend"* - BLQ

Created: 2025-12-01
