from xflexy.core.config import Settings
from xflexy.flexy.mock_provider import MockFlexyProvider
from xflexy.flexy.provider import FlexyProvider


def get_flexy_provider(settings: Settings) -> FlexyProvider:
    if settings.flexy_provider != "mock":
        raise ValueError("Only the mock Flexy provider is available in v1.")
    return MockFlexyProvider(mode=settings.mock_flexy_mode)
