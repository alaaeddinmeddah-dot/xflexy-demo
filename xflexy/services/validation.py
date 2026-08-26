import re

from xflexy.core.config import Settings


def validate_phone_number(phone_number: str, settings: Settings) -> None:
    if not re.fullmatch(settings.phone_regex, phone_number):
        raise ValueError("Invalid phone number format.")


def validate_amount(amount: int, settings: Settings) -> None:
    if amount < settings.min_flexy_amount or amount > settings.max_flexy_amount:
        raise ValueError(
            f"Amount must be between {settings.min_flexy_amount} and {settings.max_flexy_amount}."
        )
