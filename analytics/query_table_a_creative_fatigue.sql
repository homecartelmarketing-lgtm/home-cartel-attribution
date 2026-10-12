-- Query Table A: Creative Fatigue Score
-- Purpose: Compares ad-level CTR over the last 7 days against the prior 7-day period.
-- Crucial: Excludes 'FR Stores' campaigns to prevent false critical alerts.
-- Platform: Zoho Analytics SQL Query Table

SELECT
  ad_name,
  campaign_name,
  adset_name,
  ROUND(AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 7 DAY) 
                 THEN ctr_link_click_through_rate END), 2) AS ctr_last_7d,
  ROUND(AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 14 DAY) 
                  AND date < DATE_SUB(TODAY(), INTERVAL 7 DAY) 
                 THEN ctr_link_click_through_rate END), 2) AS ctr_prior_7d,
  ROUND(((AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 7 DAY) 
                   THEN ctr_link_click_through_rate END) - 
          AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 14 DAY) 
                    AND date < DATE_SUB(TODAY(), INTERVAL 7 DAY) 
                   THEN ctr_link_click_through_rate END)) / 
         NULLIF(AVG(CASE WHEN date >= DATE_SUB(TODAY(), INTERVAL 14 DAY) 
                          AND date < DATE_SUB(TODAY(), INTERVAL 7 DAY) 
                         THEN ctr_link_click_through_rate END), 0)) * 100, 1) AS ctr_change_pct
FROM Ad_Insights
WHERE date >= DATE_SUB(TODAY(), INTERVAL 14 DAY)
  AND status = 'ACTIVE'
  AND campaign_name NOT LIKE '%FR Stores%'
GROUP BY ad_name, campaign_name, adset_name
ORDER BY ctr_change_pct ASC;
