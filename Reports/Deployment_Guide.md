# Deployment & Bonus Features

Features are tagged **[Beginner]**, **[Intermediate]**, **[Advanced]**.

## Theming
- **[Beginner] Light/Dark theme** - add `.streamlit/config.toml` with a
  `[theme]` block, or a sidebar toggle that swaps the Plotly template.

## Geospatial
- **[Intermediate] Interactive India map** - `src/visualizations.choropleth_states`
  already accepts an India states GeoJSON (`featureidkey="properties.ST_NM"`);
  drop `india_states.geojson` in `dashboard/` and pass it in.
- **[Advanced] District choropleth** - join `map_transaction` to a district
  GeoJSON for sub-state drill-down.

## Performance
- **[Beginner] Caching** - dashboard already uses `st.cache_data`.
- **[Intermediate] Indexes** - `database/indexes.sql` covers filter/group-by cols.
- **[Advanced] Materialised roll-ups** - persist `vw_state_txn_summary` as a table
  refreshed by the ETL for very large datasets.

## Containerisation & hosting
- **[Intermediate] Docker** - a `Dockerfile` running `streamlit run dashboard/app.py`.
- **[Beginner] Streamlit Community Cloud** - point it at `dashboard/app.py`.
- **[Intermediate] Render / Railway** - web service, start command
  `streamlit run dashboard/app.py --server.port $PORT`.

## Automation
- **[Advanced] GitHub Actions CI** - run `python main.py all && python main.py validate`
  on every push; fail the build if any validation rule fails.
- **[Advanced] Scheduled refresh** - a cron/Action that reruns the ETL and
  `reports.build_reports`, committing the refreshed PDF.

### Example Dockerfile
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python main.py all
EXPOSE 8501
CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0"]
```

### Example GitHub Actions workflow
```yaml
name: etl-ci
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python main.py all
      - run: python main.py validate
      - run: python -m reports.build_reports
```
