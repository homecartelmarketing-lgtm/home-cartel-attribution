"""
Ad Performance Alert Engine
Ad-to-Sale Attribution System

Evaluates the alert rules of the Part 3 handoff (analytics/alert_thresholds_and_rules.md)
against the campaign-level Meta CSV import held in `meta_campaign_spend`. The Meta
Marketing API is not used.

Thresholds come from 16 months of empirical performance across 2,284 active
performance ads (January 2025 - May 2026). The mandatory 'FR Stores' exclusion
(PDF Sec 2.6.1) is applied in the evaluation query.

Emails go out when a campaign becomes flagged or escalates after a CSV import
(`notify_ad_health_changes`), plus a daily digest (`send_daily_ad_health_digest`).
"""

import html as html_lib
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from app.config import (
    ALERT_RECIPIENTS,
    ALERT_BRAND_TEAM_RECIPIENTS,
    ALERT_OWNER_RECIPIENTS,
    get_brand_config,
)
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_WARNING = "WARNING"
SEVERITY_WATCH = "WATCH"

# PDF Sec 2.6.3 confirmed thresholds for campaign-level evaluation. Also served to
# the dashboard so its Ad Health charts draw the same lines the alerts fire on.
HEALTH_THRESHOLDS = {
    "frequency": {"watch": 2.5, "warning": 3.5, "critical": 4.5},
    "ctr": {"warning": 0.67, "critical": 0.43},
    # PDF 2.6.3: CPC percentiles are reference points only. Expensive Ads fires on
    # +30% / +50% over the ad's own 30-day average, which needs the daily report.
    "cpc_reference": {"p75": 16.31, "p90": 26.48},
    # Trend checks (PDF 2.6.4 rules 1, 3, 5, 7, 9, 11). They run on the daily
    # breakdown report: the last 7 days against the 7 days before, and the last 7
    # days of CPC against the 30 days before that.
    "trend": {
        "ctr_drop": {"watch": 20, "warning": 30, "critical": 45},
        "cpc_rise": {"warning": 30, "critical": 50},
        "impressions_drop": 25,
        "spend_drop_max": 10,
    },
}

# Windows with too little traffic give noisy percentages, so the trend checks skip them.
TREND_MIN_IMPRESSIONS = 1000
TREND_MIN_CLICKS = 30
TREND_MIN_BASELINE_DAYS = 14

# PDF Sec 4.3 alert response SOPs, keyed by alert parameter. Served to the dashboard
# so each flagged campaign shows what the brand team should do.
ALERT_SOPS = {
    "Audience Saturation": {
        "title": "Audience Saturation - WARNING or CRITICAL",
        "steps": [
            "Identify the affected adset.",
            "Check the audience size and how long the adset has been running.",
            "WARNING: expand the audience (new interest layers or a higher lookalike percentage) OR rotate the creative to refresh the experience for the same audience.",
            "CRITICAL: pause the adset immediately. The audience is burned. Create a new adset with an expanded or different audience targeting the same product.",
            "Do not simply lower the budget on a saturated adset - this extends the saturation period without solving it.",
        ],
    },
    "Creative Fatigue": {
        "title": "Creative Fatigue - WARNING or CRITICAL",
        "steps": [
            "Open the Meta Ads dashboard for the affected brand.",
            "Find the specific ad mentioned in the alert.",
            "Check the ad's performance over the last 14 days - confirm the CTR trend is real, not a data anomaly.",
            "If confirmed: prepare a replacement creative from the creative library.",
            "WARNING: schedule the replacement creative for the next rotation cycle (within 3 days).",
            "CRITICAL: pause the affected ad immediately. Launch replacement creative the same day.",
            "Monitor the new creative's CTR for the first 3 days. Report the outcome to the monitoring person.",
        ],
    },
    "Delivery Problem": {
        "title": "Delivery Problem - CRITICAL",
        "steps": [
            "This is the most urgent alert - budget is being spent but ads are not being shown.",
            "Check Meta Business Manager > Account Quality for policy flags or payment issues.",
            "Check the payment method on the ad account is valid and not expired.",
            "Check whether any campaigns have been flagged or restricted.",
            "If no policy issues are found, check whether the campaign budget has been exhausted.",
            "Report findings to the business owner within 1 hour.",
        ],
    },
}

def recipients_for_severity(brand: str, severity: str) -> List[str]:
    """
    PDF Sec 2.6.5 routing.

    WATCH -> monitoring person only; WARNING -> + brand team;
    CRITICAL -> + brand team + business owner. Falls back to the monitoring
    list alone when the extra groups are not configured.
    """
    recipients = list(get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS)
    if severity in (SEVERITY_WARNING, SEVERITY_CRITICAL):
        recipients += ALERT_BRAND_TEAM_RECIPIENTS
    if severity == SEVERITY_CRITICAL:
        recipients += ALERT_OWNER_RECIPIENTS
    return list(dict.fromkeys(r for r in recipients if r))


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
        "trigger_condition": "CPC risen 30-49% above the ad's own 30-day average",
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
        "trigger_condition": "CPC risen 50%+ above the ad's own 30-day average",
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


def _rule_by_id(rule_id: int) -> Dict[str, Any]:
    return next(r for r in SECTION_264_ALERT_RULES if r["id"] == rule_id)


def _trend_alert(rule_id: int, brand: str, today_str: str, metric_name: str,
                 metric_value: str, threshold: str, detail: str) -> Dict[str, Any]:
    r = _rule_by_id(rule_id)
    return {
        "alert_id": rule_id,
        "level": r["level"],
        "parameter": r["parameter"],
        "trigger_condition": r["trigger_condition"],
        "metric_name": metric_name,
        "metric_value": metric_value,
        "threshold": threshold,
        "required_action": r["required_action"],
        "source": r["source"],
        "routing": r["routing"],
        "subject": f"[{r['level']}] — {brand} — {r['parameter']} — {today_str}",
        "detail": detail,
    }


def _load_daily_rows() -> Dict[str, Dict[date, tuple]]:
    """campaign_name -> {day: (spend, impressions, link_clicks)} from the daily report."""
    out: Dict[str, Dict[date, tuple]] = {}
    try:
        from app.database import get_connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT campaign_name, report_date, amount_spent, impressions, link_clicks FROM meta_campaign_daily"
            )
            for r in cursor.fetchall():
                try:
                    day = datetime.strptime(str(r["report_date"])[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue
                out.setdefault(r["campaign_name"], {})[day] = (
                    float(r["amount_spent"] or 0.0), int(r["impressions"] or 0), int(r["link_clicks"] or 0),
                )
    except Exception as e:
        logger.warning("Could not read the daily report table: %s", e)
    return out


def _window_totals(days: Dict[date, tuple], start: date, end: date) -> Dict[str, Any]:
    spend = 0.0
    imp = clicks = active_days = 0
    d = start
    while d <= end:
        row = days.get(d)
        if row:
            spend += row[0]
            imp += row[1]
            clicks += row[2]
            if row[1] > 0:
                active_days += 1
        d += timedelta(days=1)
    return {
        "spend": spend, "impressions": imp, "clicks": clicks, "active_days": active_days,
        "ctr": (clicks / imp * 100) if imp > 0 else None,
        "cpc": (spend / clicks) if clicks > 0 else None,
    }


def _trend_checks(name: str, days: Dict[date, tuple], latest: date, brand: str, today_str: str):
    """
    Week-over-week checks for one campaign. Returns (alerts, trend); trend holds the
    numbers behind them for the dashboard. latest is the last complete day.
    """
    th = HEALTH_THRESHOLDS["trend"]
    last7 = _window_totals(days, latest - timedelta(days=6), latest)
    prior7 = _window_totals(days, latest - timedelta(days=13), latest - timedelta(days=7))
    base30 = _window_totals(days, latest - timedelta(days=36), latest - timedelta(days=7))
    baseline_ok = base30["active_days"] >= TREND_MIN_BASELINE_DAYS

    trend: Dict[str, Any] = {
        "period_end": latest.isoformat(),
        "ctr_last7": last7["ctr"], "ctr_prior7": prior7["ctr"],
        "cpc_last7": last7["cpc"], "cpc_avg30": base30["cpc"] if baseline_ok else None,
        "impressions_last7": last7["impressions"], "impressions_prior7": prior7["impressions"],
        "spend_last7": last7["spend"], "spend_prior7": prior7["spend"],
    }
    alerts: List[Dict[str, Any]] = []

    enough_traffic = (
        last7["impressions"] >= TREND_MIN_IMPRESSIONS and prior7["impressions"] >= TREND_MIN_IMPRESSIONS
    )

    # Creative Fatigue (rules 1, 3, 7): link CTR fell vs the previous 7 days.
    if enough_traffic and last7["ctr"] is not None and prior7["ctr"]:
        drop = (prior7["ctr"] - last7["ctr"]) / prior7["ctr"] * 100
        trend["ctr_drop_pct"] = round(drop, 1)
        cut = th["ctr_drop"]
        if drop >= cut["critical"]:
            rule_id, limit = 7, cut["critical"]
        elif drop >= cut["warning"]:
            rule_id, limit = 3, cut["warning"]
        elif drop >= cut["watch"]:
            rule_id, limit = 1, cut["watch"]
        else:
            rule_id, limit = None, None
        if rule_id:
            alerts.append(_trend_alert(
                rule_id, brand, today_str, "CTR vs previous 7 days", f"-{drop:.0f}%", f">= {limit}% drop",
                f"CTR fell from {prior7['ctr']:.2f}% to {last7['ctr']:.2f}% over the last 7 days.",
            ))

    # Expensive Ads (rules 5, 9): CPC vs the ad's own 30-day average.
    if baseline_ok and base30["cpc"] and last7["clicks"] >= TREND_MIN_CLICKS and last7["cpc"] is not None:
        rise = (last7["cpc"] - base30["cpc"]) / base30["cpc"] * 100
        trend["cpc_rise_pct"] = round(rise, 1)
        cut = th["cpc_rise"]
        if rise >= cut["critical"]:
            rule_id, limit = 9, cut["critical"]
        elif rise >= cut["warning"]:
            rule_id, limit = 5, cut["warning"]
        else:
            rule_id, limit = None, None
        if rule_id:
            alerts.append(_trend_alert(
                rule_id, brand, today_str, "CPC vs 30-day average", f"+{rise:.0f}%", f">= +{limit}%",
                f"Cost per click rose from {base30['cpc']:.2f} to {last7['cpc']:.2f} (PHP).",
            ))

    # Delivery Problem (rule 11): impressions dropped while spend barely moved.
    if enough_traffic and prior7["spend"] > 0:
        imp_drop = (prior7["impressions"] - last7["impressions"]) / prior7["impressions"] * 100
        spend_drop = (prior7["spend"] - last7["spend"]) / prior7["spend"] * 100
        trend["impressions_drop_pct"] = round(imp_drop, 1)
        trend["spend_drop_pct"] = round(spend_drop, 1)
        if imp_drop >= th["impressions_drop"] and spend_drop < th["spend_drop_max"]:
            alerts.append(_trend_alert(
                11, brand, today_str, "Impressions vs spend", f"-{imp_drop:.0f}% impressions",
                f">= {th['impressions_drop']}% drop while spend fell < {th['spend_drop_max']}%",
                f"Impressions fell {imp_drop:.0f}% but spend changed only {-spend_drop:+.0f}%.",
            ))

    has_data = bool(last7["impressions"] or prior7["impressions"])
    return alerts, (trend if has_data else None)


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
                SELECT campaign_name, status, impressions, reach, link_clicks, ctr, cpc, amount_spent,
                       reporting_starts, reporting_ends, updated_at
                FROM meta_campaign_spend
                WHERE status = 'active' AND campaign_name NOT LIKE '%FR Stores%'
                ORDER BY amount_spent DESC
            """)
            rows = cursor.fetchall()
    except Exception as e:
        logger.warning("Could not evaluate alerts from meta_campaign_spend: %s", e)
        rows = []

    today_str = datetime.now().strftime("%Y-%m-%d")
    th_freq = HEALTH_THRESHOLDS["frequency"]
    th_ctr = HEALTH_THRESHOLDS["ctr"]

    # Daily report (optional): the trend checks end on the last complete day, so a
    # report pulled mid-day does not make today's partial numbers look like a drop.
    daily = _load_daily_rows()
    all_days = [d for per in daily.values() for d in per]
    latest_day = None
    if all_days:
        latest_day = min(max(all_days), datetime.now().date() - timedelta(days=1))

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
        if freq > th_freq["critical"]:
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
        elif freq > th_freq["warning"]:
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
        elif freq > th_freq["watch"]:
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
        if ctr < th_ctr["critical"]:
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
        elif ctr < th_ctr["warning"]:
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

        # Trend checks (Rules 1, 3, 5, 7, 9, 11) need the daily breakdown report.
        trend = None
        if latest_day is not None and name in daily:
            trend_alerts, trend = _trend_checks(name, daily[name], latest_day, brand, today_str)
            item_alerts.extend(trend_alerts)

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
            "trend": trend,
            "sop": ALERT_SOPS.get(primary_param),
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

    # Provenance: this view reads the campaign-level Meta CSV import, not the Meta API.
    starts = [str(r["reporting_starts"]) for r in rows if r["reporting_starts"]]
    ends = [str(r["reporting_ends"]) for r in rows if r["reporting_ends"]]
    updated = [str(r["updated_at"]) for r in rows if r["updated_at"]]

    return {
        "evaluated_at": datetime.now().isoformat(),
        "data_source": "meta_csv_import",
        "data_as_of": max(updated) if updated else None,
        "window": {
            "start": min(starts) if starts else None,
            "end": max(ends) if ends else None,
        },
        "daily_window": {
            "start": min(all_days).isoformat() if all_days else None,
            "end": max(all_days).isoformat() if all_days else None,
            "days": len(set(all_days)),
            "trend_checks": latest_day is not None,
        },
        "sops": ALERT_SOPS,
        "brand": brand,
        "counts": counts,
        "overall_status": overall_status,
        "alerts": fired_alerts,
        "evaluations": evaluations,
        "rules_reference": SECTION_264_ALERT_RULES,
        "thresholds": HEALTH_THRESHOLDS,
    }


_LEVEL_RANK = {"HEALTHY": 0, SEVERITY_WATCH: 1, SEVERITY_WARNING: 2, SEVERITY_CRITICAL: 3}


def _ensure_state_table(conn) -> None:
    """Remember the last level notified per campaign so emails only go out on change."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_health_state (
            brand TEXT NOT NULL,
            campaign_name TEXT NOT NULL,
            level TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brand, campaign_name)
        )
        """
    )
    conn.commit()


def _dispatch_campaign_alert(
    brand: str, ev: Dict[str, Any], alert: Dict[str, Any], previous_level: str,
    recipients: List[str],
) -> Dict[str, Any]:
    """Email one campaign alert (PDF Sec 2.6.5 format). Never raises."""
    esc = html_lib.escape
    sop = ev.get("sop") or {}
    steps = sop.get("steps") or []
    lines = [
        f"Brand: {brand}",
        f"Campaign: {ev['campaign_name']}",
        f"Level: {alert['level']} (was {previous_level})",
        "",
        "Triggered Metric:",
        f"- {alert['metric_name']}: {alert['metric_value']}",
        f"- Threshold: {alert['threshold']}",
        "",
        f"Required action: {alert['required_action']}",
    ]
    if steps:
        lines += ["", sop.get("title", "Response steps") + ":"] + [f"{i}. {s}" for i, s in enumerate(steps, 1)]
    lines += ["", "Source: Meta CSV import (campaign-level). 'FR Stores' Reach campaigns are excluded."]

    steps_html = "".join(f"<li>{esc(s)}</li>" for s in steps)
    html = (
        "<html><body style='font-family:Arial,Helvetica,sans-serif;color:#222;'>"
        f"<h2 style='margin-bottom:2px;'>{esc(alert['parameter'])} &mdash; {esc(alert['level'])}</h2>"
        f"<p style='margin-top:0;color:#666;'>{esc(brand)} &mdash; {esc(ev['campaign_name'])}</p>"
        "<table cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>"
        f"<tr><td><strong>{esc(alert['metric_name'])}</strong></td><td>{esc(str(alert['metric_value']))}</td></tr>"
        f"<tr><td><strong>Threshold</strong></td><td>{esc(str(alert['threshold']))}</td></tr>"
        f"<tr><td><strong>Level</strong></td><td>{esc(alert['level'])} (was {esc(previous_level)})</td></tr>"
        "</table>"
        f"<p><strong>Required action:</strong> {esc(alert['required_action'])}</p>"
        + (f"<p><strong>{esc(sop.get('title', 'Response steps'))}</strong></p><ol>{steps_html}</ol>" if steps else "")
        + "<p style='font-size:12px;color:#666;'>Source: Meta CSV import (campaign-level). "
        "Reach campaigns ('FR Stores') are excluded.</p></body></html>"
    )
    try:
        return send_email(
            subject=alert["subject"],
            body_text="\n".join(lines),
            body_html=html,
            recipients=recipients,
        )
    except Exception as e:
        logger.error("Ad health alert email failed for %s: %s", ev["campaign_name"], e)
        return {"status": "failed", "error": str(e)}


def notify_ad_health_changes(brand: str = "Home Cartel", send: bool = True) -> Dict[str, Any]:
    """
    Evaluate the current CSV data and email each campaign whose level is new or
    has escalated since the last notification (WATCH -> WARNING -> CRITICAL).

    Unchanged or improving campaigns stay quiet. The result feeds the dashboard
    pop-up, so it reports each alert and what happened to its email.
    """
    from app.database import get_connection

    summary = evaluate_campaign_spend_alerts(brand=brand)
    new_alerts: List[Dict[str, Any]] = []

    with get_connection() as conn:
        _ensure_state_table(conn)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT campaign_name, level FROM ad_health_state WHERE brand = ?", (brand,)
        )
        previous = {r["campaign_name"]: r["level"] for r in cursor.fetchall()}

        for ev in summary["evaluations"]:
            level = ev["level"]
            prev = previous.get(ev["campaign_name"], "HEALTHY")
            if _LEVEL_RANK.get(level, 0) > _LEVEL_RANK.get(prev, 0):
                alert = next((a for a in ev["alerts"] if a["level"] == level), None)
                if alert is not None:
                    recipients = recipients_for_severity(brand, level)
                    result = (
                        _dispatch_campaign_alert(brand, ev, alert, prev, recipients)
                        if send else {"status": "not_sent"}
                    )
                    new_alerts.append({
                        "campaign_name": ev["campaign_name"],
                        "level": level,
                        "previous_level": prev,
                        "parameter": alert["parameter"],
                        "metric_name": alert["metric_name"],
                        "metric_value": alert["metric_value"],
                        "threshold": alert["threshold"],
                        "required_action": alert["required_action"],
                        "sop": ev.get("sop"),
                        "email_status": result.get("status"),
                        "email_detail": result.get("reason") or result.get("error"),
                    })
            cursor.execute(
                """
                INSERT INTO ad_health_state (brand, campaign_name, level, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(brand, campaign_name) DO UPDATE SET
                    level = excluded.level, updated_at = CURRENT_TIMESTAMP
                """,
                (brand, ev["campaign_name"], level),
            )
        conn.commit()

    return {
        "brand": brand,
        "evaluated_at": summary["evaluated_at"],
        "overall_status": summary["overall_status"],
        "new_alerts": new_alerts,
        "emails_sent": sum(1 for a in new_alerts if a["email_status"] == "sent"),
    }


def send_daily_ad_health_digest(brand: str = "Home Cartel") -> Dict[str, Any]:
    """
    PDF Sec 2.6.6: daily snapshot for the monitoring person + business owner,
    sent even when no alert fires.
    """
    summary = evaluate_campaign_spend_alerts(brand=brand)
    counts = summary["counts"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    flagged = [e for e in summary["evaluations"] if e["level"] != "HEALTHY"]
    window = summary.get("window") or {}

    lines = [
        f"Daily Digest - {brand} - {today_str}",
        f"Overall status: {summary['overall_status']}",
        f"Critical {counts['critical']} | Warning {counts['warning']} | "
        f"Watch {counts['watch']} | Healthy {counts['healthy']} (of {counts['total']} active campaigns)",
        f"Data source: Meta CSV import, as of {summary.get('data_as_of') or 'n/a'} "
        f"(window {window.get('start') or '?'} to {window.get('end') or '?'})",
        "",
    ]
    if flagged:
        lines.append("Needs attention:")
        for e in flagged:
            lines.append(
                f"- [{e['level']}] {e['campaign_name']}: {e['primary_parameter']} | "
                f"Freq {e['frequency']}x | CTR {e['ctr']:.2f}% | Action: {e['primary_action']}"
            )
    else:
        lines.append("All active campaigns are inside the safe thresholds.")
    body_text = "\n".join(lines)

    rows_html = "".join(
        f"<li><strong>[{html_lib.escape(e['level'])}]</strong> {html_lib.escape(e['campaign_name'])} - "
        f"{html_lib.escape(e['primary_parameter'])} (Freq {e['frequency']}x, CTR {e['ctr']:.2f}%)<br>"
        f"<em>{html_lib.escape(e['primary_action'])}</em></li>"
        for e in flagged
    ) or "<li>All active campaigns are inside the safe thresholds.</li>"
    body_html = (
        f"<html><body style='font-family:Arial,Helvetica,sans-serif;color:#222;'>"
        f"<h2>Daily Digest - {html_lib.escape(brand)} - {today_str}</h2>"
        f"<p>Overall status: <strong>{summary['overall_status']}</strong><br>"
        f"Critical {counts['critical']} &middot; Warning {counts['warning']} &middot; "
        f"Watch {counts['watch']} &middot; Healthy {counts['healthy']}</p>"
        f"<ul>{rows_html}</ul>"
        f"<p style='font-size:12px;color:#666;'>Source: Meta CSV import, as of "
        f"{html_lib.escape(str(summary.get('data_as_of') or 'n/a'))}.</p></body></html>"
    )

    monitor = get_brand_config(brand).get("alert_recipients") or ALERT_RECIPIENTS
    recipients = list(dict.fromkeys(r for r in [*monitor, *ALERT_OWNER_RECIPIENTS] if r))
    try:
        return send_email(
            subject=f"Daily Digest — {brand} — {today_str}",
            body_text=body_text,
            body_html=body_html,
            recipients=recipients,
        )
    except Exception as e:
        logger.error("Daily digest dispatch failed: %s", e)
        return {"status": "failed", "error": str(e)}


def get_ad_evaluations_summary(brand: str = "Home Cartel") -> Dict[str, Any]:
    """Return comprehensive Section 2.6.4 alert evaluation for API & Dashboard."""
    db_results = evaluate_campaign_spend_alerts(brand=brand)
    return db_results
