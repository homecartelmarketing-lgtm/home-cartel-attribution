"""
Configuration and Environment Settings
Ad-to-Sale Attribution System (Python Native)
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Automatically load .env file if present in BASE_DIR
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k not in os.environ:
                        os.environ[k] = v
    except Exception:
        pass

# Database configuration (PostgreSQL if DATABASE_URL is set, otherwise SQLite fallback)
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_POSTGRES = bool(DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")))

if os.path.exists("/data") and os.path.isdir("/data"):
    DEFAULT_DB_PATH = "/data/attribution.db"
else:
    DEFAULT_DB_PATH = str(BASE_DIR / "attribution.db")

DATABASE_PATH = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

# Server configuration
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("PORT", os.environ.get("SERVER_PORT", "8000")))

# Zendesk Configuration (homecartelhelp.zendesk.com)
ZD_SUBDOMAIN = os.environ.get("ZD_SUBDOMAIN", "homecartelhelp")
ZD_EMAIL = os.environ.get("ZD_EMAIL", "admin@homecartel.ph")
ZD_TOKEN = os.environ.get("ZD_TOKEN", "")

# Zendesk Custom Ticket Field IDs (Live)
ZD_FIELD_SESSION_TOKEN = int(os.environ.get("ZD_FIELD_SESSION_TOKEN", "17953452223503"))
ZD_FIELD_FBCLID = int(os.environ.get("ZD_FIELD_FBCLID", "17953492031119"))
ZD_FIELD_UTM_CAMPAIGN = int(os.environ.get("ZD_FIELD_UTM_CAMPAIGN", "17953470092687"))
ZD_FIELD_UTM_SOURCE = int(os.environ.get("ZD_FIELD_UTM_SOURCE", "17953470454671"))
ZD_FIELD_UTM_MEDIUM = os.environ.get("ZD_FIELD_UTM_MEDIUM", "") or None
ZD_FIELD_UTM_CONTENT = os.environ.get("ZD_FIELD_UTM_CONTENT", "") or None
ZD_FIELD_CONTACT_CHANNEL = int(os.environ.get("ZD_FIELD_CONTACT_CHANNEL", "17953481428751"))
ZD_FIELD_ATTRIBUTION_CONFIDENCE = os.environ.get("ZD_FIELD_ATTRIBUTION_CONFIDENCE", "") or None

# Meta Conversions API (CAPI) Configuration
META_DATASET_ID = os.environ.get("META_DATASET_ID", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
META_TEST_EVENT_CODE = os.environ.get("META_TEST_EVENT_CODE", "")

# Meta Marketing API (Part 3 - Analytics & Monitoring)
# Used by the ad insights poller and the alert engine.
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID", "")

# Zoho Books Configuration
ZOHO_ORG_ID = os.environ.get("ZOHO_ORG_ID", "")
ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET", "")
ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN", "")
# Optional bootstrap token; if set it is used once and then replaced by the
# token minted from the refresh token.
ZOHO_ACCESS_TOKEN = os.environ.get("ZOHO_ACCESS_TOKEN", "")
ZOHO_API_DOMAIN = os.environ.get("ZOHO_API_DOMAIN", "https://www.zohoapis.com")
ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.com/oauth/v2/token")
# Refresh the cached access token this many seconds before it actually expires.
ZOHO_TOKEN_REFRESH_MARGIN = int(os.environ.get("ZOHO_TOKEN_REFRESH_MARGIN", "300"))
ZOHO_WEBHOOK_SECRET = os.environ.get("ZOHO_WEBHOOK_SECRET", "")

# Email / Alerting (Part 3 + Workflow 3 notifications)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
SMTP_FROM = os.environ.get("SMTP_FROM", "") or SMTP_USER
ALERT_RECIPIENTS = [
    r.strip() for r in os.environ.get("ALERT_RECIPIENTS", "").split(",") if r.strip()
]

# Timezone used by all scheduled jobs (PHT per the alert matrix).
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Manila")

# Daily attribution audit send time (HH:MM in APP_TIMEZONE).
DAILY_AUDIT_TIME = os.environ.get("DAILY_AUDIT_TIME", "08:00")

# Multi-Brand Directory & Routing Mapping
# Each brand isolates its own Meta dataset, Meta ad account, Zoho Books
# organization, Zoho refresh token and sales inbox so no data crosses brands.
BRAND_CONFIGS = {
    "Home Cartel": {
        "dataset_id": META_DATASET_ID,
        "access_token": META_ACCESS_TOKEN,
        "ad_account_id": os.environ.get("HOME_CARTEL_AD_ACCOUNT_ID", "") or META_AD_ACCOUNT_ID,
        "zoho_org_id": ZOHO_ORG_ID,
        "zoho_refresh_token": os.environ.get("HOME_CARTEL_ZOHO_REFRESH_TOKEN", "") or ZOHO_REFRESH_TOKEN,
        "sales_email": "sales@homecartel.ph",
        "alert_recipients": [
            r.strip() for r in os.environ.get("HOME_CARTEL_ALERT_RECIPIENTS", "").split(",") if r.strip()
        ] or ALERT_RECIPIENTS,
        "shopify_domain": "home-cartel.myshopify.com"
    },
    "Dear Dining": {
        "dataset_id": os.environ.get("DEAR_DINING_DATASET_ID", ""),
        "access_token": os.environ.get("DEAR_DINING_ACCESS_TOKEN", ""),
        "ad_account_id": os.environ.get("DEAR_DINING_AD_ACCOUNT_ID", ""),
        "zoho_org_id": os.environ.get("DEAR_DINING_ZOHO_ORG", ""),
        "zoho_refresh_token": os.environ.get("DEAR_DINING_ZOHO_REFRESH_TOKEN", ""),
        "sales_email": "sales@deardining.ph",
        "alert_recipients": [
            r.strip() for r in os.environ.get("DEAR_DINING_ALERT_RECIPIENTS", "").split(",") if r.strip()
        ] or ALERT_RECIPIENTS,
        "shopify_domain": "dear-dining.myshopify.com"
    },
    "Home22": {
        "dataset_id": os.environ.get("HOME22_DATASET_ID", ""),
        "access_token": os.environ.get("HOME22_ACCESS_TOKEN", ""),
        "ad_account_id": os.environ.get("HOME22_AD_ACCOUNT_ID", ""),
        "zoho_org_id": os.environ.get("HOME22_ZOHO_ORG", ""),
        "zoho_refresh_token": os.environ.get("HOME22_ZOHO_REFRESH_TOKEN", ""),
        "sales_email": "sales@home22.ph",
        "alert_recipients": [
            r.strip() for r in os.environ.get("HOME22_ALERT_RECIPIENTS", "").split(",") if r.strip()
        ] or ALERT_RECIPIENTS,
        "shopify_domain": "home22shop.myshopify.com"
    }
}


def get_brand_config(brand: str) -> dict:
    """Resolve a brand's routing config, falling back to the primary brand."""
    if not brand:
        return BRAND_CONFIGS.get("Home Cartel", {})
    return BRAND_CONFIGS.get(brand) or BRAND_CONFIGS.get("Home Cartel", {})
