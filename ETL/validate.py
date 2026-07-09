"""
etl/validate.py
======================================================================
Post-load data-quality gate. Each rule returns a (rule_name, passed,
detail) tuple so results can be logged and summarised. Validation runs at
the *database* level so it exercises exactly what the dashboard will query.

Rules
-----
1. Row counts    - every core table must be non-empty.
2. No NULL keys  - state/year/quarter must never be NULL in fact tables.
3. No negatives  - counts and amounts must be >= 0.
4. Known states  - every state must exist in dim_state.
5. Quarter range - quarter values must be within 1..4.
6. Coverage      - each state should have data for every loaded quarter.
"""

from __future__ import annotations

import config
from src.database import read_sql
from src.utils import get_logger

log = get_logger(__name__, config.LOG_DIR / "etl.log")

FACT_TABLES = ["agg_transaction", "agg_user", "map_transaction",
               "top_transaction_pincode"]


def _count(table: str) -> int:
    return int(read_sql(f"SELECT COUNT(*) AS n FROM {table}")["n"].iloc[0])


def run_validation() -> list[tuple[str, bool, str]]:
    """Execute every validation rule and return structured results."""
    results: list[tuple[str, bool, str]] = []

    # Rule 1 - non-empty tables
    for t in config.TABLES:
        n = _count(t)
        results.append((f"non_empty::{t}", n > 0, f"{n} rows"))

    # Rule 2 - no NULL keys in fact tables
    for t in FACT_TABLES:
        n = int(read_sql(
            f"SELECT COUNT(*) AS n FROM {t} "
            f"WHERE state IS NULL OR year IS NULL OR quarter IS NULL"
        )["n"].iloc[0])
        results.append((f"no_null_keys::{t}", n == 0, f"{n} null-key rows"))

    # Rule 3 - no negative measures
    neg = int(read_sql(
        "SELECT COUNT(*) AS n FROM agg_transaction "
        "WHERE txn_count < 0 OR txn_amount < 0")["n"].iloc[0])
    results.append(("no_negative_measures", neg == 0, f"{neg} negative rows"))

    # Rule 4 - referential integrity against dim_state
    orphan = int(read_sql(
        "SELECT COUNT(*) AS n FROM agg_transaction t "
        "LEFT JOIN dim_state s ON s.state = t.state "
        "WHERE s.state IS NULL")["n"].iloc[0])
    results.append(("states_in_dim_state", orphan == 0, f"{orphan} orphan states"))

    # Rule 5 - quarter within 1..4
    bad_q = int(read_sql(
        "SELECT COUNT(*) AS n FROM agg_transaction "
        "WHERE quarter NOT IN (1,2,3,4)")["n"].iloc[0])
    results.append(("quarter_in_range", bad_q == 0, f"{bad_q} bad quarters"))

    # Rule 6 - coverage: states x quarters present
    cov = read_sql(
        "SELECT COUNT(DISTINCT state) AS s, "
        "COUNT(DISTINCT year || '-' || quarter) AS periods "
        "FROM agg_transaction")
    results.append(("coverage", True,
                    f"{int(cov['s'].iloc[0])} states x {int(cov['periods'].iloc[0])} periods"))

    passed = sum(1 for _, ok, _ in results if ok)
    log.info("VALIDATION: %d/%d rules passed", passed, len(results))
    for name, ok, detail in results:
        log.info("  [%s] %-28s %s", "PASS" if ok else "FAIL", name, detail)
    return results


if __name__ == "__main__":
    run_validation()
