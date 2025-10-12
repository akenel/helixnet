✅ Pre-Swagger Testing Developer Checklist

The user seeding process is clean. Before diving into endpoint testing via Swagger, use this checklist to ensure the API environment is stable and ready for feature development.
Phase 1: Environment Stability & Core Services

    [ ] Verify All Users Exist: Run make show-users to confirm all 7 test accounts (admin, demo, chuck, marcel, etc.) are present and properly configured in the database.

    [ ] Check Token Expiry: Confirm the access token expiry (15 minutes) is correct in the HelixNet Config Matrix log (for helix-web-app).

    [ ] Check Database Tables: Run make show-tables to ensure all expected tables (users, jobs, task_results, artifacts, etc.) are present.

    [ ] Run Unit Tests (Smoke Test): Run the basic unit test suite to ensure no fundamental breakage after the last rebuild:

    make test-unit

    [ ] Run Authentication Tests: Ensure the basic login/token exchange mechanism is functional before hitting Swagger:

    make test-auth

Phase 2: API Readiness

    [ ] Access Swagger UI: Navigate to http://localhost/docs and confirm the documentation page loads correctly.

    [ ] Execute Test Endpoint (e.g., /api/v1/auth/login):

        [ ] Successfully log in with the admin@helix.net user credentials.

        [ ] Verify the response returns a valid Access Token and a Refresh Token.

    [ ] Test Protected Endpoint: Use the retrieved Access Token to authorize and call a simple protected endpoint (e.g., /api/v1/users/me) to confirm authorization works.

Next Step: Once the checklist is complete, the team is fully authorized to begin feature development and iterative testing using the Swagger UI. Good work, team!