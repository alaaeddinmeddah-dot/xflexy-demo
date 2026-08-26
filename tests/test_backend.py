from fastapi.testclient import TestClient

from xflexy.backend.main import app


ADMIN_HEADERS = {"x-admin-api-key": "change-me-local-admin-key"}


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "xflexy"}


def test_order_api_happy_path() -> None:
    with TestClient(app) as client:
        user_response = client.post(
            "/users/register",
            json={"telegram_user_id": 9001, "username": "tester", "full_name": "Test User"},
        )
        order_response = client.post(
            "/orders",
            json={"telegram_user_id": 9001, "phone_number": "0555123456", "amount": 500},
        )
        order_id = order_response.json()["order_id"]
        status_response = client.get(f"/orders/{order_id}/status")
        confirm_response = client.post(
            f"/internal/mock-payments/{order_id}/confirm",
            headers=ADMIN_HEADERS,
        )
        read_response = client.get(f"/orders/{order_id}")
        user_orders_response = client.get("/users/9001/orders")

    assert user_response.status_code == 200
    assert order_response.status_code == 200
    assert status_response.json() == {"order_id": order_id, "status": "awaiting_payment"}
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "completed"
    assert read_response.json()["order_id"] == order_id
    assert len(user_orders_response.json()) >= 1


def test_order_api_validation() -> None:
    with TestClient(app) as client:
        client.post(
            "/users/register",
            json={"telegram_user_id": 9002, "username": None, "full_name": "Bad Phone"},
        )
        response = client.post(
            "/orders",
            json={"telegram_user_id": 9002, "phone_number": "bad", "amount": 500},
        )

    assert response.status_code == 422


def test_mock_payment_endpoint_requires_admin_key() -> None:
    with TestClient(app) as client:
        response = client.post("/internal/mock-payments/not-real/confirm")

    assert response.status_code == 401


def test_admin_lists_are_protected_and_available() -> None:
    with TestClient(app) as client:
        blocked = client.get("/admin/users")
        allowed = client.get("/admin/users", headers=ADMIN_HEADERS)
        orders = client.get("/admin/orders", headers=ADMIN_HEADERS)
        payments = client.get("/admin/payments", headers=ADMIN_HEADERS)
        operations = client.get("/admin/operations", headers=ADMIN_HEADERS)
        dashboard = client.get("/admin/demo-dashboard", headers=ADMIN_HEADERS)

    assert blocked.status_code == 401
    assert allowed.status_code == 200
    assert orders.status_code == 200
    assert payments.status_code == 200
    assert operations.status_code == 200
    assert dashboard.status_code == 200
    assert "summary" in dashboard.json()


def test_mock_top_up_legacy_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/flexy/top-up",
            json={
                "telegram_user_id": 12345,
                "phone_number": "0555123456",
                "amount": 500,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["provider_reference"].startswith("mock-")
