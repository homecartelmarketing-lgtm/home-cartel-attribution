# Cumulative Monthly Ads Metrics Design Specification

**Date:** 2026-11-04  
**Author:** Antigravity  
**Status:** Approved for Implementation  
**Topic:** Cumulative Ads Metrics per Month per Campaign

---

## 1. Intent & Purpose

The user requested:
1. Cumulative record of ads metrics: CPC, CTR, CPM, Clicks, Spend, Impressions, Results, Frequency, etc. (all metrics).
2. Each campaign should have a cumulative record per month.
3. Decisions and architecture should be preserved in Obsidian notes and Graphify knowledge graphs.

This specification defines how daily performance breakdown data from Meta Ads Manager exports is parsed, stored, and aggregated into mathematically accurate monthly cumulative metrics.

---

## 2. Requirements & Calculations

### 2.1 Ingested Metrics (from Meta Ads Manager By Day Breakdown)
- **Spend:** `Amount spent (PHP)`
- **Impressions:** `Impressions`
- **Reach:** `Reach`
- **Link Clicks:** `Link clicks`
- **All Clicks:** `Clicks (all)`
- **Results:** `Results`
- **Landing Page Views:** `Landing page views`
- **Cost per Result:** `Cost per results`
- **Frequency:** `Frequency`

### 2.2 Mathematically True Cumulative Formulas
For any given campaign over a month (or all campaigns combined):

| Metric | Formula | Note |
|---|---|---|
| **Cumulative Spend** | $\sum \text{amount\_spent}$ | Sum of all daily spend in the month |
| **Cumulative Impressions** | $\sum \text{impressions}$ | Sum of impressions |
| **Cumulative Reach** | $\max(\text{reach})$ or deduplicated reach | Peak reach across the period |
| **Cumulative Link Clicks** | $\sum \text{link\_clicks}$ | Sum of link clicks |
| **Cumulative All Clicks** | $\sum \text{clicks\_all}$ | Sum of total clicks (inline, link, card) |
| **Cumulative Results** | $\sum \text{results}$ | Sum of purchases, leads, or view content |
| **Cumulative Link CPC** | $\frac{\sum \text{amount\_spent}}{\sum \text{link\_clicks}}$ | Cost per link click. Returns 0 if clicks = 0 |
| **Cumulative Link CTR** | $\frac{\sum \text{link\_clicks}}{\sum \text{impressions}} \times 100$ | Percentage of impressions clicking link |
| **Cumulative CPM** | $\frac{\sum \text{amount\_spent}}{\sum \text{impressions}} \times 1000$ | Cost per 1,000 impressions |
| **Cumulative All CPC** | $\frac{\sum \text{amount\_spent}}{\sum \text{clicks\_all}}$ | Cost per any click |
| **Cumulative All CTR** | $\frac{\sum \text{clicks\_all}}{\sum \text{impressions}} \times 100$ | Percentage of impressions taking any click |
| **Cumulative Cost per Result** | $\frac{\sum \text{amount\_spent}}{\sum \text{results}}$ | Cost per conversion/result |
| **Cumulative Cost per LPV** | $\frac{\sum \text{amount\_spent}}{\sum \text{landing\_page\_views}}$ | Cost per landing page view |
| **Cumulative Frequency** | $\frac{\sum \text{impressions}}{\max(\text{reach})}$ | Impressions per reached user |

> **Critical Rule:** Never average daily CPCs or CTRs. Doing so introduces severe weighting errors. Always divide total sums.

---

## 3. Database Architecture

We expand `meta_campaign_daily` in `app/database.py` with idempotent migration:
```sql
ALTER TABLE meta_campaign_daily ADD COLUMN clicks_all INTEGER DEFAULT 0;
ALTER TABLE meta_campaign_daily ADD COLUMN landing_page_views INTEGER DEFAULT 0;
ALTER TABLE meta_campaign_daily ADD COLUMN results INTEGER DEFAULT 0;
ALTER TABLE meta_campaign_daily ADD COLUMN cost_per_result REAL DEFAULT 0;
ALTER TABLE meta_campaign_daily ADD COLUMN cpm REAL DEFAULT 0;
ALTER TABLE meta_campaign_daily ADD COLUMN frequency REAL DEFAULT 0;
```

Monthly aggregation query:
```sql
SELECT 
    campaign_name,
    SUBSTR(report_date, 1, 7) AS report_month,
    MAX(status) AS status,
    COUNT(DISTINCT report_date) AS days_active,
    MIN(report_date) AS month_start_date,
    MAX(report_date) AS month_end_date,
    COALESCE(SUM(amount_spent), 0) AS total_spend,
    COALESCE(SUM(impressions), 0) AS total_impressions,
    COALESCE(MAX(reach), 0) AS max_reach,
    COALESCE(SUM(link_clicks), 0) AS total_link_clicks,
    COALESCE(SUM(clicks_all), 0) AS total_clicks_all,
    COALESCE(SUM(landing_page_views), 0) AS total_landing_page_views,
    COALESCE(SUM(results), 0) AS total_results
FROM meta_campaign_daily
GROUP BY campaign_name, SUBSTR(report_date, 1, 7)
ORDER BY report_month DESC, total_spend DESC;
```

---

## 4. UI / Dashboard Design

The dashboard will include:
1. **Month Dropdown Selector:** Shows all available months (`2026-10`, `2026-09`, etc.) and "All Months".
2. **KPI Highlights Bar:** Blended Spend, Blended Link CPC, Blended Link CTR, Blended CPM, Total Link Clicks, and Total Results.
3. **Interactive Table:** Full breakdown per campaign with search filter, sortable columns, and "Export CSV" feature.
