from fastapi import APIRouter, Depends, Request

from xflexy.core.security import require_admin_api_key
from xflexy.database.connection import get_connection
from xflexy.database.repositories import (
    FlexyRequestRepository,
    OrderRepository,
    PaymentRepository,
    UserRepository,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_key)],
)


@router.get("/users")
def list_users(request: Request) -> list[dict]:
    with get_connection(request.app.state.settings.database_url) as connection:
        return [user.__dict__ for user in UserRepository(connection).list_all()]


@router.get("/orders")
def list_orders(request: Request) -> list[dict]:
    with get_connection(request.app.state.settings.database_url) as connection:
        return [order.__dict__ for order in OrderRepository(connection).list_all()]


@router.get("/payments")
def list_payments(request: Request) -> list[dict]:
    with get_connection(request.app.state.settings.database_url) as connection:
        return [payment.__dict__ for payment in PaymentRepository(connection).list_all()]


@router.get("/operations")
def list_operations(request: Request) -> dict[str, list[dict]]:
    with get_connection(request.app.state.settings.database_url) as connection:
        orders = OrderRepository(connection).list_all()
        return {
            "successful": [order.__dict__ for order in orders if order.status == "completed"],
            "failed": [order.__dict__ for order in orders if order.status == "failed"],
        }


@router.get("/demo-dashboard")
def demo_dashboard(request: Request) -> dict:
    with get_connection(request.app.state.settings.database_url) as connection:
        users = UserRepository(connection).list_all()
        orders = OrderRepository(connection).list_all()
        payments = PaymentRepository(connection).list_all()
        return {
            "summary": {
                "users": len(users),
                "orders": len(orders),
                "payments": len(payments),
                "completed_orders": len([order for order in orders if order.status == "completed"]),
                "failed_orders": len([order for order in orders if order.status == "failed"]),
            },
            "users": [user.__dict__ for user in users],
            "orders": [order.__dict__ for order in orders],
            "payments": [payment.__dict__ for payment in payments],
            "operations": {
                "successful": [order.__dict__ for order in orders if order.status == "completed"],
                "failed": [order.__dict__ for order in orders if order.status == "failed"],
            },
        }


@router.get("/legacy-flexy-requests")
def list_legacy_requests(request: Request) -> list[dict]:
    with get_connection(request.app.state.settings.database_url) as connection:
        return [request_item.__dict__ for request_item in FlexyRequestRepository(connection).list_recent()]
