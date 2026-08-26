import logging
from uuid import uuid4

from xflexy.core.config import Settings
from xflexy.core.status import OrderStatus, PaymentStatus, TERMINAL_ORDER_STATUSES
from xflexy.database.repositories import Order, OrderRepository, PaymentRepository, UserRepository
from xflexy.flexy.provider import FlexyProvider, FlexyTopUpRequest
from xflexy.services.validation import validate_amount, validate_phone_number

logger = logging.getLogger(__name__)


class OrderService:
    def __init__(
        self,
        settings: Settings,
        users: UserRepository,
        orders: OrderRepository,
        payments: PaymentRepository,
        flexy_provider: FlexyProvider,
    ) -> None:
        self.settings = settings
        self.users = users
        self.orders = orders
        self.payments = payments
        self.flexy_provider = flexy_provider

    def create_order(self, telegram_user_id: int, phone_number: str, amount: int) -> Order:
        validate_phone_number(phone_number, self.settings)
        validate_amount(amount, self.settings)

        user = self.users.get_by_telegram_id(telegram_user_id)
        if user is None:
            raise ValueError("User must be registered before creating an order.")
        if user.account_status != "active":
            raise ValueError("User account is not active.")

        order = self.orders.create(
            order_id=f"ord_{uuid4().hex}",
            user_id=user.id,
            phone_number=phone_number,
            amount=amount,
            status=OrderStatus.awaiting_payment.value,
        )
        self.payments.create(
            payment_id=f"pay_{uuid4().hex}",
            order_id=order.order_id,
            amount=amount,
            status=PaymentStatus.pending.value,
        )
        logger.info("Created order order_id=%s user_id=%s", order.order_id, user.id)
        return order

    def get_order(self, order_id: str) -> Order:
        order = self.orders.get_by_order_id(order_id)
        if order is None:
            raise ValueError("Order not found.")
        return order

    def list_user_orders(self, telegram_user_id: int) -> list[Order]:
        user = self.users.get_by_telegram_id(telegram_user_id)
        if user is None:
            return []
        return self.orders.list_by_user_id(user.id)

    def cancel_order(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        if OrderStatus(order.status) in TERMINAL_ORDER_STATUSES:
            return order
        logger.info("Cancelled order order_id=%s", order_id)
        return self.orders.update_status(order_id, OrderStatus.cancelled.value)

    def confirm_mock_payment(self, order_id: str) -> Order:
        order = self.get_order(order_id)
        payment = self.payments.get_by_order_id(order_id)
        if payment is None:
            raise ValueError("Payment not found.")

        if order.status == OrderStatus.completed.value:
            logger.info("Skipped duplicate completed order order_id=%s", order_id)
            return order
        if order.status in {OrderStatus.processing.value, OrderStatus.paid.value}:
            logger.info("Skipped duplicate in-flight order order_id=%s", order_id)
            return order
        if order.status != OrderStatus.awaiting_payment.value:
            raise ValueError("Order is not awaiting payment.")
        if payment.status == PaymentStatus.confirmed.value:
            raise ValueError("Payment is already confirmed for a non-processable order.")

        self.payments.update_status(order_id, PaymentStatus.confirmed.value)
        logger.info("Confirmed mock payment order_id=%s", order_id)
        self.orders.update_status(order_id, OrderStatus.paid.value)
        self.orders.update_status(order_id, OrderStatus.processing.value)
        logger.info("Attempting mock Flexy execution order_id=%s", order_id)

        result = self.flexy_provider.top_up(
            FlexyTopUpRequest(phone_number=order.phone_number, amount=order.amount)
        )
        if result.success:
            logger.info("Mock Flexy completed order_id=%s reference=%s", order_id, result.reference)
            return self.orders.update_status(
                order_id,
                OrderStatus.completed.value,
                flexy_reference=result.reference,
                flexy_message=result.message,
            )

        logger.info("Mock Flexy failed order_id=%s reference=%s", order_id, result.reference)
        return self.orders.update_status(
            order_id,
            OrderStatus.failed.value,
            flexy_reference=result.reference,
            flexy_message=result.message,
        )
