# ISOTTO Sport Print Shop -- Testing Checklist

**Tester:** _______________
**Date:** _______________
**App:** ISOTTO Sport -- Print & Merch Management (HelixNet)
**Estimated time:** ~1.5 hours for first session

---

## ACCESS

**URL:** https://46.62.138.218/print-shop

**All passwords:** `helix_pass` (same for every account)

> **First time only:** Your browser will show a security warning ("Your connection is not private" or similar) because we use a self-signed certificate for testing. This is expected and safe:
> - **Chrome:** Click "Advanced" then "Proceed to 46.62.138.218 (unsafe)"
> - **Firefox:** Click "Advanced" then "Accept the Risk and Continue"
> - **Safari:** Click "Show Details" then "visit this website"
>
> After accepting, you should see the ISOTTO Sport login page with a blue gradient background.

---

## TEST ACCOUNTS

Pick one account per session. Start with **famousguy** (admin / owner) for the full picture.

| Username | Role | What you can do |
|----------|------|-----------------|
| **famousguy** | Admin (Owner & Master Printer) | Everything -- orders, catalog, suppliers, invoices, artworks, print queue. **Start here.** |
| **angel** | Admin (Platform Architect) | Full access, same as famousguy |
| **marco_d** | Designer (Lead Designer) | Artwork, orders, customers, catalog (read). No supplier/stock management. |
| **luca_p** | Operator (Machine Operator) | Production workflow, order status, print queue. No catalog/supplier edits. |
| **giulia_f** | Counter (Front Desk) | Create orders, customers, view everything. Cannot change order status or manage catalog. |

### Role Hierarchy

```
isotto-admin     = Full control (famousguy, angel)
isotto-manager   = Pricing, suppliers, stock, POs, invoices
isotto-operator  = Production, order status, print queue
isotto-designer  = Artwork, pre-press, proofs
isotto-counter   = Order intake, customers, basic read access
```

Each higher role includes all permissions of the roles below it.

---

## PHASE 1: FIRST LOGIN (5 min)

- [ ] Open https://46.62.138.218/print-shop
- [ ] Click the blue "Accedi" / "Log In" button
- [ ] On the Keycloak login page, enter: **famousguy** / **helix_pass**
- [ ] Click "Sign In"
- [ ] You should land on the Dashboard with a greeting
- [ ] Note: The dashboard shows stat cards (In Production, Pending Approval, Ready for Pickup, Pending Invoices)
- [ ] Check the platform nav bar at the very top: QA | Backlog | Camper | **ISOTTO** (highlighted)

**Tip:** Add `?lang=en` to any URL for English labels. Example:
`https://46.62.138.218/print-shop/dashboard?lang=en`

---

## PHASE 2: EXPLORE THE DASHBOARD (5 min)

- [ ] Read all stat cards (In Production, Pending Approval, Ready for Pickup, Pending Invoices)
- [ ] Click the Pending Invoices card -- it should navigate to the invoices page filtered by pending
- [ ] Go back to dashboard
- [ ] Check the Recent Orders section
- [ ] Check Revenue stats if shown

---

## PHASE 3: CUSTOMERS (10 min)

- [ ] Navigate to **Clienti** / Customers (via nav bar)
- [ ] You should see 4 customers (seed data)
- [ ] Click into a customer to see their details
- [ ] Try creating a NEW customer:
  - Name: Test Customer
  - Email: test@isotto.it
  - Phone: +39 333 123 4567
  - Address: Via Test 1, Trapani
- [ ] Search for the customer you just created
- [ ] Edit the customer (change phone number)
- [ ] Verify the change saved

---

## PHASE 4: CATALOG -- PRODUCTS (10 min)

- [ ] Navigate to **Catalogo** / Catalog
- [ ] You should see 10 products (seed data)
- [ ] Filter by category (T-Shirt, Hoodie, Polo, Cap, Tote, Mug)
- [ ] Filter by supplier
- [ ] Click into a product to see details (sizes, colors, price)
- [ ] Try creating a NEW product (as admin/manager):
  - Name: Test Polo Shirt
  - Category: POLO
  - Base price: 15.00
  - Pick a supplier
- [ ] Verify the product appears in the catalog

---

## PHASE 5: SUPPLIERS (5 min)

- [ ] Navigate to **Fornitori** / Suppliers
- [ ] You should see 2 suppliers (seed data)
- [ ] Click into a supplier to see details
- [ ] Try creating a NEW supplier (as admin/manager):
  - Name: Test Fornitore SRL
  - Contact: Mario Rossi
  - Email: mario@testfornitore.it
  - Phone: +39 0923 999888
- [ ] Verify the supplier appears in the list

---

## PHASE 6: ORDERS -- Full Workflow (20 min)

This is the core flow. Follow the full lifecycle of a print order.

### 6a: Create a Quotation

- [ ] Navigate to **Ordini** / Orders
- [ ] You should see 8 orders (seed data)
- [ ] Click "+ New Order" or navigate to create
- [ ] Select a customer
- [ ] Add a title: "Test Team Jerseys"
- [ ] Add a description: "10 polo shirts with team logo"
- [ ] Save -- the order should be created with status **QUOTATION**

### 6b: Add Line Items

- [ ] Open the order you just created
- [ ] Add a line item:
  - Pick a product from the catalog (e.g., a polo shirt)
  - Set quantity: 10
  - Pick size (e.g., L) and color (e.g., Navy)
  - Add personalization text if available (name on back)
- [ ] Add a second line item (different product or size)
- [ ] Verify the size summary shows correct counts

### 6c: Roster Import (Batch Orders)

- [ ] If the order has personalization, try the roster import:
  - Upload a list of names + sizes
  - Verify each name creates a line item

### 6d: Approve the Order

- [ ] Click "Approve" on the order
- [ ] Status should change to **APPROVED**
- [ ] Check the activity trail shows the approval

### 6e: Move to Production

- [ ] Change status to **IN PRODUCTION** (operator+ only)
- [ ] Check activity trail logs the change
- [ ] Line items should be trackable individually

### 6f: Complete the Order

- [ ] Advance line items through: PENDING -> IN_PRODUCTION -> QUALITY_CHECKED -> FINISHED
- [ ] Complete the order (operator+)
- [ ] Status should change to **READY FOR PICKUP** then **COMPLETED**

---

## PHASE 7: PRINT QUEUE (10 min)

- [ ] Navigate to **Print Queue** (via nav or direct URL)
- [ ] See the operator view of items in production
- [ ] Filter by status
- [ ] Try bulk status update: select multiple items, advance status
- [ ] Verify the changes reflect on the order detail page

---

## PHASE 8: PURCHASE ORDERS (10 min)

### 8a: Auto-Generate from Order

- [ ] Open an order with line items
- [ ] Click "Generate Purchase Orders" (manager+ only)
- [ ] Verify POs are created, grouped by supplier
- [ ] PO number format should be `IPO-YYYYMMDD-NNNN`

### 8b: Manual PO

- [ ] Navigate to **Ordini Acquisto** / Purchase Orders
- [ ] Create a manual PO:
  - Pick a supplier
  - Add items (product, qty, size, color)
- [ ] Advance status: DRAFT -> ORDERED -> RECEIVED
- [ ] When RECEIVED: verify stock levels auto-update
- [ ] Verify line item statuses update (STOCK_ORDERED -> STOCK_RECEIVED)

---

## PHASE 9: INVOICES (10 min)

- [ ] Navigate to **Fatture** / Invoices
- [ ] You should see 3 invoices (seed data)
- [ ] Click into an invoice to see details
- [ ] Try creating a new invoice from a completed order
- [ ] Record a partial payment:
  - Amount: half the total
  - Method: CASH
- [ ] Record the remaining payment:
  - Method: CARD
- [ ] Verify status changes: DRAFT -> ISSUED -> PAID
- [ ] Check the payment history shows both payments

---

## PHASE 10: ARTWORKS (5 min)

- [ ] Navigate to **Artwork** gallery
- [ ] View existing artworks (if any)
- [ ] Create a new artwork entry:
  - Title: "Test Logo v1"
  - Link to a customer
  - Mark as reusable
- [ ] Filter artworks by customer
- [ ] Filter by reusable only
- [ ] Edit the artwork (change title)
- [ ] Try to delete (should require manager+ role)

---

## PHASE 11: PREVIEW GALLERY (5 min)

- [ ] Open an order that has personalized items
- [ ] Navigate to the preview gallery for that order
- [ ] View personalization previews (name/number on product)
- [ ] Upload a new preview image if the form is available
- [ ] Verify previews are linked to the correct order

---

## PHASE 12: ROLE TESTING (15 min)

This phase tests that different users see different things. **Logout between each test.**

### 12a: Counter (giulia_f)

- [ ] Login as **giulia_f** / helix_pass
- [ ] Can view dashboard, orders, customers? **YES**
- [ ] Can create a new order? **YES**
- [ ] Can create a new customer? **YES**
- [ ] Try to change an order status (e.g., approve -> in_production) -- **SHOULD FAIL (403)**
- [ ] Try to create a supplier -- **SHOULD FAIL (403)**
- [ ] Try to create a catalog product -- **SHOULD FAIL (403)**
- [ ] Logout

### 12b: Designer (marco_d)

- [ ] Login as **marco_d** / helix_pass
- [ ] Can view artworks and create new ones? **YES**
- [ ] Can update artwork details? **YES**
- [ ] Can view catalog products? **YES**
- [ ] Try to delete an artwork -- **SHOULD FAIL (403, needs manager+)**
- [ ] Try to create a supplier -- **SHOULD FAIL (403)**
- [ ] Logout

### 12c: Operator (luca_p)

- [ ] Login as **luca_p** / helix_pass
- [ ] Can view print queue? **YES**
- [ ] Can change order status? **YES**
- [ ] Can bulk update print queue items? **YES**
- [ ] Can complete an order? **YES**
- [ ] Try to create a catalog product -- **SHOULD FAIL (403, needs manager+)**
- [ ] Try to create a purchase order -- **SHOULD FAIL (403, needs manager+)**
- [ ] Try to update an invoice -- **SHOULD FAIL (403, needs manager+)**
- [ ] Logout

### 12d: Admin (famousguy)

- [ ] Login as **famousguy** / helix_pass
- [ ] Can do everything above? **YES**
- [ ] Can create/edit/delete suppliers? **YES**
- [ ] Can create/edit/delete catalog products? **YES**
- [ ] Can manage stock (bulk update)? **YES**
- [ ] Can create/manage purchase orders? **YES**
- [ ] Can update invoices? **YES**
- [ ] Can delete artworks? **YES**

---

## PHASE 13: NAVIGATION & UI (5 min)

- [ ] Platform nav bar (top): QA | Backlog | Camper | ISOTTO -- all links visible and clickable
- [ ] App nav bar: all links work (Dashboard, Orders, Catalog, Suppliers, POs, Invoices, Customers, Artworks)
- [ ] Mobile: resize browser to phone width -- nav collapses to horizontal scroll
- [ ] Language switch: click IT/EN in the status bar footer -- labels change
- [ ] Status bar footer: shows system health, time, current user, language switch

---

## BUG REPORTING

When you find something broken or confusing:

1. **Screenshot it** (or describe what you see)
2. **Note which user** you were logged in as
3. **Note what you clicked** and what you expected to happen
4. **Send to Angel on Telegram** (@BigKingFisher)

### What counts as a bug:
- Page shows an error or blank screen
- Button does nothing when clicked
- Data doesn't save after you submit a form
- Something looks wrong (overlapping text, broken layout)
- A feature is missing or incomplete
- Wrong role can access something they shouldn't
- Right role is blocked from something they should access

### What's NOT a bug (for now):
- Italian labels (use `?lang=en` for English)
- Empty sections with no seed data (create your own test data)
- Session timeout after ~30 minutes (log out and back in)

---

## KNOWN ISSUES

1. **Certificate warning:** First visit will show a security warning -- accept it once (see ACCESS section).
2. **Session timeout:** Keycloak tokens expire after ~30 minutes. If you get "Not authenticated," log out and back in.
3. **English mode:** Most labels default to Italian. Add `?lang=en` to any URL for English.
4. **Artwork file upload:** Artwork entries store metadata only -- actual file upload/storage may not be fully wired yet.
5. **Preview generation:** Preview images may need to be manually uploaded rather than auto-generated.

---

## AFTER TESTING

Send Angel a quick summary:
- What worked well?
- What was confusing?
- What broke?
- Any suggestions?

---

## API ENDPOINT REFERENCE

For automated testing or API-level verification:

### Customers
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/customers` | Any |
| GET | `/api/v1/print-shop/customers` | Any |
| GET | `/api/v1/print-shop/customers/{id}` | Any |
| PUT | `/api/v1/print-shop/customers/{id}` | Any |

### Orders
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/orders` | Any |
| GET | `/api/v1/print-shop/orders` | Any |
| GET | `/api/v1/print-shop/orders/{id}` | Any |
| PUT | `/api/v1/print-shop/orders/{id}` | Operator |
| PATCH | `/api/v1/print-shop/orders/{id}/status` | Operator |
| POST | `/api/v1/print-shop/orders/{id}/approve` | Any |
| POST | `/api/v1/print-shop/orders/{id}/complete` | Operator |

### Line Items
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/orders/{id}/items` | Any |
| GET | `/api/v1/print-shop/orders/{id}/items` | Any |
| PUT | `/api/v1/print-shop/orders/{id}/items/{item_id}` | Any |
| DELETE | `/api/v1/print-shop/orders/{id}/items/{item_id}` | Any |
| PATCH | `/api/v1/print-shop/orders/{id}/items/{item_id}/status` | Operator |
| POST | `/api/v1/print-shop/orders/{id}/roster` | Any |

### Order Utilities
| Method | Endpoint | Min Role |
|--------|----------|----------|
| GET | `/api/v1/print-shop/orders/{id}/size-summary` | Any |
| GET | `/api/v1/print-shop/orders/{id}/activities` | Any |
| POST | `/api/v1/print-shop/orders/{id}/comment` | Any |
| POST | `/api/v1/print-shop/orders/{id}/previews` | Any |
| GET | `/api/v1/print-shop/orders/{id}/previews` | Any |

### Invoices
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/invoices` | Any |
| GET | `/api/v1/print-shop/invoices` | Any |
| GET | `/api/v1/print-shop/invoices/{id}` | Any |
| PUT | `/api/v1/print-shop/invoices/{id}` | Manager |
| PATCH | `/api/v1/print-shop/invoices/{id}/payment` | Any |

### Catalog Products
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/catalog/products` | Manager |
| GET | `/api/v1/print-shop/catalog/products` | Any |
| GET | `/api/v1/print-shop/catalog/products/{id}` | Any |
| PUT | `/api/v1/print-shop/catalog/products/{id}` | Manager |
| DELETE | `/api/v1/print-shop/catalog/products/{id}` | Manager |

### Stock
| Method | Endpoint | Min Role |
|--------|----------|----------|
| GET | `/api/v1/print-shop/catalog/products/{id}/stock` | Any |
| PUT | `/api/v1/print-shop/catalog/products/{id}/stock` | Manager |
| POST | `/api/v1/print-shop/catalog/products/{id}/stock/receive` | Any |

### Suppliers
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/catalog/suppliers` | Manager |
| GET | `/api/v1/print-shop/catalog/suppliers` | Any |
| GET | `/api/v1/print-shop/catalog/suppliers/{id}` | Any |
| PUT | `/api/v1/print-shop/catalog/suppliers/{id}` | Manager |
| DELETE | `/api/v1/print-shop/catalog/suppliers/{id}` | Manager |

### Purchase Orders
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/catalog/purchase-orders` | Manager |
| GET | `/api/v1/print-shop/catalog/purchase-orders` | Any |
| GET | `/api/v1/print-shop/catalog/purchase-orders/{id}` | Any |
| PUT | `/api/v1/print-shop/catalog/purchase-orders/{id}` | Manager |
| PATCH | `/api/v1/print-shop/catalog/purchase-orders/{id}/status` | Manager |
| POST | `/api/v1/print-shop/catalog/purchase-orders/generate-from-order/{order_id}` | Manager |

### Artworks
| Method | Endpoint | Min Role |
|--------|----------|----------|
| POST | `/api/v1/print-shop/catalog/artworks` | Any |
| GET | `/api/v1/print-shop/catalog/artworks` | Any |
| GET | `/api/v1/print-shop/catalog/artworks/{id}` | Any |
| PUT | `/api/v1/print-shop/catalog/artworks/{id}` | Any |
| DELETE | `/api/v1/print-shop/catalog/artworks/{id}` | Manager |

### Dashboard & Print Queue
| Method | Endpoint | Min Role |
|--------|----------|----------|
| GET | `/api/v1/print-shop/dashboard` | Any |
| GET | `/api/v1/print-shop/print-queue` | Any |
| PATCH | `/api/v1/print-shop/print-queue/bulk-status` | Any |

---

*Created: Feb 25, 2026 | HelixNet | ISOTTO Sport Print Shop | Server: Hetzner CX32*
*"If one seal fails, check all the seals."*
