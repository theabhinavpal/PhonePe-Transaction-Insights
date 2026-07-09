# Business Insights

> 40 executive-level insights, every one grounded in figures
> computed directly from the warehouse (`reports/build_reports.py`).

## Findings

1. Digital-payment value across India totals **Rs 4.52 lakh crore** over 5.47 billion transactions in the 2018-2023 window.
2. Value compounded at a **18.3% CAGR**, but the latest year's growth of **12.04%** shows adoption is entering a maturing phase.
3. The **Southern region dominates**, generating **32.45%** of national value.
4. **Maharashtra** is the single largest market with **10.05%** of value.
5. The **top 5 states control 39.8%** and the top 10 control **65.94%** of all value - a concentrated market.
6. At district level, the **top 20% of districts capture 63.92%** of value, confirming a strong Pareto (80/20) pattern.
7. **Peer-to-peer payments** remain the value leader at **56.8%** of the total.
8. **Merchant payments rose from 14.89% to 24.84%** of value between 2018 and 2023 - the clearest structural shift in the mix.
9. **Recharge & bill payments fell from 15.48% to 9.71%** of value, as the platform's use-cases broadened beyond utilities.
10. **Financial Services carry the highest average ticket** (Rs 2,450), while Recharge has the lowest, reflecting very different transaction economics.
11. **Q4 value runs 40.25% above Q1** on average - a monetisable festival-season effect.
12. The blended **average ticket size is Rs 827**, pulled down by high-frequency, low-value recharge and merchant transactions.
13. The latest quarter (Q4 2023) alone processed **Rs 29,606 Cr** across 34.44 Cr transactions.
14. **Registered users reached 7.15 Cr** with **54.75 Cr app opens** in the latest quarter - about **7.7 opens per user**, a healthy engagement signal.
15. The installed base skews to **Xiaomi (26.0%), Samsung (20.0%), Vivo (14.5%)** by device brand, useful for app-performance and partnership targeting.
16. **Insurance has scaled to Rs 882 Cr** in premium and 1.51 Cr policies since its 2020 launch.
17. Insurance premium is **concentrated in Maharashtra and Karnataka**, indicating an urban/affluent adoption pattern.
18. The **lowest-value states/UTs** (Arunachal Pradesh, Nagaland, Andaman & Nicobar) represent white-space for acquisition.
19. **Pune** is the highest-value district nationwide, ahead of Lucknow and Bengaluru Urban.
20. North (20.92%) and West (16.13%) are the second and third largest regions after the South.

## Actionable Recommendations

21. Concentrate retention spend on the top-5 states (39.8% of value) where churn is most costly.
22. Prioritise QR-code and merchant-lending features - merchant payments are the fastest-rising share.
23. Schedule marketing pushes into Q4 to ride the 40.25% seasonal uplift.
24. Run Tier-2/Tier-3 district acquisition programmes in the fast-growing long tail.
25. Cross-sell insurance into large but under-penetrated user bases outside Maharashtra.
26. Use average-ticket-size segmentation to tailor credit/BNPL offers to high-ATV states.
27. Track app-opens-per-user as a leading indicator of engagement, decoupled from value growth.
28. Build device-brand-aware performance testing given the Xiaomi/Samsung-heavy base.
29. Set state-level growth targets relative to the national CAGR to spot under-performers early.
30. Monitor category-mix drift quarterly; a stall in merchant-share growth is an early warning.
31. Establish a Pareto watch-list: the districts that make up the top 20% of value.
32. Localise offers to the top pincodes, which show extreme value concentration.
33. Model seasonality explicitly (4Q moving average) before reacting to any single-quarter dip.
34. Report YoY and QoQ together so festival seasonality is never mistaken for a trend break.
35. Treat insurance as a distinct funnel with its own state-level penetration KPI.
36. Benchmark low-share states against their regional champion to size the opportunity.
37. Segment users by transactions-per-user to find high-intent cohorts for premium products.
38. Instrument a data-quality gate (as in `etl/validate.py`) as a release blocker for every refresh.
39. Expose the warehouse via views (see `views.sql`) so BI users query stable contracts, not raw facts.
40. Automate the quarterly report build (`reports/build_reports.py`) to keep leadership numbers current.
