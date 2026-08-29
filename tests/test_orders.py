def _setup_active_announcement(client, seller_headers, price=10000, quantity=1):
    product_id = client.post(
        "/products",
        headers=seller_headers,
        json={"title": "Obra Venda", "type": "pintura"},
    ).json()["data"]["id"]
    announcement = client.post(
        "/announcements",
        headers=seller_headers,
        json={"product_id": product_id, "price": price, "quantity": quantity},
    ).json()["data"]
    client.post(f"/announcements/{announcement['id']}/publish", headers=seller_headers)
    return announcement


def test_create_order(client, auth_headers, second_user_headers):
    announcement = _setup_active_announcement(client, auth_headers, price=5000)
    response = client.post(
        "/orders",
        headers=second_user_headers,
        json={"items": [{"announcement_id": announcement["id"], "quantity": 1}]},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert float(data["total_amount"]) == 5000
    assert len(data["items"]) == 1
    assert float(data["items"][0]["unit_price"]) == 5000


def test_buy_announcement(client, auth_headers, second_user_headers):
    announcement = _setup_active_announcement(client, auth_headers, price=7500, quantity=1)
    response = client.post(
        "/orders",
        headers=second_user_headers,
        json={"items": [{"announcement_id": announcement["id"], "quantity": 1}]},
    )
    assert response.status_code == 201
    updated = client.get(f"/announcements/{announcement['id']}")
    assert updated.json()["data"]["status"] == "sold"


def test_prevent_buy_sold_announcement(client, auth_headers, second_user_headers):
    announcement = _setup_active_announcement(client, auth_headers, price=3000, quantity=1)
    client.post(
        "/orders",
        headers=second_user_headers,
        json={"items": [{"announcement_id": announcement["id"], "quantity": 1}]},
    )
    response = client.post(
        "/orders",
        headers=second_user_headers,
        json={"items": [{"announcement_id": announcement["id"], "quantity": 1}]},
    )
    assert response.status_code == 400


def test_order_total_calculation(client, auth_headers, second_user_headers):
    announcement = _setup_active_announcement(client, auth_headers, price=2000, quantity=5)
    response = client.post(
        "/orders",
        headers=second_user_headers,
        json={"items": [{"announcement_id": announcement["id"], "quantity": 3}]},
    )
    assert response.status_code == 201
    assert float(response.json()["data"]["total_amount"]) == 6000


def test_cancel_order(client, auth_headers, second_user_headers):
    announcement = _setup_active_announcement(client, auth_headers, price=4000, quantity=2)
    order = client.post(
        "/orders",
        headers=second_user_headers,
        json={"items": [{"announcement_id": announcement["id"], "quantity": 1}]},
    ).json()["data"]
    response = client.post(f"/orders/{order['id']}/cancel", headers=second_user_headers)
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "cancelled"
