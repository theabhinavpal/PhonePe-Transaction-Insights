"""
src/queries.py
======================================================================
A registry of parameterised, named SQL queries used by the analytics
layer and the Streamlit dashboard. Keeping SQL in one place (rather than
scattered as f-strings across pages) makes queries testable and reusable.

All SQL here is portable across SQLite and MySQL 8.
"""

from __future__ import annotations

# --------------------------------------------------------------------- #
# Filter fragment helper
# --------------------------------------------------------------------- #
def period_filter(year: int | None, quarter: int | None,
                  alias: str = "") -> str:
    """Build an optional WHERE fragment for year/quarter filters."""
    a = f"{alias}." if alias else ""
    clauses = []
    if year:
        clauses.append(f"{a}year = :year")
    if quarter:
        clauses.append(f"{a}quarter = :quarter")
    return (" WHERE " + " AND ".join(clauses)) if clauses else ""


QUERIES: dict[str, str] = {
    # --- KPI scalars -------------------------------------------------
    "kpi_totals": """
        SELECT SUM(txn_amount) AS total_value,
               SUM(txn_count)  AS total_volume,
               SUM(txn_amount) * 1.0 / SUM(txn_count) AS avg_ticket
        FROM agg_transaction {flt}
    """,
    "kpi_users_latest": """
        SELECT SUM(registered_users) AS registered_users,
               SUM(app_opens) AS app_opens
        FROM agg_user
        WHERE year = (SELECT MAX(year) FROM agg_user)
          AND quarter = (SELECT MAX(quarter) FROM agg_user
                         WHERE year = (SELECT MAX(year) FROM agg_user))
    """,
    "kpi_insurance": """
        SELECT SUM(policy_count) AS policies,
               SUM(premium_amount) AS premium
        FROM agg_insurance {flt}
    """,

    # --- state / region ---------------------------------------------
    "state_ranking": """
        SELECT s.state_display AS state, s.region,
               SUM(t.txn_amount) AS txn_amount,
               SUM(t.txn_count)  AS txn_count
        FROM agg_transaction t
        JOIN dim_state s ON s.state = t.state {flt}
        GROUP BY s.state_display, s.region
        ORDER BY txn_amount DESC
    """,
    "region_share": """
        SELECT s.region,
               SUM(t.txn_amount) AS txn_amount,
               SUM(t.txn_count)  AS txn_count
        FROM agg_transaction t
        JOIN dim_state s ON s.state = t.state {flt}
        GROUP BY s.region ORDER BY txn_amount DESC
    """,

    # --- category ----------------------------------------------------
    "category_breakdown": """
        SELECT category,
               SUM(txn_amount) AS txn_amount,
               SUM(txn_count)  AS txn_count
        FROM agg_transaction {flt}
        GROUP BY category ORDER BY txn_amount DESC
    """,
    "category_by_year": """
        SELECT year, category, SUM(txn_amount) AS txn_amount
        FROM agg_transaction GROUP BY year, category ORDER BY year
    """,

    # --- trends ------------------------------------------------------
    "national_quarter_trend": """
        SELECT year, quarter,
               SUM(txn_amount) AS txn_amount,
               SUM(txn_count)  AS txn_count
        FROM agg_transaction GROUP BY year, quarter ORDER BY year, quarter
    """,
    "yearly_trend": """
        SELECT year, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
        FROM agg_transaction GROUP BY year ORDER BY year
    """,

    # --- districts / pincodes ---------------------------------------
    "top_districts": """
        SELECT district, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
        FROM map_transaction {flt}
        GROUP BY district ORDER BY txn_amount DESC LIMIT :limit
    """,
    "top_pincodes": """
        SELECT pincode, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
        FROM top_transaction_pincode {flt}
        GROUP BY pincode ORDER BY txn_amount DESC LIMIT :limit
    """,

    # --- users -------------------------------------------------------
    "device_share": """
        SELECT brand, SUM(user_count) AS users
        FROM agg_user_device
        WHERE year = (SELECT MAX(year) FROM agg_user_device)
        GROUP BY brand ORDER BY users DESC
    """,
    "top_states_users": """
        SELECT s.state_display AS state, SUM(u.registered_users) AS registered_users
        FROM agg_user u JOIN dim_state s ON s.state = u.state
        WHERE u.year = (SELECT MAX(year) FROM agg_user)
        GROUP BY s.state_display ORDER BY registered_users DESC LIMIT :limit
    """,

    # --- insurance ---------------------------------------------------
    "insurance_by_state": """
        SELECT s.state_display AS state, s.region,
               SUM(i.premium_amount) AS premium,
               SUM(i.policy_count)   AS policies
        FROM agg_insurance i JOIN dim_state s ON s.state = i.state {flt}
        GROUP BY s.state_display, s.region ORDER BY premium DESC
    """,
}


def get(name: str, year: int | None = None, quarter: int | None = None,
        alias: str = "") -> str:
    """Return a named query with the {flt} placeholder resolved."""
    template = QUERIES[name]
    flt = period_filter(year, quarter, alias) if "{flt}" in template else ""
    return template.format(flt=flt)
