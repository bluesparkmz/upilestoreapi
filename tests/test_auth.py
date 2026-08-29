def test_register(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "João Silva",
            "username": "joaosilva",
            "email": "joao@example.com",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "joao@example.com"
    assert "password" not in data["data"]
    assert "password_hash" not in data["data"]


def test_login(client):
    client.post(
        "/auth/register",
        json={
            "name": "João Silva",
            "username": "joaosilva",
            "email": "joao@example.com",
            "password": "password123",
        },
    )
    response = client.post(
        "/auth/login",
        json={"email": "joao@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "name": "João Silva",
            "username": "joaosilva",
            "email": "joao@example.com",
            "password": "password123",
        },
    )
    response = client.post(
        "/auth/login",
        json={"email": "joao@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_access_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_access_with_valid_token(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["username"] == "testuser"
