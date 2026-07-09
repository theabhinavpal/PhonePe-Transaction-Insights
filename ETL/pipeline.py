"""
etl/pipeline.py
======================================================================
End-to-end orchestrator:

    Extract -> Transform -> Load -> Index/View -> Validate

Run with ``python -m etl.pipeline`` (or via ``main.py``). Emits a concise
run report and a non-zero exit code if any validation rule fails, which
makes it CI-friendly.
"""

from __future__ import annotations

import sys
import time

import config
from etl.load import apply_indexes_and_views, load_tables
from etl.transform import transform_all
from etl.validate import run_validation
from src.utils import get_logger

log = get_logger(__name__, config.LOG_DIR / "etl.log")


def run_pipeline() -> bool:
    """Execute the full ETL pipeline. Returns True when validation passes."""
    t0 = time.time()
    log.info("=" * 68)
    log.info("PhonePe ETL pipeline starting | backend=%s", config.DB_BACKEND)
    log.info("=" * 68)

    tables = transform_all()
    counts = load_tables(tables)
    apply_indexes_and_views()
    results = run_validation()

    ok = all(passed for _, passed, _ in results)
    dt = time.time() - t0
    total_rows = sum(counts.values())
    log.info("-" * 68)
    log.info("Pipeline finished in %.1fs | %d rows across %d tables | %s",
             dt, total_rows, len(counts),
             "VALIDATION PASSED" if ok else "VALIDATION FAILED")
    log.info("-" * 68)
    return ok


if __name__ == "__main__":
    sys.exit(0 if run_pipeline() else 1)
