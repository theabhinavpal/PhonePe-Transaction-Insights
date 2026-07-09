"""
etl/transform.py
======================================================================
TRANSFORM stage of the pipeline.

Turns the raw records emitted by ``extract.py`` into a set of tidy,
analysis-ready pandas DataFrames - one per fact/dimension table. Every
transformation is deliberate and documented:

* nested ``paymentInstruments`` / ``metric`` arrays are flattened;
* the folder-encoded (state, year, quarter) context becomes real columns;
* a ``dim_state`` (region/zone) and ``dim_date`` (quarter labels) are built
  from ``config`` so the star schema has proper dimensions;
* district / pincode strings are trimmed and de-suffixed for consistency;
* numeric types are coerced and negative / null values are dropped.

Returned as a ``dict[str, DataFrame]`` keyed by target table name.
"""

from __future__ import annotations

import pandas as pd

import config
from etl.extract import ExtractStats, extract_section
from src.utils import get_logger

log = get_logger(__name__, config.LOG_DIR / "etl.log")


# --------------------------------------------------------------------- #
# Dimension builders
# --------------------------------------------------------------------- #
def build_dim_state() -> pd.DataFrame:
    """State dimension with display name, region and zone."""
    rows = [{"state": s, "state_display": d, "region": r, "zone": z}
            for s, (d, r, z) in config.STATE_META.items()]
    return pd.DataFrame(rows)


def build_dim_date(years: list[int], quarters: list[int]) -> pd.DataFrame:
    """Date dimension at (year, quarter) grain."""
    rows = []
    for y in years:
        for q in quarters:
            rows.append({
                "year": y, "quarter": q,
                "quarter_label": f"Q{q} {y}",
                "period_months": config.QUARTER_MONTHS[q],
                "period_index": (y - min(years)) * 4 + (q - 1),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- #
# Fact builders
# --------------------------------------------------------------------- #
def _clean_district(name: str) -> str:
    return name.replace(" district", "").strip().title()


def build_agg_transaction(stats: ExtractStats) -> pd.DataFrame:
    rows = []
    for rec in extract_section("aggregated/transaction/country/india/state", stats):
        for item in rec["payload"].get("transactionData", []):
            inst = (item.get("paymentInstruments") or [{}])[0]
            rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "category": item.get("name"),
                "txn_count": inst.get("count", 0),
                "txn_amount": inst.get("amount", 0.0),
            })
    return pd.DataFrame(rows)


def build_agg_user(stats: ExtractStats) -> tuple[pd.DataFrame, pd.DataFrame]:
    users, devices = [], []
    for rec in extract_section("aggregated/user/country/india/state", stats):
        p = rec["payload"]
        agg = p.get("aggregated", {})
        users.append({
            "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
            "registered_users": agg.get("registeredUsers", 0),
            "app_opens": agg.get("appOpens", 0),
        })
        for d in p.get("usersByDevice") or []:
            devices.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "brand": d.get("brand"), "user_count": d.get("count", 0),
                "percentage": d.get("percentage", 0.0),
            })
    return pd.DataFrame(users), pd.DataFrame(devices)


def build_agg_insurance(stats: ExtractStats) -> pd.DataFrame:
    rows = []
    for rec in extract_section("aggregated/insurance/country/india/state", stats):
        for item in rec["payload"].get("transactionData", []):
            inst = (item.get("paymentInstruments") or [{}])[0]
            rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "policy_count": inst.get("count", 0),
                "premium_amount": inst.get("amount", 0.0),
            })
    return pd.DataFrame(rows)


def build_map_transaction(stats: ExtractStats) -> pd.DataFrame:
    rows = []
    for rec in extract_section("map/transaction/hover/country/india/state", stats):
        for item in rec["payload"].get("hoverDataList", []):
            m = (item.get("metric") or [{}])[0]
            rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "district": _clean_district(item.get("name", "")),
                "txn_count": m.get("count", 0), "txn_amount": m.get("amount", 0.0),
            })
    return pd.DataFrame(rows)


def build_map_user(stats: ExtractStats) -> pd.DataFrame:
    rows = []
    for rec in extract_section("map/user/hover/country/india/state", stats):
        hover = rec["payload"].get("hoverData", {})
        for name, vals in hover.items():
            rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "district": _clean_district(name),
                "registered_users": vals.get("registeredUsers", 0),
                "app_opens": vals.get("appOpens", 0),
            })
    return pd.DataFrame(rows)


def build_map_insurance(stats: ExtractStats) -> pd.DataFrame:
    rows = []
    for rec in extract_section("map/insurance/hover/country/india/state", stats):
        for item in rec["payload"].get("hoverDataList", []):
            m = (item.get("metric") or [{}])[0]
            rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "district": _clean_district(item.get("name", "")),
                "policy_count": m.get("count", 0), "premium_amount": m.get("amount", 0.0),
            })
    return pd.DataFrame(rows)


def build_top_transaction(stats: ExtractStats
                          ) -> tuple[pd.DataFrame, pd.DataFrame]:
    dist_rows, pin_rows = [], []
    for rec in extract_section("top/transaction/country/india/state", stats):
        p = rec["payload"]
        for d in p.get("districts", []):
            m = d.get("metric", {})
            dist_rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "district": _clean_district(d.get("entityName", "")),
                "txn_count": m.get("count", 0), "txn_amount": m.get("amount", 0.0),
            })
        for pn in p.get("pincodes", []):
            m = pn.get("metric", {})
            pin_rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "pincode": str(pn.get("entityName", "")),
                "txn_count": m.get("count", 0), "txn_amount": m.get("amount", 0.0),
            })
    return pd.DataFrame(dist_rows), pd.DataFrame(pin_rows)


def build_top_user(stats: ExtractStats) -> pd.DataFrame:
    rows = []
    for rec in extract_section("top/user/country/india/state", stats):
        for pn in rec["payload"].get("pincodes", []):
            rows.append({
                "state": rec["state"], "year": rec["year"], "quarter": rec["quarter"],
                "pincode": str(pn.get("name", "")),
                "registered_users": pn.get("registeredUsers", 0),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- #
# Cleaning
# --------------------------------------------------------------------- #
def _clean_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Coerce numeric columns, drop nulls and negative values."""
    if df.empty:
        return df
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=cols)
    for c in cols:
        df = df[df[c] >= 0]
    return df.reset_index(drop=True)


def transform_all() -> dict[str, pd.DataFrame]:
    """Run every builder and return {table_name: DataFrame}."""
    stats = ExtractStats()
    log.info("TRANSFORM: extracting and normalising all sections ...")

    agg_txn = _clean_numeric(build_agg_transaction(stats), ["txn_count", "txn_amount"])
    agg_user, agg_dev = build_agg_user(stats)
    agg_user = _clean_numeric(agg_user, ["registered_users", "app_opens"])
    agg_dev = _clean_numeric(agg_dev, ["user_count"])
    agg_ins = _clean_numeric(build_agg_insurance(stats), ["policy_count", "premium_amount"])
    map_txn = _clean_numeric(build_map_transaction(stats), ["txn_count", "txn_amount"])
    map_user = _clean_numeric(build_map_user(stats), ["registered_users", "app_opens"])
    map_ins = _clean_numeric(build_map_insurance(stats), ["policy_count", "premium_amount"])
    top_dist, top_pin = build_top_transaction(stats)
    top_dist = _clean_numeric(top_dist, ["txn_count", "txn_amount"])
    top_pin = _clean_numeric(top_pin, ["txn_count", "txn_amount"])
    top_user = _clean_numeric(build_top_user(stats), ["registered_users"])

    years = sorted(agg_txn["year"].unique().tolist())
    quarters = sorted(agg_txn["quarter"].unique().tolist())

    tables = {
        "dim_state": build_dim_state(),
        "dim_date": build_dim_date(years, quarters),
        "agg_transaction": agg_txn,
        "agg_user": agg_user,
        "agg_user_device": agg_dev,
        "agg_insurance": agg_ins,
        "map_transaction": map_txn,
        "map_user": map_user,
        "map_insurance": map_ins,
        "top_transaction_district": top_dist,
        "top_transaction_pincode": top_pin,
        "top_user_pincode": top_user,
    }
    log.info("TRANSFORM complete | extraction %s", stats.summary())
    for name, df in tables.items():
        log.info("  %-26s -> %6d rows", name, len(df))
    return tables


if __name__ == "__main__":
    transform_all()
