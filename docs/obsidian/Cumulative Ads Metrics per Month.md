---
title: Cumulative Ads Metrics per Month
tags:
  - meta-ads
  - attribution
  - analytics
  - metrics
  - architecture
date: 2026-11-04
status: implemented
related:
  - "[[Architecture Decision - Monthly Cumulative Aggregation]]"
  - "[[Meta Ads Performance Metrics Reference]]"
---

# Cumulative Ads Metrics per Month

## Overview
This system provides campaign-level cumulative performance metrics aggregated by calendar month (`YYYY-MM`). It ingests granular daily reports (`dailybreakdown.csv`) from Meta Ads Manager and aggregates them in real-time using dual-engine SQL.

## Core Metrics Captured
- **Total Spend (PHP):** Sum of daily `amount_spent`
- **Total Impressions:** Sum of daily `impressions`
- **Reach:** Maximum reach reached during the period
- **Link Clicks:** Sum of `link_clicks`
- **All Clicks:** Sum of `clicks_all`
- **Results:** Sum of conversion results (`results`)
- **Landing Page Views:** Sum of `landing_page_views`

## Cumulative Rate Formulas
To maintain strict mathematical integrity, cumulative rates are calculated from raw sums rather than arithmetic averages of daily percentages:

$$\text{Cumulative CPC} = \frac{\sum \text{Spend}}{\sum \text{Link Clicks}}$$

$$\text{Cumulative CTR (\%)} = \frac{\sum \text{Link Clicks}}{\sum \text{Impressions}} \times 100$$

$$\text{Cumulative CPM} = \frac{\sum \text{Spend}}{\sum \text{Impressions}} \times 1000$$

$$\text{Cumulative All CPC} = \frac{\sum \text{Spend}}{\sum \text{Clicks (All)}}$$

$$\text{Cumulative All CTR (\%)} = \frac{\sum \text{Clicks (All)}}{\sum \text{Impressions}} \times 100$$

$$\text{Cost per Result} = \frac{\sum \text{Spend}}{\sum \text{Results}}$$

$$\text{Cost per Landing Page View} = \frac{\sum \text{Spend}}{\sum \text{Landing Page Views}}$$

$$\text{Frequency} = \frac{\sum \text{Impressions}}{\max(\text{Reach})}$$

## Technical Implementation
- **Database Table:** `meta_campaign_daily` in `app/database.py` with unique constraint `(campaign_name, report_date)`.
- **Query Function:** `get_cumulative_monthly_campaign_metrics(month=None)`
- **REST API:** `GET /api/campaigns/monthly?month=YYYY-MM`
- **Dashboard UI:** Dedicated "Monthly Cumulative Ads Performance" panel in `app/dashboard_template.py` with month dropdown selector, blended KPI highlights, real-time search, and CSV export.

See also:
- [[Architecture Decision - Monthly Cumulative Aggregation]]
- [[Meta Ads Performance Metrics Reference]]
