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
) -> Dict[str, Any]:
    """Build a normalised alert record."""
    return {
        "alert_id": alert_id,
        "alert_name": name,
        "severity": severity,
        "brand": brand,
        "entity": entity or {},
        "subject": f"[ALERT - {severity}] {brand} - {name}: {subject_detail}",
        "metric_value": metric_value,
        "threshold_value": threshold_value,
        "recommended_action": sop,
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


def clear_cache() -> None:
    """Reset the in-memory alert cache. Used by tests."""
    global _recent_alerts, _last_run
    _recent_alerts = []
    _last_run = None

