"""
src/analytics.py
======================================================================
Analytics layer: thin, well-named functions that return tidy DataFrames
for the dashboard and reports. Each function wraps a query from
``src.queries`` (or a small bespoke query) and adds derived columns such
as market share, growth % and cumulative totals.

Design: functions are pure (DB in, DataFrame out) and cache-friendly so
the Streamlit layer can wrap them with ``st.cache_data``.
"""

from __future__ import annotations

import pandas as pd

from src import queries as Q
from src.database import read_sql
from src.utils import get_logger

log = get_logger(__name__)


# --------------------------------------------------------------------- #
# KPI scalars
# --------------------------------------------------------------------- #
def kpi_summary(year: int | None = None, quarter: int | None = None) -> dict:
    """Return the headline KPI dictionary for the executive cards."""
    params = {k: v for k, v in {"year": year, "quarter": quarter}.items() if v}
    totals = read_sql(Q.get("kpi_totals", year, quarter), params).iloc[0]
    users = read_sql(Q.get("kpi_users_latest")).iloc[0]
    ins = read_sql(Q.get("kpi_insurance", year, quarter), params).iloc[0]
    return {
        "total_value": float(totals["total_value"] or 0),
        "total_volume": int(totals["total_volume"] or 0),
        "avg_ticket": float(totals["avg_ticket"] or 0),
        "registered_users": int(users["registered_users"] or 0),
        "app_opens": int(users["app_opens"] or 0),
        "insurance_premium": float(ins["premium"] or 0),
        "insurance_policies": int(ins["policies"] or 0),
    }


# --------------------------------------------------------------------- #
# State / region
# --------------------------------------------------------------------- #
def state_ranking(year: int | None = None, quarter: int | None = None) -> pd.DataFrame:
    """State leaderboard with market share and rank."""
    params = {k: v for k, v in {"year": year, "quarter": quarter}.items() if v}
    df = read_sql(Q.get("state_ranking", year, quarter, alias="t"), params)
    if df.empty:
        return df
    total = df["txn_amount"].sum()
    df["market_share_pct"] = (100 * df["txn_amount"] / total).round(2)
    df["rank"] = df["txn_amount"].rank(ascending=False, method="min").astype(int)
    df["avg_ticket"] = (df["txn_amount"] / df["txn_count"]).round(2)
    return df


def region_share(year: int | None = None, quarter: int | None = None) -> pd.DataFrame:
    params = {k: v for k, v in {"year": year, "quarter": quarter}.items() if v}
    df = read_sql(Q.get("region_share", year, quarter, alias="t"), params)
    if not df.empty:
        df["pct_share"] = (100 * df["txn_amount"] / df["txn_amount"].sum()).round(2)
    return df


# --------------------------------------------------------------------- #
# Category
# --------------------------------------------------------------------- #
def category_breakdown(year: int | None = None, quarter: int | None = None) -> pd.DataFrame:
    params = {k: v for k, v in {"year": year, "quarter": quarter}.items() if v}
    df = read_sql(Q.get("category_breakdown", year, quarter), params)
    if not df.empty:
        df["pct_value"] = (100 * df["txn_amount"] / df["txn_amount"].sum()).round(2)
        df["avg_ticket"] = (df["txn_amount"] / df["txn_count"]).round(2)
    return df


def category_by_year() -> pd.DataFrame:
    return read_sql(Q.get("category_by_year"))


# --------------------------------------------------------------------- #
# Trends
# --------------------------------------------------------------------- #
def national_trend() -> pd.DataFrame:
    """Quarter-over-quarter national trend with QoQ growth and 4Q MA."""
    df = read_sql(Q.get("national_quarter_trend"))
    if df.empty:
        return df
    df["period"] = "Q" + df["quarter"].astype(str) + " " + df["year"].astype(str)
    df["qoq_pct"] = (df["txn_amount"].pct_change() * 100).round(2)
    df["ma_4q"] = df["txn_amount"].rolling(4, min_periods=1).mean()
    df["running_total"] = df["txn_amount"].cumsum()
    return df


def yoy_growth() -> pd.DataFrame:
    """Yearly value with YoY growth %."""
    df = read_sql(Q.get("yearly_trend"))
    if df.empty:
        return df
    df["yoy_pct"] = (df["txn_amount"].pct_change() * 100).round(2)
    return df


# --------------------------------------------------------------------- #
# Districts / pincodes
# --------------------------------------------------------------------- #
def top_districts(limit: int = 15, year: int | None = None,
                  quarter: int | None = None) -> pd.DataFrame:
    params = {"limit": limit}
    params.update({k: v for k, v in {"year": year, "quarter": quarter}.items() if v})
    return read_sql(Q.get("top_districts", year, quarter), params)


def top_pincodes(limit: int = 15, year: int | None = None,
                 quarter: int | None = None) -> pd.DataFrame:
    params = {"limit": limit}
    params.update({k: v for k, v in {"year": year, "quarter": quarter}.items() if v})
    return read_sql(Q.get("top_pincodes", year, quarter), params)


# --------------------------------------------------------------------- #
# Users / insurance
# --------------------------------------------------------------------- #
def device_share() -> pd.DataFrame:
    df = read_sql(Q.get("device_share"))
    if not df.empty:
        df["pct"] = (100 * df["users"] / df["users"].sum()).round(2)
    return df


def top_states_by_users(limit: int = 10) -> pd.DataFrame:
    return read_sql(Q.get("top_states_users"), {"limit": limit})


def insurance_by_state(year: int | None = None, quarter: int | None = None) -> pd.DataFrame:
    params = {k: v for k, v in {"year": year, "quarter": quarter}.items() if v}
    return read_sql(Q.get("insurance_by_state", year, quarter, alias="i"), params)


# --------------------------------------------------------------------- #
# Filter option helpers
# --------------------------------------------------------------------- #
def available_years() -> list[int]:
    return read_sql("SELECT DISTINCT year FROM agg_transaction ORDER BY year")["year"].tolist()


def available_quarters() -> list[int]:
    return read_sql("SELECT DISTINCT quarter FROM agg_transaction ORDER BY quarter")["quarter"].tolist()
