"""
etl/load.py
======================================================================
LOAD stage of the pipeline.

Writes the transformed DataFrames into the target database, then applies
indexes and analytical views. Index / view DDL is dialect-aware so the same
code path works on both SQLite (portable) and MySQL 8 (production).
"""

from __future__ import annotations

import config
from src.database import get_engine, write_dataframe
from src.utils import get_logger
from sqlalchemy import text

log = get_logger(__name__, config.LOG_DIR / "etl.log")


# Index definitions kept dialect-neutral (plain CREATE INDEX works on both).
INDEX_DDL = [
    "CREATE INDEX IF NOT EXISTS ix_aggtxn_state ON agg_transaction(state)",
    "CREATE INDEX IF NOT EXISTS ix_aggtxn_yq ON agg_transaction(year, quarter)",
    "CREATE INDEX IF NOT EXISTS ix_aggtxn_cat ON agg_transaction(category)",
    "CREATE INDEX IF NOT EXISTS ix_agguser_state ON agg_user(state)",
    "CREATE INDEX IF NOT EXISTS ix_aggins_state ON agg_insurance(state)",
    "CREATE INDEX IF NOT EXISTS ix_maptxn_state ON map_transaction(state)",
    "CREATE INDEX IF NOT EXISTS ix_toppin_state ON top_transaction_pincode(state)",
]

# Analytical views - written in ANSI SQL that both SQLite and MySQL accept.
VIEW_DDL = {
    "vw_state_txn_summary": """
        CREATE VIEW vw_state_txn_summary AS
        SELECT t.state, s.state_display, s.region, t.year, t.quarter,
               SUM(t.txn_count)  AS txn_count,
               SUM(t.txn_amount) AS txn_amount
        FROM agg_transaction t
        JOIN dim_state s ON s.state = t.state
        GROUP BY t.state, s.state_display, s.region, t.year, t.quarter
    """,
    "vw_national_quarter": """
        CREATE VIEW vw_national_quarter AS
        SELECT year, quarter,
               SUM(txn_count)  AS txn_count,
               SUM(txn_amount) AS txn_amount
        FROM agg_transaction
        GROUP BY year, quarter
    """,
    "vw_category_share": """
        CREATE VIEW vw_category_share AS
        SELECT category,
               SUM(txn_count)  AS txn_count,
               SUM(txn_amount) AS txn_amount
        FROM agg_transaction
        GROUP BY category
    """,
}


def load_tables(tables: dict) -> dict[str, int]:
    """Write all DataFrames and return a {table: rows} report."""
    log.info("LOAD: writing %d tables to %s", len(tables), config.DB_BACKEND)
    counts = {name: write_dataframe(df, name) for name, df in tables.items()}
    return counts


def apply_indexes_and_views() -> None:
    """Create indexes and (re)create analytical views."""
    engine = get_engine()
    with engine.begin() as conn:
        for ddl in INDEX_DDL:
            try:
                conn.execute(text(ddl))
            except Exception as exc:                      # pragma: no cover
                log.warning("Index skipped: %s (%s)", ddl.split()[5], exc)
        for name, ddl in VIEW_DDL.items():
            conn.execute(text(f"DROP VIEW IF EXISTS {name}"))
            conn.execute(text(ddl))
            log.info("View ready: %s", name)


if __name__ == "__main__":
    from etl.transform import transform_all
    counts = load_tables(transform_all())
    apply_indexes_and_views()
    log.info("LOAD complete: %s", counts)
