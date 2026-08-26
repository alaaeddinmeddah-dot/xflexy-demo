import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    telegram_user_id: int
    username: str | None
    full_name: str
    account_status: str
    registered_at: str


@dataclass(frozen=True)
class Order:
    id: int
    order_id: str
    user_id: int
    phone_number: str
    amount: int
    status: str
    flexy_reference: str | None
    flexy_message: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class Payment:
    id: int
    payment_id: str
    order_id: str
    amount: int
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class FlexyRequest:
    id: int
    telegram_user_id: int
    phone_number: str
    amount: int
    status: str
    provider_reference: str | None


def _user(row: sqlite3.Row | None) -> User | None:
    return User(**dict(row)) if row else None


def _order(row: sqlite3.Row | None) -> Order | None:
    return Order(**dict(row)) if row else None


def _payment(row: sqlite3.Row | None) -> Payment | None:
    return Payment(**dict(row)) if row else None


class UserRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def upsert_telegram_user(
        self,
        telegram_user_id: int,
        username: str | None,
        full_name: str,
        account_status: str = "active",
    ) -> User:
        self.connection.execute(
            """
            INSERT INTO users (telegram_user_id, username, full_name, account_status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (telegram_user_id, username, full_name, account_status),
        )
        user = self.get_by_telegram_id(telegram_user_id)
        if user is None:
            raise RuntimeError("Failed to create user.")
        return user

    def get_by_id(self, user_id: int) -> User | None:
        return _user(
            self.connection.execute(
                """
                SELECT id, telegram_user_id, username, full_name, account_status, registered_at
                FROM users
                WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
        )

    def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        return _user(
            self.connection.execute(
                """
                SELECT id, telegram_user_id, username, full_name, account_status, registered_at
                FROM users
                WHERE telegram_user_id = ?
                """,
                (telegram_user_id,),
            ).fetchone()
        )

    def list_all(self) -> list[User]:
        rows = self.connection.execute(
            """
            SELECT id, telegram_user_id, username, full_name, account_status, registered_at
            FROM users
            ORDER BY id DESC
            """
        ).fetchall()
        return [User(**dict(row)) for row in rows]


class OrderRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, order_id: str, user_id: int, phone_number: str, amount: int, status: str) -> Order:
        self.connection.execute(
            """
            INSERT INTO orders (order_id, user_id, phone_number, amount, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (order_id, user_id, phone_number, amount, status),
        )
        order = self.get_by_order_id(order_id)
        if order is None:
            raise RuntimeError("Failed to create order.")
        return order

    def get_by_order_id(self, order_id: str) -> Order | None:
        return _order(
            self.connection.execute(
                """
                SELECT id, order_id, user_id, phone_number, amount, status,
                       flexy_reference, flexy_message, created_at, updated_at
                FROM orders
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()
        )

    def list_by_user_id(self, user_id: int) -> list[Order]:
        rows = self.connection.execute(
            """
            SELECT id, order_id, user_id, phone_number, amount, status,
                   flexy_reference, flexy_message, created_at, updated_at
            FROM orders
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()
        return [Order(**dict(row)) for row in rows]

    def list_all(self) -> list[Order]:
        rows = self.connection.execute(
            """
            SELECT id, order_id, user_id, phone_number, amount, status,
                   flexy_reference, flexy_message, created_at, updated_at
            FROM orders
            ORDER BY id DESC
            """
        ).fetchall()
        return [Order(**dict(row)) for row in rows]

    def update_status(
        self,
        order_id: str,
        status: str,
        flexy_reference: str | None = None,
        flexy_message: str | None = None,
    ) -> Order:
        self.connection.execute(
            """
            UPDATE orders
            SET status = ?,
                flexy_reference = COALESCE(?, flexy_reference),
                flexy_message = COALESCE(?, flexy_message),
                updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
            """,
            (status, flexy_reference, flexy_message, order_id),
        )
        order = self.get_by_order_id(order_id)
        if order is None:
            raise ValueError("Order not found.")
        return order


class PaymentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(self, payment_id: str, order_id: str, amount: int, status: str) -> Payment:
        self.connection.execute(
            """
            INSERT INTO payments (payment_id, order_id, amount, status)
            VALUES (?, ?, ?, ?)
            """,
            (payment_id, order_id, amount, status),
        )
        payment = self.get_by_order_id(order_id)
        if payment is None:
            raise RuntimeError("Failed to create payment.")
        return payment

    def get_by_order_id(self, order_id: str) -> Payment | None:
        return _payment(
            self.connection.execute(
                """
                SELECT id, payment_id, order_id, amount, status, created_at, updated_at
                FROM payments
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()
        )

    def list_all(self) -> list[Payment]:
        rows = self.connection.execute(
            """
            SELECT id, payment_id, order_id, amount, status, created_at, updated_at
            FROM payments
            ORDER BY id DESC
            """
        ).fetchall()
        return [Payment(**dict(row)) for row in rows]

    def update_status(self, order_id: str, status: str) -> Payment:
        self.connection.execute(
            """
            UPDATE payments
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
            """,
            (status, order_id),
        )
        payment = self.get_by_order_id(order_id)
        if payment is None:
            raise ValueError("Payment not found.")
        return payment


class FlexyRequestRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(
        self,
        telegram_user_id: int,
        phone_number: str,
        amount: int,
        status: str,
        provider_reference: str | None = None,
    ) -> FlexyRequest:
        cursor = self.connection.execute(
            """
            INSERT INTO flexy_requests (
                telegram_user_id,
                phone_number,
                amount,
                status,
                provider_reference
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_user_id, phone_number, amount, status, provider_reference),
        )
        return FlexyRequest(
            id=int(cursor.lastrowid),
            telegram_user_id=telegram_user_id,
            phone_number=phone_number,
            amount=amount,
            status=status,
            provider_reference=provider_reference,
        )

    def list_recent(self, limit: int = 20) -> list[FlexyRequest]:
        rows = self.connection.execute(
            """
            SELECT id, telegram_user_id, phone_number, amount, status, provider_reference
            FROM flexy_requests
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [FlexyRequest(**dict(row)) for row in rows]
