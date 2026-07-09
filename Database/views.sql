-- ====================================================================
-- views.sql  -  Reusable analytical views (ANSI SQL, MySQL + SQLite safe)
-- ====================================================================
USE phonepe_insights;

DROP VIEW IF EXISTS vw_state_txn_summary;
CREATE VIEW vw_state_txn_summary AS
SELECT t.state, s.state_display, s.region, t.year, t.quarter,
       SUM(t.txn_count)  AS txn_count,
       SUM(t.txn_amount) AS txn_amount
FROM agg_transaction t
JOIN dim_state s ON s.state = t.state
GROUP BY t.state, s.state_display, s.region, t.year, t.quarter;

DROP VIEW IF EXISTS vw_national_quarter;
CREATE VIEW vw_national_quarter AS
SELECT year, quarter,
       SUM(txn_count)  AS txn_count,
       SUM(txn_amount) AS txn_amount
FROM agg_transaction
GROUP BY year, quarter;

DROP VIEW IF EXISTS vw_category_share;
CREATE VIEW vw_category_share AS
SELECT category,
       SUM(txn_count)  AS txn_count,
       SUM(txn_amount) AS txn_amount
FROM agg_transaction
GROUP BY category;

DROP VIEW IF EXISTS vw_state_avg_ticket;
CREATE VIEW vw_state_avg_ticket AS
SELECT s.state_display, s.region,
       SUM(t.txn_amount) / SUM(t.txn_count) AS avg_ticket
FROM agg_transaction t
JOIN dim_state s ON s.state = t.state
GROUP BY s.state_display, s.region;

DROP VIEW IF EXISTS vw_insurance_state;
CREATE VIEW vw_insurance_state AS
SELECT s.state_display, s.region,
       SUM(i.policy_count)   AS policy_count,
       SUM(i.premium_amount) AS premium_amount
FROM agg_insurance i
JOIN dim_state s ON s.state = i.state
GROUP BY s.state_display, s.region;
