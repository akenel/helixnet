# KB-025: HelixNet Scope & Boundaries - Payroll Integration

**Created**: 2024-11-29 (Black Friday evening, after demo with Felix)
**Author**: Angel (based on Felix feedback)
**Status**: CRITICAL - Defines what HelixNet is NOT

---

## The Conversation

Felix asked: *"Can Helix track employee times? I pay them for every minute they work."*

**Honest Answer**: No. HelixNet is a **POS sales system**, not a time management or payroll system.

---

## Felix's Current Payroll System (Works Great!)

Felix has a master spreadsheet perfected over years:

```
📊 Felix_Payroll_Master.xlsx
├── Tab: Pam
│   ├── AHV Number (Swiss Social Security)
│   ├── IBAN
│   ├── Personal details
│   ├── Monthly hours worked
│   ├── 80% sick day calculations
│   └── Running totals
├── Tab: Ralph
├── Tab: Michael
├── Tab: Leandra (new hire!)
└── Tab: Year Summary → Lohnausweis
```

### Key Features of Felix's System:
- **Minute-level tracking**: Pays for every minute worked
- **Swiss payroll compliance**: 80% sick pay, AHV contributions
- **Year-end ready**: Zeros out in December, preps new year
- **Same-day closeout**: Can generate Lohnausweis immediately
- **Battle-tested**: Years of refinement, column calculations perfected

---

## What HelixNet DOES vs DOESN'T Do

| Function | HelixNet | Felix's Spreadsheet |
|----------|----------|---------------------|
| Product sales | ✅ Yes | ❌ No |
| Transaction history | ✅ Yes | ❌ No |
| Cashier performance (sales) | ✅ Yes | ❌ No |
| Employee hours/minutes | ❌ No | ✅ Yes |
| Payroll calculations | ❌ No | ✅ Yes |
| AHV/IBAN storage | ❌ No | ✅ Yes |
| Lohnausweis generation | ❌ No | ✅ Yes |
| Sick day tracking | ❌ No | ✅ Yes |

---

## Integration Point (Future KB-026?)

The two systems can work together:

```
┌─────────────────┐         ┌──────────────────────┐
│   HelixNet POS  │         │  Felix's Payroll.xlsx │
│                 │         │                      │
│  - Who sold     │ ──────► │  - Hours worked      │
│  - When (login) │         │  - Pay calculations  │
│  - Sales total  │         │  - Lohnausweis       │
└─────────────────┘         └──────────────────────┘
```

**Possible Export**: HelixNet could export "cashier session times" (login→logout) as a starting point, but Felix's detailed minute tracking is beyond scope.

---

## Why This Matters

1. **Don't over-promise**: HelixNet is focused on POS, not HR/payroll
2. **Respect existing tools**: Felix's spreadsheet WORKS and is Swiss-compliant
3. **Integration over replacement**: Better to connect than to compete
4. **BLQ principle**: Keep it simple, don't bloat the system

---

## Action Items

- [ ] Ask Mosey tomorrow how he handles payroll with multiple shops
- [ ] Document Mosey's approach in KB-026
- [ ] Consider: Simple "shift start/end" logging in HelixNet (not payroll)
- [ ] Felix keeps his spreadsheet - it's his competitive advantage!

---

## Felix's Closing Thought

> "Every year over Christmas I prepare the new sheet for the next year and zero out the times... with this spreadsheet I can close out the year the same day."

**Translation**: His system is DONE. Don't try to replace it. Just help it work alongside HelixNet.

---

*Next morning: Meet Mosey, then show at 11am. Bis morgen!*
