from fastapi.testclient import TestClient


def test_health_reaches_the_database(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
