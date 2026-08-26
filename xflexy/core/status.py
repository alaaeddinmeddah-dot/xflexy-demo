from enum import StrEnum


class AccountStatus(StrEnum):
    active = "active"
    blocked = "blocked"


class OrderStatus(StrEnum):
    pending = "pending"
    awaiting_payment = "awaiting_payment"
    paid = "paid"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"
    failed = "failed"


class PaymentStatus(StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"
    expired = "expired"


TERMINAL_ORDER_STATUSES = {
    OrderStatus.completed,
    OrderStatus.cancelled,
    OrderStatus.failed,
}
