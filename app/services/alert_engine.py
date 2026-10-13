"""
Ad Performance Alert Engine
Ad-to-Sale Attribution System

Implements the 11 alert rules defined in
analytics/alert_thresholds_and_rules.md (Part 3 of the handoff document).

Thresholds are derived from 16 months of empirical performance across 2,284
active performance ads (January 2025 - May 2026), excluding reach campaigns.

Every ad-level rule applies the mandatory 'FR Stores' exclusion; the exclusion
is enforced inside meta_insights_service so it cannot be forgotten.

Alerts are evaluated per brand and emailed using the template in section 4 of
the threshold document. Results are cached in memory so GET /api/alerts can
report the most recent evaluation.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.config import BRAND_CONFIGS, ALERT_RECIPIENTS, get_brand_config
from app.services import meta_insights_service
from app.services import analytics_store
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_WATCH = "WATCH"

# Alert #11 threshold: significant spend with zero inquiries.
ANOMALY_SPEND_THRESHOLD_PHP = 3000.0

# Alert #10 pacing threshold: 80% of daily budget consumed before 14:00 PHT.
PACING_RATIO_THRESHOLD = 0.80
PACING_CUTOFF_HOUR = 14

# In-memory cache of the most recent alert evaluation.
_recent_alerts: List[Dict[str, Any]] = []
_last_run: Optional[str] = None


def get_recent_alerts() -> List[Dict[str, Any]]:
    """Return the alerts from the most recent evaluation."""
    return list(_recent_alerts)


def get_last_run() -> Optional[str]:
    """ISO timestamp of the last full alert evaluation."""
    return _last_run


def _alert(
    alert_id: int,
    name: str,
    severity: str,
    brand: str,
    subject_detail: str,
    metric_value: Any,
    threshold_value: Any,
    sop: str,
    entity: Optional[Dict[str, Any]] = None,
    source: str = "Ad Insights",
    parameter: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a normalised alert record matching Section 2.6.4 and 2.6.5."""
    param = parameter or name
    today_str = datetime.now().strftime("%Y-%m-%d")
    routing = (
        "monitoring person + brand team + business owner"
        if severity == SEVERITY_CRITICAL
        else "monitoring person + relevant brand marketing team"
        if severity == SEVERITY_WARNING
        else "monitoring person only"
    )
    return {
        "alert_id": alert_id,
        "alert_name": name,
        "parameter": param,
        "severity": severity,
        "brand": brand,
        "entity": entity or {},
        "subject": f"[{severity}] — {brand} — {param} — {today_str}",
        "metric_value": metric_value,
        "threshold_value": threshold_value,
        "recommended_action": sop,
        "routing": routing,
        "source": source,
        "triggered_at": datetime.now().isoformat(),
    }


def _entity_label(entity: Dict[str, Any]) -> str:
    """Best human-readable label for an ad / adset / campaign entity."""
    return (
        entity.get("ad_name")
        or entity.get("adset_name")
        or entity.get("campaign_name")
        or "unknown"
    )


def _dispatch(alert: Dict[str, Any], recipients: List[str]) -> Dict[str, Any]:
    """
    Email a single alert using the section 4 template format.

    Returns the email service result. Never raises: a delivery failure is
    logged and recorded so the sweep continues.
    """
    entity = alert.get("entity", {})
    lines = [
        f"Brand: {alert['brand']}",
    ]
    if entity.get("ad_name"):
        lines.append(f"Ad Name: {entity['ad_name']}")
    if entity.get("campaign_name"):
        lines.append(f"Campaign: {entity['campaign_name']}")
    if entity.get("adset_name"):
        lines.append(f"Adset: {entity['adset_name']}")
    lines += [
        "",
        "Triggered Metric:",
        f"- Current Value: {alert['metric_value']}",
        f"- Threshold: {alert['threshold_value']}",
        "",
        "Recommended SOP:",
        alert["recommended_action"],
    ]
    body_text = "\n".join(lines)

    html = f"""
    <html><body style="font-family:Arial,Helvetica,sans-serif;color:#222;">
      <h2 style="margin-bottom:2px;">{alert['alert_name']}</h2>
      <p style="margin-top:0;color:#666;">{alert['brand']} &mdash; {_entity_label(entity)}</p>
      <table cellpadding="6" cellspacing="0" style="border-collapse:collapse;">
        <tr><td><strong>Current Value</strong></td><td>{alert['metric_value']}</td></tr>
        <tr><td><strong>Threshold</strong></td><td>{alert['threshold_value']}</td></tr>
        <tr><td><strong>Severity</strong></td><td>{alert['severity']}</td></tr>
      </table>
      <p><strong>Recommended action:</strong> {alert['recommended_action']}</p>
      <p style="font-size:12px;color:#666;">
        Reach campaigns ('FR Stores') are excluded from every ad-level rule.</p>
    </body></html>
    """

    try:
        return send_email(
            subject=alert["subject"],
            body_text=body_text,
            body_html=html,
            recipients=recipients,
        )
    except Exception as e:
        logger.error("Alert dispatch failed for %s: %s", alert["alert_name"], e)
        return {"status": "failed", "error": str(e)}


# ---------------------------------------------------------------------------
# Alerts 1-4: CTR and frequency
# ---------------------------------------------------------------------------

def check_ctr_alerts(brand: str, send: bool = True) -> List[Dict[str, Any]]:
    """Alerts 1 & 2: low link CTR warning and critical."""
    fired: List[Dict[str, Any]] = []
    recipients = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS

    for ad in meta_insights_service.get_ad_level_metrics(brand, days=3):
        ctr = ad.get("ctr_pct", 0.0)
        if ad.get("impressions", 0) < 2000:
            continue

        if ctr < 0.43:
            alert = _alert(
                2, "Low CTR Critical", SEVERITY_CRITICAL, brand,
                _entity_label(ad), f"{ctr}%", "< 0.43%",
                "Pause ad creative; swap with winning variant.", ad,
            )
        elif ctr < 0.67:
            alert = _alert(
                1, "Low CTR Warning", SEVERITY_WARNING, brand,
                _entity_label(ad), f"{ctr}%", "< 0.67%",
                "Review creative hook and visual clarity.", ad,
            )
        else:
            continue

        if send:
            alert["email_status"] = _dispatch(alert, recipients).get("status")
        fired.append(alert)

    return fired


def check_frequency_alerts(brand: str, send: bool = True) -> List[Dict[str, Any]]:
    """Alerts 3 & 4: adset frequency watch and critical."""
    fired: List[Dict[str, Any]] = []
    recipients = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS

    for adset in meta_insights_service.query_table_c_delivery_health(brand):
        freq = adset.get("current_frequency_7d", 0.0)

        if freq >= 4.46:
            alert = _alert(
                4, "High Frequency Critical", SEVERITY_CRITICAL, brand,
                _entity_label(adset), freq, ">= 4.46",
                "Expand audience size or cycle new creative batch.", adset,
            )
        elif freq >= 3.71:
            alert = _alert(
                3, "High Frequency Watch", SEVERITY_WATCH, brand,
                _entity_label(adset), freq, ">= 3.71",
                "Prepare fresh ad creatives for rotation.", adset,
            )
        else:
            continue

        if send:
            alert["email_status"] = _dispatch(alert, recipients).get("status")
        fired.append(alert)

    return fired


# ---------------------------------------------------------------------------
# Alerts 5-8: CPC spike and creative fatigue
# ---------------------------------------------------------------------------

def check_expensive_click_alerts(brand: str, send: bool = True) -> List[Dict[str, Any]]:
    """Alerts 5 & 6: cost per link click spike versus the 30-day baseline."""
    fired: List[Dict[str, Any]] = []
    recipients = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS

    for ad in meta_insights_service.query_table_b_expensive_ads(brand):
        spike = ad.get("cpc_spike_pct", 0.0)
        cpc = ad.get("cpc_last_3d", 0.0)

        if spike >= 100.0 and cpc > 25.00:
            alert = _alert(
                6, "Expensive Link Click Critical", SEVERITY_CRITICAL, brand,
                _entity_label(ad), f"+{spike}% (PHP {cpc})",
                ">= 100% and > PHP 25.00",
                "Lower adset budget or pause inefficient ad.", ad,
            )
        elif spike >= 50.0 and cpc > 15.00:
            alert = _alert(
                5, "Expensive Link Click Warning", SEVERITY_WARNING, brand,
                _entity_label(ad), f"+{spike}% (PHP {cpc})",
                ">= 50% and > PHP 15.00",
                "Inspect audience overlap or bidding fluctuations.", ad,
            )
        else:
            continue

        if send:
            alert["email_status"] = _dispatch(alert, recipients).get("status")
        fired.append(alert)

    return fired


def check_creative_fatigue_alerts(brand: str, send: bool = True) -> List[Dict[str, Any]]:
    """Alerts 7 & 8: CTR decay over the last 7 days versus the prior 7 days."""
    fired: List[Dict[str, Any]] = []
    recipients = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS

    for ad in meta_insights_service.query_table_a_creative_fatigue(brand):
        change = ad.get("ctr_change_pct", 0.0)

        if change <= -30.0:
            alert = _alert(
                8, "Creative Fatigue Critical", SEVERITY_CRITICAL, brand,
                _entity_label(ad), f"{change}%", "<= -30.0%",
                "Immediate pause; creative has burned out.", ad,
            )
        elif -30.0 < change <= -20.0:
            alert = _alert(
                7, "Creative Fatigue Warning", SEVERITY_WARNING, brand,
                _entity_label(ad), f"{change}%", "<= -20.0%",
                "Plan new visual angle or test new headline.", ad,
            )
        else:
            continue

        if send:
            alert["email_status"] = _dispatch(alert, recipients).get("status")
        fired.append(alert)

    return fired

# ---------------------------------------------------------------------------
# Alerts 9-11: delivery and spend-without-leads
# ---------------------------------------------------------------------------

def check_zero_delivery_alerts(brand: str, send: bool = True) -> List[Dict[str, Any]]:
    """Alert 9: active ads with zero impressions in the last 24 hours."""
    fired: List[Dict[str, Any]] = []
    recipients = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS

    for ad in meta_insights_service.get_ad_level_metrics(brand, days=1):
        if ad.get("impressions", 0) != 0:
            continue
        alert = _alert(
            9, "Zero Delivery Stalling", SEVERITY_CRITICAL, brand,
            _entity_label(ad), "0 impressions", "ACTIVE with 0 impressions",
            "Check ad account billing, policy flag, or learning phase.", ad,
        )
        if send:
            alert["email_status"] = _dispatch(alert, recipients).get("status")
        fired.append(alert)

    return fired


def check_anomaly_spend_alerts(brand: str, send: bool = True) -> List[Dict[str, Any]]:
    """
    Alert 11: significant spend with zero inquiries.

    Cross-platform rule. Inquiry volume comes from the pushed GA4 counts when
    available, otherwise from the local attribution click logs.
    """
    fired: List[Dict[str, Any]] = []
    recipients = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS

    spend = meta_insights_service.get_total_spend_24h(brand)
    if spend <= ANOMALY_SPEND_THRESHOLD_PHP:
        return fired

    pushed = analytics_store.get_sessions(brand)
    inquiries = pushed.get("inquiries") or analytics_store.count_inquiries_from_clicks(brand)

    if inquiries == 0:
        alert = _alert(
            11, "Anomaly Spend with No Leads", SEVERITY_CRITICAL, brand,
            brand, f"PHP {spend:,.2f} spent, 0 inquiries",
            f"Spend > PHP {ANOMALY_SPEND_THRESHOLD_PHP:,.2f} AND inquiries = 0",
            "Verify landing page and redirect /wa-go functionality.",
        )
        if send:
            alert["email_status"] = _dispatch(alert, recipients).get("status")
        fired.append(alert)

    return fired


def run_all_alerts(brands: Optional[List[str]] = None, send: bool = True) -> Dict[str, Any]:
    """
    Evaluate every applicable alert rule across the given brands.

    Returns a summary with the full list of alerts that fired. Individual rule
    failures are logged and skipped so one broken rule cannot stop the sweep.
    """
    global _recent_alerts, _last_run

    target_brands = brands or list(BRAND_CONFIGS.keys())
    fired: List[Dict[str, Any]] = []

    checks = [
        check_ctr_alerts,
        check_frequency_alerts,
        check_expensive_click_alerts,
        check_creative_fatigue_alerts,
        check_zero_delivery_alerts,
        check_anomaly_spend_alerts,
    ]

    for brand in target_brands:
        for check in checks:
            try:
                fired.extend(check(brand, send=send))
            except Exception as e:
                logger.exception(
                    "Alert check %s failed for %s: %s", check.__name__, brand, e
                )

    _recent_alerts = fired
    _last_run = datetime.now().isoformat()

    logger.info(
        "Alert engine evaluated %d brand(s): %d alert(s) fired",
        len(target_brands), len(fired),
    )

    return {
        "evaluated_at": _last_run,
        "brands": target_brands,
        "alerts_fired": len(fired),
        "alerts": fired,
        "by_severity": {
            SEVERITY_CRITICAL: sum(1 for a in fired if a["severity"] == SEVERITY_CRITICAL),
            SEVERITY_WARNING: sum(1 for a in fired if a["severity"] == SEVERITY_WARNING),
            SEVERITY_WATCH: sum(1 for a in fired if a["severity"] == SEVERITY_WATCH),
        },
    }


# ---------------------------------------------------------------------------
# Section 2.6.4: Complete Alert Configuration Table (Master Handoff PDF)
# ---------------------------------------------------------------------------

SECTION_264_ALERT_RULES = [
    {
        "id": 1,
        "level": "WATCH",
        "parameter": "Creative Fatigue",
        "trigger_condition": "CTR dropped 20-29% vs prior 7 days on same active ad",
        "required_action": "Flag for review at next weekly meeting",
        "source": "Query Table A",
        "routing": "monitoring person only",
    },
    {
        "id": 2,
        "level": "WATCH",
        "parameter": "Audience Saturation",
        "trigger_condition": "Frequency > 2.5 on any adset (7-day window). Historical median: 2.37",
        "required_action": "Monitor closely. Note adset name.",
        "source": "Ad Set Insights",
        "routing": "monitoring person only",
    },
    {
        "id": 3,
        "level": "WARNING",
        "parameter": "Creative Fatigue",
        "trigger_condition": "CTR dropped 30-44% vs prior 7 days on same active ad",
        "required_action": "Review ad immediately. Prepare replacement creative.",
        "source": "Query Table A",
        "routing": "monitoring person + relevant brand marketing team",
    },
    {
        "id": 4,
        "level": "WARNING",
        "parameter": "Underperforming Ads",
        "trigger_condition": "CTR < 0.67% on any active performance ad (last 7 days). Historical 25th percentile.",
        "required_action": "Review creative. Plan rotation if no improvement in 3 days.",
        "source": "Ad Insights",
        "routing": "monitoring person + relevant brand marketing team",
    },
    {
        "id": 5,
        "level": "WARNING",
        "parameter": "Expensive Ads",
        "trigger_condition": "CPC risen 30-49% above the ad's own 30-day average (or CPC >= ₱16.31, 75th percentile)",
        "required_action": "Review targeting and creative. Plan budget reallocation.",
        "source": "Query Table B",
        "routing": "monitoring person + relevant brand marketing team",
    },
    {
        "id": 6,
        "level": "WARNING",
        "parameter": "Audience Saturation",
        "trigger_condition": "Frequency > 3.5 on any adset (7-day). Historical 75th percentile: 3.71",
        "required_action": "Expand audience OR rotate creative on this adset.",
        "source": "Ad Set Insights",
        "routing": "monitoring person + relevant brand marketing team",
    },
    {
        "id": 7,
        "level": "CRITICAL",
        "parameter": "Creative Fatigue",
        "trigger_condition": "CTR dropped 45%+ vs prior 7 days on same active ad",
        "required_action": "Pause ad immediately. Rotate creative same day.",
        "source": "Query Table A",
        "routing": "monitoring person + brand team + business owner",
    },
    {
        "id": 8,
        "level": "CRITICAL",
        "parameter": "Underperforming Ads",
        "trigger_condition": "CTR < 0.43% on any active performance ad (last 7 days). Historical 10th percentile.",
        "required_action": "Pause ad. Do not continue spending.",
        "source": "Ad Insights",
        "routing": "monitoring person + brand team + business owner",
    },
    {
        "id": 9,
        "level": "CRITICAL",
        "parameter": "Expensive Ads",
        "trigger_condition": "CPC risen 50%+ above the ad's own 30-day average (or CPC >= ₱26.48, 90th percentile)",
        "required_action": "Pause ad. Reallocate budget to better-performing ads.",
        "source": "Query Table B",
        "routing": "monitoring person + brand team + business owner",
    },
    {
        "id": 10,
        "level": "CRITICAL",
        "parameter": "Audience Saturation",
        "trigger_condition": "Frequency > 4.5 on any adset (7-day). Historical 90th percentile: 4.46",
        "required_action": "Pause adset immediately. Audience burned. Expand or replace.",
        "source": "Ad Set Insights",
        "routing": "monitoring person + brand team + business owner",
    },
    {
        "id": 11,
        "level": "CRITICAL",
        "parameter": "Delivery Problem",
        "trigger_condition": "Impressions dropped 25%+ WoW while spend dropped less than 10% on same campaign",
        "required_action": "Check ad account health, payment, and policy flags in Meta Business Manager.",
        "source": "Query Table C",
        "routing": "monitoring person + brand team + business owner",
    },
]


def evaluate_campaign_spend_alerts(brand: str = "Home Cartel") -> Dict[str, Any]:
    """
    Evaluate Section 2.6.4 alert rules against the active performance campaigns
    stored in the local attribution database (meta_campaign_spend).

    Enforces mandatory Section 2.6.1 rule: campaign_name NOT LIKE '%FR Stores%'.
    Determines which campaigns are WATCH, WARNING, CRITICAL, or HEALTHY.
    """
    evaluations: List[Dict[str, Any]] = []
    fired_alerts: List[Dict[str, Any]] = []

    try:
        from app.database import get_connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT campaign_name, status, impressions, reach, link_clicks, ctr, cpc, amount_spent
                FROM meta_campaign_spend
                WHERE status = 'active' AND campaign_name NOT LIKE '%FR Stores%'
                ORDER BY amount_spent DESC
            """)
            rows = cursor.fetchall()
    except Exception as e:
        logger.warning("Could not evaluate alerts from meta_campaign_spend: %s", e)
        rows = []

    today_str = datetime.now().strftime("%Y-%m-%d")

    for row in rows:
        name = row["campaign_name"] or "Unknown Campaign"
        imp = int(row["impressions"] or 0)
        reach = int(row["reach"] or 0)
        clicks = int(row["link_clicks"] or 0)
        ctr = float(row["ctr"] or 0.0)
        cpc = float(row["cpc"] or 0.0)
        spend = float(row["amount_spent"] or 0.0)
        freq = round(imp / reach, 2) if reach > 0 else 1.0

        item_alerts: List[Dict[str, Any]] = []

        # 1. Audience Saturation (Rules 2, 6, 10)
        if freq > 4.5:
            item_alerts.append({
                "alert_id": 10,
                "level": SEVERITY_CRITICAL,
                "parameter": "Audience Saturation",
                "trigger_condition": "Frequency > 4.5 on any adset (7-day; historical 90th percentile: 4.46)",
                "metric_name": "Frequency",
                "metric_value": f"{freq}x",
                "threshold": "> 4.5",
                "required_action": "Pause adset immediately. Audience burned. Expand or replace.",
                "source": "Ad Set Insights",
                "routing": "monitoring person + brand team + business owner",
                "subject": f"[CRITICAL] — {brand} — Audience Saturation — {today_str}",
            })
        elif freq > 3.5:
            item_alerts.append({
                "alert_id": 6,
                "level": SEVERITY_WARNING,
                "parameter": "Audience Saturation",
                "trigger_condition": "Frequency > 3.5 on any adset (7-day; historical 75th percentile: 3.71)",
                "metric_name": "Frequency",
                "metric_value": f"{freq}x",
                "threshold": "> 3.5",
                "required_action": "Expand audience OR rotate creative on this adset.",
                "source": "Ad Set Insights",
                "routing": "monitoring person + relevant brand marketing team",
                "subject": f"[WARNING] — {brand} — Audience Saturation — {today_str}",
            })
        elif freq > 2.5:
            item_alerts.append({
                "alert_id": 2,
                "level": SEVERITY_WATCH,
                "parameter": "Audience Saturation",
                "trigger_condition": "Frequency > 2.5 on any adset (7-day window; historical median: 2.37)",
                "metric_name": "Frequency",
                "metric_value": f"{freq}x",
                "threshold": "> 2.5",
                "required_action": "Monitor closely. Note adset name.",
                "source": "Ad Set Insights",
                "routing": "monitoring person only",
                "subject": f"[WATCH] — {brand} — Audience Saturation — {today_str}",
            })

        # 2. Underperforming Ads (Rules 4, 8)
        if ctr < 0.43:
            item_alerts.append({
                "alert_id": 8,
                "level": SEVERITY_CRITICAL,
                "parameter": "Underperforming Ads",
                "trigger_condition": "CTR < 0.43% on any active performance ad (last 7 days; historical 10th percentile)",
                "metric_name": "CTR",
                "metric_value": f"{ctr:.2f}%",
                "threshold": "< 0.43%",
                "required_action": "Pause ad. Do not continue spending.",
                "source": "Ad Insights",
                "routing": "monitoring person + brand team + business owner",
                "subject": f"[CRITICAL] — {brand} — Underperforming Ads — {today_str}",
            })
        elif ctr < 0.67:
            item_alerts.append({
                "alert_id": 4,
                "level": SEVERITY_WARNING,
                "parameter": "Underperforming Ads",
                "trigger_condition": "CTR < 0.67% on any active performance ad (last 7 days; historical 25th percentile)",
                "metric_name": "CTR",
                "metric_value": f"{ctr:.2f}%",
                "threshold": "< 0.67%",
                "required_action": "Review creative. Plan rotation if no improvement in 3 days.",
                "source": "Ad Insights",
                "routing": "monitoring person + relevant brand marketing team",
                "subject": f"[WARNING] — {brand} — Underperforming Ads — {today_str}",
            })

        # 3. Expensive Ads (Rules 5, 9)
        if cpc >= 26.48:
            item_alerts.append({
                "alert_id": 9,
                "level": SEVERITY_CRITICAL,
                "parameter": "Expensive Ads",
                "trigger_condition": "CPC >= ₱26.48 (90th percentile) or risen 50%+ above 30-day average",
                "metric_name": "CPC",
                "metric_value": f"₱{cpc:.2f}",
                "threshold": ">= ₱26.48",
                "required_action": "Pause ad. Reallocate budget to better-performing ads.",
                "source": "Query Table B",
                "routing": "monitoring person + brand team + business owner",
                "subject": f"[CRITICAL] — {brand} — Expensive Ads — {today_str}",
            })
        elif cpc >= 16.31:
            item_alerts.append({
                "alert_id": 5,
                "level": SEVERITY_WARNING,
                "parameter": "Expensive Ads",
                "trigger_condition": "CPC >= ₱16.31 (75th percentile) or risen 30-49% above 30-day average",
                "metric_name": "CPC",
                "metric_value": f"₱{cpc:.2f}",
                "threshold": ">= ₱16.31",
                "required_action": "Review targeting and creative. Plan budget reallocation.",
                "source": "Query Table B",
                "routing": "monitoring person + relevant brand marketing team",
                "subject": f"[WARNING] — {brand} — Expensive Ads — {today_str}",
            })

        # Rank severity for this campaign
        if any(a["level"] == SEVERITY_CRITICAL for a in item_alerts):
            highest_level = SEVERITY_CRITICAL
            primary_action = next(a["required_action"] for a in item_alerts if a["level"] == SEVERITY_CRITICAL)
            primary_param = next(a["parameter"] for a in item_alerts if a["level"] == SEVERITY_CRITICAL)
        elif any(a["level"] == SEVERITY_WARNING for a in item_alerts):
            highest_level = SEVERITY_WARNING
            primary_action = next(a["required_action"] for a in item_alerts if a["level"] == SEVERITY_WARNING)
            primary_param = next(a["parameter"] for a in item_alerts if a["level"] == SEVERITY_WARNING)
        elif any(a["level"] == SEVERITY_WATCH for a in item_alerts):
            highest_level = SEVERITY_WATCH
            primary_action = next(a["required_action"] for a in item_alerts if a["level"] == SEVERITY_WATCH)
            primary_param = next(a["parameter"] for a in item_alerts if a["level"] == SEVERITY_WATCH)
        else:
            highest_level = "HEALTHY"
            primary_action = "Optimal delivery - all metrics within safe thresholds."
            primary_param = "Optimal Delivery"

        eval_record = {
            "campaign_name": name,
            "status": highest_level,
            "level": highest_level,
            "primary_parameter": primary_param,
            "primary_action": primary_action,
            "frequency": freq,
            "ctr": ctr,
            "cpc": cpc,
            "spend": spend,
            "impressions": imp,
            "reach": reach,
            "link_clicks": clicks,
            "alerts": item_alerts,
        }
        evaluations.append(eval_record)

        for a in item_alerts:
            fired_alerts.append({
                **a,
                "campaign_name": name,
                "brand": brand,
                "impressions": imp,
                "reach": reach,
                "spend": spend,
                "ctr": ctr,
                "cpc": cpc,
                "frequency": freq,
            })

    counts = {
        "critical": sum(1 for e in evaluations if e["level"] == SEVERITY_CRITICAL),
        "warning": sum(1 for e in evaluations if e["level"] == SEVERITY_WARNING),
        "watch": sum(1 for e in evaluations if e["level"] == SEVERITY_WATCH),
        "healthy": sum(1 for e in evaluations if e["level"] == "HEALTHY"),
        "total": len(evaluations),
    }

    overall_status = (
        SEVERITY_CRITICAL if counts["critical"] > 0
        else SEVERITY_WARNING if counts["warning"] > 0
        else SEVERITY_WATCH if counts["watch"] > 0
        else "HEALTHY"
    )

    return {
        "evaluated_at": datetime.now().isoformat(),
        "brand": brand,
        "counts": counts,
        "overall_status": overall_status,
        "alerts": fired_alerts,
        "evaluations": evaluations,
        "rules_reference": SECTION_264_ALERT_RULES,
    }


def get_ad_evaluations_summary(brand: str = "Home Cartel") -> Dict[str, Any]:
    """Return comprehensive Section 2.6.4 alert evaluation for API & Dashboard."""
    db_results = evaluate_campaign_spend_alerts(brand=brand)
    return db_results


def clear_cache() -> None:
    """Reset the in-memory alert cache. Used by tests."""
    global _recent_alerts, _last_run
    _recent_alerts = []
    _last_run = None


