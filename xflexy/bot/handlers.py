from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler

from xflexy.core.config import get_settings
from xflexy.database.connection import get_connection
from xflexy.database.repositories import OrderRepository, PaymentRepository, UserRepository
from xflexy.flexy.factory import get_flexy_provider
from xflexy.services.order_service import OrderService
from xflexy.services.user_service import UserService
from xflexy.services.validation import validate_amount, validate_phone_number

ASK_PHONE, ASK_AMOUNT, CONFIRM_ORDER = range(3)


def _full_name(update: Update) -> str:
    user = update.effective_user
    if user is None:
        return "Telegram User"
    return " ".join(part for part in [user.first_name, user.last_name] if part) or "Telegram User"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    settings = get_settings()
    with get_connection(settings.database_url) as connection:
        service = UserService(UserRepository(connection))
        service.register_telegram_user(
            telegram_user_id=update.effective_user.id,
            username=update.effective_user.username,
            full_name=_full_name(update),
        )
    await update.message.reply_text(
        "Welcome to xflexy Demo.\n"
        "Your Telegram profile is registered for the demo.\n"
        "Use /flexy to create a mock Flexy request. No real payment or transfer will happen."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "Available commands:\n"
        "/start - register for the demo\n"
        "/flexy - create a mock Flexy order\n"
        "/cancel - cancel the current draft"
    )


async def flexy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    await update.message.reply_text("Enter a demo beneficiary phone number, for example: 0555123456")
    return ASK_PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    settings = get_settings()
    phone_number = update.message.text or ""
    try:
        validate_phone_number(phone_number, settings)
    except ValueError as exc:
        await update.message.reply_text(f"Phone number problem: {exc}\nPlease enter a valid demo number.")
        return ASK_PHONE
    context.user_data["phone_number"] = phone_number
    await update.message.reply_text("Enter the demo amount.")
    return ASK_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message is None:
        return ConversationHandler.END
    settings = get_settings()
    try:
        amount = int(update.message.text or "")
        validate_amount(amount, settings)
    except ValueError as exc:
        await update.message.reply_text(f"Amount problem: {exc}\nPlease enter an allowed demo amount.")
        return ASK_AMOUNT

    context.user_data["amount"] = amount
    phone_number = context.user_data["phone_number"]
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm order", callback_data="confirm_order"),
                InlineKeyboardButton("Cancel", callback_data="cancel_order"),
            ]
        ]
    )
    await update.message.reply_text(
        f"Demo order summary:\n"
        f"Phone: {phone_number}\n"
        f"Amount: {amount}\n"
        "Status after confirmation: awaiting_payment\n"
        "Confirm this mock order?",
        reply_markup=keyboard,
    )
    return CONFIRM_ORDER


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return ConversationHandler.END
    await query.answer()
    settings = get_settings()
    with get_connection(settings.database_url) as connection:
        users = UserRepository(connection)
        UserService(users).register_telegram_user(
            telegram_user_id=update.effective_user.id,
            username=update.effective_user.username,
            full_name=_full_name(update),
        )
        service = OrderService(
            settings=settings,
            users=users,
            orders=OrderRepository(connection),
            payments=PaymentRepository(connection),
            flexy_provider=get_flexy_provider(settings),
        )
        order = service.create_order(
            telegram_user_id=update.effective_user.id,
            phone_number=str(context.user_data["phone_number"]),
            amount=int(context.user_data["amount"]),
        )
    await query.edit_message_text(
        f"Demo order created.\n"
        f"Order ID: {order.order_id}\n"
        f"Phone: {order.phone_number}\n"
        f"Amount: {order.amount}\n"
        f"Status: {order.status}\n"
        "Next demo step: confirm mock payment from the protected internal endpoint."
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query is not None:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Demo order cancelled. No payment or Flexy action was made.")
    elif update.message is not None:
        await update.message.reply_text("Demo order cancelled. No payment or Flexy action was made.")
    return ConversationHandler.END
