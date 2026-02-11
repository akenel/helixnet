# EP8 - Multi-Tenant Platform -- Voiceover Script

## Scene 1: Login
- "Welcome back to the HelixNet Keycloak series."
- "Episode 8 -- Multi-Tenant Platform."
- "We've covered keys, RBAC, clients, and authentication flows."
- "Now we zoom out. Six realms, five businesses, one Keycloak instance."
- "This is multi-tenancy in action."

## Scene 2: Master Realm Dashboard (OPENING SHOT)
- "The master realm. This is the control plane."
- "Every Keycloak instance starts here. Master manages everything."
- "It's the admin realm -- not for end users, not for applications."
- "Think of it as the building manager's office in a multi-tenant building."

## Scene 3: Master Realm Clients (MONEY SHOT)
- "Look at the clients list in master. These are not application clients."
- "artemis-realm, blowup-realm, blowup-v2-realm, fourtwenty-realm."
- "kc-pos-realm-dev-realm, kc-realm-dev-realm."
- "Each tenant realm registers as a client in master. That's how Keycloak manages them."
- "Five business realms, all visible from this one screen."

## Scene 4: HelixPOS Dev -- Users
- "HelixPOS Development. The biggest tenant. Nine users."
- "aleena, andy, felix, leandra, michael, pam, ralph."
- "Plus pos-auditor and pos-developer -- system accounts."
- "Notice the email domains. blowup-littau.local, artemis-store.local."
- "Users from different stores, all in one POS realm."

## Scene 5: HelixPOS Dev -- Roles (MONEY SHOT)
- "The POS realm's roles. Five custom roles with emoji prefixes."
- "Crown for admin. Chart for auditor. Cash for cashier."
- "Wrench for developer. Tie for manager."
- "Plus the Keycloak defaults: offline_access, uma_authorization."
- "This is the RBAC system from Episode 5, now in context."

## Scene 6: HelixNet Dev -- Users
- "HelixNet Development. The main platform realm. Six users."
- "This is where the platform developers and admins live."
- "Separate from POS. Different users, different roles, different purpose."

## Scene 7: HelixNet Dev -- Roles
- "Four emoji roles here. Admin, auditor, developer, guest."
- "Simpler than POS. Different business, different needs."
- "Same Keycloak, completely independent role system."

## Scene 8: 420 Wholesale -- Users
- "420 Wholesale. The Mosey Network. Swiss cannabis wholesale."
- "Four users: chuck from Bern, demo, mosey the Oracle, and a supplier."
- "Email domains: bern-store.ch, 420-network.ch."
- "Completely isolated from the POS realm. No data leaks between tenants."

## Scene 9: 420 Wholesale -- Roles
- "Different industry, different roles."
- "pos-buyer, pos-seller, pos-network-boss."
- "Not admin and cashier. Buyer and seller. The roles match the business."
- "That's the power of realms -- each tenant defines its own language."

## Scene 10: Artemis Headshop -- Users
- "Artemis Headshop. Luzern. Five users."
- "Felix the Owner. Leandra the Designer. Mike the Developer."
- "Pam the Cashier. Ralph the Manager."
- "All with @artemis.ch email addresses."
- "A complete retail team in their own isolated realm."

## Scene 11: BlowUp V2 -- Dashboard (MONEY SHOT)
- "BlowUp V2. And look at this -- custom branding."
- "The BlowUp logo, the welcome page, the dark theme."
- "Each realm can have its own look and feel."
- "Users logging into BlowUp see BlowUp, not Keycloak."
- "That's white-labeling at the identity layer."

## Scene 12: BlowUp V2 -- Users
- "Two users. The smallest tenant."
- "It doesn't matter if you have two users or two thousand."
- "Same isolation. Same security. Same Keycloak."
- "The architecture scales from startup to enterprise."

## Scene 13: Final Shot -- Master Realm
- "Back to master. The control plane."
- "Six realms. Twenty-six users across five businesses."
- "Cannabis wholesale, headshops, POS systems, platform development."
- "All on one Keycloak instance. All completely isolated."
- "One login page per business. One admin console to manage them all."
- "That's multi-tenancy. That's the HelixNet platform."

## Key Messages
- Master realm is the control plane, not for end users
- Each business realm registers as a client in master
- Realms provide complete tenant isolation (users, roles, clients, scopes)
- Different businesses define different roles to match their language
- Custom branding per realm (white-labeling at identity layer)
- Scales from 2 users to thousands per tenant
- One Keycloak instance serves an entire multi-tenant platform
- Episodes 4-8: from login to multi-tenant architecture in 5 episodes
