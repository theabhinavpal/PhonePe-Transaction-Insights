"""
etl/extract.py
======================================================================
EXTRACT stage of the pipeline.

Responsibilities
----------------
* Walk the nested PhonePe-Pulse folder tree.
* Read every JSON file for a requested (category, level) combination.
* Attach the folder context (state / year / quarter) that Pulse encodes in
  the *path* rather than inside the file.
* Fail soft: a missing or corrupt file is logged and skipped, never fatal.

The extractor yields lightweight ``dict`` records; turning those into tidy
tables is the job of ``transform.py``. Keeping extraction dumb and generic
means new Pulse categories can be added without touching this file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import config
from src.utils import get_logger

log = get_logger(__name__, config.LOG_DIR / "etl.log")


@dataclass
class ExtractStats:
    """Counters describing an extraction run - surfaced for logging/tests."""
    files_seen: int = 0
    files_ok: int = 0
    files_missing: int = 0
    files_corrupt: int = 0
    problems: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (f"seen={self.files_seen} ok={self.files_ok} "
                f"missing={self.files_missing} corrupt={self.files_corrupt}")


def _read_json(path: Path, stats: ExtractStats) -> dict | None:
    """Read a single JSON file, recording corruption instead of raising."""
    if not path.exists():
        stats.files_missing += 1
        return None
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        stats.files_corrupt += 1
        stats.problems.append(f"{path}: {exc}")
        log.warning("Corrupt JSON skipped: %s (%s)", path, exc)
        return None


def iter_state_year_quarter(section: Path) -> Iterator[tuple[str, int, int, Path]]:
    """Yield (state, year, quarter, json_path) tuples under a section folder.

    ``section`` is the ``.../country/india/state`` directory for a given
    category+level, e.g. ``aggregated/transaction/country/india/state``.
    """
    if not section.exists():
        log.warning("Section not found: %s", section)
        return
    for state_dir in sorted(p for p in section.iterdir() if p.is_dir()):
        state = state_dir.name
        for year_dir in sorted(p for p in state_dir.iterdir() if p.is_dir()):
            try:
                year = int(year_dir.name)
            except ValueError:
                continue
            for jf in sorted(year_dir.glob("*.json")):
                try:
                    quarter = int(jf.stem)
                except ValueError:
                    continue
                yield state, year, quarter, jf


def extract_section(relative: str, stats: ExtractStats | None = None
                    ) -> Iterator[dict]:
    """Extract every file for one Pulse section.

    Parameters
    ----------
    relative : str
        Section path relative to the dataset root, ending at
        ``country/india/state`` - for example
        ``"aggregated/transaction/country/india/state"``.
    stats : ExtractStats, optional
        Reused so a caller can aggregate counters across sections.

    Yields
    ------
    dict
        ``{state, year, quarter, payload}`` where *payload* is the parsed
        ``data`` object from the Pulse envelope.
    """
    stats = stats or ExtractStats()
    section = config.DATASET_DIR / relative
    for state, year, quarter, jf in iter_state_year_quarter(section):
        stats.files_seen += 1
        raw = _read_json(jf, stats)
        if raw is None:
            continue
        payload = raw.get("data", raw)     # tolerate both wrapped & bare JSON
        if not payload:
            stats.problems.append(f"{jf}: empty data")
            continue
        stats.files_ok += 1
        yield {"state": state, "year": year, "quarter": quarter,
               "payload": payload}


if __name__ == "__main__":
    s = ExtractStats()
    n = sum(1 for _ in extract_section(
        "aggregated/transaction/country/india/state", s))
    log.info("Aggregated transaction records: %s | %s", n, s.summary())
