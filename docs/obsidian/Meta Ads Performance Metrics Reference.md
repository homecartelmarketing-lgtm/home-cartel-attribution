---
title: Meta Ads Performance Metrics Reference
tags:
  - reference
  - meta-ads
  - glossary
date: 2026-11-04
status: active
related:
  - "[[Cumulative Ads Metrics per Month]]"
  - "[[Architecture Decision - Monthly Cumulative Aggregation]]"
---

# Meta Ads Performance Metrics Reference

Comprehensive definitions and calculation methodologies for all advertising performance metrics in the system.

| Metric | Source / Header Name | Unit | Cumulative Formula | Purpose / Interpretation |
|---|---|---|---|---|
| **Amount Spent** | `Amount spent (PHP)` | PHP (₱) | $\sum \text{amount\_spent}$ | Direct media spend allocated to campaign. |
| **Impressions** | `Impressions` | Count | $\sum \text{impressions}$ | Total times ads were on screen. |
| **Reach** | `Reach` | Unique Count | $\max(\text{reach})$ | Unique audience reached during period. |
| **Frequency** | `Frequency` | Ratio | $\frac{\sum \text{impressions}}{\max(\text{reach})}$ | Average times each unique viewer saw the ad. Triggers warning if $> 2.5\times$. |
| **Link Clicks** | `Link clicks` | Count | $\sum \text{link\_clicks}$ | Number of clicks specifically redirecting to destination URLs. |
| **Link CPC** | `CPC (cost per link click) (PHP)` | PHP (₱) | $\frac{\sum \text{amount\_spent}}{\sum \text{link\_clicks}}$ | Effective cost per interested visitor click. |
| **Link CTR** | `CTR (link click-through rate)` | Percentage (%) | $\frac{\sum \text{link\_clicks}}{\sum \text{impressions}} \times 100$ | Click rate to destination URL. Indicator of creative engagement. |
| **Clicks (All)** | `Clicks (all)` | Count | $\sum \text{clicks\_all}$ | Total clicks of any kind (card swipes, read more, reactions, link clicks). |
| **All CPC** | `CPC (all) (PHP)` | PHP (₱) | $\frac{\sum \text{amount\_spent}}{\sum \text{clicks\_all}}$ | Overall cost per interaction. |
| **All CTR** | `CTR (all)` | Percentage (%) | $\frac{\sum \text{clicks\_all}}{\sum \text{impressions}} \times 100$ | Total interaction engagement percentage. |
| **CPM** | `CPM (cost per 1,000 impressions) (PHP)` | PHP (₱) | $\frac{\sum \text{amount\_spent}}{\sum \text{impressions}} \times 1000$ | Baseline cost to purchase 1,000 ad impressions in Meta's auction. |
| **Results** | `Results` | Count | $\sum \text{results}$ | Primary optimization objective (e.g., Purchases, View Content, Messages). |
| **Cost per Result** | `Cost per results` | PHP (₱) | $\frac{\sum \text{amount\_spent}}{\sum \text{results}}$ | Unit cost to acquire primary optimization action. |
| **Landing Page Views** | `Landing page views` | Count | $\sum \text{landing\_page\_views}$ | Confirmed webpage loads with pixel fire. |
| **Cost per LPV** | `Cost per landing page view (PHP)` | PHP (₱) | $\frac{\sum \text{amount\_spent}}{\sum \text{landing\_page\_views}}$ | Cost per customer who fully loaded the website. |

See also:
- [[Cumulative Ads Metrics per Month]]
- [[Architecture Decision - Monthly Cumulative Aggregation]]
