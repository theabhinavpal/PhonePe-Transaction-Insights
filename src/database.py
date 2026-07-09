"""
src/database.py
======================================================================
Thin database access layer built on SQLAlchemy so the rest of the code is
backend-agnostic (SQLite for local/dev, MySQL 8 for production). Exposes a
cached engine, a ``read_sql`` helper and a ``write_dataframe`` helper.
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

import config
from src.utils import get_logger

log = get_logger(__name__, config.LOG_DIR / "database.log")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Return a process-wide cached SQLAlchemy engine for the active backend."""
    url = config.get_database_url()
    log.info("Creating engine for backend=%s", config.DB_BACKEND)
    kwargs = {"pool_pre_ping": True}
    if config.DB_BACKEND == "sqlite":
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def read_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    """Execute a SELECT and return the result as a DataFrame."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def write_dataframe(df: pd.DataFrame, table: str,
                    if_exists: str = "replace") -> int:
    """Write a DataFrame to a table; returns the number of rows written."""
    if df is None or df.empty:
        log.warning("Skipping empty table: %s", table)
        return 0
    with get_engine().begin() as conn:
        df.to_sql(table, conn, if_exists=if_exists, index=False)
    log.info("Wrote %6d rows -> %s", len(df), table)
    return len(df)


def execute_script(sql: str) -> None:
    """Execute a multi-statement SQL script (semicolon separated)."""
    with get_engine().begin() as conn:
        for stmt in filter(str.strip, sql.split(";")):
            conn.execute(text(stmt))
