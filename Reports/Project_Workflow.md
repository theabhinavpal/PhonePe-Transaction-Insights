# Project Workflow

## One-time setup
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cold-start build (SQLite, zero external services)
```bash
python main.py all          # generate dataset + run full ETL
python -m reports.build_reports
streamlit run dashboard/app.py
```

## Step-by-step
| Step | Command | Output |
|---|---|---|
| 1. Generate data | `python main.py generate` | 6,336 Pulse-format JSON files |
| 2. Run ETL | `python main.py etl` | 12 tables, ~48k rows, indexes + views |
| 3. Validate | `python main.py validate` | 20/20 data-quality rules |
| 4. Build reports | `python -m reports.build_reports` | MD + PDF (live figures) |
| 5. Launch dashboard | `python main.py dashboard` | Streamlit at :8501 |

## Production (MySQL 8)
```bash
mysql -u root -p < database/database_schema.sql
export PHONEPE_DB=mysql MYSQL_USER=root MYSQL_PASSWORD=***
python -m database.insert_data          # schema + load + indexes + views
mysql -u root -p phonepe_insights < database/stored_procedures.sql   # optional
```

## Refresh cadence
The ETL is idempotent (tables are replace-loaded and views recreated), so a
scheduled `python main.py etl && python -m reports.build_reports` safely
refreshes the warehouse and the executive report each quarter.
