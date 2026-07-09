# Resume Bullets & Interview Preparation

## ATS-friendly resume bullets
1. Built an end-to-end analytics platform on a PhonePe Pulse-style dataset
   (**~48,000 rows across 12 tables, 36 states, 6 years**), spanning a Python
   ETL, a SQL star-schema warehouse and a 10-page Streamlit/Plotly dashboard.
2. Engineered a reusable **Extract-Transform-Load pipeline** (SQLAlchemy) that
   parses **6,300+ nested JSON files**, normalises them into a star schema, and
   loads SQLite or **MySQL 8** through one backend-agnostic code path.
3. Authored **60+ analytical SQL queries** using window functions, CTEs, ranking
   and running totals to quantify market share, YoY/QoQ growth, seasonality and
   Pareto concentration (top 5 states = **~40%** of value).
4. Implemented a **20-rule data-quality gate** (null, negative, referential and
   coverage checks) with a CI-friendly exit code, and **auto-generated executive
   MD + PDF reports** directly from the warehouse so figures never drift.
5. Delivered an interactive BI dashboard with **KPI cards, filters, treemaps,
   choropleth-ready maps and trend charts**, surfacing insights such as merchant
   payments growing from **~15% to ~25%** of value over the period.

## Recruiter / behavioural questions (10)
1. **Walk me through this project.** ETL over nested JSON -> SQL star-schema
   warehouse -> analytics layer -> Streamlit dashboard + auto reports. I built it
   to mirror a real BI stack, with a data-quality gate and tested queries.
2. **Why this dataset?** Digital payments are a rich, multi-dimensional domain
   (geography x time x category x product) - perfect for demonstrating modelling,
   SQL and storytelling.
3. **What was the hardest part?** Designing a schema that serves aggregated,
   district and pincode grains without duplication, and keeping SQL portable
   across SQLite and MySQL.
4. **How did you ensure quality?** A 20-rule validation module runs after every
   load and blocks the pipeline on failure; queries are executed against the DB in
   tests, not just written.
5. **How is it production-like?** Config-driven backends, logging, modular OOP-ish
   layers, indexes/views, and automated reporting - all wired behind one CLI.
6. **What would you add next?** A live India choropleth, a Dockerfile, and a
   scheduled GitHub Action to refresh the warehouse and PDF each quarter.
7. **Who is the audience?** Business leadership - hence KPI cards, an executive
   summary and recommendations, not just charts.
8. **How did you validate the insights?** Every number in the docs is computed by
   `build_reports.py` from the live DB, so the narrative and the data always agree.
9. **How long did it take / how did you scope it?** I scoped by layer (data ->
   ETL -> SQL -> dashboard -> docs) so each layer was independently testable.
10. **What did you learn?** How much of "analytics" is really data engineering and
    contract design - clean dimensions and validated loads make everything above
    them simpler.

## SQL questions (10)
1. **Difference between WHERE and HAVING?** WHERE filters rows before aggregation;
   HAVING filters groups after. Q25 uses HAVING to keep categories above a
   value threshold.
2. **What is a window function?** A calculation across a row set related to the
   current row without collapsing it. I use `RANK()`, `LAG()`, `SUM() OVER` and
   `NTILE()` for ranking, growth and Pareto quintiles.
3. **RANK vs DENSE_RANK vs ROW_NUMBER?** RANK leaves gaps after ties, DENSE_RANK
   does not, ROW_NUMBER is always unique. I use ROW_NUMBER for "top-N per group".
4. **How do you compute YoY growth in SQL?** `LAG(value) OVER (ORDER BY year)`
   then `(value - prev)/prev` (Q28).
5. **What is a CTE and why use it?** A named temporary result set (`WITH`) that
   improves readability and enables multi-step logic - used throughout the trend
   and Pareto queries.
6. **How do you get top-N per group?** `ROW_NUMBER() OVER (PARTITION BY grp ORDER
   BY metric DESC)` then filter `rn <= N` (Q40, Q46).
7. **Running total?** `SUM(value) OVER (ORDER BY period)` (Q30).
8. **Moving average?** `AVG(value) OVER (ORDER BY period ROWS BETWEEN 3 PRECEDING
   AND CURRENT ROW)` (Q29).
9. **How did you optimise performance?** Composite indexes on the filter/group-by
   columns (year, quarter, state, category) and pre-built views.
10. **How do you keep SQL portable?** Stick to ANSI features both engines support,
    avoid `||` string concat, and route everything through SQLAlchemy.

## Python questions (10)
1. **How is the code structured?** Layered modules (config, utils, database,
   etl.*, src.*), each with a single responsibility and docstrings.
2. **How do you handle bad input?** Extraction fails soft: missing/corrupt JSON is
   logged and skipped via an `ExtractStats` counter, never crashing the run.
3. **Generators vs lists here?** `extract.py` yields records lazily so we never
   hold all JSON in memory at once.
4. **How do you avoid duplicated code?** Shared helpers (formatting, logging, DB
   access) and a named-query registry rather than inline f-strings everywhere.
5. **How is configuration managed?** `config.py` reads env vars (`PHONEPE_DB`,
   `MYSQL_*`) so the same code runs locally and in production.
6. **Type hints & docstrings?** Used throughout; functions are pure (DB in,
   DataFrame out) which makes them cacheable and testable.
7. **How does caching work in the dashboard?** `st.cache_data` wraps the analytics
   accessors so repeated interactions don't re-query.
8. **How do you test it?** Compile checks on all modules, the ETL runs end-to-end,
   and all 60 SQL statements are executed against the DB.
9. **Pandas techniques used?** `groupby`, `pct_change`, `rolling`, `cumsum`,
   `rank`, and vectorised derived columns.
10. **Why SQLAlchemy over a raw driver?** Backend abstraction, connection pooling,
    parameter binding (safer), and `pandas.read_sql` integration.

## Business Intelligence questions (10)
1. **What KPIs did you choose and why?** Value, volume, ATV, users, app opens,
   growth %, market share, insurance coverage - the metrics leadership acts on.
2. **Star schema vs flat table?** The star keeps facts narrow and dimensions
   reusable, enabling fast, consistent roll-ups.
3. **How do you show seasonality vs trend?** A 4-quarter moving average overlaid on
   raw value separates the festival-season bump from the underlying trend.
4. **What story does the data tell?** A maturing market: high CAGR but decelerating
   YoY, concentrated in the South and top-5 states, with merchant payments taking
   share from recharge.
5. **How do you make a dashboard actionable?** Pair every chart with a KPI and an
   insight/recommendation; add filters for self-service drill-down.
6. **What is a good chart choice for category mix?** A donut for a snapshot, a
   stacked-area for the mix over time - avoid pie charts for many categories.
7. **How do you convey concentration?** A cumulative-share (Pareto) line and a
   quintile share ("top 20% of districts = ~64% of value").
8. **How do you keep BI trustworthy?** A validation gate + reports generated from
   the live warehouse so the numbers on the slide match the database.
9. **How would you scale this to real Pulse data?** Same schema; swap the generator
   for the real repo reader, move to MySQL, and materialise roll-ups.
10. **What's the business value?** It turns raw payment logs into where-to-invest
    decisions: which states to defend, which categories to push, when to run
    campaigns, and where to grow insurance.

## How to present this confidently
- Open with the outcome ("a 10-page BI dashboard over ~48k rows with auto reports"),
  then the architecture, then one or two crisp insights with numbers.
- Emphasise the engineering rigour (validation gate, tested queries, portable SQL).
- Keep a couple of specific figures ready: top-5 states ~40% of value, merchant
  share ~15%->25%, Q4 ~40% above Q1.
