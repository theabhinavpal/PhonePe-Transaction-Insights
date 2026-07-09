"""
src/utils.py
======================================================================
Small, dependency-light helpers shared across the ETL, analytics and
dashboard layers: structured logging, Indian-number formatting (lakh /
crore) and a couple of light validation utilities.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# --------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------- #
def get_logger(name: str, log_file: str | Path | None = None,
               level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger that writes to stdout and optionally a file.

    Parameters
    ----------
    name : str
        Logger name (usually ``__name__``).
    log_file : str | Path | None
        Optional path to also persist log records to disk.
    level : int
        Logging level, defaults to ``logging.INFO``.
    """
    logger = logging.getLogger(name)
    if logger.handlers:              # avoid duplicate handlers on re-import
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


# --------------------------------------------------------------------- #
# Number formatting
# --------------------------------------------------------------------- #
def inr_crore(value: float) -> str:
    """Format a raw INR value as crores (1 crore = 10,000,000)."""
    return f"Rs {value / 1e7:,.2f} Cr"


def inr_compact(value: float) -> str:
    """Human-friendly INR scale: Cr / Lakh."""
    if abs(value) >= 1e7:
        return f"Rs {value / 1e7:,.2f} Cr"
    if abs(value) >= 1e5:
        return f"Rs {value / 1e5:,.2f} L"
    return f"Rs {value:,.0f}"


def human_count(value: float) -> str:
    """Compact count formatting using Cr / L / K suffixes."""
    if abs(value) >= 1e7:
        return f"{value / 1e7:,.2f} Cr"
    if abs(value) >= 1e5:
        return f"{value / 1e5:,.2f} L"
    if abs(value) >= 1e3:
        return f"{value / 1e3:,.1f} K"
    return f"{value:,.0f}"


def pct(numerator: float, denominator: float) -> float:
    """Safe percentage; returns 0.0 when the denominator is zero."""
    return 0.0 if not denominator else round(100.0 * numerator / denominator, 2)
