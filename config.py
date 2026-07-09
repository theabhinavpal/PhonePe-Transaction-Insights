"""
config.py
======================================================================
Single source of truth for paths, database connection settings and a few
project-wide constants. Everything reads its configuration from here so
there are no magic strings scattered across the codebase.

Database selection
------------------
The project targets MySQL 8 in production (as required by the brief) but
ships with a portable SQLite fallback so the full ETL + analytics stack
runs on any machine with zero server setup - which is exactly how the
numbers quoted in the docs were produced and verified.

Set the DB backend with the ``PHONEPE_DB`` environment variable:
    PHONEPE_DB=sqlite   (default - portable, file based)
    PHONEPE_DB=mysql    (production - reads MYSQL_* env vars)
"""

from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset" / "pulse" / "data"
DATABASE_DIR = BASE_DIR / "database"
REPORTS_DIR = BASE_DIR / "reports"
IMAGES_DIR = BASE_DIR / "images"
LOG_DIR = BASE_DIR / "logs"
SQLITE_PATH = BASE_DIR / "database" / "phonepe.db"

for _d in (LOG_DIR, REPORTS_DIR, IMAGES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------- #
# Database
# --------------------------------------------------------------------- #
DB_BACKEND = os.getenv("PHONEPE_DB", "sqlite").lower()

MYSQL = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "phonepe_insights"),
}


def get_database_url() -> str:
    """Return a SQLAlchemy connection URL for the selected backend."""
    if DB_BACKEND == "mysql":
        return (
            f"mysql+pymysql://{MYSQL['user']}:{MYSQL['password']}"
            f"@{MYSQL['host']}:{MYSQL['port']}/{MYSQL['database']}?charset=utf8mb4"
        )
    return f"sqlite:///{SQLITE_PATH}"


# --------------------------------------------------------------------- #
# Domain constants
# --------------------------------------------------------------------- #
QUARTER_MONTHS = {1: "Jan-Mar", 2: "Apr-Jun", 3: "Jul-Sep", 4: "Oct-Dec"}

# State -> (display name, region, zone). Used to build dim_state and to power
# regional roll-ups in the dashboard and SQL views.
STATE_META = {
    "andaman-&-nicobar-islands": ("Andaman & Nicobar", "East", "Islands"),
    "andhra-pradesh": ("Andhra Pradesh", "South", "Southern"),
    "arunachal-pradesh": ("Arunachal Pradesh", "Northeast", "Northeastern"),
    "assam": ("Assam", "Northeast", "Northeastern"),
    "bihar": ("Bihar", "East", "Eastern"),
    "chandigarh": ("Chandigarh", "North", "Northern"),
    "chhattisgarh": ("Chhattisgarh", "Central", "Central"),
    "dadra-&-nagar-haveli-&-daman-&-diu": ("Dadra & Nagar Haveli and Daman & Diu", "West", "Western"),
    "delhi": ("Delhi", "North", "Northern"),
    "goa": ("Goa", "West", "Western"),
    "gujarat": ("Gujarat", "West", "Western"),
    "haryana": ("Haryana", "North", "Northern"),
    "himachal-pradesh": ("Himachal Pradesh", "North", "Northern"),
    "jammu-&-kashmir": ("Jammu & Kashmir", "North", "Northern"),
    "jharkhand": ("Jharkhand", "East", "Eastern"),
    "karnataka": ("Karnataka", "South", "Southern"),
    "kerala": ("Kerala", "South", "Southern"),
    "ladakh": ("Ladakh", "North", "Northern"),
    "lakshadweep": ("Lakshadweep", "South", "Islands"),
    "madhya-pradesh": ("Madhya Pradesh", "Central", "Central"),
    "maharashtra": ("Maharashtra", "West", "Western"),
    "manipur": ("Manipur", "Northeast", "Northeastern"),
    "meghalaya": ("Meghalaya", "Northeast", "Northeastern"),
    "mizoram": ("Mizoram", "Northeast", "Northeastern"),
    "nagaland": ("Nagaland", "Northeast", "Northeastern"),
    "odisha": ("Odisha", "East", "Eastern"),
    "puducherry": ("Puducherry", "South", "Southern"),
    "punjab": ("Punjab", "North", "Northern"),
    "rajasthan": ("Rajasthan", "North", "Northern"),
    "sikkim": ("Sikkim", "Northeast", "Northeastern"),
    "tamil-nadu": ("Tamil Nadu", "South", "Southern"),
    "telangana": ("Telangana", "South", "Southern"),
    "tripura": ("Tripura", "Northeast", "Northeastern"),
    "uttar-pradesh": ("Uttar Pradesh", "Central", "Northern"),
    "uttarakhand": ("Uttarakhand", "North", "Northern"),
    "west-bengal": ("West Bengal", "East", "Eastern"),
}

# Table names created by the ETL (kept here so every module agrees).
TABLES = [
    "dim_state", "dim_date",
    "agg_transaction", "agg_user", "agg_user_device", "agg_insurance",
    "map_transaction", "map_user", "map_insurance",
    "top_transaction_district", "top_transaction_pincode", "top_user_pincode",
]
