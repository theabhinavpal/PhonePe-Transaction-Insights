"""
tests/test_pipeline.py
======================================================================
Lightweight, dependency-free tests (run with `pytest` or plain python).
They assume the ETL has been run (`python main.py all`) against SQLite.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import read_sql          # noqa: E402
from etl.validate import run_validation    # noqa: E402
from src import analytics as A             # noqa: E402


def test_all_validation_rules_pass():
    results = run_validation()
    assert all(ok for _, ok, _ in results), "some data-quality rules failed"


def test_core_tables_have_rows():
    for t in ["agg_transaction", "agg_user", "map_transaction",
              "top_transaction_pincode", "agg_insurance"]:
        n = int(read_sql(f"SELECT COUNT(*) AS n FROM {t}")["n"].iloc[0])
        assert n > 0, f"{t} is empty"


def test_no_negative_measures():
    n = int(read_sql(
        "SELECT COUNT(*) AS n FROM agg_transaction "
        "WHERE txn_count < 0 OR txn_amount < 0")["n"].iloc[0])
    assert n == 0


def test_market_share_sums_to_100():
    sr = A.state_ranking()
    assert abs(sr["market_share_pct"].sum() - 100.0) < 1.0


def test_kpis_are_positive():
    k = A.kpi_summary()
    assert k["total_value"] > 0 and k["total_volume"] > 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn(); passed += 1
        print(f"PASS  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} tests passed")
