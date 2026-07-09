# PhonePe Transaction Insights

### End-to-End Data Analytics & Business Intelligence — Python · SQL · Streamlit · Plotly

An enterprise-style analytics platform over a **PhonePe Pulse-formatted** digital-payments
dataset for India. It ships a reusable **ETL pipeline**, a **SQL star-schema warehouse**,
**60+ analytical queries**, an interactive **10-page Streamlit dashboard**, and
**auto-generated executive reports** — all runnable with a single command and a zero-setup
SQLite backend (or MySQL 8 in production).

> **Note:** independent portfolio project, not affiliated with PhonePe. The bundled dataset
> is *synthetically generated* to mirror the PhonePe Pulse schema, with realistic economic
> signal baked in (growth, seasonality, geographic Pareto, category-mix drift). Regenerate it
> deterministically with `python main.py generate`.

---

## Headline numbers (computed live from the warehouse)

| Metric | Value |
|---|---|
| Total transaction value | **Rs 4.52 lakh crore** |
| Total transactions | **5.47 billion** |
| Average ticket size | **Rs 827** |
| Value CAGR (2018–2023) | **18.3%** |
| Latest YoY growth | **12.04%** |
| Top region | **South — 32.45%** of value |
| Top state | **Maharashtra — 10.05%** (top 5 = **39.8%**) |
| District Pareto | **top 20% of districts = 63.9%** of value |
| Merchant-share shift | **14.9% → 24.8%** (2018→2023) |
| Q4 seasonal uplift | **+40%** vs Q1 |
| Registered users (latest Q) | **7.15 Cr** |
| Insurance premium (since 2020) | **Rs 882 Cr** |

Every figure above is produced by `reports/build_reports.py` straight from the database,
so the documentation can never drift from the data.

---

## Tech stack
**Python 3.11+** · pandas · NumPy · SQLAlchemy · **MySQL 8** / SQLite · **Streamlit** ·
**Plotly** · reportlab · Git/GitHub.

---

## Architecture

```
PhonePe Pulse-style JSON  ──▶  Extract  ──▶  Transform  ──▶  Load  ──▶  SQL Warehouse
                                                                          │
                                              Validate (20 rules) ◀───────┤
                                                                          ▼
                                          Analytics ──▶ Plotly ──▶ Streamlit (10 pages)
                                              │
                                              └──▶ Auto reports (Markdown + PDF)
```

See `reports/Architecture.md` and `reports/ER_Diagram.md` for full diagrams.

---

## Repository structure
```
PhonePe-Transaction-Insights/
├── main.py                     # single CLI: generate | etl | validate | all | dashboard
├── config.py                   # paths + backend selection (sqlite/mysql)
├── requirements.txt · LICENSE · .gitignore
├── dataset/
│   └── generate_pulse_data.py  # reproducible Pulse-format data generator
│       pulse/data/...          # 6,336 nested JSON files (generated)
├── etl/
│   ├── extract.py transform.py load.py validate.py pipeline.py
├── database/
│   ├── database_schema.sql create_tables.sql indexes.sql
│   ├── views.sql stored_procedures.sql queries.sql   # 60 documented queries
│   └── insert_data.py
├── src/
│   ├── database.py queries.py analytics.py visualizations.py utils.py
├── dashboard/
│   ├── app.py  dash_utils.py
│   └── pages/  # Executive, Transactions, Users, Insurance, State,
│               # District, Pincode, Trend, Business Insights
├── reports/
│   ├── build_reports.py
│   ├── Executive_Summary.md KPIs.md Business_Insights.md (40 insights)
│   ├── Business_Questions.md (75)  Interview_QA.md  Data_Dictionary.md
│   ├── Architecture.md Project_Workflow.md ER_Diagram.md Deployment_Guide.md
│   └── Business_Report.pdf
└── images/  logs/  tests/
```

---

## Quickstart (SQLite — zero external services)
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python main.py all                 # generate dataset + full ETL (+ 20-rule validation)
python -m reports.build_reports    # build MD + PDF reports from the live DB
streamlit run dashboard/app.py     # launch the dashboard at http://localhost:8501
```

## Production (MySQL 8)
```bash
mysql -u root -p < database/database_schema.sql
export PHONEPE_DB=mysql MYSQL_USER=root MYSQL_PASSWORD=***
python -m database.insert_data                          # schema + load + indexes + views
mysql -u root -p phonepe_insights < database/stored_procedures.sql   # optional
```

---

## What's inside

- **ETL pipeline** — walks 6,300+ nested JSON files, fails soft on missing/corrupt input,
  normalises nested arrays into a **star schema**, cleans types, and loads 12 tables
  (~48k rows) through one backend-agnostic SQLAlchemy path.
- **Data-quality gate** — 20 rules (non-empty, no null keys, no negatives, referential
  integrity, quarter range, coverage) with a **CI-friendly exit code**.
- **SQL warehouse** — dimensions + facts + indexes + analytical views, and
  **60 documented queries** (window functions, CTEs, ranking, running totals, moving
  averages) — all executed against the DB in testing.
- **Dashboard** — 10 pages of KPI cards, filters, treemaps, choropleth-ready maps,
  trend lines and drill-downs.
- **Auto reports** — Executive Summary, KPIs, 40 insights and a branded PDF, generated
  from the live warehouse.

---

## Verified / tested
This repository was built and executed end-to-end before publishing:
- ✅ ETL pipeline runs clean: **48,476 rows across 12 tables**
- ✅ **20/20** data-quality rules pass
- ✅ **60/60** SQL queries execute successfully
- ✅ All Python modules compile; dashboard imports resolve
- ✅ Reports + PDF generate from the live DB

---

## Documentation index
| Doc | Contents |
|---|---|
| `reports/Executive_Summary.md` | One-page leadership summary |
| `reports/KPIs.md` | KPI catalogue with live values |
| `reports/Business_Insights.md` | 40 data-grounded insights + recommendations |
| `reports/Business_Questions.md` | 75 business questions |
| `reports/Data_Dictionary.md` | Every table & column |
| `reports/ER_Diagram.md` | Star-schema ER (Mermaid) |
| `reports/Architecture.md` | System & layer design |
| `reports/Project_Workflow.md` | Commands & refresh cadence |
| `reports/Deployment_Guide.md` | Docker, CI/CD, hosting, bonus features |
| `reports/Interview_QA.md` | Resume bullets + 40 interview Q&A |

## License
MIT — see `LICENSE`.
