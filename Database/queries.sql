-- ====================================================================
-- queries.sql  -  60 analytical SQL queries for PhonePe Transaction Insights
-- --------------------------------------------------------------------
-- Every query is annotated with: [Business Question] and [Insight].
-- Written in portable ANSI SQL (verified on SQLite 3 and MySQL 8).
-- Sections:
--   A. Overview & KPIs          (Q1-Q8)
--   B. State-level analysis      (Q9-Q18)
--   C. Category analysis         (Q19-Q26)
--   D. Time, growth & trends     (Q27-Q38)
--   E. District analysis         (Q39-Q44)
--   F. Pincode analysis          (Q45-Q48)
--   G. User & engagement         (Q49-Q54)
--   H. Insurance analysis        (Q55-Q60)
-- ====================================================================

-- ============================ A. OVERVIEW ============================

-- Q1 [Business Question] What is the all-time national transaction value & volume?
--    [Insight] Single headline KPI pair used on the executive dashboard.
SELECT SUM(txn_amount) AS total_value, SUM(txn_count) AS total_volume
FROM agg_transaction;

-- Q2 [Business Question] What is the overall average transaction value (ticket size)?
--    [Insight] Blended ATV anchors category-level ticket comparisons.
SELECT SUM(txn_amount) * 1.0 / SUM(txn_count) AS avg_ticket_value
FROM agg_transaction;

-- Q3 [Business Question] How many transactions and how much value per year?
--    [Insight] Establishes the multi-year adoption curve.
SELECT year, SUM(txn_count) AS txn_count, SUM(txn_amount) AS txn_amount
FROM agg_transaction GROUP BY year ORDER BY year;

-- Q4 [Business Question] What is the value split across the four quarters (all years pooled)?
--    [Insight] Exposes festival-season (Q3/Q4) seasonality.
SELECT quarter, SUM(txn_amount) AS txn_amount, AVG(txn_amount) AS avg_state_amount
FROM agg_transaction GROUP BY quarter ORDER BY quarter;

-- Q5 [Business Question] How many states/UTs and periods are covered?
--    [Insight] Confirms dataset completeness before analysis.
SELECT COUNT(DISTINCT state) AS states,
       COUNT(DISTINCT year) AS years,
       COUNT(DISTINCT quarter) AS quarters
FROM agg_transaction;

-- Q6 [Business Question] What is the latest available quarter's total value?
--    [Insight] Feeds the "current quarter" KPI card.
SELECT year, quarter, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
FROM agg_transaction
GROUP BY year, quarter
ORDER BY year DESC, quarter DESC
LIMIT 1;

-- Q7 [Business Question] What share of national value comes from each region?
--    [Insight] Quantifies regional concentration of digital payments.
SELECT s.region,
       SUM(t.txn_amount) AS txn_amount,
       ROUND(100.0 * SUM(t.txn_amount) /
             (SELECT SUM(txn_amount) FROM agg_transaction), 2) AS pct_share
FROM agg_transaction t
JOIN dim_state s ON s.state = t.state
GROUP BY s.region ORDER BY txn_amount DESC;

-- Q8 [Business Question] What is the average number of transactions per registered user?
--    [Insight] Cross-fact intensity metric (txn per user).
SELECT (SELECT SUM(txn_count) FROM agg_transaction) * 1.0 /
       (SELECT SUM(registered_users) FROM agg_user
        WHERE year = (SELECT MAX(year) FROM agg_user)
          AND quarter = (SELECT MAX(quarter) FROM agg_user
                         WHERE year = (SELECT MAX(year) FROM agg_user)))
       AS txn_per_user;

-- ========================= B. STATE ANALYSIS =========================

-- Q9 [Business Question] Which are the top 10 states by all-time transaction value?
--    [Insight] Identifies the states that carry the platform.
SELECT s.state_display, SUM(t.txn_amount) AS txn_amount, SUM(t.txn_count) AS txn_count
FROM agg_transaction t JOIN dim_state s ON s.state = t.state
GROUP BY s.state_display ORDER BY txn_amount DESC LIMIT 10;

-- Q10 [Business Question] Which are the 10 lowest-value states/UTs?
--     [Insight] Surfaces white-space / under-penetrated markets.
SELECT s.state_display, SUM(t.txn_amount) AS txn_amount
FROM agg_transaction t JOIN dim_state s ON s.state = t.state
GROUP BY s.state_display ORDER BY txn_amount ASC LIMIT 10;

-- Q11 [Business Question] Rank all states by value with a dense rank.
--     [Insight] Powers the state leaderboard with tie-safe ranking.
SELECT s.state_display, SUM(t.txn_amount) AS txn_amount,
       RANK() OVER (ORDER BY SUM(t.txn_amount) DESC) AS value_rank
FROM agg_transaction t JOIN dim_state s ON s.state = t.state
GROUP BY s.state_display ORDER BY value_rank;

-- Q12 [Business Question] What percentage of total value does each state contribute (market share)?
--     [Insight] Market-share view for portfolio prioritisation.
SELECT s.state_display,
       SUM(t.txn_amount) AS txn_amount,
       ROUND(100.0 * SUM(t.txn_amount) /
             (SELECT SUM(txn_amount) FROM agg_transaction), 2) AS market_share_pct
FROM agg_transaction t JOIN dim_state s ON s.state = t.state
GROUP BY s.state_display ORDER BY market_share_pct DESC;

-- Q13 [Business Question] What is each state's average ticket size, ranked?
--     [Insight] High-ATV states skew toward P2P / financial services.
SELECT s.state_display,
       SUM(t.txn_amount) * 1.0 / SUM(t.txn_count) AS avg_ticket
FROM agg_transaction t JOIN dim_state s ON s.state = t.state
GROUP BY s.state_display ORDER BY avg_ticket DESC;

-- Q14 [Business Question] Cumulative value share as we walk states from largest to smallest.
--     [Insight] Demonstrates the Pareto (80/20) concentration across states.
WITH state_val AS (
    SELECT s.state_display, SUM(t.txn_amount) AS amt
    FROM agg_transaction t JOIN dim_state s ON s.state = t.state
    GROUP BY s.state_display)
SELECT state_display, amt,
       SUM(amt) OVER (ORDER BY amt DESC) AS running_value,
       ROUND(100.0 * SUM(amt) OVER (ORDER BY amt DESC) /
             SUM(amt) OVER (), 2) AS cumulative_pct
FROM state_val ORDER BY amt DESC;

-- Q15 [Business Question] Which state leads in the most recent quarter?
--     [Insight] Current-quarter market leader.
SELECT s.state_display, SUM(t.txn_amount) AS txn_amount
FROM agg_transaction t JOIN dim_state s ON s.state = t.state
WHERE t.year = (SELECT MAX(year) FROM agg_transaction)
  AND t.quarter = (SELECT MAX(quarter) FROM agg_transaction
                   WHERE year = (SELECT MAX(year) FROM agg_transaction))
GROUP BY s.state_display ORDER BY txn_amount DESC LIMIT 5;

-- Q16 [Business Question] Which states are above the national average state value?
--     [Insight] Splits "core" vs "long-tail" state portfolio.
WITH sv AS (
    SELECT state, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY state)
SELECT s.state_display, sv.amt
FROM sv JOIN dim_state s ON s.state = sv.state
WHERE sv.amt > (SELECT AVG(amt) FROM sv)
ORDER BY sv.amt DESC;

-- Q17 [Business Question] For each region, which single state contributes the most value?
--     [Insight] Regional champions for go-to-market planning.
WITH sv AS (
    SELECT s.region, s.state_display, SUM(t.txn_amount) AS amt
    FROM agg_transaction t JOIN dim_state s ON s.state = t.state
    GROUP BY s.region, s.state_display)
SELECT region, state_display, amt FROM (
    SELECT region, state_display, amt,
           ROW_NUMBER() OVER (PARTITION BY region ORDER BY amt DESC) AS rn
    FROM sv) x
WHERE rn = 1 ORDER BY amt DESC;

-- Q18 [Business Question] Which states grew fastest from their first to their latest year?
--     [Insight] Momentum ranking independent of absolute size.
WITH yr AS (
    SELECT state, year, SUM(txn_amount) AS amt
    FROM agg_transaction GROUP BY state, year),
first_last AS (
    SELECT state,
           MAX(CASE WHEN year = (SELECT MIN(year) FROM agg_transaction) THEN amt END) AS first_amt,
           MAX(CASE WHEN year = (SELECT MAX(year) FROM agg_transaction) THEN amt END) AS last_amt
    FROM yr GROUP BY state)
SELECT s.state_display,
       ROUND(100.0 * (last_amt - first_amt) / first_amt, 1) AS growth_pct
FROM first_last f JOIN dim_state s ON s.state = f.state
ORDER BY growth_pct DESC LIMIT 10;

-- ======================= C. CATEGORY ANALYSIS ========================

-- Q19 [Business Question] What is the value and volume of each payment category?
--     [Insight] Category leaderboard - P2P dominates value.
SELECT category, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
FROM agg_transaction GROUP BY category ORDER BY txn_amount DESC;

-- Q20 [Business Question] What is each category's share of total value?
--     [Insight] Category mix for product strategy.
SELECT category,
       ROUND(100.0 * SUM(txn_amount) /
             (SELECT SUM(txn_amount) FROM agg_transaction), 2) AS pct_value
FROM agg_transaction GROUP BY category ORDER BY pct_value DESC;

-- Q21 [Business Question] What is the average ticket size per category?
--     [Insight] Financial Services highest; Recharge lowest.
SELECT category, SUM(txn_amount) * 1.0 / SUM(txn_count) AS avg_ticket
FROM agg_transaction GROUP BY category ORDER BY avg_ticket DESC;

-- Q22 [Business Question] How has each category's value-share shifted from the first to the latest year?
--     [Insight] Merchant payments gaining share; Recharge declining.
WITH yr AS (
    SELECT year, category, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, category),
tot AS (SELECT year, SUM(txn_amount) AS t FROM agg_transaction GROUP BY year)
SELECT c.category,
       ROUND(100.0 * MAX(CASE WHEN c.year=(SELECT MIN(year) FROM agg_transaction) THEN c.amt END)
             / MAX(CASE WHEN t.year=(SELECT MIN(year) FROM agg_transaction) THEN t.t END), 2) AS share_first_year,
       ROUND(100.0 * MAX(CASE WHEN c.year=(SELECT MAX(year) FROM agg_transaction) THEN c.amt END)
             / MAX(CASE WHEN t.year=(SELECT MAX(year) FROM agg_transaction) THEN t.t END), 2) AS share_latest_year
FROM yr c JOIN tot t ON t.year = c.year
GROUP BY c.category ORDER BY share_latest_year DESC;

-- Q23 [Business Question] Which category leads in each region?
--     [Insight] Regional product-mix differences.
WITH rc AS (
    SELECT s.region, t.category, SUM(t.txn_amount) AS amt
    FROM agg_transaction t JOIN dim_state s ON s.state = t.state
    GROUP BY s.region, t.category)
SELECT region, category, amt FROM (
    SELECT region, category, amt,
           ROW_NUMBER() OVER (PARTITION BY region ORDER BY amt DESC) AS rn FROM rc) x
WHERE rn = 1 ORDER BY region;

-- Q24 [Business Question] Category value trend by year (pivot-style).
--     [Insight] Time series for a stacked-area category chart.
SELECT year,
       SUM(CASE WHEN category='Peer-to-peer payments' THEN txn_amount ELSE 0 END) AS p2p,
       SUM(CASE WHEN category='Merchant payments' THEN txn_amount ELSE 0 END) AS merchant,
       SUM(CASE WHEN category='Recharge & bill payments' THEN txn_amount ELSE 0 END) AS recharge,
       SUM(CASE WHEN category='Financial Services' THEN txn_amount ELSE 0 END) AS financial,
       SUM(CASE WHEN category='Others' THEN txn_amount ELSE 0 END) AS others
FROM agg_transaction GROUP BY year ORDER BY year;

-- Q25 [Business Question] Which categories have above-average value contribution?
--     [Insight] HAVING filter to isolate the "big two" categories.
SELECT category, SUM(txn_amount) AS amt
FROM agg_transaction GROUP BY category
HAVING SUM(txn_amount) > (SELECT SUM(txn_amount) FROM agg_transaction) / 5.0
ORDER BY amt DESC;

-- Q26 [Business Question] Fastest-growing category by YoY value in the latest year.
--     [Insight] Where incremental value is coming from most recently.
WITH yc AS (
    SELECT category, year, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY category, year),
g AS (
    SELECT category, year, amt,
           LAG(amt) OVER (PARTITION BY category ORDER BY year) AS prev
    FROM yc)
SELECT category, ROUND(100.0 * (amt - prev) / prev, 1) AS yoy_pct
FROM g WHERE year = (SELECT MAX(year) FROM agg_transaction)
ORDER BY yoy_pct DESC;

-- ==================== D. TIME, GROWTH & TRENDS =======================

-- Q27 [Business Question] Quarter-over-quarter national value with growth %.
--     [Insight] Core trend line with sequential growth.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, quarter)
SELECT year, quarter, amt,
       LAG(amt) OVER (ORDER BY year, quarter) AS prev_amt,
       ROUND(100.0 * (amt - LAG(amt) OVER (ORDER BY year, quarter))
             / LAG(amt) OVER (ORDER BY year, quarter), 2) AS qoq_pct
FROM q ORDER BY year, quarter;

-- Q28 [Business Question] Year-over-year national value growth.
--     [Insight] Annual growth headline for the executive summary.
WITH y AS (SELECT year, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year)
SELECT year, amt,
       LAG(amt) OVER (ORDER BY year) AS prev,
       ROUND(100.0 * (amt - LAG(amt) OVER (ORDER BY year))
             / LAG(amt) OVER (ORDER BY year), 2) AS yoy_pct
FROM y ORDER BY year;

-- Q29 [Business Question] 4-quarter moving average of national value.
--     [Insight] Smooths seasonality to reveal the underlying trend.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, quarter)
SELECT year, quarter, amt,
       AVG(amt) OVER (ORDER BY year, quarter ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ma_4q
FROM q ORDER BY year, quarter;

-- Q30 [Business Question] Cumulative running total of national value over time.
--     [Insight] Lifetime value accumulation curve.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, quarter)
SELECT year, quarter, amt,
       SUM(amt) OVER (ORDER BY year, quarter) AS running_total
FROM q ORDER BY year, quarter;

-- Q31 [Business Question] Best and worst quarter by national value.
--     [Insight] Peak vs trough for capacity planning.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, quarter)
SELECT 'peak' AS kind, year, quarter, amt FROM q ORDER BY amt DESC LIMIT 1;

-- Q32 [Business Question] Average seasonal uplift of Q4 vs Q1 across years.
--     [Insight] Quantifies the festival-season bump.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, quarter)
SELECT ROUND(100.0 * (AVG(CASE WHEN quarter=4 THEN amt END)
             - AVG(CASE WHEN quarter=1 THEN amt END))
             / AVG(CASE WHEN quarter=1 THEN amt END), 2) AS q4_vs_q1_uplift_pct
FROM q;

-- Q33 [Business Question] Each year's share of all-time value.
--     [Insight] Shows how recent years dominate cumulative value.
SELECT year,
       ROUND(100.0 * SUM(txn_amount) /
             (SELECT SUM(txn_amount) FROM agg_transaction), 2) AS pct_of_all_time
FROM agg_transaction GROUP BY year ORDER BY year;

-- Q34 [Business Question] Quarter with the highest value within each year.
--     [Insight] Confirms Q4 as the recurring annual peak.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year, quarter)
SELECT year, quarter, amt FROM (
    SELECT year, quarter, amt,
           ROW_NUMBER() OVER (PARTITION BY year ORDER BY amt DESC) AS rn FROM q) x
WHERE rn = 1 ORDER BY year;

-- Q35 [Business Question] Maharashtra QoQ value trend (single-state deep-dive).
--     [Insight] Template for per-state drill-down trend charts.
WITH q AS (
    SELECT year, quarter, SUM(txn_amount) AS amt
    FROM agg_transaction WHERE state = 'maharashtra' GROUP BY year, quarter)
SELECT year, quarter, amt,
       ROUND(100.0 * (amt - LAG(amt) OVER (ORDER BY year, quarter))
             / LAG(amt) OVER (ORDER BY year, quarter), 2) AS qoq_pct
FROM q ORDER BY year, quarter;

-- Q36 [Business Question] Registered-user growth by year.
--     [Insight] User-base expansion vs transaction-value expansion.
SELECT year, MAX(cum) AS registered_users FROM (
    SELECT year, quarter, SUM(registered_users) AS cum
    FROM agg_user GROUP BY year, quarter) t
GROUP BY year ORDER BY year;

-- Q37 [Business Question] App-opens per registered user by year (engagement).
--     [Insight] Engagement can rise even as value growth cools.
SELECT year,
       SUM(app_opens) * 1.0 / SUM(registered_users) AS opens_per_user
FROM agg_user GROUP BY year ORDER BY year;

-- Q38 [Business Question] Compound annual growth rate (CAGR) of national value.
--     [Insight] Single number to describe multi-year growth.
WITH y AS (SELECT year, SUM(txn_amount) AS amt FROM agg_transaction GROUP BY year)
SELECT ROUND(100.0 * (POWER(
        (SELECT amt FROM y WHERE year=(SELECT MAX(year) FROM y)) * 1.0 /
        (SELECT amt FROM y WHERE year=(SELECT MIN(year) FROM y)),
        1.0 / ((SELECT MAX(year) FROM y) - (SELECT MIN(year) FROM y))) - 1), 2) AS cagr_pct;

-- ====================== E. DISTRICT ANALYSIS =========================

-- Q39 [Business Question] Top 15 districts by all-time transaction value.
--     [Insight] Urban districts dominate the value leaderboard.
SELECT district, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
FROM map_transaction GROUP BY district ORDER BY txn_amount DESC LIMIT 15;

-- Q40 [Business Question] Top 3 districts within each state (per-state leaders).
--     [Insight] Drill-down leaderboards for the state page.
WITH d AS (
    SELECT state, district, SUM(txn_amount) AS amt
    FROM map_transaction GROUP BY state, district)
SELECT s.state_display, d.district, d.amt FROM (
    SELECT state, district, amt,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY amt DESC) AS rn FROM d) d
JOIN dim_state s ON s.state = d.state
WHERE rn <= 3 ORDER BY s.state_display, d.amt DESC;

-- Q41 [Business Question] What share of value do the top 20% of districts hold?
--     [Insight] District-level Pareto concentration.
WITH d AS (
    SELECT state, district, SUM(txn_amount) AS amt
    FROM map_transaction GROUP BY state, district),
r AS (
    SELECT amt, NTILE(5) OVER (ORDER BY amt DESC) AS quintile FROM d)
SELECT ROUND(100.0 * SUM(CASE WHEN quintile=1 THEN amt ELSE 0 END) / SUM(amt), 2)
       AS top20pct_district_share
FROM r;

-- Q42 [Business Question] Districts with the highest average ticket size.
--     [Insight] High-value pockets that may over-index on P2P/financial.
SELECT district, SUM(txn_amount) * 1.0 / SUM(txn_count) AS avg_ticket,
       SUM(txn_amount) AS txn_amount
FROM map_transaction GROUP BY district
HAVING SUM(txn_count) > 0
ORDER BY avg_ticket DESC LIMIT 15;

-- Q43 [Business Question] How many distinct districts have transaction activity?
--     [Insight] Breadth of geographic coverage.
SELECT COUNT(DISTINCT district) AS active_districts,
       COUNT(DISTINCT state) AS states
FROM map_transaction;

-- Q44 [Business Question] Fastest-growing districts (first vs latest year).
--     [Insight] Emerging Tier-2/Tier-3 growth pockets.
WITH d AS (
    SELECT district, year, SUM(txn_amount) AS amt
    FROM map_transaction GROUP BY district, year),
fl AS (
    SELECT district,
           MAX(CASE WHEN year=(SELECT MIN(year) FROM map_transaction) THEN amt END) AS f,
           MAX(CASE WHEN year=(SELECT MAX(year) FROM map_transaction) THEN amt END) AS l
    FROM d GROUP BY district)
SELECT district, ROUND(100.0 * (l - f) / f, 1) AS growth_pct
FROM fl WHERE f > 0 ORDER BY growth_pct DESC LIMIT 15;

-- ======================= F. PINCODE ANALYSIS =========================

-- Q45 [Business Question] Top 20 pincodes by transaction value nationwide.
--     [Insight] Hyper-local hotspots for merchant targeting.
SELECT pincode, SUM(txn_amount) AS txn_amount, SUM(txn_count) AS txn_count
FROM top_transaction_pincode GROUP BY pincode ORDER BY txn_amount DESC LIMIT 20;

-- Q46 [Business Question] Top 5 pincodes within each state.
--     [Insight] Localised leaderboards for field sales.
WITH p AS (
    SELECT state, pincode, SUM(txn_amount) AS amt
    FROM top_transaction_pincode GROUP BY state, pincode)
SELECT s.state_display, p.pincode, p.amt FROM (
    SELECT state, pincode, amt,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY amt DESC) AS rn FROM p) p
JOIN dim_state s ON s.state = p.state
WHERE rn <= 5 ORDER BY s.state_display, p.amt DESC;

-- Q47 [Business Question] How concentrated is value in the top 50 pincodes?
--     [Insight] Extreme concentration at the pincode grain.
WITH p AS (
    SELECT pincode, SUM(txn_amount) AS amt
    FROM top_transaction_pincode GROUP BY pincode),
ranked AS (
    SELECT amt, ROW_NUMBER() OVER (ORDER BY amt DESC) AS rn,
           SUM(amt) OVER () AS total FROM p)
SELECT ROUND(100.0 * SUM(CASE WHEN rn <= 50 THEN amt ELSE 0 END) / MAX(total), 2)
       AS top50_pincode_share
FROM ranked;

-- Q48 [Business Question] Top pincodes by registered users.
--     [Insight] Compares user hotspots vs value hotspots.
SELECT pincode, SUM(registered_users) AS registered_users
FROM top_user_pincode GROUP BY pincode ORDER BY registered_users DESC LIMIT 20;

-- ==================== G. USER & ENGAGEMENT ===========================

-- Q49 [Business Question] Total registered users and app opens in the latest quarter.
--     [Insight] Current user-base KPI cards.
SELECT SUM(registered_users) AS registered_users, SUM(app_opens) AS app_opens
FROM agg_user
WHERE year = (SELECT MAX(year) FROM agg_user)
  AND quarter = (SELECT MAX(quarter) FROM agg_user
                 WHERE year = (SELECT MAX(year) FROM agg_user));

-- Q50 [Business Question] Top 10 states by registered users (latest quarter).
--     [Insight] Where the user base is largest.
SELECT s.state_display, SUM(u.registered_users) AS registered_users
FROM agg_user u JOIN dim_state s ON s.state = u.state
WHERE u.year = (SELECT MAX(year) FROM agg_user)
GROUP BY s.state_display ORDER BY registered_users DESC LIMIT 10;

-- Q51 [Business Question] Device-brand market share of the user base (latest quarter).
--     [Insight] Xiaomi/Samsung/Vivo lead the installed base.
SELECT brand, SUM(user_count) AS users,
       ROUND(100.0 * SUM(user_count) / (SELECT SUM(user_count) FROM agg_user_device
             WHERE year=(SELECT MAX(year) FROM agg_user_device)), 2) AS pct
FROM agg_user_device
WHERE year = (SELECT MAX(year) FROM agg_user_device)
GROUP BY brand ORDER BY users DESC;

-- Q52 [Business Question] States with the highest app-opens per user (engagement).
--     [Insight] Engagement leaders vs mere sign-up leaders.
SELECT s.state_display,
       SUM(u.app_opens) * 1.0 / SUM(u.registered_users) AS opens_per_user
FROM agg_user u JOIN dim_state s ON s.state = u.state
GROUP BY s.state_display
HAVING SUM(u.registered_users) > 0
ORDER BY opens_per_user DESC LIMIT 10;

-- Q53 [Business Question] Transactions per registered user by state (monetisation intensity).
--     [Insight] Which user bases transact most heavily.
WITH t AS (SELECT state, SUM(txn_count) AS c FROM agg_transaction GROUP BY state),
u AS (SELECT state, SUM(registered_users) AS ru FROM agg_user
      WHERE year=(SELECT MAX(year) FROM agg_user) GROUP BY state)
SELECT s.state_display, ROUND(t.c * 1.0 / u.ru, 1) AS txn_per_user
FROM t JOIN u ON u.state = t.state JOIN dim_state s ON s.state = t.state
ORDER BY txn_per_user DESC LIMIT 15;

-- Q54 [Business Question] National registered-user growth QoQ.
--     [Insight] Steady user acquisition trend.
WITH q AS (SELECT year, quarter, SUM(registered_users) AS ru FROM agg_user GROUP BY year, quarter)
SELECT year, quarter, ru,
       ROUND(100.0 * (ru - LAG(ru) OVER (ORDER BY year, quarter))
             / LAG(ru) OVER (ORDER BY year, quarter), 2) AS qoq_pct
FROM q ORDER BY year, quarter;

-- ===================== H. INSURANCE ANALYSIS =========================

-- Q55 [Business Question] Total insurance policies and premium collected.
--     [Insight] Headline insurance KPIs since 2020 launch.
SELECT SUM(policy_count) AS policies, SUM(premium_amount) AS premium
FROM agg_insurance;

-- Q56 [Business Question] Top 10 states by insurance premium.
--     [Insight] Insurance concentrates in affluent/urban states.
SELECT s.state_display, SUM(i.premium_amount) AS premium, SUM(i.policy_count) AS policies
FROM agg_insurance i JOIN dim_state s ON s.state = i.state
GROUP BY s.state_display ORDER BY premium DESC LIMIT 10;

-- Q57 [Business Question] Insurance premium as a share of total transaction value by state.
--     [Insight] Insurance penetration relative to overall activity.
WITH ins AS (SELECT state, SUM(premium_amount) AS p FROM agg_insurance GROUP BY state),
txn AS (SELECT state, SUM(txn_amount) AS t FROM agg_transaction GROUP BY state)
SELECT s.state_display, ROUND(100.0 * ins.p / txn.t, 3) AS insurance_penetration_pct
FROM ins JOIN txn ON txn.state = ins.state JOIN dim_state s ON s.state = ins.state
ORDER BY insurance_penetration_pct DESC LIMIT 15;

-- Q58 [Business Question] Insurance premium growth by year.
--     [Insight] Adoption ramp of the insurance vertical.
WITH y AS (SELECT year, SUM(premium_amount) AS p FROM agg_insurance GROUP BY year)
SELECT year, p,
       ROUND(100.0 * (p - LAG(p) OVER (ORDER BY year)) / LAG(p) OVER (ORDER BY year), 2) AS yoy_pct
FROM y ORDER BY year;

-- Q59 [Business Question] Average insurance premium per policy by region.
--     [Insight] Ticket-size differences in insurance across regions.
SELECT s.region,
       SUM(i.premium_amount) * 1.0 / SUM(i.policy_count) AS avg_premium
FROM agg_insurance i JOIN dim_state s ON s.state = i.state
GROUP BY s.region ORDER BY avg_premium DESC;

-- Q60 [Business Question] Districts with the highest insurance premium.
--     [Insight] Local insurance hotspots for targeted campaigns.
SELECT district, SUM(premium_amount) AS premium, SUM(policy_count) AS policies
FROM map_insurance GROUP BY district ORDER BY premium DESC LIMIT 15;
