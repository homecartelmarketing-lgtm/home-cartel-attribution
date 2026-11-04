---
title: Architecture Decision - Monthly Cumulative Aggregation
tags:
  - adr
  - architecture
  - database
  - decision-record
date: 2026-11-04
status: accepted
related:
  - "[[Cumulative Ads Metrics per Month]]"
  - "[[Meta Ads Performance Metrics Reference]]"
---

# Architecture Decision Record (ADR): Monthly Cumulative Aggregation

## Context
The attribution system requires cumulative records of all ad performance metrics (CPC, CTR, CPM, Clicks, Spend, Impressions, Results, Frequency) per campaign broken down by calendar month.

Two architectural options were evaluated:
1. **Dynamic SQL Aggregation on Granular Daily Table (`meta_campaign_daily`):** Store rich daily breakdown rows, and compute monthly metrics dynamically grouped by `campaign_name` and `SUBSTR(report_date, 1, 7)`.
2. **Materialized / Separate Monthly Table (`meta_campaign_monthly`):** Precompute and store monthly rows in a separate table on every CSV import.

## Decision
We chose **Option 1 (Dynamic SQL Aggregation on `meta_campaign_daily`)**.

## Rationale
1. **Single Source of Truth:** Daily rows from `dailybreakdown.csv` are the fundamental unit of time. Re-uploading daily data or importing missing days automatically updates monthly figures without needing dual-table sync logic.
2. **Mathematically Accurate Cumulative Ratios:** Rate metrics like CPC, CTR, and CPM are non-additive. Calculating them on-the-fly from raw sums ($\sum \text{spend} / \sum \text{clicks}$) eliminates statistical distortion.
3. **Dual-Engine Compatibility:** `SUBSTR(report_date, 1, 7)` operates identically across SQLite and PostgreSQL for standard `YYYY-MM-DD` string dates, avoiding dialect incompatibilities.
4. **Performance:** The number of daily records across 20-50 campaigns for a year is under 20,000 rows. In-memory or indexed query execution takes under 5 milliseconds.

## Consequences
- `meta_campaign_daily` schema expanded with columns: `clicks_all`, `landing_page_views`, `results`, `cost_per_result`, `cpm`, `frequency`.
- Importer in `import_meta_spend.py` maps all rich columns from Meta Ads Manager exports.
- `get_cumulative_monthly_campaign_metrics()` provides single-call access to available months, selected month, blended KPIs, and campaign lists.

See also:
- [[Cumulative Ads Metrics per Month]]
- [[Meta Ads Performance Metrics Reference]]
