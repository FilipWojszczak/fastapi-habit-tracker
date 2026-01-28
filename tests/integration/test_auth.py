from fastapi.testclient import TestClient


def test_authentication(client: TestClient):
    email = "john.smith@example.com"
    password = "securepassword"

    # Register a new user
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    data = response.json()
    assert response.status_code == 201
    assert data["email"] == email
    assert data["is_active"] is True
    assert isinstance(data["id"], int)

    # Log in to obtain an access token
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password},
    )
    data = response.json()
    assert response.status_code == 200
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    access_token = data["access_token"]

    # Access a protected endpoint
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = response.json()
    assert response.status_code == 200
    assert data["email"] == email
    assert data["is_active"] is True
    assert isinstance(data["id"], int)
