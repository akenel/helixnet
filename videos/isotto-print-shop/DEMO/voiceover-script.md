# ISOTTO Sport -- Print Shop Management Demo

## Overview
- **Target audience:** Famous (owner), ISOTTO staff, prospective print shops
- **Language:** English (base), Italian labels visible on-screen
- **Runtime:** ~4:30
- **Demo data:** 4 customers, 7 orders (Angel's real postcard printing as the story)

---

## Scene 1: Intro Card (5s)
*Static title card -- no voiceover during this shot.*

---

## Scene 2: Login (15s)
*Screen shows the ISOTTO Sport login page at /print-shop*

- "This is ISOTTO Sport -- a print shop management system built for Trapani's finest since nineteen sixty-eight."
- "We're logging in as Famous, the owner, through Keycloak single sign-on."

---

## Scene 3: Dashboard -- Morning Overview (25s)
*Screen shows the dashboard with 4 stat cards and active orders table*

- "Every morning, Famous opens the dashboard."
- "Four numbers: orders in production, pending approval, ready for pickup, and completed today."
- "Below that -- every active job at a glance. Customer name, product type, status. One screen, no paper."
- "Quick actions at the bottom -- new order, customer lookup, or jump straight to ready-for-pickup."

---

## Scene 4: Order Board -- All Orders (20s)
*Screen shows /print-shop/orders with all orders listed, filters visible*

- "The order board. Every print job in the shop -- filterable by status, product type, or free text search."
- "Seven orders, across the full lifecycle. Postcards invoiced, business cards ready, menus in production, new quotes waiting."
- "Color-coded badges tell you the status instantly."

---

## Scene 5: Order Detail -- Pizza Planet 4-UP (30s -- MONEY SHOT)
*Screen shows /print-shop/orders/{id} for the Pizza Planet postcard order*

- "Let's open a real job. Pizza Planet four-UP postcards -- two hundred cards for Ciccio's wood-fired pizza in Bonagia."
- "The quote section: quantity, unit price, total. Twenty-five cents per card, fifty euro."
- "Now the print specifications -- this is what makes it a print shop system."
- "Two-fifty GSM card stock. CMYK full color. Duplex with short-edge flip. No lamination."
- "Cutting instructions: one horizontal cut, one vertical cut through center. Four cards from one A4 sheet."
- "Proof approved, production notes logged. The complete paper trail -- digitally."

---

## Scene 6: Create New Order (30s)
*Screen shows /print-shop/orders/new, filling in a new order*

- "A customer walks in. New order."
- "Pick the customer, enter a title and description."
- "Product type -- postcard. Quantity, price. Then the print specs."
- "Paper weight, color mode, duplex settings, lamination, size, copies per sheet."
- "Cutting instructions for the machine operator. Save -- and it starts as a quote."
- "Counter staff creates it. Manager approves it. Operator prints it."

---

## Scene 7: Status Workflow -- Advance Order (20s)
*Screen shows a QUOTED order, then clicking through status transitions*

- "The PuntaTipa hotel postcard set. Status: Quoted."
- "Famous reviews the estimate. Clicks Approve. Status moves to Approved."
- "Assign an operator, start production, quality check, ready for pickup."
- "Eight steps from quote to invoice. Every transition logged with timestamp."

---

## Scene 8: Customer Lookup (20s)
*Screen shows /print-shop/customers, search for "Angelo"*

- "Customer lookup. Search by name, company, phone, or email."
- "Angelo Kenel -- UFA Foo Fighters. Four orders, eighty-five euro total spend."
- "Expand to see the full order history. Pizza Planet postcards, Camper tent cards, Color Clean batch, wax seal labels."
- "Every customer, every euro, tracked from day one."

---

## Scene 9: RBAC Demo -- Giulia at the Counter (25s)
*Screen shows logout, login as giulia_f, limited access visible*

- "Now let's switch users. Giulia works the front desk."
- "She logs in with her own Keycloak account. Same system, different view."
- "She can create orders, look up customers, prepare quotes."
- "But she can't approve orders, can't change production status, can't see pricing controls."
- "Role-based access. The counter sees what the counter needs. The boss sees everything."

---

## Scene 10: Outro Card (5s)
*Static recap card -- no voiceover during this shot.*

---

## Key Messages
- Replace paper notebooks and WhatsApp threads with searchable, trackable digital records
- Print-specific fields: GSM, CMYK, duplex mode, lamination, cutting instructions
- 8-step order lifecycle from quote to invoice, fully visible
- Dashboard gives morning overview without asking around the shop
- Customer spend and order history builds business intelligence
- Role-based access: counter staff, designers, operators, managers, admin
- Real data from real postcard printing -- not fake demos

## Demo Credentials (Keycloak)
| User | Password | Role | Access |
|------|----------|------|--------|
| famousguy | helix_pass | isotto-admin + all | Full access |
| giulia_f | helix_pass | isotto-counter | Orders + customers only |
| luca_p | helix_pass | isotto-operator | Production + quality |
| marco_d | helix_pass | isotto-designer + counter | Design + counter |
| angel | helix_pass | isotto-admin + all | System admin |
