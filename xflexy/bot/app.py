from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from xflexy.bot.handlers import (
    ASK_AMOUNT,
    ASK_PHONE,
    CONFIRM_ORDER,
    cancel,
    confirm_order,
    flexy_command,
    help_command,
    receive_amount,
    receive_phone,
    start,
)
from xflexy.core.config import Settings


def create_bot_application(settings: Settings) -> Application:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required to run the Telegram bot.")

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("flexy", flexy_command)],
            states={
                ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
                ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)],
                CONFIRM_ORDER: [
                    CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                    CallbackQueryHandler(cancel, pattern="^cancel_order$"),
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )
    return application
