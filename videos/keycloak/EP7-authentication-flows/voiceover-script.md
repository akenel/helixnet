# EP7 - Authentication Flows -- Voiceover Script

## Scene 1: Login
- "Welcome back to the HelixNet Keycloak series."
- "Episode 7 -- Authentication Flows."
- "Last episode we covered client architecture -- three OIDC patterns."
- "Today we go deeper. How does the actual login process work?"
- "Seven built-in flows, eleven required actions, and security policies."

## Scene 2: Authentication Flows List (OPENING SHOT)
- "Here's the Authentication section. Seven built-in flows."
- "Browser, clients, direct grant, docker auth, first broker login, registration, reset credentials."
- "Each flow is a pipeline of execution steps."
- "Steps can be Required, Alternative, Conditional, or Disabled."
- "All seven are built-in. You can duplicate and customize, but never delete the originals."

## Scene 3: Browser Flow (MONEY SHOT)
- "The browser flow. This is THE login flow. Every interactive login goes through here."
- "First: Cookie -- checks if you already have a session. Alternative, so it can be skipped."
- "Second: Kerberos -- enterprise SSO. Disabled by default."
- "Third: Identity Provider Redirector -- for federated login. Also Alternative."
- "Then the forms sub-flow. This is where it gets interesting."
- "Username Password Form -- Required. This is the actual login prompt."
- "Browser - Conditional OTP. A sub-flow that checks if the user has OTP configured."
- "If they do, they get the OTP prompt. If not, it's skipped."
- "This is the beauty of flows -- conditional logic, not just checkboxes."

## Scene 4: Direct Grant Flow
- "Direct grant. This is the Resource Owner Password Credentials flow."
- "Used by APIs and CLI tools -- no browser, no redirect."
- "Username Validation, then Password, then Conditional OTP."
- "Same security steps as browser, but headless. Machine-to-machine with user credentials."

## Scene 5: Registration Flow
- "The registration flow. What happens when a new user signs up."
- "Registration User Profile Creation -- builds the user object."
- "Password Validation -- enforces the password policy."
- "Recaptcha -- Disabled by default. Enable it to stop bots."
- "Terms and Conditions -- also Disabled. Enable it when you need consent."
- "Notice the pattern: disabled steps are ready to activate, not missing."

## Scene 6: Reset Credentials Flow
- "Reset credentials. The password recovery pipeline."
- "Choose User -- finds the account."
- "Send Reset Email -- delivers the reset link."
- "Reset Password -- the actual change form."
- "Then Conditional OTP again -- even password reset respects MFA."
- "Four steps, each one auditable, each one configurable."

## Scene 7: First Broker Login Flow
- "First broker login. This fires when a user authenticates through an external identity provider for the first time."
- "Review Profile -- verify the imported user data."
- "Create User If Unique -- if no matching account exists, create one."
- "Handle Existing Account -- if the email matches an existing user, link the accounts."
- "This is identity federation. Google login, corporate SAML, social providers -- they all land here."

## Scene 8: Docker Auth Flow
- "Docker auth. The simplest flow in the system."
- "One step: Docker Authenticator. Required."
- "This authenticates docker login commands against Keycloak."
- "Container registries, private repos -- Keycloak handles the auth."
- "One step. One purpose. Clean."

## Scene 9: Clients Flow
- "The clients flow. How client applications authenticate themselves."
- "Client ID and Secret -- the most common method."
- "Signed JWT -- the client signs a token with its private key."
- "Signed JWT with Client Secret -- HMAC-based, simpler but less secure."
- "X509 Certificate -- mutual TLS, the most secure option."
- "All four are Alternative -- Keycloak tries each method until one succeeds."

## Scene 10: Required Actions (MONEY SHOT)
- "Required Actions. These are actions that can be forced on users."
- "Configure OTP -- force users to set up two-factor authentication."
- "Terms and Conditions -- require acceptance before proceeding."
- "Update Password -- force a password change on next login."
- "Update Profile -- make users complete their profile."
- "Verify Email -- email verification on registration."
- "Eleven actions total. Each one has an Enabled toggle and a Default toggle."
- "Enabled means available. Default means every new user gets it automatically."
- "This is how you enforce security policies across all users."

## Scene 11: Policies Tab
- "Policies. Five policy types."
- "Password Policy -- minimum length, complexity, history, expiration."
- "OTP Policy -- algorithm, digits, period, look-ahead window."
- "Webauthn Policy -- hardware security keys, biometrics."
- "Webauthn Passwordless -- FIDO2 passwordless login."
- "CIBA -- Client Initiated Backchannel Authentication."
- "Right now no password policies are configured. In production, you'd set minimum length, special characters, expiration."

## Scene 12: Final Shot -- Flows List
- "Back to the flows list. Seven flows, each one a security pipeline."
- "Browser for interactive login. Direct grant for APIs."
- "Registration for new users. Reset credentials for recovery."
- "First broker for federation. Docker for containers. Clients for service auth."
- "Every step is configurable. Required, Alternative, Conditional, or Disabled."
- "Next episode: multi-tenant platform -- how all six realms work together."

## Key Messages
- Authentication flows are ordered pipelines of execution steps
- Four requirement levels: Required, Alternative, Conditional, Disabled
- Browser flow is the main interactive login (Cookie -> Kerberos -> IdP -> Forms -> OTP)
- Conditional OTP appears in multiple flows (browser, direct grant, reset credentials)
- Required Actions enforce security policies on all users (OTP, Terms, Email verification)
- Disabled steps are ready to activate, not missing -- defense in depth
- Each flow is auditable and configurable without code changes
