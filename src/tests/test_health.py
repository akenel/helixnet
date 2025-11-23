# tests/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_login_and_me(async_client):
    # 1️⃣ Login as admin
    response = await async_client.post(
        "/api/v1/auth/token",
        data={"username": "admin@helix.net", "password": "admin"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

    # 2️⃣ Use the token to access /users/me
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    me = await async_client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    me_data = me.json()

    assert me_data["email"] == "admin@helix.net"
    assert "id" in me_data
