import logging

from xflexy.core.status import AccountStatus
from xflexy.database.repositories import User, UserRepository

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def register_telegram_user(
        self,
        telegram_user_id: int,
        username: str | None,
        full_name: str,
    ) -> User:
        existing = self.users.get_by_telegram_id(telegram_user_id)
        user = self.users.upsert_telegram_user(
            telegram_user_id=telegram_user_id,
            username=username,
            full_name=full_name or "Telegram User",
            account_status=AccountStatus.active.value,
        )
        if existing is None:
            logger.info("Created user telegram_user_id=%s", telegram_user_id)
        return user
