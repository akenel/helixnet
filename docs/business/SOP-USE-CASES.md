# SOP-as-Program Use Cases

*Applications for the Context Engineering methodology*

**Date:** January 31, 2026
**Companion doc:** `SOPs-ARE-PROGRAMS.md` / `SOPs-ARE-PROGRAMS.html`

---

## The Common Pattern

Every use case follows the same formula:

```
Intake checklist → Structured context → Template → Tool → Verification → Ship
```

The only things that change are the templates and the domain knowledge. The pipeline is identical.

---

## Tier 1: Ready Now

We have the skills, tools, and presence in Trapani to execute these immediately.

### 1. Small Business Marketing Kits
**What:** Walk into any business with a full kit: tent card, menu, Google review, social media posts, business card -- all generated from one intake checklist. One visit, one SOP, complete brand package.

| Element | Detail |
|---------|--------|
| SOP | Client intake checklist → templates → Puppeteer → print |
| Tool | Puppeteer + ISOTTO printing |
| Revenue | 50-200 EUR per business |
| Proof | Camper & Tour, Color Clean, Mixology -- already in pipeline |

### 2. Hotel Operations Consulting
**What:** 10 hotel SOPs (ISO 9001 aligned) already written. Any hotel in Sicily running on chaos could use these. The SOP documents ARE the product. Hand them a binder, train the staff, done.

| Element | Detail |
|---------|--------|
| SOP | Hotel SOP Master → customize per property → PDF package |
| Tool | Puppeteer with headers/footers/page numbers (sop-to-pdf.js) |
| Revenue | 500-2000 EUR per hotel |
| Proof | PuntaTipa prototype (Dualism card), 10 SOPs written |

### 3. SAP Integration Documentation
**What:** Angel's wheelhouse. Companies pay consultants $200/hr to document integration mappings. Generate structured mapping docs from a YAML context file. Start with documentation, not code.

| Element | Detail |
|---------|--------|
| SOP | YAML context + JSON schema → mapping doc → human review |
| Tool | Claude + templates + git version control |
| Revenue | Project-based, 5K-50K EUR |
| Proof | HelixNet middleware vision documented, postcard pipeline proves the pattern |

### 4. Real Estate Listings (Sicily)
**What:** Every property listing needs: photos processed, bilingual description (IT/EN/DE), floor plan notes, Google Maps embed, PDF brochure. One intake form, one SOP, consistent output.

| Element | Detail |
|---------|--------|
| SOP | Property checklist → photo processing → bilingual listing → PDF |
| Tool | Puppeteer + image pipeline |
| Revenue | 50-100 EUR per listing, volume play with agencies |
| Proof | Same pipeline as postcards -- photos + context + template = output |

---

## Tier 2: Near-Term

Need one more piece (template, relationship, or domain knowledge) to execute.

### 5. Restaurant Menu Design
**What:** Same pattern as postcards. Photo of dishes + business info → bilingual menu (IT/EN for tourists) → print-ready PDF. Every restaurant in a tourist town needs this. Trapani has hundreds.

| Element | Detail |
|---------|--------|
| SOP | Menu intake → template → Puppeteer → print at ISOTTO |
| Tool | Puppeteer + ISOTTO |
| Revenue | 100-300 EUR per menu |
| Next step | Build one menu template, pitch to a restaurant we already know |

### 6. Airbnb / Booking.com Listing Optimization
**What:** Hosts write terrible descriptions. One intake form: property details, amenities, photos, neighborhood highlights → optimized listing in 3 languages (IT/EN/DE) + house rules PDF + welcome guide.

| Element | Detail |
|---------|--------|
| SOP | Property intake → listing template → 3 language versions → guest welcome PDF |
| Tool | Claude (multilingual) + Puppeteer |
| Revenue | 100-200 EUR per property, recurring for updates |
| Next step | Build intake form + listing template, pitch to PuntaTipa or local hosts |

### 7. Event Programs & Wedding Packages
**What:** Sicily is a wedding destination. Programs, seating charts, menus, bilingual ceremony guides -- all from one intake form. Same pipeline, different templates.

| Element | Detail |
|---------|--------|
| SOP | Event intake → template selection → bilingual output → print |
| Tool | Puppeteer + ISOTTO (programs, menus, place cards) |
| Revenue | 200-500 EUR per event |
| Next step | Build one wedding program template, connect with a wedding planner |

### 8. Compliance Documentation for Small Businesses
**What:** HACCP for restaurants, safety SOPs for workshops, GDPR privacy policies. Small businesses in Italy need these but can't afford consultants. Template-based, customized per business.

| Element | Detail |
|---------|--------|
| SOP | Business type → regulatory template → customize → PDF package |
| Tool | Puppeteer with sop-to-pdf.js (headers, footers, TOC, page numbers) |
| Revenue | 200-500 EUR per business |
| Next step | Research Italian HACCP requirements, build one restaurant compliance pack |

---

## Tier 3: The Big Play

### 9. SOP-as-a-Service Platform
**What:** Package the whole methodology. A business owner fills out a web form (like our intake checklist). The system generates their complete SOP package: operations manual, marketing materials, compliance docs. HelixNet becomes the platform that runs it.

| Element | Detail |
|---------|--------|
| SOP | The SOP that generates SOPs |
| Tool | HelixNet (FastAPI + Keycloak) + Claude API + Puppeteer |
| Revenue | SaaS model, 50-200 EUR/month per business |
| Next step | Prove all Tier 1 + Tier 2 use cases manually first, then automate |

### 10. Training Other "Guys with Laptops"
**What:** Teach the methodology. Sell the templates. License the pipeline. Other freelancers in other tourist towns do what Angel does in Trapani. Franchise the SOP framework, not the postcards.

| Element | Detail |
|---------|--------|
| SOP | The course IS an SOP for building SOPs |
| Tool | Video + documentation + template pack + CLAUDE.md starter kit |
| Revenue | Course + template license, 500-1000 EUR per person |
| Next step | Document everything (already doing this), package it for handoff |

---

## Priority Matrix

| Use Case | Revenue | Effort | Ready? | Score |
|----------|---------|--------|--------|-------|
| 1. Marketing Kits | Medium | Low | NOW | HIGH |
| 5. Restaurant Menus | Medium | Low | Near | HIGH |
| 2. Hotel Consulting | High | Medium | NOW | HIGH |
| 6. Airbnb Listings | Medium | Low | Near | MEDIUM |
| 4. Real Estate | Medium | Medium | NOW | MEDIUM |
| 8. Compliance Docs | Medium | Medium | Near | MEDIUM |
| 3. SAP Integration | High | High | NOW | MEDIUM |
| 7. Event Programs | Medium | Medium | Near | MEDIUM |
| 9. SaaS Platform | Very High | Very High | Later | LONG-TERM |
| 10. Training/Franchise | High | High | Later | LONG-TERM |

---

## Closest to Money Right Now

1. **Marketing Kits (#1)** -- already walking into businesses, already have templates, already have ISOTTO
2. **Restaurant Menus (#5)** -- add menus to the postcard pitch, double the offering without building anything new
3. **Hotel Consulting (#2)** -- 10 SOPs already written, just need the first paying client

---

*"The only things that change are the templates and the domain knowledge. The pipeline is identical."*
*"Intake checklist → Structured context → Template → Tool → Verification → Ship"*
