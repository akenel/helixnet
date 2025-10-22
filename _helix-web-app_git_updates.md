git add -A

git commit -m "🔐️ FEAT: Implement Keycloak OIDC for full application authentication.

This major change integrates Keycloak as the single source of truth for user authentication and authorization across the application. Automated the helix json REALM upload and install.

Key KC_ KeyCloak Changes:
👉️ Replaced custom JWT logic with OIDC standard flow.
🦄️ Added `keycloak_auth_service` and `keycloak_proxy_service`.
🫰️ Updated core security, configuration, and user models.
🔑 Requesting Admin Token from: http://keycloak:8080/realms/master/protocol/openid-connect/token
👤 Using User: admin (Client: admin-cli)
---------------------------------------------------------
✅ TOKEN ACQUIRED SUCCESSFULLY!
   Realm: master (Auth for bootstrap admin)
   Token Type: Bearer
   Expires In: 60 seconds
🏁️ **QA Proof:** Included `get_admin_token.py` to confirm successful bootstrap connection to Keycloak master realm. Use 'make toke' to test authentication via the terminal"


git tag v1.4.0-keycloak-auth-complete

git push origin main
git push --tags

