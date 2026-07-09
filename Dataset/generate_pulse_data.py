"""
generate_pulse_data.py
======================================================================
Generates a realistic, PhonePe-Pulse-formatted dataset on disk.

Why this file exists
--------------------
The official PhonePe Pulse repository ships nested JSON folders that are
several GB in size and change over time. For a *reproducible, testable*
portfolio project we synthesise a dataset that mirrors the exact folder
layout and JSON schema of PhonePe Pulse, but with well-understood,
economically-plausible signal baked in so the downstream analytics tell a
coherent story instead of describing random noise.

Signal deliberately engineered into the data
---------------------------------------------
1. Secular growth ...... digital payments compound quarter-over-quarter
                         (fast 2018-2020, tapering afterwards).
2. Seasonality ......... Q3/Q4 lift for the Indian festival season
                         (Dussehra, Diwali, year-end shopping).
3. Geographic Pareto ... a handful of large/southern/western states carry
                         the bulk of value; within a state a few districts
                         and pincodes dominate (~80/20).
4. Category mix drift .. Peer-to-peer dominates value; Merchant payments
                         steadily gain share; Recharge & bill payments
                         lose share over time.
5. Ticket-size spread .. each category has a distinct average transaction
                         value (financial services high, recharge low).
6. Insurance ramp ...... insurance only appears from 2020 Q1 and is
                         concentrated in urban / higher-income states.

The output can be regenerated deterministically via the RNG seed, so the
numbers quoted in the documentation always match what the ETL loads.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

# --------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------- #
SEED = 20240117
YEARS = list(range(2018, 2024))          # 2018 .. 2023 inclusive
QUARTERS = [1, 2, 3, 4]
INSURANCE_START = (2020, 1)              # (year, quarter) insurance goes live

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "pulse" / "data"           # mirrors PhonePePulse/data/...

TXN_CATEGORIES = [
    "Recharge & bill payments",
    "Peer-to-peer payments",
    "Merchant payments",
    "Financial Services",
    "Others",
]

# Average ticket size (INR) per category - drives count = amount / ticket.
CATEGORY_TICKET = {
    "Recharge & bill payments": 260.0,
    "Peer-to-peer payments": 1650.0,
    "Merchant payments": 640.0,
    "Financial Services": 2450.0,
    "Others": 820.0,
}

DEVICE_BRANDS = [
    ("Xiaomi", 0.26), ("Samsung", 0.20), ("Vivo", 0.145), ("Oppo", 0.115),
    ("Realme", 0.095), ("OnePlus", 0.045), ("Apple", 0.035),
    ("Motorola", 0.02), ("Others", 0.085),
]

# State: (relative economic weight, urban/affluence factor, pincode prefix).
# Weight drives transaction value share; urban factor drives insurance and
# average ticket; prefix makes generated pincodes look regionally authentic.
STATES = {
    "maharashtra":       (1.00, 0.95, "4"),
    "karnataka":         (0.82, 0.93, "5"),
    "uttar-pradesh":     (0.78, 0.55, "2"),
    "tamil-nadu":        (0.71, 0.88, "6"),
    "telangana":         (0.63, 0.90, "5"),
    "andhra-pradesh":    (0.58, 0.70, "5"),
    "rajasthan":         (0.47, 0.58, "3"),
    "west-bengal":       (0.46, 0.62, "7"),
    "gujarat":           (0.52, 0.82, "3"),
    "madhya-pradesh":    (0.41, 0.55, "4"),
    "delhi":             (0.55, 0.97, "1"),
    "kerala":            (0.44, 0.85, "6"),
    "haryana":           (0.36, 0.78, "1"),
    "bihar":             (0.34, 0.42, "8"),
    "punjab":            (0.31, 0.72, "1"),
    "odisha":            (0.27, 0.50, "7"),
    "assam":             (0.20, 0.48, "7"),
    "jharkhand":         (0.19, 0.47, "8"),
    "chhattisgarh":      (0.18, 0.49, "4"),
    "uttarakhand":       (0.14, 0.63, "2"),
    "himachal-pradesh":  (0.09, 0.60, "1"),
    "jammu-&-kashmir":   (0.10, 0.52, "1"),
    "goa":               (0.06, 0.90, "4"),
    "tripura":           (0.04, 0.50, "7"),
    "meghalaya":         (0.03, 0.48, "7"),
    "manipur":           (0.03, 0.46, "7"),
    "nagaland":          (0.02, 0.45, "7"),
    "arunachal-pradesh": (0.02, 0.40, "7"),
    "mizoram":           (0.02, 0.47, "7"),
    "sikkim":            (0.02, 0.55, "7"),
    "puducherry":        (0.03, 0.80, "6"),
    "chandigarh":        (0.04, 0.95, "1"),
    "andaman-&-nicobar-islands": (0.01, 0.55, "7"),
    "dadra-&-nagar-haveli-&-daman-&-diu": (0.02, 0.70, "3"),
    "ladakh":            (0.01, 0.45, "1"),
    "lakshadweep":       (0.005, 0.50, "6"),
}

# A curated set of real districts for the larger states; smaller states get a
# short generated list. Districts receive Pareto weights inside a state.
DISTRICTS = {
    "maharashtra": ["pune", "mumbai", "thane", "nagpur", "nashik", "ahmednagar", "solapur", "kolhapur"],
    "karnataka": ["bengaluru urban", "belgaum", "mysuru", "tumakuru", "kalaburagi", "ballari", "dakshina kannada"],
    "uttar-pradesh": ["lucknow", "kanpur nagar", "gautam buddha nagar", "ghaziabad", "agra", "varanasi", "meerut", "prayagraj"],
    "tamil-nadu": ["chennai", "coimbatore", "kancheepuram", "salem", "erode", "madurai", "tiruppur"],
    "telangana": ["hyderabad", "rangareddy", "medchal malkajgiri", "warangal urban", "karimnagar", "khammam"],
    "andhra-pradesh": ["visakhapatnam", "krishna", "guntur", "east godavari", "chittoor", "west godavari"],
    "rajasthan": ["jaipur", "jodhpur", "udaipur", "kota", "ajmer", "bikaner", "alwar"],
    "west-bengal": ["kolkata", "north 24 parganas", "south 24 parganas", "howrah", "hooghly", "bardhaman"],
    "gujarat": ["ahmedabad", "surat", "vadodara", "rajkot", "gandhinagar", "bhavnagar"],
    "madhya-pradesh": ["indore", "bhopal", "jabalpur", "gwalior", "ujjain", "sagar"],
    "delhi": ["new delhi", "south delhi", "west delhi", "north delhi", "east delhi", "central delhi"],
    "kerala": ["ernakulam", "thiruvananthapuram", "thrissur", "kozhikode", "malappuram", "kollam"],
    "haryana": ["gurugram", "faridabad", "hisar", "panipat", "karnal", "ambala"],
    "bihar": ["patna", "gaya", "muzaffarpur", "bhagalpur", "darbhanga"],
    "punjab": ["ludhiana", "amritsar", "jalandhar", "patiala", "mohali"],
    "gujarat ": [],
}


def districts_for(state: str) -> list[str]:
    """Return a plausible district list for a state (curated or generated)."""
    if state in DISTRICTS and DISTRICTS[state]:
        return DISTRICTS[state]
    pretty = state.replace("-", " ").replace("&", "and").title()
    return [f"{pretty} District {i}" for i in range(1, 6)]


# --------------------------------------------------------------------- #
# Growth / seasonality helpers
# --------------------------------------------------------------------- #
def period_index(year: int, quarter: int) -> int:
    """Sequential quarter index with 2018 Q1 = 0."""
    return (year - YEARS[0]) * 4 + (quarter - 1)


def growth_multiplier(year: int, quarter: int) -> float:
    """Compounding adoption curve: quick early growth that tapers off."""
    t = period_index(year, quarter)
    # Per-quarter growth rate decays from ~13% toward ~4%.
    g = 0.04 + 0.09 * np.exp(-t / 9.0)
    mult = 1.0
    for _ in range(t):
        mult *= (1 + g)
    return mult


SEASONALITY = {1: 0.94, 2: 1.00, 3: 1.06, 4: 1.17}


def category_shares(year: int, quarter: int) -> dict[str, float]:
    """Category value-share that drifts over time (merchant up, recharge down)."""
    t = period_index(year, quarter)
    frac = t / (len(YEARS) * 4)
    shares = {
        "Peer-to-peer payments": 0.60 - 0.06 * frac,
        "Merchant payments": 0.14 + 0.12 * frac,
        "Recharge & bill payments": 0.16 - 0.07 * frac,
        "Financial Services": 0.06 + 0.005 * frac,
        "Others": 0.04,
    }
    total = sum(shares.values())
    return {k: v / total for k, v in shares.items()}


def pareto_weights(n: int, rng: np.random.Generator, alpha: float = 1.15) -> np.ndarray:
    """Zipf-like descending weights that sum to 1 (drives 80/20 concentration)."""
    ranks = np.arange(1, n + 1)
    w = 1.0 / np.power(ranks, alpha)
    w *= rng.uniform(0.9, 1.1, size=n)     # light jitter so it isn't perfectly smooth
    w = np.sort(w)[::-1]
    return w / w.sum()


# --------------------------------------------------------------------- #
# JSON writers (exact PhonePe Pulse schema)
# --------------------------------------------------------------------- #
def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def pulse_envelope(data: dict) -> dict:
    """Wrap payload the way PhonePe Pulse does (success flag + responseCode)."""
    return {"success": True, "code": "SUCCESS", "data": data, "responseTimestamp": 0}


def build():
    rng = np.random.default_rng(SEED)
    if BASE.exists():
        shutil.rmtree(BASE.parent)

    # National scale constant so headline numbers land in a realistic range.
    NATIONAL_BASE = 9.0e9   # INR value for the reference state in 2018 Q1

    file_count = 0
    for state, (weight, urban, prefix) in STATES.items():
        state_districts = districts_for(state)
        dist_w = pareto_weights(len(state_districts), rng)

        for year in YEARS:
            for q in QUARTERS:
                gm = growth_multiplier(year, q)
                seas = SEASONALITY[q]
                state_value = NATIONAL_BASE * weight * gm * seas * rng.uniform(0.95, 1.05)

                # ---------- AGGREGATED / TRANSACTION ----------
                shares = category_shares(year, q)
                txn_list = []
                for cat in TXN_CATEGORIES:
                    amt = state_value * shares[cat] * rng.uniform(0.97, 1.03)
                    cnt = int(amt / CATEGORY_TICKET[cat])
                    txn_list.append({
                        "name": cat,
                        "paymentInstruments": [
                            {"type": "TOTAL", "count": cnt, "amount": round(amt, 2)}
                        ],
                    })
                write_json(
                    BASE / "aggregated" / "transaction" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                    pulse_envelope({"from": 0, "to": 0, "transactionData": txn_list}),
                )
                file_count += 1

                # ---------- AGGREGATED / USER ----------
                registered = int((state_value / 4200.0) * rng.uniform(0.9, 1.1))
                app_opens = int(registered * rng.uniform(6.5, 9.5))
                brands = []
                for brand, share in DEVICE_BRANDS:
                    b_cnt = int(registered * share * rng.uniform(0.95, 1.05))
                    brands.append({"brand": brand, "count": b_cnt,
                                   "percentage": round(share, 4)})
                write_json(
                    BASE / "aggregated" / "user" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                    pulse_envelope({
                        "aggregated": {"registeredUsers": registered, "appOpens": app_opens},
                        "usersByDevice": brands,
                    }),
                )
                file_count += 1

                # ---------- AGGREGATED / INSURANCE ----------
                if (year, q) >= INSURANCE_START:
                    ins_ramp = growth_multiplier(year, q) / growth_multiplier(*INSURANCE_START)
                    ins_amount = state_value * 0.0026 * urban * ins_ramp * rng.uniform(0.9, 1.1)
                    ins_count = int(ins_amount / (620.0 * urban + 120.0))
                    write_json(
                        BASE / "aggregated" / "insurance" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                        pulse_envelope({"from": 0, "to": 0, "transactionData": [
                            {"name": "Insurance", "paymentInstruments": [
                                {"type": "TOTAL", "count": ins_count, "amount": round(ins_amount, 2)}]}]}),
                    )
                    file_count += 1

                # ---------- MAP / TRANSACTION (district level) ----------
                txn_total_amt = state_value
                txn_total_cnt = sum(t["paymentInstruments"][0]["count"] for t in txn_list)
                hover = []
                for d, w in zip(state_districts, dist_w):
                    hover.append({
                        "name": f"{d} district",
                        "metric": [{"type": "TOTAL",
                                    "count": int(txn_total_cnt * w),
                                    "amount": round(txn_total_amt * w, 2)}],
                    })
                write_json(
                    BASE / "map" / "transaction" / "hover" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                    pulse_envelope({"hoverDataList": hover}),
                )
                file_count += 1

                # ---------- MAP / USER (district level) ----------
                hover_u = {}
                for d, w in zip(state_districts, dist_w):
                    hover_u[f"{d} district"] = {
                        "registeredUsers": int(registered * w),
                        "appOpens": int(app_opens * w),
                    }
                write_json(
                    BASE / "map" / "user" / "hover" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                    pulse_envelope({"hoverData": hover_u}),
                )
                file_count += 1

                # ---------- MAP / INSURANCE ----------
                if (year, q) >= INSURANCE_START:
                    hover_i = []
                    for d, w in zip(state_districts, dist_w):
                        hover_i.append({
                            "name": f"{d} district",
                            "metric": [{"type": "TOTAL",
                                        "count": int(ins_count * w),
                                        "amount": round(ins_amount * w, 2)}],
                        })
                    write_json(
                        BASE / "map" / "insurance" / "hover" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                        pulse_envelope({"hoverDataList": hover_i}),
                    )
                    file_count += 1

                # ---------- TOP / TRANSACTION (districts + pincodes) ----------
                n_pin = 10
                pin_w = pareto_weights(n_pin, rng, alpha=1.05)
                pincodes = [f"{prefix}{rng.integers(10000, 99999)}" for _ in range(n_pin)]
                top_districts = [
                    {"entityName": d,
                     "metric": {"type": "TOTAL", "count": int(txn_total_cnt * w),
                                "amount": round(txn_total_amt * w, 2)}}
                    for d, w in zip(state_districts[:10], dist_w[:10])
                ]
                top_pincodes = [
                    {"entityName": p,
                     "metric": {"type": "TOTAL", "count": int(txn_total_cnt * w),
                                "amount": round(txn_total_amt * w, 2)}}
                    for p, w in zip(pincodes, pin_w)
                ]
                write_json(
                    BASE / "top" / "transaction" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                    pulse_envelope({"districts": top_districts, "pincodes": top_pincodes}),
                )
                file_count += 1

                # ---------- TOP / USER ----------
                top_u_dist = [
                    {"name": d, "registeredUsers": int(registered * w)}
                    for d, w in zip(state_districts[:10], dist_w[:10])
                ]
                top_u_pin = [
                    {"name": p, "registeredUsers": int(registered * w)}
                    for p, w in zip(pincodes, pin_w)
                ]
                write_json(
                    BASE / "top" / "user" / "country" / "india" / "state" / state / str(year) / f"{q}.json",
                    pulse_envelope({"districts": top_u_dist, "pincodes": top_u_pin}),
                )
                file_count += 1

    print(f"Generated {file_count} JSON files under {BASE}")
    return file_count


if __name__ == "__main__":
    build()
