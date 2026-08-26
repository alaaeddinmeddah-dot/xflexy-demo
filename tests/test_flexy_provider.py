from xflexy.flexy.mock_provider import MockFlexyProvider
from xflexy.flexy.provider import FlexyTopUpRequest


def test_mock_provider_success() -> None:
    provider = MockFlexyProvider()

    result = provider.top_up(FlexyTopUpRequest(phone_number="0555123456", amount=100))

    assert result.success is True
    assert result.status == "completed"
    assert result.reference.startswith("mock-")


def test_mock_provider_rejects_invalid_amount() -> None:
    provider = MockFlexyProvider()

    result = provider.top_up(FlexyTopUpRequest(phone_number="0555123456", amount=0))

    assert result.success is False
    assert result.status == "failed"
