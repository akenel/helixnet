✅ Pre-Swagger Testing Developer Checklist (V1.1.0 Security Verification)

The user seeding process is clean. Before diving into endpoint testing via Swagger, use this checklist to ensure the API environment is stable and ready for feature development.
Phase 1: Environment Stability & Core Services

    x

     Verify All Users Exist: Run make show-users to confirm all 7 test accounts (admin, demo, chuck, marcel, etc.) are present and properly configured in the database. (Confirmed by startup logs)

     Check Token Expiry: Confirm the access token expiry (15 minutes) is correct in the HelixNet Config Matrix log (for helix-web-app).

     Check Database Tables: Run make show-tables to ensure all expected tables (users, jobs, task_results, artifacts, refresh_tokens, etc.) are present.

     Run Unit Tests (Smoke Test): Run the basic unit test suite to ensure no fundamental breakage after the last rebuild:

    make test-unit


     Run Authentication Tests: Ensure the basic login/token exchange mechanism is functional before hitting Swagger (use the updated make test-auth if available, or proceed to Swagger):

    make test-auth


Phase 2: API Readiness (Testing the New Refresh Token Flow)

     Access Swagger UI: Navigate to http://localhost/docs and confirm the documentation page loads correctly.

     Execute Login Endpoint (/api/v1/auth/login):

         Successfully log in with the admin@helix.net user credentials.

         Verify the response returns a valid Access Token and a Refresh Token. (Save the Refresh Token!)

     Test Token Refresh Endpoint (/api/v1/auth/token/refresh):

         Use the saved Refresh Token in a POST request to this endpoint.

         Verify the response returns a brand new Access Token and a brand new Refresh Token.

         Crucial Security Check: Attempt to immediately re-use the original Refresh Token; the API must reject it (HTTP 401/400) because of the One-Time Use policy.

     Test Protected Endpoint: Use the newly acquired Access Token to authorize and call a simple protected endpoint (e.g., /api/v1/users/me) to confirm authorization still works.

Next Step: Once this entire checklist is complete and the refresh flow is confirmed secure, we lock down V1.1.0 and move directly to MinIO and the LLM integration. Good work, team!