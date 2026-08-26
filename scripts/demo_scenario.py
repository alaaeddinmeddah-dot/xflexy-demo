import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from xflexy.backend.main import app


ADMIN_HEADERS = {"x-admin-api-key": "change-me-local-admin-key"}
DEMO_USER = {
    "telegram_user_id": 424242001,
    "username": "demo_customer",
    "full_name": "Demo Customer",
}
DEMO_ORDER = {
    "telegram_user_id": 424242001,
    "phone_number": "0555123456",
    "amount": 500,
}


def main() -> None:
    with TestClient(app) as client:
        user = client.post("/users/register", json=DEMO_USER)
        user.raise_for_status()
        print("1. User registered")
        print(user.json())

        order = client.post("/orders", json=DEMO_ORDER)
        order.raise_for_status()
        order_payload = order.json()
        order_id = order_payload["order_id"]
        print("\n2. Flexy order created")
        print(order_payload)

        status = client.get(f"/orders/{order_id}/status")
        status.raise_for_status()
        print("\n3. Order is awaiting mock payment")
        print(status.json())

        confirmed = client.post(
            f"/internal/mock-payments/{order_id}/confirm",
            headers=ADMIN_HEADERS,
        )
        confirmed.raise_for_status()
        print("\n4. Mock payment confirmed and mock Flexy executed")
        print(confirmed.json())

        dashboard = client.get("/admin/demo-dashboard", headers=ADMIN_HEADERS)
        dashboard.raise_for_status()
        print("\n5. Admin demo dashboard")
        print(dashboard.json())


if __name__ == "__main__":
    main()
