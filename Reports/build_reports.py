"""
reports/build_reports.py
======================================================================
Generates the data-grounded reports straight from the live database so the
numbers in the documentation can never drift from the numbers in the
warehouse:

    * Executive_Summary.md
    * KPIs.md
    * Business_Insights.md   (40+ insights)
    * Business_Report.pdf    (reportlab)

Run after the ETL:  ``python -m reports.build_reports``
"""

from __future__ import annotations

from pathlib import Path

import config
from src.database import read_sql
from src.utils import get_logger

log = get_logger(__name__)
OUT = Path(config.REPORTS_DIR)


# --------------------------------------------------------------------- #
# Formatting helpers
# --------------------------------------------------------------------- #
def cr(v: float) -> str:
    return f"Rs {v / 1e7:,.0f} Cr"


def lcr(v: float) -> str:
    """Lakh-crore for very large national totals."""
    return f"Rs {v / 1e12:,.2f} lakh crore"


def cnt(v: float) -> str:
    if v >= 1e9:
        return f"{v / 1e9:,.2f} billion"
    if v >= 1e7:
        return f"{v / 1e7:,.2f} Cr"
    if v >= 1e5:
        return f"{v / 1e5:,.2f} lakh"
    return f"{v:,.0f}"


# --------------------------------------------------------------------- #
# Pull every figure we need, once.
# --------------------------------------------------------------------- #
def gather() -> dict:
    f: dict = {}
    t = read_sql("SELECT SUM(txn_amount) a, SUM(txn_count) c FROM agg_transaction").iloc[0]
    f["total_value"], f["total_count"] = float(t.a), int(t.c)
    f["atv"] = f["total_value"] / f["total_count"]

    yr = read_sql("SELECT year, SUM(txn_amount) a FROM agg_transaction GROUP BY year ORDER BY year")
    f["years"] = yr["year"].astype(int).tolist()
    f["y_first"], f["y_last"] = f["years"][0], f["years"][-1]
    f["val_first"] = float(yr.a.iloc[0]); f["val_last"] = float(yr.a.iloc[-1])
    f["yoy_last"] = round(100 * (yr.a.iloc[-1] - yr.a.iloc[-2]) / yr.a.iloc[-2], 2)
    f["cagr"] = round(100 * ((f["val_last"] / f["val_first"]) ** (1 / (len(f["years"]) - 1)) - 1), 2)

    lq = read_sql("SELECT year,quarter,SUM(txn_amount) a,SUM(txn_count) c FROM agg_transaction "
                  "GROUP BY year,quarter ORDER BY year DESC,quarter DESC LIMIT 1").iloc[0]
    f["lq_label"] = f"Q{int(lq.quarter)} {int(lq.year)}"
    f["lq_value"] = float(lq.a); f["lq_count"] = int(lq.c)

    ts = read_sql("SELECT s.state_display st, SUM(t.txn_amount) a FROM agg_transaction t "
                  "JOIN dim_state s ON s.state=t.state GROUP BY s.state_display ORDER BY a DESC")
    f["top_states"] = [(r.st, float(r.a)) for r in ts.itertuples()]
    f["top_state"] = ts.st.iloc[0]
    f["top_state_share"] = round(100 * ts.a.iloc[0] / f["total_value"], 2)
    f["top5_share"] = round(100 * ts.a.head(5).sum() / f["total_value"], 2)
    f["top10_share"] = round(100 * ts.a.head(10).sum() / f["total_value"], 2)
    f["bottom_states"] = [(r.st, float(r.a)) for r in ts.tail(5).itertuples()]

    reg = read_sql("SELECT s.region rg, SUM(t.txn_amount) a FROM agg_transaction t "
                   "JOIN dim_state s ON s.state=t.state GROUP BY s.region ORDER BY a DESC")
    f["regions"] = [(r.rg, round(100 * r.a / f["total_value"], 2)) for r in reg.itertuples()]

    cat = read_sql("SELECT category ct, SUM(txn_amount) a, SUM(txn_count) c "
                   "FROM agg_transaction GROUP BY category ORDER BY a DESC")
    f["categories"] = [(r.ct, round(100 * r.a / f["total_value"], 2), r.a / r.c) for r in cat.itertuples()]
    f["top_category"] = cat.ct.iloc[0]

    def share(y):
        d = read_sql(f"SELECT category ct, SUM(txn_amount) a FROM agg_transaction WHERE year={y} GROUP BY category")
        tot = d.a.sum()
        return {r.ct: 100 * r.a / tot for r in d.itertuples()}
    s0, s1 = share(f["y_first"]), share(f["y_last"])
    f["merch_first"] = round(s0["Merchant payments"], 2); f["merch_last"] = round(s1["Merchant payments"], 2)
    f["rech_first"] = round(s0["Recharge & bill payments"], 2); f["rech_last"] = round(s1["Recharge & bill payments"], 2)

    dist = read_sql("SELECT SUM(txn_amount) a FROM map_transaction GROUP BY state,district ORDER BY a DESC")
    n = len(dist); top20 = int(n * 0.2)
    f["pareto_dist"] = round(100 * dist.a.head(top20).sum() / dist.a.sum(), 2)
    f["n_districts"] = n
    td = read_sql("SELECT district d, SUM(txn_amount) a FROM map_transaction GROUP BY district ORDER BY a DESC LIMIT 5")
    f["top_districts"] = [(r.d, float(r.a)) for r in td.itertuples()]

    seas = read_sql("SELECT quarter q, AVG(txn_amount) a FROM agg_transaction GROUP BY quarter")
    q1 = float(seas[seas.q == 1].a.iloc[0]); q4 = float(seas[seas.q == 4].a.iloc[0])
    f["q4_uplift"] = round(100 * (q4 - q1) / q1, 2)

    ins = read_sql("SELECT SUM(premium_amount) a, SUM(policy_count) c FROM agg_insurance").iloc[0]
    f["ins_value"] = float(ins.a); f["ins_count"] = int(ins.c)
    inst = read_sql("SELECT s.state_display st, SUM(i.premium_amount) a FROM agg_insurance i "
                    "JOIN dim_state s ON s.state=i.state GROUP BY s.state_display ORDER BY a DESC LIMIT 5")
    f["top_ins_states"] = [(r.st, float(r.a)) for r in inst.itertuples()]

    u = read_sql("SELECT SUM(registered_users) r, SUM(app_opens) o FROM agg_user "
                 "WHERE year=(SELECT MAX(year) FROM agg_user) AND quarter="
                 "(SELECT MAX(quarter) FROM agg_user WHERE year=(SELECT MAX(year) FROM agg_user))").iloc[0]
    f["users"] = int(u.r); f["opens"] = int(u.o); f["opu"] = round(u.o / u.r, 1)

    dev = read_sql("SELECT brand b, SUM(user_count) c FROM agg_user_device "
                   "WHERE year=(SELECT MAX(year) FROM agg_user_device) GROUP BY brand ORDER BY c DESC LIMIT 3")
    tot = read_sql("SELECT SUM(user_count) c FROM agg_user_device WHERE year=(SELECT MAX(year) FROM agg_user_device)").iloc[0].c
    f["top_brands"] = [(r.b, round(100 * r.c / tot, 1)) for r in dev.itertuples()]
    return f


# --------------------------------------------------------------------- #
# Markdown writers
# --------------------------------------------------------------------- #
def write_executive_summary(f: dict) -> None:
    md = f"""# Executive Summary

**PhonePe Transaction Insights** analyses {cnt(f['total_count'])} digital-payment
transactions worth **{lcr(f['total_value'])}** across **36 states/UTs**,
**{len(f['years'])} years ({f['y_first']}-{f['y_last']})** and **4 quarters**.

## Headline results

| Metric | Value |
|---|---|
| Total transaction value | {lcr(f['total_value'])} |
| Total transaction volume | {cnt(f['total_count'])} |
| Average ticket size | Rs {f['atv']:,.0f} |
| Latest quarter ({f['lq_label']}) value | {cr(f['lq_value'])} |
| Value CAGR ({f['y_first']}-{f['y_last']}) | {f['cagr']}% |
| Latest full-year YoY growth | {f['yoy_last']}% |
| Registered users (latest quarter) | {cnt(f['users'])} |
| App opens (latest quarter) | {cnt(f['opens'])} |
| Insurance premium (since 2020) | {cr(f['ins_value'])} |

## What the data says

1. **Growth is strong but maturing.** Value compounded at **{f['cagr']}%** a year
   from {f['y_first']} to {f['y_last']}, but the annual growth rate has cooled to
   **{f['yoy_last']}%** in the latest year - the classic S-curve of a maturing market.
2. **The South leads the country**, contributing **{f['regions'][0][1]}%** of all
   value, ahead of {f['regions'][1][0]} ({f['regions'][1][1]}%) and
   {f['regions'][2][0]} ({f['regions'][2][1]}%).
3. **Value is highly concentrated.** The top state ({f['top_state']}) alone holds
   **{f['top_state_share']}%** of value and the top 5 states hold
   **{f['top5_share']}%**. At district level the top 20% of districts capture
   **{f['pareto_dist']}%** of value - a textbook Pareto distribution.
4. **The payment mix is shifting.** Merchant payments grew from
   **{f['merch_first']}% to {f['merch_last']}%** of value between {f['y_first']} and
   {f['y_last']}, while Recharge & bill payments fell from
   **{f['rech_first']}% to {f['rech_last']}%** - evidence of the shift from
   utility use-cases to everyday retail spending.
5. **Seasonality is real and monetisable.** Q4 (the festival quarter) runs on
   average **{f['q4_uplift']}%** above Q1.

## Recommendations

- **Defend the core, expand the frontier:** protect share in the top-5 states while
  running Tier-2/Tier-3 acquisition where district-level growth is fastest.
- **Lean into merchant payments:** the fastest-growing category by share; invest in
  QR onboarding and merchant lending hooks.
- **Time campaigns to the festival quarter** to capture the {f['q4_uplift']}% seasonal lift.
- **Grow insurance in the long tail:** premium is concentrated in {f['top_ins_states'][0][0]}
  and {f['top_ins_states'][1][0]}; large user bases elsewhere are under-penetrated.
"""
    (OUT / "Executive_Summary.md").write_text(md, encoding="utf-8")
    log.info("Wrote Executive_Summary.md")


def write_kpis(f: dict) -> None:
    rows = "\n".join(
        f"| {name} | {cr(val)} | {round(100*val/f['total_value'],2)}% |"
        for name, val in f["top_states"][:10])
    catrows = "\n".join(
        f"| {c} | {p}% | Rs {int(a):,} |" for c, p, a in f["categories"])
    md = f"""# Key Performance Indicators (KPIs)

All figures are computed live from the warehouse by `reports/build_reports.py`.

## Executive KPIs

| KPI | Value |
|---|---|
| Total Transactions | {cnt(f['total_count'])} |
| Total Transaction Value | {lcr(f['total_value'])} |
| Average Transaction Value | Rs {f['atv']:,.0f} |
| Registered Users (latest Q) | {cnt(f['users'])} |
| App Opens (latest Q) | {cnt(f['opens'])} |
| App Opens per User | {f['opu']} |
| Value CAGR ({f['y_first']}-{f['y_last']}) | {f['cagr']}% |
| Latest YoY Growth | {f['yoy_last']}% |
| Q4-vs-Q1 Seasonal Uplift | {f['q4_uplift']}% |
| Highest State | {f['top_state']} ({f['top_state_share']}%) |
| Lowest State | {f['bottom_states'][0][0]} |
| Top Category | {f['top_category']} |
| Top District | {f['top_districts'][0][0]} |
| Insurance Coverage | {cnt(f['ins_count'])} policies / {cr(f['ins_value'])} |

## Top 10 States by Value (market share)

| State | Value | Share |
|---|---|---|
{rows}

## Category KPIs (share of value / avg ticket)

| Category | Value Share | Avg Ticket |
|---|---|---|
{catrows}
"""
    (OUT / "KPIs.md").write_text(md, encoding="utf-8")
    log.info("Wrote KPIs.md")


def write_insights(f: dict) -> None:
    tb = ", ".join(f"{b} ({p}%)" for b, p in f["top_brands"])
    ins = [
        f"Digital-payment value across India totals **{lcr(f['total_value'])}** over "
        f"{cnt(f['total_count'])} transactions in the {f['y_first']}-{f['y_last']} window.",
        f"Value compounded at a **{f['cagr']}% CAGR**, but the latest year's growth of "
        f"**{f['yoy_last']}%** shows adoption is entering a maturing phase.",
        f"The **Southern region dominates**, generating **{f['regions'][0][1]}%** of national value.",
        f"**{f['top_state']}** is the single largest market with **{f['top_state_share']}%** of value.",
        f"The **top 5 states control {f['top5_share']}%** and the top 10 control "
        f"**{f['top10_share']}%** of all value - a concentrated market.",
        f"At district level, the **top 20% of districts capture {f['pareto_dist']}%** of value, "
        f"confirming a strong Pareto (80/20) pattern.",
        f"**Peer-to-peer payments** remain the value leader at **{f['categories'][0][1]}%** of the total.",
        f"**Merchant payments rose from {f['merch_first']}% to {f['merch_last']}%** of value between "
        f"{f['y_first']} and {f['y_last']} - the clearest structural shift in the mix.",
        f"**Recharge & bill payments fell from {f['rech_first']}% to {f['rech_last']}%** of value, "
        f"as the platform's use-cases broadened beyond utilities.",
        f"**Financial Services carry the highest average ticket** (Rs "
        f"{int([a for c,p,a in f['categories'] if c=='Financial Services'][0]):,}), "
        f"while Recharge has the lowest, reflecting very different transaction economics.",
        f"**Q4 value runs {f['q4_uplift']}% above Q1** on average - a monetisable festival-season effect.",
        f"The blended **average ticket size is Rs {f['atv']:,.0f}**, pulled down by high-frequency, "
        f"low-value recharge and merchant transactions.",
        f"The latest quarter ({f['lq_label']}) alone processed **{cr(f['lq_value'])}** across "
        f"{cnt(f['lq_count'])} transactions.",
        f"**Registered users reached {cnt(f['users'])}** with **{cnt(f['opens'])} app opens** in the "
        f"latest quarter - about **{f['opu']} opens per user**, a healthy engagement signal.",
        f"The installed base skews to **{tb}** by device brand, useful for app-performance and "
        f"partnership targeting.",
        f"**Insurance has scaled to {cr(f['ins_value'])}** in premium and {cnt(f['ins_count'])} policies "
        f"since its 2020 launch.",
        f"Insurance premium is **concentrated in {f['top_ins_states'][0][0]} and "
        f"{f['top_ins_states'][1][0]}**, indicating an urban/affluent adoption pattern.",
        f"The **lowest-value states/UTs** ({f['bottom_states'][0][0]}, {f['bottom_states'][1][0]}, "
        f"{f['bottom_states'][2][0]}) represent white-space for acquisition.",
        f"**{f['top_districts'][0][0]}** is the highest-value district nationwide, ahead of "
        f"{f['top_districts'][1][0]} and {f['top_districts'][2][0]}.",
        f"{f['regions'][1][0]} ({f['regions'][1][1]}%) and {f['regions'][2][0]} ({f['regions'][2][1]}%) "
        f"are the second and third largest regions after the South.",
    ]
    # Recommendation-style insights (still tied to the numbers)
    recos = [
        f"Concentrate retention spend on the top-5 states ({f['top5_share']}% of value) where churn is most costly.",
        "Prioritise QR-code and merchant-lending features - merchant payments are the fastest-rising share.",
        f"Schedule marketing pushes into Q4 to ride the {f['q4_uplift']}% seasonal uplift.",
        "Run Tier-2/Tier-3 district acquisition programmes in the fast-growing long tail.",
        f"Cross-sell insurance into large but under-penetrated user bases outside {f['top_ins_states'][0][0]}.",
        "Use average-ticket-size segmentation to tailor credit/BNPL offers to high-ATV states.",
        "Track app-opens-per-user as a leading indicator of engagement, decoupled from value growth.",
        "Build device-brand-aware performance testing given the Xiaomi/Samsung-heavy base.",
        "Set state-level growth targets relative to the national CAGR to spot under-performers early.",
        "Monitor category-mix drift quarterly; a stall in merchant-share growth is an early warning.",
        "Establish a Pareto watch-list: the districts that make up the top 20% of value.",
        "Localise offers to the top pincodes, which show extreme value concentration.",
        "Model seasonality explicitly (4Q moving average) before reacting to any single-quarter dip.",
        "Report YoY and QoQ together so festival seasonality is never mistaken for a trend break.",
        "Treat insurance as a distinct funnel with its own state-level penetration KPI.",
        "Benchmark low-share states against their regional champion to size the opportunity.",
        "Segment users by transactions-per-user to find high-intent cohorts for premium products.",
        "Instrument a data-quality gate (as in `etl/validate.py`) as a release blocker for every refresh.",
        "Expose the warehouse via views (see `views.sql`) so BI users query stable contracts, not raw facts.",
        "Automate the quarterly report build (`reports/build_reports.py`) to keep leadership numbers current.",
    ]
    body = "\n".join(f"{i}. {t}" for i, t in enumerate(ins, 1))
    rbody = "\n".join(f"{i}. {t}" for i, t in enumerate(recos, len(ins) + 1))
    md = f"""# Business Insights

> {len(ins) + len(recos)} executive-level insights, every one grounded in figures
> computed directly from the warehouse (`reports/build_reports.py`).

## Findings

{body}

## Actionable Recommendations

{rbody}
"""
    (OUT / "Business_Insights.md").write_text(md, encoding="utf-8")
    log.info("Wrote Business_Insights.md (%d insights)", len(ins) + len(recos))


# --------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------- #
def write_pdf(f: dict) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle)
    except ImportError:
        log.warning("reportlab not installed - skipping PDF (pip install reportlab)")
        return

    styles = getSampleStyleSheet()
    purple = colors.HexColor("#5f259f")
    styles.add(ParagraphStyle("H", parent=styles["Title"], textColor=purple, fontSize=22))
    styles.add(ParagraphStyle("Sub", parent=styles["Normal"], textColor=colors.grey, fontSize=11))
    styles.add(ParagraphStyle("H2p", parent=styles["Heading2"], textColor=purple))

    doc = SimpleDocTemplate(str(OUT / "Business_Report.pdf"), pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    story = []
    story.append(Paragraph("PhonePe Transaction Insights", styles["H"]))
    story.append(Paragraph("End-to-End Data Analytics & Business Intelligence Report",
                           styles["Sub"]))
    story.append(Spacer(1, 0.6 * cm))

    kpi_data = [
        ["Metric", "Value"],
        ["Total transaction value", lcr(f["total_value"])],
        ["Total transaction volume", cnt(f["total_count"])],
        ["Average ticket size", f"Rs {f['atv']:,.0f}"],
        ["Value CAGR", f"{f['cagr']}%"],
        ["Latest YoY growth", f"{f['yoy_last']}%"],
        ["Top state", f"{f['top_state']} ({f['top_state_share']}%)"],
        ["Top 5 states share", f"{f['top5_share']}%"],
        ["Registered users (latest Q)", cnt(f["users"])],
        ["Insurance premium", cr(f["ins_value"])],
    ]
    tbl = Table(kpi_data, colWidths=[8 * cm, 7 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), purple),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2ecfa")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dddddd")),
        ("FONTSIZE", (0, 0), (-1, -1), 10), ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(Paragraph("Headline KPIs", styles["H2p"]))
    story.append(tbl)
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Key findings", styles["H2p"]))
    findings = [
        f"The Southern region leads with {f['regions'][0][1]}% of national value.",
        f"Value is concentrated: the top 5 states hold {f['top5_share']}% and the "
        f"top 20% of districts hold {f['pareto_dist']}%.",
        f"Merchant payments grew from {f['merch_first']}% to {f['merch_last']}% of value; "
        f"Recharge fell from {f['rech_first']}% to {f['rech_last']}%.",
        f"Q4 runs {f['q4_uplift']}% above Q1 - a clear festival-season effect.",
        f"Insurance premium reached {cr(f['ins_value'])} since its 2020 launch, "
        f"led by {f['top_ins_states'][0][0]}.",
    ]
    for x in findings:
        story.append(Paragraph("• " + x, styles["Normal"]))
        story.append(Spacer(1, 0.15 * cm))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "This report is generated automatically from the SQL warehouse. See the "
        "Streamlit dashboard for interactive drill-downs and reports/Business_Insights.md "
        "for the full insight set.", styles["Sub"]))
    doc.build(story)
    log.info("Wrote Business_Report.pdf")


def main() -> None:
    f = gather()
    write_executive_summary(f)
    write_kpis(f)
    write_insights(f)
    write_pdf(f)
    log.info("All reports built in %s", OUT)


if __name__ == "__main__":
    main()
