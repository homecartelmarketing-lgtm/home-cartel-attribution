-- Query Table B: Expensive Ads vs 30-Day Baseline
-- Purpose: Identifies ads whose cost-per-link-click has spiked relative to their 30-day baseline average.
-- Platform: Zoho Analytics SQL Query Table

SELECT
  ad_name,
  campaign_name,
  adset_name,
  ROUND(AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 3 DAY) 
                 THEN cost_per_inline_link_click END), 2) AS cpc_last_3d,
  ROUND(AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 30 DAY) 
                 THEN cost_per_inline_link_click END), 2) AS cpc_baseline_30d,
  ROUND(((AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 3 DAY) 
                   THEN cost_per_inline_link_click END) - 
          AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 30 DAY) 
                   THEN cost_per_inline_link_click END)) / 
         NULLIF(AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 30 DAY) 
                         THEN cost_per_inline_link_click END), 0)) * 100, 1) AS cpc_spike_pct
FROM Ad_Insights
WHERE date >= DATE_SUB(TODAY(), INTERVAL 30 DAY)
  AND status = 'ACTIVE'
  AND campaign_name NOT LIKE '%FR Stores%'
GROUP BY ad_name, campaign_name, adset_name
HAVING AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 30 DAY) THEN cost_per_inline_link_click END) > 0
ORDER BY cpc_spike_pct DESC;
