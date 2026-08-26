import pytest

from xflexy.core.config import Settings
from xflexy.database.connection import get_connection
from xflexy.database.repositories import OrderRepository, PaymentRepository, UserRepository
from xflexy.database.schema import initialize_schema
from xflexy.flexy.mock_provider import MockFlexyProvider
from xflexy.services.order_service import OrderService
from xflexy.services.user_service import UserService


def _service(settings: Settings, mode: str = "success"):
    connection_cm = get_connection(settings.database_url)
    connection = connection_cm.__enter__()
    initialize_schema(connection)
    users = UserRepository(connection)
    return (
        connection_cm,
        connection,
        UserService(users),
        OrderService(
            settings=settings,
            users=users,
            orders=OrderRepository(connection),
            payments=PaymentRepository(connection),
            flexy_provider=MockFlexyProvider(mode=mode),
        ),
        PaymentRepository(connection),
    )


def test_register_user_is_idempotent(settings: Settings) -> None:
    cm, _, users, _, _ = _service(settings)
    try:
        first = users.register_telegram_user(1, "alice", "Alice A")
        second = users.register_telegram_user(1, "alice2", "Alice B")
    finally:
        cm.__exit__(None, None, None)

    assert first.id == second.id
    assert second.username == "alice2"


def test_create_order_and_payment(settings: Settings) -> None:
    cm, _, users, orders, payments = _service(settings)
    try:
        users.register_telegram_user(1, "alice", "Alice")
        order = orders.create_order(1, "0555123456", 500)
        payment = payments.get_by_order_id(order.order_id)
    finally:
        cm.__exit__(None, None, None)

    assert order.status == "awaiting_payment"
    assert payment is not None
    assert payment.status == "pending"


@pytest.mark.parametrize("phone,amount", [("abc", 500), ("0555123456", 0), ("0555123456", 49)])
def test_order_validation(settings: Settings, phone: str, amount: int) -> None:
    cm, _, users, orders, _ = _service(settings)
    try:
        users.register_telegram_user(1, "alice", "Alice")
        with pytest.raises(ValueError):
            orders.create_order(1, phone, amount)
    finally:
        cm.__exit__(None, None, None)


def test_confirm_payment_completes_successful_mock(settings: Settings) -> None:
    cm, _, users, orders, payments = _service(settings)
    try:
        users.register_telegram_user(1, "alice", "Alice")
        order = orders.create_order(1, "0555123456", 500)
        completed = orders.confirm_mock_payment(order.order_id)
        payment = payments.get_by_order_id(order.order_id)
    finally:
        cm.__exit__(None, None, None)

    assert completed.status == "completed"
    assert completed.flexy_reference is not None
    assert payment is not None
    assert payment.status == "confirmed"


def test_confirm_payment_fails_with_failed_mock(settings: Settings) -> None:
    cm, _, users, orders, _ = _service(settings, mode="failure")
    try:
        users.register_telegram_user(1, "alice", "Alice")
        order = orders.create_order(1, "0555123456", 500)
        failed = orders.confirm_mock_payment(order.order_id)
    finally:
        cm.__exit__(None, None, None)

    assert failed.status == "failed"
    assert failed.flexy_reference.startswith("mock-failed-")


def test_duplicate_execution_is_skipped(settings: Settings) -> None:
    cm, _, users, orders, _ = _service(settings)
    try:
        users.register_telegram_user(1, "alice", "Alice")
        order = orders.create_order(1, "0555123456", 500)
        first = orders.confirm_mock_payment(order.order_id)
        second = orders.confirm_mock_payment(order.order_id)
    finally:
        cm.__exit__(None, None, None)

    assert first.status == "completed"
    assert second.status == "completed"
    assert first.flexy_reference == second.flexy_reference
