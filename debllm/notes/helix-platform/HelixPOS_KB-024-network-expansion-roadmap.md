# KB-024: HelixNet Network Expansion Roadmap

**Status:** ACTIVE
**Created:** 2025-11-30
**Author:** Angel (Platform Architect)
**Category:** Strategic - Deployment

---

## Overview

Following the successful Week 1 launch at Artemis Store Zurich and the Saturday demo event, HelixNet is expanding to multiple locations. This KB documents the deployment roadmap and rollout strategy.

## Current State (End of Week 1)

### Artemis Store - Zurich (LIVE)

| Metric | Value |
|--------|-------|
| Status | ✅ Production |
| Go-Live | 2025-11-25 |
| Staff | Felix (Manager), Pam (Cashier), Ralph (Cashier/Inventory) |
| Transactions | 46 |
| Revenue | CHF 4,571.40 |
| Products | 64 (28 base + 35 Sylvie + 10 Cynthia) |
| Vending Machines | 1 (16 products, 4-language) |
| KBs Created | KB-020 through KB-024 |

### Key Achievements
- Artisan integration workflow proven (Sylvie, Cynthia)
- Batch entry: 35 products in < 2 minutes
- Remote management: Felix approved changes from mobile
- Multi-language support: 4 Swiss languages
- Vending machine: Same-day configuration

---

## Expansion Pipeline

### Phase 1: Artemis Littau (January 1, 2026)

**Type:** Second company location

| Detail | Value |
|--------|-------|
| Target Launch | 2026-01-01 |
| Location | Littau, Switzerland |
| Operator | Felix (remote management) |
| Vending | 1 machine (Marco 50/50 deal) |
| Integration | Shared HelixNet instance |

**Marco Vending Deal:**
- Marco provides vending machine FREE
- Revenue split: 50/50 on total sales
- Felix supplies products
- Cost not included in split (Felix absorbs)
- Win-win: Marco gets product variety, Felix gets distribution

**Technical Requirements:**
- [ ] Store entity in multi-store module
- [ ] Separate cash drawer tracking
- [ ] Shared product catalog
- [ ] Location-specific reporting

---

### Phase 2: Chuck's Store - Bern (PoC)

**Type:** Mosey network pilot

| Detail | Value |
|--------|-------|
| Target | December 2025 (PoC meeting Friday) |
| Location | Bern, Switzerland |
| Operator | Chuck (solo) |
| Current System | Paper & Pencil + Excel |
| Vending Machines | 3 (!!) |
| Parent Network | Mosey's 420 Stores |

**Chuck's Profile:**
- Keener - eager technology adopter
- Solo operator - fast decision making
- Schedule: Thu-Sat store, Mon-Wed admin
- Pain point: 1 hour daily for 5-minute tasks
- Creates amazing Excel reports manually

**Discovery Meeting Agenda (Friday):**
1. Happy hour + sample show (Chuck's specialty)
2. Current workflow walkthrough
3. Excel report review
4. 3 vending machine assessment
5. HelixNet demo
6. Paper-to-digital migration plan

**Success Criteria:**
- [ ] Chuck understands batch entry (Ralph's workflow)
- [ ] Vending machine integration plan
- [ ] Data migration from Excel feasible
- [ ] Chuck commits to pilot

---

### Phase 3: Mosey Network Rollout

**Type:** Franchise/network deployment

| Detail | Value |
|--------|-------|
| Network | Mosey's 420 Stores |
| Current System | Magento (main stores) |
| Confirmed Interest | 5 shop owners from demo |
| Additional Interest | 3 more |
| Strategy | Chuck success → network rollout |

**Integration Considerations:**
- Magento used for main stores
- HelixNet for specialty/solo locations
- Potential Magento↔HelixNet bridge
- Centralized reporting across systems

---

## Deployment Checklist Template

### Pre-Deployment
- [ ] Site assessment
- [ ] Network/connectivity check
- [ ] Hardware requirements (terminals, printers, scanners)
- [ ] Vending machine count and specs
- [ ] Current system data export
- [ ] Staff count and roles

### Deployment
- [ ] HelixNet instance configuration
- [ ] User accounts (Keycloak)
- [ ] RBAC role assignment
- [ ] Product catalog setup (batch entry)
- [ ] Vending machine configuration
- [ ] Payment terminal integration
- [ ] Receipt printer setup

### Training
- [ ] Manager dashboard walkthrough
- [ ] Cashier POS training
- [ ] Batch entry training (if applicable)
- [ ] Vending reconciliation process
- [ ] KB documentation review

### Go-Live
- [ ] Parallel run (old + new system)
- [ ] Data verification
- [ ] First transaction test
- [ ] Vending machine test
- [ ] Staff sign-off
- [ ] Go-live decision

### Post-Launch
- [ ] Daily check-ins (Week 1)
- [ ] Issue tracking
- [ ] KB updates based on feedback
- [ ] Performance review (Week 2)
- [ ] Optimization recommendations

---

## December Schedule

| Date | Location | Activity |
|------|----------|----------|
| Dec 1-4 | Zurich | Normal ops, December prep |
| Dec 5 (Fri) | Bern | Chuck meeting (Angel + Mosey) |
| Dec 6-7 | Zurich | Black Friday weekend |
| Dec 8-11 | - | Chuck PoC prep (if approved) |
| Dec 12-14 | Zurich | Black Friday weekend #2 |
| Dec 15-21 | Bern | Chuck deployment (target) |
| Dec 22-31 | Zurich | Holiday operations |

**Note:** Felix unavailable Fridays in December (Black Friday every week)

---

## Contact Directory

| Name | Role | Location | Contact |
|------|------|----------|---------|
| Felix | Store Manager | Zurich | felix@artemis-store.ch |
| Pam | Cashier | Zurich | pam@artemis-store.ch |
| Ralph | Inventory | Zurich | ralph@artemis-store.ch |
| Mosey | Network Owner | 420 Stores | mosey@420stores.ch |
| Chuck | Solo Operator | Bern | TBD |
| Angel | Platform Architect | HelixNet | angel@helixnet.ch |
| Marco | Vending Partner | Littau | TBD |
| Sylvie | Artisan | Zurich | sylvie@ecolution.ch |
| Cynthia | Artisan | Zurich | cynthia@ecolution-cbd.ch |

---

## Success Metrics

### Per-Store Targets (Week 1)

| Metric | Target | Artemis Zurich Actual |
|--------|--------|----------------------|
| Transactions | 30+ | 46 ✅ |
| Revenue | CHF 2,500+ | CHF 4,571 ✅ |
| Products Added | 10+ | 45 ✅ |
| System Uptime | 99%+ | 100% ✅ |
| Staff Adoption | Full | Full ✅ |

### Network Targets (Q1 2026)

| Metric | Target |
|--------|--------|
| Stores Live | 3 (Zurich, Littau, Bern) |
| Total Vending Machines | 5 |
| Network Revenue | CHF 50,000+ |
| Staff Trained | 5+ |
| Mosey Stores Pipeline | 5+ |

---

## The BLQ Philosophy

> "Bruce Lee Quality - Clean, fast, no bloat."
> - Ralph, Artemis Store

This is how we deploy:
- **Clean:** Simple setup, clear documentation
- **Fast:** Hours not weeks, batch not manual
- **No Bloat:** Only what's needed, nothing extra

25 years of the old way.
Week 1 of the new way.

**KB... roger roger.**

---

**Document Status:** ACTIVE
**Last Updated:** 2025-11-30
**Next Review:** After Chuck PoC
