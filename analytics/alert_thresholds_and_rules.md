# Zoho Analytics: 11 Alert Thresholds & Rules Matrix

All thresholds are derived from **16 months of empirical account performance** (January 2025 – May 2026 across 2,284 active performance ads), excluding reach/retail campaigns (`FR Stores`).

---

## 1. Baseline Percentiles Reference

| Metric | 10th Pct | 25th Pct | Median | 75th Pct | 90th Pct | Basis |
|---|---|---|---|---|---|---|
| **Link CTR** | 0.43% | 0.67% | 1.17% | 1.84% | 2.59% | Performance ads |
| **Adset Frequency** | 1.80 | 2.05 | 2.37 | 3.71 | 4.46 | 7-day rolling window |
| **Cost Per Click (CPC)** | ₱2.50 | ₱4.45 | ₱9.15 | ₱16.31 | ₱26.48 | % rise above 30-day baseline |

---

## 2. Complete Alert Rules Table

| # | Alert Name | Severity | Source Table | Condition (Exclude `FR Stores`) | Schedule | Action SOP |
|---|---|---|---|---|---|---|
| **1** | Low CTR Warning | **WARNING** | `Ad_Insights` | `CTR < 0.67%` AND `Impressions >= 2,000` (Last 3 days) | Daily 08:00 PHT | Review creative hook and visual clarity |
| **2** | Low CTR Critical | **CRITICAL** | `Ad_Insights` | `CTR < 0.43%` AND `Impressions >= 2,000` (Last 3 days) | Daily 08:00 PHT | Pause ad creative; swap with winning variant |
| **3** | High Frequency Watch | **WATCH** | `Adset_Insights` | `Frequency >= 3.71` (Last 7 days) | Daily 08:00 PHT | Prepare fresh ad creatives for rotation |
| **4** | High Frequency Critical | **CRITICAL** | `Adset_Insights` | `Frequency >= 4.46` (Last 7 days) | Daily 08:00 PHT | Expand audience size or cycle new creative batch |
| **5** | Expensive Link Click Warning | **WARNING** | `Query Table B` | `cpc_spike_pct >= 50.0%` AND `cpc_last_3d > ₱15.00` | Daily 08:00 PHT | Inspect audience overlap or bidding fluctuations |
| **6** | Expensive Link Click Critical | **CRITICAL** | `Query Table B` | `cpc_spike_pct >= 100.0%` AND `cpc_last_3d > ₱25.00` | Daily 08:00 PHT | Lower adset budget or pause inefficient ad |
| **7** | Creative Fatigue Warning | **WARNING** | `Query Table A` | `ctr_change_pct <= -20.0%` AND `ctr_change_pct > -30.0%` | Daily 08:00 PHT | Plan new visual angle or test new headline |
| **8** | Creative Fatigue Critical | **CRITICAL** | `Query Table A` | `ctr_change_pct <= -30.0%` (Prior 7d vs Last 7d) | Daily 08:00 PHT | Immediate pause; creative has burned out |
| **9** | Zero Delivery Stalling | **CRITICAL** | `Ad_Insights` | `Status = 'ACTIVE'` AND `Impressions = 0` (Last 24h) | Daily 10:00 PHT | Check ad account billing, policy flag, or learning phase |
| **10** | Rapid Budget Pacing | **WATCH** | `Campaign_Insights` | `Spend / Daily_Budget >= 0.80` before 14:00 PHT | Daily 14:00 PHT | Verify dayparting or accidental budget edits |
| **11** | Anomaly Spend with No Leads | **CRITICAL** | Cross-platform | `Spend > ₱3,000` (Last 24h) AND `Zendesk Inquiries = 0` | Daily 18:00 PHT | Verify landing page and redirect `/wa-go` functionality |

---

## 3. Mandatory Filter Rule
Every alert relying on ad-level data MUST have the following filter:
```sql
Campaign Name does not contain 'FR Stores'
```
*Reason*: Reach campaigns naturally run at 0.03% – 0.06% CTR by design. Omitting this filter will trigger false critical alarms daily.

---

## 4. Email Alert Template Format

```
Subject: [ALERT - {SEVERITY}] {Brand Name} - {Alert Name}: {Ad / Campaign Name}

Brand: Home Cartel
Ad Name: {ad_name}
Campaign: {campaign_name}
Adset: {adset_name}

Triggered Metric:
- Current Value: {metric_value}
- Threshold: {threshold_value}

Recommended SOP:
{step_by_step_response_action}

View Dashboard: https://analytics.zoho.com/workspace/home-cartel-ads
```
