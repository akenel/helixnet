# BLQ ISO 9001:2015 Framework
## Quality Management System Foundation for 420 Operations
### Version 1.0 | December 2025

---

## Purpose

This document establishes the ISO 9001:2015 Quality Management System (QMS) framework for 420 operations, built on the existing BLQ (BlowUp Littau) knowledge base structure.

---

## ISO 9001:2015 Requirements Mapped to HelixNet

### Clause 4: Context of the Organization

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 4.1 Understanding the organization | BLQ_KB-001 Vision document | ✅ Done |
| 4.2 Interested parties | Character Bible (stakeholders) | ✅ Done |
| 4.3 Scope of QMS | This document | ✅ Done |
| 4.4 QMS processes | BLQ_KB articles | 🔄 In Progress |

### Clause 5: Leadership

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 5.1 Leadership commitment | Mosey report | ✅ Done |
| 5.2 Quality policy | To be documented | ⏳ Pending |
| 5.3 Roles & responsibilities | Keycloak RBAC | ✅ Done |

### Clause 6: Planning

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 6.1 Risk assessment | Security audit findings | ✅ Done |
| 6.2 Quality objectives | BLQ_KB-001 Success metrics | ✅ Done |
| 6.3 Planning changes | Git version control | ✅ Done |

### Clause 7: Support

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 7.1 Resources | Team capability matrix | ✅ Done |
| 7.2 Competence | Training records | ⏳ Pending |
| 7.3 Awareness | BLQ training scenarios | ✅ Done |
| 7.4 Communication | This documentation | ✅ Done |
| 7.5 Documented information | KB articles + Git | ✅ Done |

### Clause 8: Operation

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 8.1 Operational planning | BLQ_KB-004 Daily SOP | ✅ Done |
| 8.2 Product requirements | Product catalog specs | ✅ Done |
| 8.3 Design & development | N/A (reseller) | N/A |
| 8.4 External providers | FourTwenty supplier integration | ✅ Done |
| 8.5 Production & service | POS transaction system | ✅ Done |
| 8.6 Release of products | Stock management | ✅ Done |
| 8.7 Nonconforming outputs | Returns handling | ⏳ Pending |

### Clause 9: Performance Evaluation

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 9.1 Monitoring & measurement | Health checks, logs | ✅ Done |
| 9.2 Internal audit | Security assessment | ✅ Done |
| 9.3 Management review | Mosey report | ✅ Done |

### Clause 10: Improvement

| Requirement | HelixNet Implementation | Status |
|-------------|------------------------|--------|
| 10.1 General | Continuous improvement plan | 🔄 In Progress |
| 10.2 Nonconformity | Issue tracking (GitHub) | ✅ Done |
| 10.3 Continual improvement | Version releases | ✅ Done |

---

## Quality Policy (Draft)

```
420 Quality Policy

We are committed to:

1. Customer Satisfaction
   - Providing quality products from verified suppliers
   - Fast, accurate order fulfillment
   - Fair pricing with transparent margins

2. Compliance
   - Swiss CBD regulations adherence
   - Age verification for restricted products
   - Proper documentation and traceability

3. Continuous Improvement
   - Regular system updates and security patches
   - Staff training and knowledge sharing
   - Process optimization based on feedback

4. Team Excellence
   - Clear roles and responsibilities
   - Open communication
   - Work-life balance (264/420 culture)

Signed: _________________ Date: _________________
        Mosey, Owner
```

---

## Document Control Matrix

### Document Types

| Code | Type | Owner | Review Cycle |
|------|------|-------|--------------|
| QMS | Quality Management | Senior IT | Annual |
| SOP | Standard Operating Procedure | Operations | 6 months |
| WI | Work Instruction | Department | As needed |
| KB | Knowledge Base | All | Continuous |
| FORM | Forms & Templates | Admin | Annual |

### Existing BLQ Documents → ISO Mapping

| BLQ Document | ISO Clause | Document Type |
|--------------|------------|---------------|
| BLQ_KB-001 Vision | 4.1, 6.2 | QMS |
| BLQ_KB-002 SKU System | 8.5 | SOP |
| BLQ_KB-003 Batch Tracking | 8.5.2 | SOP |
| BLQ_KB-004 Daily Operations | 8.1 | SOP |
| BLQ_KB-016 Labeling Compliance | 8.5.1 | WI |
| BLQ_KB-019 Communication | 7.4 | SOP |
| BLQ_KB-020 Vending Strategy | 8.1 | SOP |
| Characters Bible | 4.2, 7.3 | QMS |

---

## Required SOPs (Priority Order)

### Critical (Month 1-2)

1. **SOP-001: Daily Opening Procedure**
   - System health check
   - Cash drawer verification
   - Stock spot check

2. **SOP-002: Daily Closing Procedure**
   - Transaction reconciliation
   - Daily backup
   - Cash count and deposit

3. **SOP-003: Product Receiving**
   - Delivery verification
   - Stock entry
   - Quality check

4. **SOP-004: Customer Sale Process**
   - Age verification (if required)
   - Transaction processing
   - Receipt generation

### Important (Month 3-4)

5. **SOP-005: Returns & Exchanges**
   - Return policy
   - Defect handling
   - Refund processing

6. **SOP-006: Inventory Management**
   - Cycle counting
   - Stock alerts
   - Reorder process

7. **SOP-007: Supplier Management**
   - FourTwenty sync procedure
   - Price change review
   - New supplier onboarding

### Supporting (Month 5-6)

8. **SOP-008: User Access Management**
   - Keycloak user creation
   - Role assignment
   - Password policy

9. **SOP-009: Backup & Recovery**
   - Daily backup verification
   - Monthly restore test
   - Disaster recovery

10. **SOP-010: Incident Management**
    - System outage response
    - Data breach protocol
    - Escalation matrix

---

## Training Matrix

### Role-Based Training Requirements

| Training | Cashier | Manager | Developer | Admin |
|----------|---------|---------|-----------|-------|
| POS Operations | ✅ | ✅ | ○ | ○ |
| Customer Service | ✅ | ✅ | ○ | ○ |
| Age Verification | ✅ | ✅ | ○ | ○ |
| Inventory Management | ○ | ✅ | ○ | ○ |
| Reporting | ○ | ✅ | ✅ | ✅ |
| User Management | ○ | ○ | ✅ | ✅ |
| System Administration | ○ | ○ | ✅ | ✅ |
| Backup/Recovery | ○ | ○ | ✅ | ✅ |
| Security Awareness | ✅ | ✅ | ✅ | ✅ |
| ISO Awareness | ✅ | ✅ | ✅ | ✅ |

### Training Record Template

```
TRAINING RECORD

Employee: _________________
Date: _________________
Training: _________________
Trainer: _________________
Duration: _________________

Assessment: [ ] Pass [ ] Needs Review

Signature (Employee): _________________
Signature (Trainer): _________________
```

---

## Audit Schedule

### Internal Audits

| Quarter | Focus Area | Auditor |
|---------|------------|---------|
| Q1 | Operations (SOP 1-4) | Manager |
| Q2 | Inventory & Suppliers | Senior IT |
| Q3 | IT Systems & Security | External |
| Q4 | Full QMS Review | Management |

### External Audits

| Year | Type | Estimated Cost |
|------|------|----------------|
| Year 1 | Gap Analysis | CHF 10-15K |
| Year 1 | Pre-certification | CHF 5-10K |
| Year 1-2 | Certification Audit | CHF 15-20K |
| Ongoing | Surveillance (annual) | CHF 5-8K |

---

## Metrics & KPIs

### Operational KPIs

| Metric | Target | Measure |
|--------|--------|---------|
| Daily backup success | 100% | Automated check |
| System uptime | 99.5% | Health monitoring |
| Transaction accuracy | 99.9% | Reconciliation |
| Stock accuracy | 98% | Cycle counts |
| Customer complaints | <1% | Feedback tracking |

### ISO KPIs

| Metric | Target | Measure |
|--------|--------|---------|
| SOP compliance | 95% | Audit findings |
| Training completion | 100% | Training records |
| Document currency | 100% | Review dates |
| Corrective actions closed | 90% in 30 days | Issue tracker |

---

## Next Steps

### Immediate (This Week)
- [ ] Review this framework with Mosey
- [ ] Assign SOP owners
- [ ] Set up training record system

### Short Term (December 2025)
- [ ] Complete SOP-001 through SOP-004
- [ ] Initial staff training on ISO basics
- [ ] Establish audit schedule

### Medium Term (Q1 2026)
- [ ] Complete all 10 SOPs
- [ ] Full training cycle complete
- [ ] Internal audit #1

### Long Term (2026-2027)
- [ ] Gap analysis with ISO consultant
- [ ] System improvements based on gaps
- [ ] Certification audit

---

## Appendix: ISO 9001:2015 Quick Reference

### The 7 Quality Management Principles

1. **Customer Focus** - Meet and exceed customer expectations
2. **Leadership** - Create unity of purpose and direction
3. **Engagement of People** - Competent, empowered people at all levels
4. **Process Approach** - Manage activities as interrelated processes
5. **Improvement** - Ongoing focus on improvement
6. **Evidence-based Decision Making** - Data-driven decisions
7. **Relationship Management** - Manage relationships with interested parties

### PDCA Cycle (Plan-Do-Check-Act)

```
    ┌──────────┐
    │   PLAN   │ → Define objectives, processes
    └────┬─────┘
         │
    ┌────▼─────┐
    │    DO    │ → Implement the plan
    └────┬─────┘
         │
    ┌────▼─────┐
    │  CHECK   │ → Monitor, measure, analyze
    └────┬─────┘
         │
    ┌────▼─────┐
    │   ACT    │ → Take action to improve
    └────┬─────┘
         │
         └──────→ (back to PLAN)
```

---

*This document is version controlled in Git. Last updated: December 2, 2025*

