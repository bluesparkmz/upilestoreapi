def _create_product(client, headers):
    return client.post(
        "/products",
        headers=headers,
        json={"title": "Obra Anúncio", "type": "pintura", "artist": "Artista Y"},
    ).json()["data"]["id"]


def test_create_announcement(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    response = client.post(
        "/announcements",
        headers=auth_headers,
        json={"product_id": product_id, "price": 5000, "currency": "MZN", "quantity": 2},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "draft"
    assert float(data["price"]) == 5000


def test_publish_announcement(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    created = client.post(
        "/announcements",
        headers=auth_headers,
        json={"product_id": product_id, "price": 3000, "quantity": 1},
    )
    announcement_id = created.json()["data"]["id"]
    response = client.post(f"/announcements/{announcement_id}/publish", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "active"


def test_update_announcement(client, auth_headers):
    product_id = _create_product(client, auth_headers)
    created = client.post(
        "/announcements",
        headers=auth_headers,
        json={"product_id": product_id, "price": 2000, "quantity": 1},
    )
    announcement_id = created.json()["data"]["id"]
    response = client.put(
        f"/announcements/{announcement_id}",
        headers=auth_headers,
        json={"price": 2500},
    )
    assert response.status_code == 200
    assert float(response.json()["data"]["price"]) == 2500


def test_prevent_update_by_other_user(client, auth_headers, second_user_headers):
    product_id = _create_product(client, auth_headers)
    created = client.post(
        "/announcements",
        headers=auth_headers,
        json={"product_id": product_id, "price": 1000, "quantity": 1},
    )
    announcement_id = created.json()["data"]["id"]
    response = client.put(
        f"/announcements/{announcement_id}",
        headers=second_user_headers,
        json={"price": 1},
    )
    assert response.status_code == 403
