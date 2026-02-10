# EP4 - Keys to the Kingdom -- Voiceover Script

**Video:** KC-EP4-Keys-to-the-Kingdom.mp4 (2:22)
**Style:** Casual, confident, walking someone through YOUR system

---

## Scene-by-Scene Talking Points

### 0:00-0:10 -- Chrome Opens + Loading
> "This is Keycloak -- the identity and access management layer that runs our entire platform. Every user, every role, every permission flows through here."

### 0:10-0:20 -- Login Page
> "Standard OIDC login. Username, password, JWT token back. This is the admin console -- the master control panel."

### 0:20-0:35 -- Master Dashboard
> "We're in the master realm now. This is the god view -- you can see everything from here. Server info shows us Keycloak 24 running on Java 17."

### 0:35-0:55 -- REALM DROPDOWN (Money Shot)
> "And here's the magic -- one Keycloak instance, SIX business realms. Each business gets its own realm with its own users, roles, and clients. 420 Wholesale, Artemis Headshop in Luzern, BlowUp in Littau -- each one completely isolated."

### 0:55-1:10 -- POS Users List
> "Let's look inside the POS realm. Nine users, each with specific roles. Pam is a cashier, Ralph is a manager, Michael is a developer. The system knows exactly what each person can do."

### 1:10-1:25 -- User Detail + Role Mapping
> "Aleena here has two roles -- pos-cashier and pos-manager. The cashier role lets her process transactions with up to 10% discount. The manager role gives her full product management and reporting. This is real RBAC -- role-based access control."

### 1:25-1:40 -- Clients
> "Three custom clients: the mobile app, the service account for backend operations, and the web application for POS terminals. Each one has its own OAuth2 configuration, its own scopes, its own permissions."

### 1:40-2:00 -- Realm Tour (420, Artemis, BlowUp)
> "Quick tour of the other businesses -- each one gets the same treatment. Their own realm, their own identity. When we onboard a new client, we spin up a realm, configure their roles, and they're live. This is what makes HelixNet a real multi-tenant platform."

### 2:00-2:22 -- Final Dropdown + Close
> "Back to master. Six realms, one platform. This is the foundation that everything else builds on. SAP charges six figures for this. We built it with open source."

---

## Key Messages to Hit

1. **Multi-tenant isolation** -- each business gets its own realm
2. **Real RBAC** -- not fake roles, actual permission boundaries
3. **Three clients per realm** -- mobile, service, web (proper architecture)
4. **SAP killer** -- same capability, fraction of the cost
5. **One instance, many businesses** -- that's the money shot

---

*Record voiceover separately, mix in post. Keep it under 2:30 total.*
