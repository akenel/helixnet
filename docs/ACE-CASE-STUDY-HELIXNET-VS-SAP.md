# ACE CASE STUDY: HelixNet
## Open Source ERP vs. Traditional Enterprise Software
### A Comparative Analysis for Swiss SME Digital Transformation

---

**Document Classification:** Business Case Study
**Version:** 1.0
**Date:** December 2025
**Authors:** HelixNet Foundation

---

## Executive Summary

This case study examines the implementation of HelixNet, an open-source ERP solution, against the traditional SAP/Big Four consulting model for a Swiss SME with CHF 10M+ annual revenue and 40+ employees.

**Key Findings:**

| Metric | HelixNet (OSS) | SAP + Big Four |
|--------|----------------|----------------|
| 5-Year TCO | CHF 150,000 | CHF 722,000+ |
| Time to Value | 90 days | 12-18 months |
| Ownership | Full | Licensed |
| Vendor Lock-in | None | Significant |
| Internal Capability Built | Yes | No |

**Verdict:** For SMEs seeking agility, cost control, and ownership, the OSS approach delivers 5x better ROI with acceptable risk when properly managed.

---

## 1. Background

### 1.1 The Traditional Path

Swiss SMEs face a common challenge: outgrowing spreadsheets but being too small for enterprise solutions. The default response from consultants:

```
"You need SAP."
"You need a Big Four implementation partner."
"Budget CHF 500,000 minimum."
"Plan for 18 months."
```

This advice has remained unchanged since 1998.

### 1.2 The Hidden Costs of "Enterprise Grade"

What the sales pitch excludes:

| Line Item | Quoted | Actual |
|-----------|--------|--------|
| Implementation | CHF 150K | CHF 220K (47% overrun avg) |
| Customization | "Included" | CHF 75K (never included) |
| Integration | "Simple" | CHF 50K+ per connector |
| Training | CHF 30K | CHF 60K (retraining after changes) |
| Change Requests | "Reasonable" | CHF 1,500/hour |
| Annual Maintenance | 18% | 22% (always increases) |
| Exit Cost | "N/A" | CHF 200K+ (data migration) |

**Industry data:** 50% of SAP implementations exceed budget. 35% exceed timeline. 20% are classified as failures. (Source: Panorama Consulting, 2024)

---

## 2. The HelixNet Approach

### 2.1 Philosophy: YAGNI + KISS

HelixNet applies two engineering principles:

- **YAGNI** (You Ain't Gonna Need It) — Build only what's needed today
- **KISS** (Keep It Simple, Stupid) — Complexity is the enemy

This contrasts with enterprise software that ships 10,000 features when you need 50.

### 2.2 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    HELIXNET STACK                       │
├─────────────────────────────────────────────────────────┤
│  PRESENTATION    │ FastAPI + Jinja2 + HTMX             │
│  AUTHENTICATION  │ Keycloak (OSS, Swiss-hosted)        │
│  BUSINESS LOGIC  │ Python + Pydantic Schemas           │
│  DATA LAYER      │ PostgreSQL + SQLAlchemy             │
│  TASK QUEUE      │ Celery + Redis                      │
│  CONTAINER       │ Docker + Traefik                    │
│  MONITORING      │ Dozzle + Health Checks              │
└─────────────────────────────────────────────────────────┘
```

**All components:** Open source. No license fees. Ever.

### 2.3 Current Metrics

| Component | Count |
|-----------|-------|
| Python Files | 142 |
| Lines of Code | 36,521 |
| Data Schemas | 24 |
| API Routes | 12 |
| Database Models | 15+ |
| Test Coverage | Growing |

### 2.4 Modules Delivered

| Module | Status | SAP Equivalent |
|--------|--------|----------------|
| POS (Point of Sale) | Production | SAP Retail |
| Inventory Management | Production | SAP MM |
| Customer Management | Production | SAP CRM |
| Order Processing | Production | SAP SD |
| E2E Track & Trace | Production | SAP GTS |
| Equipment/Asset Mgmt | Production | SAP PM |
| HR Core | Schema Ready | SAP HCM |
| Supply Chain | Schema Ready | SAP SCM |
| Farm-to-Locker | Schema Ready | N/A (Custom) |

---

## 3. Total Cost of Ownership Analysis

### 3.1 HelixNet TCO (5 Years)

| Year | Development | Hosting | Support | Total |
|------|-------------|---------|---------|-------|
| 1 | CHF 40,000 | CHF 6,000 | CHF 5,000 | CHF 51,000 |
| 2 | CHF 20,000 | CHF 6,000 | CHF 5,000 | CHF 31,000 |
| 3 | CHF 15,000 | CHF 6,000 | CHF 5,000 | CHF 26,000 |
| 4 | CHF 10,000 | CHF 6,000 | CHF 5,000 | CHF 21,000 |
| 5 | CHF 10,000 | CHF 6,000 | CHF 5,000 | CHF 21,000 |
| **TOTAL** | **CHF 95,000** | **CHF 30,000** | **CHF 25,000** | **CHF 150,000** |

**Notes:**
- Development costs decrease as system matures
- Hosting on Swiss VPS (Infomaniak/Exoscale)
- Support includes AI-assisted maintenance (Claude Code)

### 3.2 SAP + Big Four TCO (5 Years)

| Year | License | Consulting | Hosting | Maint. | Total |
|------|---------|------------|---------|--------|-------|
| 1 | CHF 45K | CHF 200K | CHF 18K | CHF 25K | CHF 288K |
| 2 | - | CHF 75K | CHF 18K | CHF 25K | CHF 118K |
| 3 | - | CHF 25K | CHF 18K | CHF 30K | CHF 73K |
| 4 | - | CHF 25K | CHF 18K | CHF 30K | CHF 73K |
| 5 | - | CHF 30K | CHF 20K | CHF 35K | CHF 85K |
| **TOTAL** | **CHF 45K** | **CHF 355K** | **CHF 92K** | **CHF 145K** | **CHF 637K** |

*Add 15% contingency: **CHF 732,000***

### 3.3 Cost Differential

```
SAP Path:      CHF 732,000
HelixNet:      CHF 150,000
─────────────────────────────
SAVINGS:       CHF 582,000 (79% reduction)
```

**What CHF 582,000 buys:**
- 3 years of a full-time senior developer
- Complete ISO 9001 certification
- Hardware refresh for entire company
- Or: A very nice sailboat for Mosey

---

## 4. Risk Analysis

### 4.1 HelixNet Risks (and Mitigations)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Key developer leaves | Medium | High | Documentation, code handoff, AI-assisted maintenance |
| Security vulnerability | Medium | High | Regular audits, community patches, Swiss hosting |
| Scaling limits | Low | Medium | Architecture supports horizontal scaling |
| No vendor support | Certain | Low | Community + AI + documented procedures |
| Integration gaps | Medium | Medium | API-first design, custom connectors |

### 4.2 SAP Risks (often ignored)

| Risk | Probability | Impact | Notes |
|------|-------------|--------|-------|
| Budget overrun | High (50%) | High | Industry standard |
| Timeline overrun | High (35%) | Medium | "Go-live" vs "working" |
| Consultant dependency | Certain | High | Can't change a field without them |
| Version upgrade forced | High | High | SAP roadmap, not yours |
| License true-up audit | Medium | High | Surprise bills |
| Vendor price increase | Certain | Medium | Annual increases locked in |

### 4.3 Risk-Adjusted Analysis

**If HelixNet fails completely:**
- Lost investment: CHF 50,000
- Recovery time: 3 months (migrate to SAP)
- Total damage: CHF 50,000

**If SAP implementation fails:**
- Lost investment: CHF 300,000+
- Recovery time: 12+ months
- Political damage: Significant
- Total damage: CHF 400,000+

**Asymmetric risk:** HelixNet failure is recoverable. SAP failure is catastrophic.

---

## 5. Strategic Considerations

### 5.1 Capability Building

| Factor | HelixNet | SAP |
|--------|----------|-----|
| Internal team learns | Yes | No |
| Knowledge stays in-house | Yes | No |
| Can modify without vendor | Yes | No |
| Training new staff | Simple | Complex |
| Documentation owned | Yes | Licensed |

**Long-term impact:** HelixNet builds organizational capability. SAP builds vendor dependency.

### 5.2 Agility Comparison

| Scenario | HelixNet | SAP |
|----------|----------|-----|
| Add new field to form | 30 minutes | Change request + CHF 1,500 |
| New report | 2 hours | 2 weeks + CHF 5,000 |
| Integration with new supplier | 1-2 days | 4-6 weeks + CHF 15,000 |
| Regulatory change | Same day | Quarterly release cycle |
| Business pivot | Immediate | "Let's discuss scope" |

### 5.3 Exit Strategy

**From HelixNet:**
- Export all data (you own it)
- Documentation available
- Code is yours
- Time: Days

**From SAP:**
- Data export: Complex, often incomplete
- Proprietary formats
- License termination fees
- Time: Months
- Cost: CHF 50,000+ minimum

---

## 6. The AI Factor

### 6.1 How HelixNet Leverages AI

```
┌─────────────────────────────────────────────────────────┐
│                 AI-ASSISTED DEVELOPMENT                 │
├─────────────────────────────────────────────────────────┤
│  Claude Code    │ Real-time coding assistant           │
│  Documentation  │ AI-generated, human-reviewed         │
│  Testing        │ AI-suggested test cases              │
│  Debugging      │ AI-assisted root cause analysis      │
│  Maintenance    │ AI can read and modify codebase      │
└─────────────────────────────────────────────────────────┘
```

**Key insight:** AI doesn't replace developers but reduces the "bus factor" risk. Any competent developer + Claude Code can maintain HelixNet.

### 6.2 SAP and AI

SAP offers "SAP Joule" — an AI assistant locked to SAP's ecosystem, requiring additional licensing, and limited to SAP-approved operations.

**The difference:** HelixNet + AI = Full access. SAP + AI = Guided tour.

---

## 7. Implementation Approach

### 7.1 HelixNet Methodology: BLQ

The BLQ (Bruce Lee Quotient) methodology:

```
1. BUILD    │ Working software in weeks, not months
2. LEARN    │ Real user feedback immediately
3. QUALITY  │ Fix what matters, ignore what doesn't
```

**Compared to traditional:**
```
TRADITIONAL:
1. Requirements (3 months)
2. Design (2 months)
3. Build (6 months)
4. Test (2 months)
5. Deploy (1 month)
6. Discover it doesn't work (ongoing)
```

### 7.2 Proof Points

| Deliverable | HelixNet Time | Traditional Estimate |
|-------------|---------------|----------------------|
| POS System | 6 weeks | 4-6 months |
| Keycloak Auth | 2 weeks | 6-8 weeks |
| CSV Integration | 3 days | 3-4 weeks |
| E2E Tracking | 2 weeks | 8-12 weeks |
| Health Dashboard | 1 week | 4-6 weeks |

---

## 8. Who Should Choose What

### 8.1 Choose HelixNet If:

- Revenue under CHF 50M
- Team willing to learn
- Agility is competitive advantage
- Budget is constrained
- Want to own your future
- Have or can hire technical talent
- Value simplicity over features

### 8.2 Choose SAP If:

- Revenue over CHF 100M
- Planning acquisition/exit (investors expect it)
- No internal technical capability desired
- Budget is not a constraint
- Industry requires it (pharma, banking)
- Global multi-subsidiary operations
- Need to "blame the vendor"

### 8.3 The Hybrid Path

Many organizations succeed with:

```
CORE OPERATIONS     → HelixNet (owned, agile)
FINANCIALS          → Swiss accounting package (certified)
COMPLIANCE          → Purpose-built tools
INTEGRATION         → API layer connecting all
```

This avoids the "one vendor to rule them all" trap.

---

## 9. Conclusion

### 9.1 The Numbers Don't Lie

| Metric | HelixNet | SAP |
|--------|----------|-----|
| 5-Year Cost | CHF 150K | CHF 732K |
| Time to Value | 90 days | 12-18 months |
| Flexibility | High | Low |
| Exit Cost | Minimal | Significant |
| Risk if Fails | CHF 50K | CHF 300K+ |

### 9.2 The Real Question

> "Do you want to rent software from a vendor, or own software built for your business?"

Both paths work. But they lead to different places.

**SAP path:** You become a customer. Forever.

**HelixNet path:** You become capable. Forever.

---

## 10. Appendices

### Appendix A: HelixNet Module List

```
src/schemas/
├── auth.py                    # Authentication/Authorization
├── customer_schema.py         # Customer Management
├── e2e_track_trace_schema.py  # End-to-End Tracking
├── equipment_supply_chain_schema.py  # Asset Management
├── farm_to_locker_schema.py   # Supply Chain (Custom)
├── hr_schema.py               # Human Resources
├── inventory_schema.py        # Inventory Control
├── job_schema.py              # Job/Task Management
├── pos_schema.py              # Point of Sale
├── salad_bar_ecosystem_schema.py     # F&B Operations
├── tiger_byte_schema.py       # Quick Service
├── worker_lunchbox_schema.py  # Meal Programs
└── [12 more specialized schemas]
```

### Appendix B: Technology Stack Details

| Layer | Technology | License | Swiss Hosting |
|-------|------------|---------|---------------|
| Language | Python 3.11 | PSF | N/A |
| Framework | FastAPI | MIT | N/A |
| Database | PostgreSQL | PostgreSQL | Exoscale |
| Auth | Keycloak | Apache 2.0 | Self-hosted |
| Queue | Redis + Celery | BSD | Self-hosted |
| Container | Docker | Apache 2.0 | Self-hosted |
| Proxy | Traefik | MIT | Self-hosted |
| AI Assist | Claude Code | Commercial | API |

### Appendix C: Glossary

| Term | Definition |
|------|------------|
| ACE | Accelerated Capability Enablement |
| BLQ | Bruce Lee Quotient (methodology) |
| KISS | Keep It Simple, Stupid |
| OSS | Open Source Software |
| TCO | Total Cost of Ownership |
| YAGNI | You Ain't Gonna Need It |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2025 | HelixNet Team + Claude | Initial release |

---

*"Simplicity is the ultimate sophistication."* — Leonardo da Vinci

*"Be water, my friend."* — Bruce Lee

---

**END OF DOCUMENT**
