import pytest

from xflexy.core.config import Settings
from xflexy.database.connection import get_connection
from xflexy.database.schema import initialize_schema
from xflexy.flexy.mock_provider import MockFlexyProvider


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite:///:memory:",
        admin_api_key="test-admin-key",
        min_flexy_amount=50,
        max_flexy_amount=50000,
        mock_flexy_mode="success",
    )


@pytest.fixture
def initialized_connection(settings: Settings):
    with get_connection(settings.database_url) as connection:
        initialize_schema(connection)
        yield connection


@pytest.fixture
def mock_flexy_provider() -> MockFlexyProvider:
    return MockFlexyProvider(mode="success")
