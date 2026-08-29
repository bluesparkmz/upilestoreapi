def test_create_product(client, auth_headers):
    response = client.post(
        "/products",
        headers=auth_headers,
        json={
            "title": "O Espírito de Maputo",
            "description": "Pintura a óleo",
            "category": "arte contemporânea",
            "type": "pintura",
            "artist": "Artista X",
            "year": 2024,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "O Espírito de Maputo"
    assert data["type"] == "pintura"


def test_list_products(client, auth_headers):
    client.post(
        "/products",
        headers=auth_headers,
        json={"title": "Obra 1", "type": "pintura"},
    )
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_get_product(client, auth_headers):
    created = client.post(
        "/products",
        headers=auth_headers,
        json={"title": "Obra Detalhe", "type": "escultura"},
    )
    product_id = created.json()["data"]["id"]
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Obra Detalhe"


def test_update_product(client, auth_headers):
    created = client.post(
        "/products",
        headers=auth_headers,
        json={"title": "Original", "type": "desenho"},
    )
    product_id = created.json()["data"]["id"]
    response = client.put(
        f"/products/{product_id}",
        headers=auth_headers,
        json={"title": "Atualizado"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Atualizado"


def test_prevent_update_by_other_user(client, auth_headers, second_user_headers):
    created = client.post(
        "/products",
        headers=auth_headers,
        json={"title": "Protegida", "type": "fotografia"},
    )
    product_id = created.json()["data"]["id"]
    response = client.put(
        f"/products/{product_id}",
        headers=second_user_headers,
        json={"title": "Hack"},
    )
    assert response.status_code == 403
