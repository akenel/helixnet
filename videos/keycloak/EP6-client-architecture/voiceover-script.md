# EP6 - Client Architecture -- Voiceover Script

## Scene 1: Login
- "Welcome back to the HelixNet Keycloak series."
- "Episode 6 -- Client Architecture."
- "Last episode we covered RBAC -- five roles, four users, role accumulation."
- "Today we look at the other side: how applications connect to Keycloak."
- "Three clients, three different OIDC patterns, one realm."

## Scene 2: Clients List (MONEY SHOT)
- "Here's our POS realm clients list. Nine total, but three are ours."
- "helix_pos_web -- the browser-based POS terminal."
- "helix_pos_mobile -- the tablet and smartphone app."
- "helix_pos_service -- the backend service account."
- "Notice each client has an emoji name and a clear description."

## Scene 3: helix_pos_web -- Settings
- "Starting with the web client. This is a public client -- no client secret."
- "Why public? Because JavaScript running in a browser can't keep secrets."
- "Look at the redirect URIs. Seven different URLs for different environments."
- "pos.blowup-littau.local, pos.artemis-store.local, localhost:3000."
- "Each POS deployment gets its own redirect URI."

## Scene 4: helix_pos_web -- Client Scopes
- "The web client has eight scopes. The most comprehensive of the three."
- "Default scopes: email, profile, roles, web-origins -- always included in the token."
- "Optional scopes: address, phone, offline_access -- requested on demand."
- "The dedicated scope holds custom mappers for this specific client."

## Scene 5: helix_pos_mobile -- Settings
- "Now the mobile client. Also public -- same reason, the app binary can be decompiled."
- "Key difference: look at the redirect URI. helixpos://oauth/callback."
- "That's a custom URL scheme. When Keycloak finishes auth, it sends the user back to the app."
- "Not a web URL, an app URL. This is how native OAuth works."

## Scene 6: helix_pos_mobile -- Client Scopes
- "The mobile client is leaner. Six scopes instead of eight."
- "No address, no phone -- a mobile POS doesn't need those claims."
- "Principle of least privilege applies to scopes too, not just roles."

## Scene 7: helix_pos_service -- Settings (CONFIDENTIAL)
- "And now the big one. helix_pos_service."
- "Notice the difference immediately: Client authentication is ON."
- "This is a confidential client. It has a secret."
- "Why? Because this runs on the backend. Server-side code CAN keep secrets."
- "This is machine-to-machine authentication."

## Scene 8: helix_pos_service -- Credentials (MONEY SHOT)
- "The Credentials tab. This is where it gets real."
- "Client ID and Client Secret. This is how the backend proves its identity."
- "The secret is masked by default. The Regenerate button rotates it."
- "In production, this secret goes into environment variables, never source code."
- "This is the handshake between your backend and Keycloak."

## Scene 9: helix_pos_service -- Service Account Roles
- "Service account roles. The service client gets its own virtual user."
- "service-account-helix_pos_service -- that's the identity."
- "This user can be assigned roles just like a human user."
- "Right now it has the default realm roles. In production, you'd assign specific permissions."

## Scene 10: helix_pos_service -- Client Scopes
- "And the service client's scopes. Only five."
- "The leanest of the three. No offline_access -- services don't need refresh tokens the same way."
- "Machine-to-machine: authenticate, get token, use it, done."

## Scene 11: Realm Client Scopes
- "Zooming out. These are the realm-level client scopes."
- "Ten scopes total, shared across all clients."
- "Nine OpenID Connect, one SAML for legacy systems."
- "Default scopes are included automatically. Optional scopes must be requested."
- "This is the menu. Each client picks what it needs."

## Scene 12: Final Shot -- Clients List
- "Back to the clients list. Three clients, three patterns."
- "Web: public, browser-based, many redirect URIs."
- "Mobile: public, native app, custom scheme callback."
- "Service: confidential, client secret, machine-to-machine."
- "One realm handles all three. That's the power of OIDC."
- "Next episode: authentication flows -- how the actual login process works."

## Key Messages
- Public vs Confidential clients (browser/app can't keep secrets, servers can)
- Redirect URIs matter (web URLs vs custom schemes for native apps)
- Client scopes control what goes into the JWT (least privilege for scopes)
- Service accounts are virtual users for backend authentication
- Client secrets belong in environment variables, never source code
- One realm, multiple client patterns -- that's real OIDC architecture
