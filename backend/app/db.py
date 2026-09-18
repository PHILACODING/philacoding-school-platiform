from collections.abc import Generator

import psycopg
from psycopg.rows import dict_row

from .settings import get_settings


def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Open one short-lived transaction per request and always close it."""
    connection = psycopg.connect(get_settings().database_url, row_factory=dict_row)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
