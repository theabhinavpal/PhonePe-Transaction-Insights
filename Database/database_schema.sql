-- ====================================================================
-- database_schema.sql
-- PhonePe Transaction Insights - Production schema (MySQL 8+)
-- --------------------------------------------------------------------
-- Star-schema design: two conformed dimensions (dim_state, dim_date)
-- surrounded by aggregated / map / top fact tables sourced from the
-- three PhonePe Pulse layers (aggregated, map, top).
--
-- Portability note: the portable test harness loads the same logical
-- model into SQLite via the Python ETL (etl/pipeline.py). This file is
-- the canonical MySQL definition used in production deployments.
-- ====================================================================

CREATE DATABASE IF NOT EXISTS phonepe_insights
    CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE phonepe_insights;

-- --------------------------------------------------------------------
-- DIMENSIONS
-- --------------------------------------------------------------------

-- Conformed geography dimension. Exists so every fact can roll up to
-- region / zone without repeating those attributes on each fact row.
CREATE TABLE IF NOT EXISTS dim_state (
    state          VARCHAR(64)  NOT NULL,
    state_display  VARCHAR(96)  NOT NULL,
    region         VARCHAR(24)  NOT NULL,
    zone           VARCHAR(24)  NOT NULL,
    PRIMARY KEY (state)
) ENGINE=InnoDB;

-- Conformed time dimension at (year, quarter) grain. Centralises quarter
-- labels and a monotonic period_index used for trend / window queries.
CREATE TABLE IF NOT EXISTS dim_date (
    year           SMALLINT     NOT NULL,
    quarter        TINYINT      NOT NULL,
    quarter_label  VARCHAR(12)  NOT NULL,
    period_months  VARCHAR(12)  NOT NULL,
    period_index   SMALLINT     NOT NULL,
    PRIMARY KEY (year, quarter),
    CONSTRAINT chk_quarter CHECK (quarter BETWEEN 1 AND 4)
) ENGINE=InnoDB;

-- --------------------------------------------------------------------
-- AGGREGATED FACTS (state x period grain)
-- --------------------------------------------------------------------

-- Transaction value/volume by payment category. The primary fact table
-- powering almost every KPI on the dashboard.
CREATE TABLE IF NOT EXISTS agg_transaction (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    state       VARCHAR(64)  NOT NULL,
    year        SMALLINT     NOT NULL,
    quarter     TINYINT      NOT NULL,
    category    VARCHAR(48)  NOT NULL,
    txn_count   BIGINT       NOT NULL,
    txn_amount  DECIMAL(20,2) NOT NULL,
    CONSTRAINT fk_aggtxn_state FOREIGN KEY (state) REFERENCES dim_state(state),
    CONSTRAINT fk_aggtxn_date  FOREIGN KEY (year, quarter) REFERENCES dim_date(year, quarter),
    CONSTRAINT chk_aggtxn_nonneg CHECK (txn_count >= 0 AND txn_amount >= 0)
) ENGINE=InnoDB;

-- Registered users and app opens by state x period.
CREATE TABLE IF NOT EXISTS agg_user (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    state             VARCHAR(64) NOT NULL,
    year              SMALLINT    NOT NULL,
    quarter           TINYINT     NOT NULL,
    registered_users  BIGINT      NOT NULL,
    app_opens         BIGINT      NOT NULL,
    CONSTRAINT fk_agguser_state FOREIGN KEY (state) REFERENCES dim_state(state),
    CONSTRAINT fk_agguser_date  FOREIGN KEY (year, quarter) REFERENCES dim_date(year, quarter)
) ENGINE=InnoDB;

-- Device-brand breakdown of the user base (long format).
CREATE TABLE IF NOT EXISTS agg_user_device (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    state       VARCHAR(64) NOT NULL,
    year        SMALLINT    NOT NULL,
    quarter     TINYINT     NOT NULL,
    brand       VARCHAR(32) NOT NULL,
    user_count  BIGINT      NOT NULL,
    percentage  DECIMAL(8,4) NOT NULL,
    CONSTRAINT fk_aggdev_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;

-- Insurance policies sold and premium collected (live from 2020 Q1).
CREATE TABLE IF NOT EXISTS agg_insurance (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    state           VARCHAR(64) NOT NULL,
    year            SMALLINT    NOT NULL,
    quarter         TINYINT     NOT NULL,
    policy_count    BIGINT      NOT NULL,
    premium_amount  DECIMAL(20,2) NOT NULL,
    CONSTRAINT fk_aggins_state FOREIGN KEY (state) REFERENCES dim_state(state),
    CONSTRAINT fk_aggins_date  FOREIGN KEY (year, quarter) REFERENCES dim_date(year, quarter)
) ENGINE=InnoDB;

-- --------------------------------------------------------------------
-- MAP FACTS (state x district x period grain)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS map_transaction (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    state       VARCHAR(64) NOT NULL,
    year        SMALLINT    NOT NULL,
    quarter     TINYINT     NOT NULL,
    district    VARCHAR(96) NOT NULL,
    txn_count   BIGINT      NOT NULL,
    txn_amount  DECIMAL(20,2) NOT NULL,
    CONSTRAINT fk_maptxn_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS map_user (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    state             VARCHAR(64) NOT NULL,
    year              SMALLINT    NOT NULL,
    quarter           TINYINT     NOT NULL,
    district          VARCHAR(96) NOT NULL,
    registered_users  BIGINT      NOT NULL,
    app_opens         BIGINT      NOT NULL,
    CONSTRAINT fk_mapuser_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS map_insurance (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    state           VARCHAR(64) NOT NULL,
    year            SMALLINT    NOT NULL,
    quarter         TINYINT     NOT NULL,
    district        VARCHAR(96) NOT NULL,
    policy_count    BIGINT      NOT NULL,
    premium_amount  DECIMAL(20,2) NOT NULL,
    CONSTRAINT fk_mapins_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;

-- --------------------------------------------------------------------
-- TOP FACTS (ranked district / pincode leaderboards per period)
-- --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS top_transaction_district (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    state       VARCHAR(64) NOT NULL,
    year        SMALLINT    NOT NULL,
    quarter     TINYINT     NOT NULL,
    district    VARCHAR(96) NOT NULL,
    txn_count   BIGINT      NOT NULL,
    txn_amount  DECIMAL(20,2) NOT NULL,
    CONSTRAINT fk_topdist_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS top_transaction_pincode (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    state       VARCHAR(64) NOT NULL,
    year        SMALLINT    NOT NULL,
    quarter     TINYINT     NOT NULL,
    pincode     VARCHAR(12) NOT NULL,
    txn_count   BIGINT      NOT NULL,
    txn_amount  DECIMAL(20,2) NOT NULL,
    CONSTRAINT fk_toppin_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS top_user_pincode (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    state             VARCHAR(64) NOT NULL,
    year              SMALLINT    NOT NULL,
    quarter           TINYINT     NOT NULL,
    pincode           VARCHAR(12) NOT NULL,
    registered_users  BIGINT      NOT NULL,
    CONSTRAINT fk_topupin_state FOREIGN KEY (state) REFERENCES dim_state(state)
) ENGINE=InnoDB;
