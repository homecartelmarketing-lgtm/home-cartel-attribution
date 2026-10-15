"""
Zoho Creator Integration Service
Ad-to-Sale Attribution System
Connects to Zoho Creator (homecartel / cms) to ingest:
1. Estimates1_Report (Quotations created)
2. Sales_Orders_Report (Sales Orders where Payment_Status == 'paid')
Matches records to Ad Clicks by Estimate Number, Phone Number, or Session Token.
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
import requests

from app.config import (
    ZOHO_CLIENT_ID,
    ZOHO_CLIENT_SECRET,
    ZOHO_REFRESH_TOKEN,
    ZOHO_API_DOMAIN,
    ZOHO_ACCOUNTS_URL,
)
from app.database import (
    get_connection,
    is_sales_order_processed,
    log_conversion,
    update_click_rfq,
    update_click_sale,
    lookup_customer_session_token,
    lookup_customer_by_phone,
    save_customer_identity,
)
from app.services.meta_capi_service import send_purchase_event, retry_pending_capi_conversions

logger = logging.getLogger(__name__)

# Zoho Creator Configuration
ZOHO_CREATOR_ACCOUNT = os.environ.get("ZOHO_CREATOR_ACCOUNT", "homecartel")
ZOHO_CREATOR_APP = os.environ.get("ZOHO_CREATOR_APP", "cms")
ZOHO_CREATOR_SALES_ORDERS_REPORT = os.environ.get(
    "ZOHO_CREATOR_SALES_ORDERS_REPORT",
    os.environ.get("ZOHO_CREATOR_PAGE", "Sales_Orders_Report")
)
ZOHO_CREATOR_ESTIMATES_REPORT = os.environ.get("ZOHO_CREATOR_ESTIMATES_REPORT", "Estimates1_Report")
ZOHO_CREATOR_BASE_URL = f"{ZOHO_API_DOMAIN}/creator/v2.1"

# In-memory Token Cache
_cached_access_token: Optional[str] = None
_token_expiry_ts: float = 0.0


def normalize_phone(phone_raw: Any) -> str:
    """
    Normalize Philippine phone numbers to standard 10 digits starting with 9 (e.g., 9171234567).
    Strips all non-digit characters and handles malformed prefixes:
      - '+63-09178389270'   -> '9178389270'
      - '+63-+639052126300' -> '9052126300'
      - '09175563077'       -> '9175563077'
      - '+639955805699'     -> '9955805699'
      - '9171234567'        -> '9171234567'
    """
    if not phone_raw:
        return ""
    digits = re.sub(r"\D", "", str(phone_raw))
    if not digits:
        return ""
    # Extract the terminal 10-digit sequence starting with 9
    match = re.search(r"9\d{9}$", digits)
    if match:
        return match.group(0)
    if len(digits) == 11 and digits.startswith("09"):
        return digits[1:]
    if len(digits) == 12 and digits.startswith("639"):
        return digits[2:]
    return digits


def get_access_token(force_refresh: bool = False) -> str:
    """Get valid Zoho Creator OAuth access token, refreshing if needed."""
    global _cached_access_token, _token_expiry_ts

    now = time.time()
    if _cached_access_token and not force_refresh and now < (_token_expiry_ts - 120):
        return _cached_access_token

    if not all([ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN]):
        raise RuntimeError("Zoho Creator credentials missing in .env (ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN).")

    url = ZOHO_ACCOUNTS_URL or "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }

    resp = requests.post(url, data=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    if "access_token" not in data:
        raise RuntimeError(f"Zoho token refresh failed: {data}")

    _cached_access_token = data["access_token"]
    expires_in = int(data.get("expires_in", 3600))
    _token_expiry_ts = now + expires_in
    logger.info("[+] Zoho Creator access token refreshed successfully.")
    return _cached_access_token


def _creator_request(method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
    """Issue authenticated request to Zoho Creator API with retry on 401."""
    for attempt in (1, 2):
        try:
            token = get_access_token(force_refresh=(attempt == 2))
            headers = {
                "Authorization": f"Zoho-oauthtoken {token}",
                "Accept": "application/json",
            }
            url = f"https://creator.zoho.com/api/v2/{ZOHO_CREATOR_ACCOUNT}/{ZOHO_CREATOR_APP}{path}"
            r = requests.request(method, url, headers=headers, params=params, timeout=25)
            if r.status_code == 401 and attempt == 1:
                logger.warning("[!] Zoho Creator token rejected (401), refreshing token and retrying...")
                continue
            return r
        except Exception as e:
            logger.error(f"[-] Error calling Zoho Creator API: {e}")
            if attempt == 2:
                return None
    return None


def fetch_report_records(report_link_name: str, criteria: Optional[str] = None, max_records: int = 100) -> List[Dict[str, Any]]:
    """Fetch records from a Zoho Creator report."""
    path = f"/report/{report_link_name}"
    params: Dict[str, Any] = {"max_records": max_records}
    if criteria:
        params["criteria"] = criteria

    r = _creator_request("GET", path, params=params)
    if r is not None and r.status_code == 200:
        data = r.json().get("data", [])
        return data if isinstance(data, list) else []
    
    if r is not None and r.status_code != 200:
        logger.error(f"[-] Failed to fetch {report_link_name}: {r.status_code} {r.text[:200]}")
    return []


def find_matching_session(estimate_number: str = "", phone: str = "", customer_name: str = "") -> Optional[Dict[str, Any]]:
    """
    Search attribution database to match a Zoho Creator record back to an Ad click.
    Checks:
    1. Direct match on zoho_estimate_num
    2. Phone match via customer_identities table
    3. Phone match in pending / recent click logs
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # 1. Match by Estimate Number
        if estimate_number:
            cursor.execute("""
                SELECT * FROM click_logs 
                WHERE zoho_estimate_num = ? AND zoho_estimate_num != ''
                ORDER BY id DESC LIMIT 1
            """, (estimate_number,))
            row = cursor.fetchone()
            if row:
                return dict(row)

        # 2. Match by normalized phone in customer_identities (channel-agnostic)
        norm_phone = normalize_phone(phone)
        if norm_phone:
            token = lookup_customer_by_phone(norm_phone, "Home Cartel")
            if not token:
                token = lookup_customer_session_token("phone", norm_phone, "Home Cartel")
            if token:
                cursor.execute("SELECT * FROM click_logs WHERE session_token = ?", (token,))
                row = cursor.fetchone()
                if row:
                    return dict(row)

        return None


def sync_estimates(max_records: int = 100) -> Dict[str, Any]:
    """
    Sync quotes from Estimates1_Report to record quote numbers and amounts.
    Advances matching click logs from 'inquired' -> 'quoted'.
    """
    records = fetch_report_records(ZOHO_CREATOR_ESTIMATES_REPORT, max_records=max_records)
    logger.info(f"[+] Retrieved {len(records)} records from {ZOHO_CREATOR_ESTIMATES_REPORT}.")

    processed = 0
    matched = 0

    for rec in records:
        est_num = str(rec.get("Estimate_Number") or "").strip()
        if not est_num:
            continue

        raw_total = str(rec.get("Total") or "0").replace(",", "")
        try:
            total_amount = float(raw_total)
        except ValueError:
            total_amount = 0.0

        phone = rec.get("Billing_Phone") or rec.get("Shipping_Phone") or ""
        cust_name = rec.get("Customer_Name") or ""

        # Normalize phone and store identity mapping if known
        norm_phone = normalize_phone(phone)

        # Find matching click
        click = find_matching_session(estimate_number=est_num, phone=norm_phone, customer_name=cust_name)
        if click and click.get("session_token"):
            session_token = click["session_token"]
            # If not already quoted with this number, update click log
            if click.get("zoho_estimate_num") != est_num:
                update_click_rfq(session_token, est_num)
                if norm_phone:
                    save_customer_identity("phone", norm_phone, session_token, "Home Cartel")
                matched += 1
        processed += 1

    return {"status": "ok", "total_fetched": len(records), "processed": processed, "matched": matched}


def sync_paid_sales_orders(max_records: int = 100) -> Dict[str, Any]:
    """
    Sync paid sales orders from Sales_Orders_Report where Payment_Status == 'paid'.
    Dispatches Meta CAPI offline Purchase event and updates database revenue.
    """
    records = fetch_report_records(ZOHO_CREATOR_SALES_ORDERS_REPORT, max_records=max_records)
    logger.info(f"[+] Retrieved {len(records)} records from {ZOHO_CREATOR_SALES_ORDERS_REPORT}.")

    paid_orders = 0
    newly_attributed = 0
    unattributed = 0

    for rec in records:
        payment_status = str(rec.get("Payment_Status") or "").strip().lower()
        if payment_status != "paid":
            continue

        so_number = str(rec.get("Sales_Order_Number") or rec.get("ID") or "").strip()
        if not so_number:
            continue

        paid_orders += 1

        # Check if already processed to prevent duplicate CAPI conversions
        if is_sales_order_processed(so_number):
            continue

        raw_total = str(rec.get("Total") or "0").replace(",", "")
        try:
            total_amount = float(raw_total)
        except ValueError:
            total_amount = 0.0

        est_num = str(rec.get("Estimate_Number") or "").strip()
        phone = rec.get("Billing_Phone") or rec.get("Shipping_Phone") or ""
        cust_name = rec.get("Customer_Name") or ""
        norm_phone = normalize_phone(phone)

        # Match back to ad click
        click = find_matching_session(estimate_number=est_num, phone=norm_phone, customer_name=cust_name)

        if click and click.get("session_token"):
            session_token = click["session_token"]
            fbclid = click.get("fbclid") or ""
            brand = click.get("brand") or "Home Cartel"

            logger.info(
                f"[★] ATTRIBUTION MATCH! SO #{so_number} (₱{total_amount:,.2f}) "
                f"matched to Session {session_token} (Campaign: {click.get('utm_campaign') or 'N/A'})."
            )

            if norm_phone and len(norm_phone) == 10 and norm_phone.startswith("9"):
                save_customer_identity("phone", norm_phone, session_token, brand)

            # 1. Update click log in database
            capi_status = "sent" if os.environ.get("META_ACCESS_TOKEN") else "pending_credentials"
            update_click_sale(session_token, so_number, total_amount, capi_status)

            # 2. Trigger Meta CAPI offline Purchase event
            send_purchase_event(
                salesorder_id=so_number,
                total_amount=total_amount,
                phone=norm_phone,
                fbclid=fbclid,
                brand=brand,
                session_token=session_token,
            )

            newly_attributed += 1
        else:
            logger.info(
                f"[i] Paid SO #{so_number} (₱{total_amount:,.2f}) recorded as Unattributed / Organic."
            )
            # Log as unattributed so dashboard has true total revenue numbers
            log_conversion(
                salesorder_id=so_number,
                session_token="",
                fbclid="",
                total=total_amount,
                status="unattributed",
                meta_response="Organic / Direct (No ad click matched)",
            )
            unattributed += 1

    return {
        "status": "ok",
        "total_fetched": len(records),
        "total_paid_orders": paid_orders,
        "newly_attributed": newly_attributed,
        "unattributed": unattributed,
    }


def run_full_zoho_creator_sync() -> Dict[str, Any]:
    """Full sync routine: estimates + paid sales orders + CAPI retry."""
    logger.info("[*] Starting Zoho Creator Full Sync...")
    est_res = sync_estimates(max_records=100)
    so_res = sync_paid_sales_orders(max_records=100)
    capi_retry = retry_pending_capi_conversions()
    return {
        "estimates": est_res,
        "sales_orders": so_res,
        "capi_retry": capi_retry,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

