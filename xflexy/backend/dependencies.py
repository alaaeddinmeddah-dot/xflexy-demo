from typing import Iterator

from fastapi import Request

from xflexy.database.connection import get_connection
from xflexy.database.repositories import (
    FlexyRequestRepository,
    OrderRepository,
    PaymentRepository,
    UserRepository,
)
from xflexy.services.order_service import OrderService
from xflexy.services.user_service import UserService


def get_repositories(request: Request) -> Iterator[tuple[UserRepository, OrderRepository, PaymentRepository]]:
    with get_connection(request.app.state.settings.database_url) as connection:
        yield (
            UserRepository(connection),
            OrderRepository(connection),
            PaymentRepository(connection),
        )


def get_user_service(request: Request) -> Iterator[UserService]:
    with get_connection(request.app.state.settings.database_url) as connection:
        yield UserService(UserRepository(connection))


def get_order_service(request: Request) -> Iterator[OrderService]:
    with get_connection(request.app.state.settings.database_url) as connection:
        yield OrderService(
            settings=request.app.state.settings,
            users=UserRepository(connection),
            orders=OrderRepository(connection),
            payments=PaymentRepository(connection),
            flexy_provider=request.app.state.flexy_provider,
        )


def get_request_repository(request: Request) -> Iterator[FlexyRequestRepository]:
    with get_connection(request.app.state.settings.database_url) as connection:
        yield FlexyRequestRepository(connection)
