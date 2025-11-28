# HelixNet Documentation Library

> Organized knowledge base for HelixNet POS platform development and operations.

## Directory Structure

```
docs/
├── api/                    # API specifications and testing guides
├── architecture/           # System design, components, workflows
├── business/               # Business rules, pricing, strategy
├── compliance/             # Swiss VAT, CBD regulations, age verification
├── demos/                  # Demo scripts and presentation materials
├── keycloak/               # Identity provider setup and realm configs
├── legacy/                 # Archived docs, old scripts, reference material
├── CHANGELOG.md            # Sprint history and release notes
└── README.md               # This file
```

## Quick Links by Role

### For New Developers
1. [POS System Overview](architecture/POS_SYSTEM.md) - Start here
2. [Race Conditions Analysis](architecture/race-conditions-startup-analysis.md) - Critical startup order
3. [Dev Container Setup](architecture/dev-container-setup-instructions.md)
4. [API Specification](api/helixnet-openapi.json)

### For Business/Operations
1. [Out-of-the-Box Rules](business/helixnet-out-of-the-box-rules.md) - Pricing tiers, gamification
2. [Product Catalog](business/artemis-product-catalog.md) - Felix's Artemis store products
3. [Cutover Strategy](business/preference-cutover-strategy.md)
4. [Todo List](business/toDo-List.md) - DR/Backup strategy

### For Demos
1. [5-Scene Demo Script](demos/demo-scripts.md) - Quick demo flow
2. [Artemis POS Demo](demos/demo-script-artemis-pos.md) - Full walkthrough

### For DevOps/Security
1. [Keycloak Setup](keycloak/KEYCLOAK_SETUP.md) - Identity provider config
2. [Realm Configs](keycloak/) - UAT and Production realm JSONs
3. [MailHog Workflow](architecture/mailhog-kb-workflow-spec.md) - Email testing

## DebLLM Knowledge Base

The main operational knowledge lives in `debllm/notes/`:

```
debllm/notes/
├── helix-platform/         # POS-specific KBs (Felix's Headshop, errors)
├── redis/                  # Redis connection issues
├── celery/                 # Worker/task issues
├── keycloak/               # Auth issues
└── traefik/                # Routing issues
```

## Contributing

When adding documentation:
1. Place in appropriate category folder
2. Use descriptive filenames (kebab-case)
3. Add frontmatter for KB-style docs
4. Update this README if adding new categories

---

**Last Updated:** 2025-11-28 | **Maintainer:** angel
