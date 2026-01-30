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


def test_register_existing_user(client: TestClient):
    email = "john.smith@example.com"
    password = "securepassword"

    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201

    # Attempt to register the same user again
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    data = response.json()
    assert response.status_code == 409
    assert data["detail"] == "User with this email already exists"


def test_login_invalid_credentials(client: TestClient):
    email = "john.smith@example.com"
    password = "securepassword"
    not_existing_email = "abc@example.com"
    wrong_password = "wrongpassword"

    # Register a new user
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201

    # Log in with incorrect password
    response = client.post(
        "/auth/token",
        data={"username": email, "password": wrong_password},
    )
    data = response.json()
    assert response.status_code == 401
    assert "access_token" not in data
    assert data["detail"] == "Incorrect email or password"

    # Log in with non-existing email
    response = client.post(
        "/auth/token",
        data={"username": not_existing_email, "password": password},
    )
    data = response.json()
    assert response.status_code == 401
    assert "access_token" not in data
    assert data["detail"] == "Incorrect email or password"


def test_access_protected_endpoint_no_token(client: TestClient):
    # Attempt to access a protected endpoint without a token
    response = client.get("/auth/me")
    data = response.json()
    assert response.status_code == 401
    assert data["detail"] == "Not authenticated"
