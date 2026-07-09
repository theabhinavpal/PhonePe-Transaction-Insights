-- ====================================================================
-- stored_procedures.sql  (MySQL 8+)  -  optional convenience routines
-- ====================================================================
USE phonepe_insights;

DELIMITER //

-- Top-N states by transaction value for a given year + quarter.
DROP PROCEDURE IF EXISTS sp_top_states//
CREATE PROCEDURE sp_top_states (IN p_year INT, IN p_quarter INT, IN p_limit INT)
BEGIN
    SELECT s.state_display,
           SUM(t.txn_amount) AS txn_amount,
           SUM(t.txn_count)  AS txn_count
    FROM agg_transaction t
    JOIN dim_state s ON s.state = t.state
    WHERE t.year = p_year AND t.quarter = p_quarter
    GROUP BY s.state_display
    ORDER BY txn_amount DESC
    LIMIT p_limit;
END//

-- Year-over-year growth of national transaction value.
DROP PROCEDURE IF EXISTS sp_yoy_growth//
CREATE PROCEDURE sp_yoy_growth ()
BEGIN
    SELECT year,
           SUM(txn_amount) AS txn_amount,
           LAG(SUM(txn_amount)) OVER (ORDER BY year) AS prev_year,
           ROUND(100 * (SUM(txn_amount) - LAG(SUM(txn_amount)) OVER (ORDER BY year))
                 / LAG(SUM(txn_amount)) OVER (ORDER BY year), 2) AS yoy_pct
    FROM agg_transaction
    GROUP BY year
    ORDER BY year;
END//

DELIMITER ;
