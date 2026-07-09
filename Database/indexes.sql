-- ====================================================================
-- indexes.sql  -  Performance indexes for common access patterns
-- Run AFTER data load. All are secondary (non-unique) indexes chosen to
-- cover the dashboard's filter + group-by columns (state, year, quarter,
-- category). On MySQL/InnoDB the PRIMARY KEY already clusters on id.
-- ====================================================================
USE phonepe_insights;

CREATE INDEX ix_aggtxn_state  ON agg_transaction (state);
CREATE INDEX ix_aggtxn_yq     ON agg_transaction (year, quarter);
CREATE INDEX ix_aggtxn_cat    ON agg_transaction (category);
CREATE INDEX ix_aggtxn_cover  ON agg_transaction (year, quarter, state, category);

CREATE INDEX ix_agguser_state ON agg_user (state);
CREATE INDEX ix_agguser_yq    ON agg_user (year, quarter);

CREATE INDEX ix_aggins_state  ON agg_insurance (state);
CREATE INDEX ix_aggins_yq     ON agg_insurance (year, quarter);

CREATE INDEX ix_maptxn_state  ON map_transaction (state, year, quarter);
CREATE INDEX ix_mapuser_state ON map_user (state, year, quarter);

CREATE INDEX ix_topdist_state ON top_transaction_district (state, year, quarter);
CREATE INDEX ix_toppin_state  ON top_transaction_pincode (state, year, quarter);
CREATE INDEX ix_topupin_state ON top_user_pincode (state, year, quarter);
