# Data Dictionary

Star schema: two conformed dimensions (`dim_state`, `dim_date`) surrounded by
aggregated / map / top fact tables sourced from the three PhonePe Pulse layers.

## Dimensions

### dim_state
| Column | Type | Description |
|---|---|---|
| state | VARCHAR(64) | Slug key, e.g. `tamil-nadu` (PK) |
| state_display | VARCHAR(96) | Human-readable name, e.g. `Tamil Nadu` |
| region | VARCHAR(24) | North / South / East / West / Central / Northeast |
| zone | VARCHAR(24) | Broader zone grouping |

### dim_date
| Column | Type | Description |
|---|---|---|
| year | SMALLINT | Calendar year (PK part) |
| quarter | TINYINT | 1-4 (PK part) |
| quarter_label | VARCHAR(12) | e.g. `Q3 2022` |
| period_months | VARCHAR(12) | e.g. `Jul-Sep` |
| period_index | SMALLINT | Monotonic index (2018 Q1 = 0) for window functions |

## Aggregated facts (state x period)

### agg_transaction
| Column | Type | Description |
|---|---|---|
| state, year, quarter | keys | FK to dimensions |
| category | VARCHAR(48) | Recharge & bill payments / Peer-to-peer / Merchant / Financial Services / Others |
| txn_count | BIGINT | Number of transactions |
| txn_amount | DECIMAL(20,2) | Transaction value in INR |

### agg_user
| Column | Type | Description |
|---|---|---|
| state, year, quarter | keys | FK to dimensions |
| registered_users | BIGINT | Cumulative registered users |
| app_opens | BIGINT | App opens in the quarter |

### agg_user_device
| Column | Type | Description |
|---|---|---|
| state, year, quarter | keys | FK to dimensions |
| brand | VARCHAR(32) | Device brand (Xiaomi, Samsung, ...) |
| user_count | BIGINT | Users on that brand |
| percentage | DECIMAL(8,4) | Brand share (0-1) |

### agg_insurance
| Column | Type | Description |
|---|---|---|
| state, year, quarter | keys | FK to dimensions (live from 2020 Q1) |
| policy_count | BIGINT | Policies sold |
| premium_amount | DECIMAL(20,2) | Premium collected in INR |

## Map facts (state x district x period)
`map_transaction`, `map_user`, `map_insurance` mirror the aggregated measures
at **district** grain (`district VARCHAR(96)` replaces `category`).

## Top facts (leaderboards per period)
| Table | Grain | Measures |
|---|---|---|
| top_transaction_district | state x district x period | txn_count, txn_amount |
| top_transaction_pincode | state x pincode x period | txn_count, txn_amount |
| top_user_pincode | state x pincode x period | registered_users |

## Derived / analytics columns (computed in `src/analytics.py`)
| Column | Definition |
|---|---|
| market_share_pct | 100 * state value / national value |
| avg_ticket | txn_amount / txn_count |
| yoy_pct | 100 * (value_t - value_{t-1}) / value_{t-1} |
| qoq_pct | quarter-over-quarter growth |
| ma_4q | 4-quarter moving average of value |
| running_total | cumulative value over time |
