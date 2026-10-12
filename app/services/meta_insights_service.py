"""
Meta Marketing API Insights Service
Ad-to-Sale Attribution System

Pulls ad / adset / campaign performance from the Meta Marketing API so the
alert engine can evaluate the Part 3 thresholds without depending on a Zoho
Analytics workspace.

Implements the three analytics query tables in Python:
  * Query Table A - creative fatigue (CTR last 7d vs prior 7d)
  * Query Table B - expensive ads (CPC 3d vs 30d baseline)
  * Query Table C - delivery health (7-day adset frequency)

The mandatory 'FR Stores' reach-campaign exclusion from
analytics/alert_thresholds_and_rules.md section 3 is applied to every query.
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

import requests

from app.config import META_ACCESS_TOKEN, get_brand_config

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

# Reach campaigns run at 0.03-0.06% CTR by design. Including them would fire
# false critical CTR alarms every single day, so they are always excluded.
EXCLUDED_CAMPAIGN_KEYWORD = "FR Stores"

# Insight fields requested from the Marketing API.
AD_FIELDS = [
    "ad_id", "ad_name", "campaign_id", "campaign_name", "adset_id", "adset_name",
    "impressions", "inline_link_clicks", "clicks", "spend", "ctr", "cpc",
    "frequency", "actions", "date_start", "date_stop",
]

ADSET_FIELDS = [
    "adset_id", "adset_name", "campaign_id", "campaign_name",
    "impressions", "reach", "spend", "frequency",
]


def _derive_link_ctr(row: Dict[str, Any]) -> Optional[float]:
    """Compute link CTR (%) for an insight row."""
    clicks = float(row.get("inline_link_clicks") or 0.0)
    impressions = float(row.get("impressions") or 0.0)
    if clicks and impressions:
        return round((clicks / impressions) * 100, 4)
    ctr = row.get("ctr")
    return float(ctr) if ctr is not None else None


def _derive_link_cpc(row: Dict[str, Any]) -> Optional[float]:
    """Compute cost per link click (PHP) for an insight row."""
    spend = float(row.get("spend") or 0.0)
    clicks = float(row.get("inline_link_clicks") or 0.0)
    if clicks:
        return round(spend / clicks, 2)
    cpc = row.get("cpc")
    return float(cpc) if cpc is not None else None


def _excludes_reach_campaign(campaign_name: str) -> bool:
    """True when a campaign should be included in threshold evaluation."""
    return EXCLUDED_CAMPAIGN_KEYWORD.lower() not in (campaign_name or "").lower()


def _row_date(row: Dict[str, Any]) -> Optional[date]:
    """Parse the date from a daily insights row."""
    raw = row.get("date_start") or row.get("date")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw)[:10])
    except ValueError:
        return None


def fetch_insights(
    level: str,
    brand: str = "Home Cartel",
    days: int = 30,
    access_token: Optional[str] = None,
    ad_account_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch daily ad / adset insights for the last `days` days.

    Returns a list of normalised row dicts with reach campaigns already
    removed. Returns [] when Meta credentials are missing or the call fails,
    so a misconfigured brand never breaks the other brands in the sweep.
    """
    brand_cfg = get_brand_config(brand)
    token = access_token or brand_cfg.get("access_token") or META_ACCESS_TOKEN
    account = ad_account_id or brand_cfg.get("ad_account_id") or ""

    if not token or not account:
        logger.warning(
            "Meta insights skipped for '%s': missing ad account or access token.", brand
        )
        return []

    if not account.startswith("act_"):
        account = f"act_{account}"

    since = (date.today() - timedelta(days=days)).isoformat()
    until = date.today().isoformat()
    fields = AD_FIELDS if level == "ad" else ADSET_FIELDS

    params: Dict[str, Any] = {
        "access_token": token,
        "level": level,
        "fields": ",".join(fields),
        "time_range": f'{{"since":"{since}","until":"{until}"}}',
        "time_increment": 1,
        "limit": 500,
    }

    rows: List[Dict[str, Any]] = []
    url = f"{GRAPH_BASE}/{account}/insights"

    try:
        while url:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code != 200:
                logger.error(
                    "Meta insights API error for '%s': %s - %s",
                    brand, r.status_code, r.text[:300],
                )
                break

            data = r.json()
            rows.extend(data.get("data") or [])
            url = (data.get("paging") or {}).get("next")
            # The cursor URL already carries every filter.
            params = {"access_token": token}
    except Exception as e:
        logger.error("Meta insights request failed for '%s': %s", brand, e)
        return []

    return [row for row in rows if _excludes_reach_campaign(row.get("campaign_name", ""))]


def query_table_a_creative_fatigue(
    brand: str = "Home Cartel", access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query Table A: CTR change over the last 7 days versus the prior 7 days.

    Mirrors analytics/query_table_a_creative_fatigue.sql.
    """
    rows = fetch_insights("ad", brand=brand, days=14, access_token=access_token)
    if not rows:
        return []

    today = date.today()
    last7_start = today - timedelta(days=7)
    prior7_start = today - timedelta(days=14)

    grouped: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        key = (row.get("ad_name"), row.get("campaign_name"), row.get("adset_name"))
        bucket = grouped.setdefault(
            key,
            {
                "ad_name": row.get("ad_name"),
                "campaign_name": row.get("campaign_name"),
                "adset_name": row.get("adset_name"),
                "last7": [],
                "prior7": [],
            },
        )
        ctr = _derive_link_ctr(row)
        if ctr is None:
            continue

        row_date = _row_date(row)
        if row_date and row_date >= last7_start:
            bucket["last7"].append(ctr)
        elif row_date and row_date >= prior7_start:
            bucket["prior7"].append(ctr)

    results: List[Dict[str, Any]] = []
    for bucket in grouped.values():
        last_ctrs = bucket.pop("last7")
        prior_ctrs = bucket.pop("prior7")
        if not last_ctrs or not prior_ctrs:
            continue

        ctr_last = round(sum(last_ctrs) / len(last_ctrs), 2)
        ctr_prior = round(sum(prior_ctrs) / len(prior_ctrs), 2)
        if ctr_prior == 0:
            continue

        change_pct = round(((ctr_last - ctr_prior) / ctr_prior) * 100, 1)
        results.append(
            {
                **bucket,
                "ctr_last_7d": ctr_last,
                "ctr_prior_7d": ctr_prior,
                "ctr_change_pct": change_pct,
            }
        )

    results.sort(key=lambda r: r["ctr_change_pct"])
    return results


def query_table_b_expensive_ads(
    brand: str = "Home Cartel", access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query Table B: cost per link click over 3 days versus the 30-day baseline.

    Mirrors analytics/query_table_b_expensive_ads.sql.
    """
    rows = fetch_insights("ad", brand=brand, days=30, access_token=access_token)
    if not rows:
        return []

    today = date.today()
    last3_start = today - timedelta(days=3)

    grouped: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        key = (row.get("ad_name"), row.get("campaign_name"), row.get("adset_name"))
        bucket = grouped.setdefault(
            key,
            {
                "ad_name": row.get("ad_name"),
                "campaign_name": row.get("campaign_name"),
                "adset_name": row.get("adset_name"),
                "last3": [],
                "baseline": [],
            },
        )
        cpc = _derive_link_cpc(row)
        if cpc is None:
            continue

        row_date = _row_date(row)
        if row_date and row_date >= last3_start:
            bucket["last3"].append(cpc)
        elif row_date:
            bucket["baseline"].append(cpc)

    results: List[Dict[str, Any]] = []
    for bucket in grouped.values():
        last3 = bucket.pop("last3")
        baseline = bucket.pop("baseline")
        if not last3 or not baseline:
            continue

        cpc_last = round(sum(last3) / len(last3), 2)
        cpc_base = round(sum(baseline) / len(baseline), 2)
        if cpc_base <= 0:
            continue

        spike_pct = round(((cpc_last - cpc_base) / cpc_base) * 100, 1)
        results.append(
            {
                **bucket,
                "cpc_last_3d": cpc_last,
                "cpc_baseline_30d": cpc_base,
                "cpc_spike_pct": spike_pct,
            }
        )

    results.sort(key=lambda r: r["cpc_spike_pct"], reverse=True)
    return results


def query_table_c_delivery_health(
    brand: str = "Home Cartel", access_token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query Table C: 7-day adset frequency saturation status.

    Mirrors analytics/query_table_c_delivery_health.sql.
    """
    rows = fetch_insights("adset", brand=brand, days=7, access_token=access_token)
    if not rows:
        return []

    grouped: Dict[tuple, Dict[str, Any]] = {}
    for row in rows:
        key = (row.get("campaign_name"), row.get("adset_name"))
        bucket = grouped.setdefault(
            key,
            {
                "campaign_name": row.get("campaign_name"),
                "adset_name": row.get("adset_name"),
                "frequencies": [],
                "impressions": 0.0,
                "reach": 0.0,
                "spend": 0.0,
            },
        )
        freq = row.get("frequency")
        if freq is not None:
            try:
                bucket["frequencies"].append(float(freq))
            except (TypeError, ValueError):
                pass
        for field in ("impressions", "reach", "spend"):
            try:
                bucket[field] += float(row.get(field) or 0.0)
            except (TypeError, ValueError):
                pass

    results: List[Dict[str, Any]] = []
    for bucket in grouped.values():
        freqs = bucket.pop("frequencies")
        if not freqs:
            continue

        avg_freq = round(sum(freqs) / len(freqs), 2)
        # Thresholds from analytics/alert_thresholds_and_rules.md section 2.
        if avg_freq >= 4.46:
            status = "CRITICAL_SATURATION"
        elif avg_freq >= 3.71:
            status = "WATCH_FREQUENCY"
        else:
            status = "HEALTHY"

        results.append(
            {**bucket, "current_frequency_7d": avg_freq, "delivery_status": status}
        )

    results.sort(key=lambda r: r["current_frequency_7d"], reverse=True)
    return results


def get_ad_level_metrics(
    brand: str = "Home Cartel", access_token: Optional[str] = None, days: int = 3
) -> List[Dict[str, Any]]:
    """
    Per-ad CTR / impression / spend totals, used by CTR and delivery alerts.
    """
    rows = fetch_insights("ad", brand=brand, days=days, access_token=access_token)

    grouped: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        ad_key = row.get("ad_id") or row.get("ad_name")
        bucket = grouped.setdefault(
            ad_key,
            {
                "ad_id": row.get("ad_id"),
                "ad_name": row.get("ad_name"),
                "campaign_name": row.get("campaign_name"),
                "adset_name": row.get("adset_name"),
                "impressions": 0.0,
                "clicks": 0.0,
                "spend": 0.0,
                "ctrs": [],
            },
        )
        try:
            bucket["impressions"] += float(row.get("impressions") or 0.0)
            bucket["clicks"] += float(
                row.get("inline_link_clicks") or row.get("clicks") or 0.0
            )
            bucket["spend"] += float(row.get("spend") or 0.0)
        except (TypeError, ValueError):
            pass
        ctr = _derive_link_ctr(row)
        if ctr is not None:
            bucket["ctrs"].append(ctr)

    results: List[Dict[str, Any]] = []
    for bucket in grouped.values():
        ctrs = bucket.pop("ctrs")
        bucket["impressions"] = int(bucket["impressions"])
        bucket["clicks"] = int(bucket["clicks"])
        bucket["spend"] = round(bucket["spend"], 2)
        bucket["ctr_pct"] = round(sum(ctrs) / len(ctrs), 4) if ctrs else 0.0
        results.append(bucket)

    return results


def get_total_spend_24h(
    brand: str = "Home Cartel", access_token: Optional[str] = None
) -> float:
    """Total ad spend in the last 24 hours, for Alert #11."""
    rows = fetch_insights("ad", brand=brand, days=1, access_token=access_token)
    total = 0.0
    for row in rows:
        try:
            total += float(row.get("spend") or 0.0)
        except (TypeError, ValueError):
            pass
    return round(total, 2)


