-- Query Table C: Delivery Health & Frequency Saturation
-- Purpose: Monitors adset delivery frequency to identify audience saturation before ad fatigue degrades conversion efficiency.
-- Platform: Zoho Analytics SQL Query Table

SELECT
  campaign_name,
  adset_name,
  ROUND(AVG(frequency), 2) AS current_frequency_7d,
  SUM(impressions) AS impressions_7d,
  SUM(reach) AS reach_7d,
  SUM(spend) AS spend_7d,
  CASE
    WHEN AVG(frequency) >= 4.46 THEN 'CRITICAL_SATURATION'
    WHEN AVG(frequency) >= 3.71 THEN 'WATCH_FREQUENCY'
    ELSE 'HEALTHY'
  END AS delivery_status
FROM Adset_Insights
WHERE date >= DATE_SUB(TODAY(), INTERVAL 7 DAY)
  AND campaign_name NOT LIKE '%FR Stores%'
GROUP BY campaign_name, adset_name
ORDER BY current_frequency_7d DESC;
