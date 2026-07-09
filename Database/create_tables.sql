-- ====================================================================
-- create_tables.sql
-- Portable, idempotent CREATE TABLE statements (no CREATE DATABASE).
-- Kept ANSI-friendly so it runs on both MySQL 8 and SQLite. The Python
-- loader (insert_data.py) and the ETL both rely on these definitions.
-- For full MySQL constraints/engine options see database_schema.sql.
-- ====================================================================

CREATE TABLE IF NOT EXISTS dim_state (
    state          VARCHAR(64) PRIMARY KEY,
    state_display  VARCHAR(96) NOT NULL,
    region         VARCHAR(24) NOT NULL,
    zone           VARCHAR(24) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    year           SMALLINT NOT NULL,
    quarter        SMALLINT NOT NULL,
    quarter_label  VARCHAR(12) NOT NULL,
    period_months  VARCHAR(12) NOT NULL,
    period_index   SMALLINT NOT NULL,
    PRIMARY KEY (year, quarter)
);

CREATE TABLE IF NOT EXISTS agg_transaction (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    category VARCHAR(48), txn_count BIGINT, txn_amount DECIMAL(20,2)
);

CREATE TABLE IF NOT EXISTS agg_user (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    registered_users BIGINT, app_opens BIGINT
);

CREATE TABLE IF NOT EXISTS agg_user_device (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    brand VARCHAR(32), user_count BIGINT, percentage DECIMAL(8,4)
);

CREATE TABLE IF NOT EXISTS agg_insurance (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    policy_count BIGINT, premium_amount DECIMAL(20,2)
);

CREATE TABLE IF NOT EXISTS map_transaction (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    district VARCHAR(96), txn_count BIGINT, txn_amount DECIMAL(20,2)
);

CREATE TABLE IF NOT EXISTS map_user (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    district VARCHAR(96), registered_users BIGINT, app_opens BIGINT
);

CREATE TABLE IF NOT EXISTS map_insurance (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    district VARCHAR(96), policy_count BIGINT, premium_amount DECIMAL(20,2)
);

CREATE TABLE IF NOT EXISTS top_transaction_district (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    district VARCHAR(96), txn_count BIGINT, txn_amount DECIMAL(20,2)
);

CREATE TABLE IF NOT EXISTS top_transaction_pincode (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    pincode VARCHAR(12), txn_count BIGINT, txn_amount DECIMAL(20,2)
);

CREATE TABLE IF NOT EXISTS top_user_pincode (
    state VARCHAR(64), year SMALLINT, quarter SMALLINT,
    pincode VARCHAR(12), registered_users BIGINT
);
