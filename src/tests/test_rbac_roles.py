# File: src/tests/test_rbac_roles.py
"""
RBAC Role Tests -- The safety net for Keycloak + FastAPI auth.

Tests the role extraction and access control logic that sits between
Keycloak JWTs and FastAPI route protection. No Keycloak needed --
these are pure unit tests against the Python logic.

If the prefix filter in extract_roles() silently drops a role,
or require_roles() stops matching, these tests catch it before
a user gets a mysterious 403 in production.

"If one seal fails, check all the seals."
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient

from src.core.keycloak_auth import extract_roles
from src.main import app
from src.db.database import get_db_session
from src.core.keycloak_auth import verify_token


# ================================================================
# UNIT TESTS: extract_roles()
# ================================================================

class TestExtractRoles:
    """Test the JWT role extraction and prefix filtering."""

    def test_camper_roles_pass_filter(self):
        """All camper-* roles must survive the prefix filter."""
        payload = {
            "realm_access": {
                "roles": [
                    "camper-counter",
                    "camper-mechanic",
                    "camper-manager",
                    "camper-admin",
                    "camper-auditor",
                    "camper-hr",
                    "camper-accountant",
                    "camper-qa-tester",
                ]
            }
        }
        roles = extract_roles(payload)
        assert "camper-counter" in roles
        assert "camper-mechanic" in roles
        assert "camper-manager" in roles
        assert "camper-admin" in roles
        assert "camper-auditor" in roles
        assert "camper-hr" in roles
        assert "camper-accountant" in roles
        assert "camper-qa-tester" in roles
        assert len(roles) == 8

    def test_non_app_roles_filtered_out(self):
        """Roles without a known app prefix must be filtered out."""
        payload = {
            "realm_access": {
                "roles": [
                    "camper-admin",
                    "offline_access",
                    "uma_authorization",
                ]
            }
        }
        roles = extract_roles(payload)
        assert "offline_access" not in roles
        assert "uma_authorization" not in roles
        assert "camper-admin" in roles

    def test_pos_roles_pass_filter(self):
        """POS realm roles must survive the prefix filter."""
        payload = {
            "realm_access": {
                "roles": [
                    "pos-cashier",
                    "pos-manager",
                    "pos-developer",
                    "pos-auditor",
                    "pos-admin",
                ]
            }
        }
        roles = extract_roles(payload)
        assert len(roles) == 5
        assert "pos-cashier" in roles
        assert "pos-admin" in roles

    def test_isotto_roles_pass_filter(self):
        """ISOTTO realm roles must survive the prefix filter."""
        payload = {
            "realm_access": {
                "roles": [
                    "isotto-counter",
                    "isotto-designer",
                    "isotto-operator",
                    "isotto-manager",
                    "isotto-admin",
                ]
            }
        }
        roles = extract_roles(payload)
        assert len(roles) == 5
        assert "isotto-admin" in roles

    def test_qa_tester_role_passes_filter(self):
        """The camper-qa-tester role MUST pass the prefix filter.

        This is the critical test. If someone renames the role to
        'qa-tester' (dropping the camper- prefix), this test catches
        it before Anne gets locked out with a silent 403.
        """
        payload = {
            "realm_access": {
                "roles": ["camper-qa-tester"]
            }
        }
        roles = extract_roles(payload)
        assert "camper-qa-tester" in roles
        assert len(roles) == 1

    def test_bare_qa_tester_role_would_be_filtered(self):
        """A role named 'qa-tester' (no camper- prefix) MUST be filtered out.

        This proves why we named it camper-qa-tester and not qa-tester.
        If this test ever fails, the prefix filter was changed and all
        role naming assumptions need to be re-evaluated.
        """
        payload = {
            "realm_access": {
                "roles": ["qa-tester"]
            }
        }
        roles = extract_roles(payload)
        assert len(roles) == 0

    def test_empty_realm_access(self):
        """No realm_access in token should return empty list."""
        assert extract_roles({}) == []
        assert extract_roles({"realm_access": {}}) == []
        assert extract_roles({"realm_access": {"roles": []}}) == []

    def test_emoji_prefixed_roles(self):
        """Emoji-prefixed POS roles must pass the filter."""
        payload = {
            "realm_access": {
                "roles": [
                    "\U0001f4b0\ufe0f pos-cashier",
                    "\U0001f454\ufe0f pos-manager",
                    "\U0001f451\ufe0f pos-admin",
                ]
            }
        }
        roles = extract_roles(payload)
        assert len(roles) == 3

    def test_unknown_prefix_filtered(self):
        """Roles without a known prefix must be filtered out."""
        payload = {
            "realm_access": {
                "roles": [
                    "admin",
                    "user",
                    "mystery-role",
                    "test-role",
                ]
            }
        }
        roles = extract_roles(payload)
        assert len(roles) == 0


# ================================================================
# INTEGRATION TESTS: QA dashboard route access
# ================================================================

@pytest_asyncio.fixture
async def qa_tester_client(db_session):
    """Test client authenticated as Anne with camper-qa-tester role."""
    async def mock_verify_qa_tester():
        return {
            "sub": "test-qa-tester-id",
            "preferred_username": "anne",
            "email": "anne@helixnet.test",
            "realm_access": {
                "roles": [
                    "camper-qa-tester",
                    "default-roles-kc-camper-service-realm-dev",
                    "offline_access",
                    "uma_authorization",
                ]
            },
        }

    app.dependency_overrides[get_db_session] = lambda: db_session
    app.dependency_overrides[verify_token] = mock_verify_qa_tester

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


class TestQADashboardAccess:
    """Test that QA routes are accessible (currently no auth required)."""

    @pytest.mark.asyncio
    async def test_testing_dashboard_html_accessible(self, qa_tester_client):
        """The /testing HTML page should return 200."""
        resp = await qa_tester_client.get("/testing")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_qa_summary_accessible(self, qa_tester_client):
        """The /api/v1/testing/summary endpoint should return 200."""
        resp = await qa_tester_client.get("/api/v1/testing/summary")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_qa_bugs_list_accessible(self, qa_tester_client):
        """The /api/v1/testing/bugs endpoint should return 200."""
        resp = await qa_tester_client.get("/api/v1/testing/bugs")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_training_page_accessible(self, qa_tester_client):
        """The /training page should return 200."""
        resp = await qa_tester_client.get("/training")
        assert resp.status_code == 200


class TestCamperRouteProtection:
    """Test that camper business routes reject QA-only users."""

    @pytest.mark.asyncio
    async def test_qa_tester_cannot_access_camper_vehicles(self, qa_tester_client):
        """A QA tester should NOT be able to list camper vehicles (needs camper-counter+)."""
        resp = await qa_tester_client.get("/api/v1/camper/vehicles")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_qa_tester_cannot_access_camper_jobs(self, qa_tester_client):
        """A QA tester should NOT be able to list camper jobs."""
        resp = await qa_tester_client.get("/api/v1/camper/jobs")
        assert resp.status_code == 403
