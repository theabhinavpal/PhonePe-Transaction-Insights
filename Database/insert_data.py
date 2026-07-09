"""
database/insert_data.py
======================================================================
Standalone loader that (re)creates the schema and inserts the transformed
data into the *configured* backend. It is a thin convenience wrapper around
the ETL transform step plus the SQL DDL files, and is handy when you want to
(re)load the database without running the full ``etl.pipeline``.

Usage
-----
    # SQLite (default, portable)
    python -m database.insert_data

    # MySQL 8 (production)
    PHONEPE_DB=mysql MYSQL_USER=root MYSQL_PASSWORD=*** \
        python -m database.insert_data

For MySQL you must first create the database and schema, e.g.:
    mysql -u root -p < database/database_schema.sql
    mysql -u root -p phonepe_insights < database/indexes.sql
    mysql -u root -p phonepe_insights < database/views.sql
"""

from __future__ import annotations

from pathlib import Path

import config
from etl.load import apply_indexes_and_views, load_tables
from etl.transform import transform_all
from src.database import execute_script, get_engine
from src.utils import get_logger

log = get_logger(__name__, config.LOG_DIR / "load.log")


def ensure_schema() -> None:
    """Create tables from the portable DDL if they do not yet exist."""
    ddl = (Path(config.DATABASE_DIR) / "create_tables.sql").read_text(encoding="utf-8")
    # strip the leading USE statement (not valid on SQLite)
    stmts = [s for s in ddl.split(";") if s.strip() and not s.strip().upper().startswith("USE")]
    with get_engine().begin() as conn:
        from sqlalchemy import text
        for s in stmts:
            conn.execute(text(s))
    log.info("Schema ensured for backend=%s", config.DB_BACKEND)


def main() -> None:
    log.info("Insert data: backend=%s", config.DB_BACKEND)
    ensure_schema()
    counts = load_tables(transform_all())        # replace-loads every table
    apply_indexes_and_views()
    log.info("Load complete: %s rows across %s tables",
             sum(counts.values()), len(counts))


if __name__ == "__main__":
    main()
