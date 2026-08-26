from uuid import uuid4

from xflexy.flexy.provider import FlexyProvider, FlexyTopUpRequest, FlexyTopUpResult


class MockFlexyProvider(FlexyProvider):
    def __init__(self, mode: str = "success") -> None:
        self.mode = mode

    def top_up(self, request: FlexyTopUpRequest) -> FlexyTopUpResult:
        if request.amount <= 0:
            return FlexyTopUpResult(
                success=False,
                reference=f"mock-failed-{uuid4().hex[:10]}",
                status="failed",
                message="Amount must be greater than zero.",
            )
        if self.mode == "failure":
            return FlexyTopUpResult(
                success=False,
                reference=f"mock-failed-{uuid4().hex[:10]}",
                status="failed",
                message="Mock Flexy top-up failed.",
            )
        if self.mode == "timeout":
            return FlexyTopUpResult(
                success=False,
                reference=f"mock-timeout-{uuid4().hex[:10]}",
                status="timeout",
                message="Mock Flexy top-up timed out.",
                timed_out=True,
            )

        return FlexyTopUpResult(
            success=True,
            reference=f"mock-{uuid4().hex[:10]}",
            status="completed",
            message="Mock Flexy top-up completed.",
        )
