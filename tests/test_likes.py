def _create_product(client, headers, title="Obra Like"):
    return client.post(
        "/products",
        headers=headers,
        json={"title": title, "type": "pintura"},
    ).json()["data"]["id"]


def test_like_product(client, auth_headers, second_user_headers):
    product_id = _create_product(client, auth_headers)
    response = client.post(f"/products/{product_id}/like", headers=second_user_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["likes_count"] == 1
    assert data["liked_by_me"] is True


def test_unlike_product(client, auth_headers, second_user_headers):
    product_id = _create_product(client, auth_headers)
    client.post(f"/products/{product_id}/like", headers=second_user_headers)
    response = client.delete(f"/products/{product_id}/like", headers=second_user_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["likes_count"] == 0
    assert data["liked_by_me"] is False


def test_prevent_duplicate_like(client, auth_headers, second_user_headers):
    product_id = _create_product(client, auth_headers)
    client.post(f"/products/{product_id}/like", headers=second_user_headers)
    response = client.post(f"/products/{product_id}/like", headers=second_user_headers)
    assert response.status_code == 200
    assert response.json()["data"]["likes_count"] == 1


def test_count_likes(client, auth_headers, second_user_headers):
    product_id = _create_product(client, auth_headers)
    client.post(f"/products/{product_id}/like", headers=second_user_headers)
    response = client.get(f"/products/{product_id}/likes", headers=second_user_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["likes_count"] == 1
    assert data["liked_by_me"] is True
