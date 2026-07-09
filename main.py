"""
main.py
======================================================================
Single command-line entry point for the whole project.

Examples
--------
    python main.py generate     # (re)build the PhonePe Pulse-style dataset
    python main.py etl          # run Extract -> Transform -> Load -> Validate
    python main.py validate     # run data-quality checks only
    python main.py all          # generate + etl (full cold-start build)
    python main.py dashboard    # launch the Streamlit app

Backend is selected via the PHONEPE_DB env var (sqlite default, mysql prod).
"""

from __future__ import annotations

import argparse
import subprocess
import sys

import config
from src.utils import get_logger

log = get_logger("main", config.LOG_DIR / "main.log")


def cmd_generate() -> int:
    from dataset.generate_pulse_data import build
    build()
    return 0


def cmd_etl() -> int:
    from etl.pipeline import run_pipeline
    return 0 if run_pipeline() else 1


def cmd_validate() -> int:
    from etl.validate import run_validation
    results = run_validation()
    return 0 if all(ok for _, ok, _ in results) else 1


def cmd_dashboard() -> int:
    return subprocess.call(
        [sys.executable, "-m", "streamlit", "run", "dashboard/app.py"])


def main() -> int:
    parser = argparse.ArgumentParser(description="PhonePe Transaction Insights")
    parser.add_argument(
        "command",
        choices=["generate", "etl", "validate", "all", "dashboard"],
        help="action to run")
    args = parser.parse_args()

    log.info("Command: %s | backend=%s", args.command, config.DB_BACKEND)
    if args.command == "generate":
        return cmd_generate()
    if args.command == "etl":
        return cmd_etl()
    if args.command == "validate":
        return cmd_validate()
    if args.command == "all":
        cmd_generate()
        return cmd_etl()
    if args.command == "dashboard":
        return cmd_dashboard()
    return 1


if __name__ == "__main__":
    sys.exit(main())
