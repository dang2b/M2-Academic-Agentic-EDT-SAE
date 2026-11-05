from fastapi.testclient import TestClient


def test_list_roles_returns_reference_roles_in_id_order(client: TestClient) -> None:
    response = client.get("/roles")

    assert response.status_code == 200
    assert [r["code"] for r in response.json()] == ["ADMIN", "MANAGER", "TEACHER", "STUDENT"]
    assert set(response.json()[0]) == {"id", "code", "label"}


def test_list_roles_paginates(client: TestClient) -> None:
    response = client.get("/roles", params={"limit": 2, "offset": 1})

    assert [r["code"] for r in response.json()] == ["MANAGER", "TEACHER"]


def test_list_roles_rejects_a_limit_above_the_maximum(client: TestClient) -> None:
    assert client.get("/roles", params={"limit": 201}).status_code == 422
