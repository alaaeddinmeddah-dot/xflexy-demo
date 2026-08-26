import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


def sqlite_path_from_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// database URLs are supported in v1.")
    return database_url.removeprefix(prefix)


@contextmanager
def get_connection(database_url: str) -> Iterator[sqlite3.Connection]:
    db_path = sqlite_path_from_url(database_url)
    if db_path not in (":memory:", ""):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
