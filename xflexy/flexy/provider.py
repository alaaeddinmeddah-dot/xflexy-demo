from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FlexyTopUpRequest:
    phone_number: str
    amount: int


@dataclass(frozen=True)
class FlexyTopUpResult:
    success: bool
    reference: str
    status: str
    message: str
    timed_out: bool = False


class FlexyProvider(Protocol):
    def top_up(self, request: FlexyTopUpRequest) -> FlexyTopUpResult:
        """Send a top-up request to a provider."""
