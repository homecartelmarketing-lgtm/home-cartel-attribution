"""
Meta Conversions API (CAPI) Service
Ad-to-Sale Attribution System
Handles PII normalization, SHA-256 hashing, fbc generation, and event dispatching.
"""

import hashlib
import time
import requests
import json
from typing import Dict, Any, Optional
from app.config import META_DATASET_ID, META_ACCESS_TOKEN, META_TEST_EVENT_CODE, BRAND_CONFIGS
from app.database import is_sales_order_processed, log_conversion

def normalize_email(email: str) -> str:
    return email.strip().lower() if email else ""

def normalize_phone(phone: str) -> str:
    """Normalize Philippine mobile phone number to E.164 (+639XXXXXXXXX)."""
    if not phone:
        return ""
    digits = "".join(filter(str.isdigit, phone))
    if digits.startswith("63"):
        return "+" + digits
    elif digits.startswith("09"):
        return "+63" + digits[1:]
    elif digits.startswith("9") and len(digits) == 10:
        return "+63" + digits
    return "+" + digits

def hash_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else ""

def build_fbc(fbclid: str, timestamp_ms: Optional[int] = None) -> str:
    if not fbclid:
        return ""
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    return f"fb.1.{timestamp_ms}.{fbclid}"

def send_purchase_event(
    salesorder_id: str,
    total_amount: float,
    email: str = "",
    phone: str = "",
    fbclid: str = "",
    brand: str = "Home Cartel",
    dataset_id: Optional[str] = None,
    access_token: Optional[str] = None,
    session_token: Optional[str] = "",
    force_retry: bool = False
) -> Dict[str, Any]:
    """
    Sends offline Purchase conversion to Meta CAPI.
    Guarantees deduplication using event_id: SO-<salesorder_id>.
    """
    # 1. Deduplication check (F8)
    if not force_retry and is_sales_order_processed(salesorder_id):
        print(f"[!] Sales Order #{salesorder_id} already sent to Meta CAPI. Skipping duplicate.")
        return {"status": "duplicate", "message": "Event already processed"}

    # 2. Resolve credentials per brand
    brand_cfg = BRAND_CONFIGS.get(brand, {})
    target_dataset = dataset_id if dataset_id is not None else (brand_cfg.get("dataset_id") or META_DATASET_ID)
    target_token = access_token if access_token is not None else (brand_cfg.get("access_token") or os.environ.get("META_ACCESS_TOKEN", "") or META_ACCESS_TOKEN)
    
    if not target_dataset or not target_token:
        err_msg = f"Missing Meta Dataset ID or Access Token for brand '{brand}'"
        print(f"[-] {err_msg}")
        log_conversion(salesorder_id, session_token or "", fbclid, total_amount, "failed_missing_credentials", err_msg)
        return {"status": "error", "message": err_msg}

    # 3. Hash PII and prepare payload
    norm_em = normalize_email(email)
    norm_ph = normalize_phone(phone)
    h_em = hash_sha256(norm_em)
    h_ph = hash_sha256(norm_ph)
    fbc = build_fbc(fbclid)
    
    user_data = {}
    if h_em: user_data["em"] = [h_em]
    if h_ph: user_data["ph"] = [h_ph]
    if fbc: user_data["fbc"] = fbc
    
    event_payload = {
        "event_name": "Purchase",
        "event_time": int(time.time()),
        "action_source": "system_generated",
        "event_id": f"SO-{salesorder_id}",
        "user_data": user_data,
        "custom_data": {
            "value": float(total_amount),
            "currency": "PHP"
        }
    }
    
    body = {"data": [event_payload]}
    if META_TEST_EVENT_CODE:
        body["test_event_code"] = META_TEST_EVENT_CODE

    # 4. Dispatch to Meta Graph API
    url = f"https://graph.facebook.com/v19.0/{target_dataset}/events"
    params = {"access_token": target_token}
    
    try:
        response = requests.post(url, params=params, json=body, timeout=20)
        resp_data = response.text
        if response.status_code == 200:
            print(f"[+] Successfully sent Purchase SO-{salesorder_id} (PHP {total_amount:,.2f}) to Meta CAPI")
            log_conversion(salesorder_id, session_token or "", fbclid, total_amount, "success", resp_data)
            return {"status": "success", "event_id": f"SO-{salesorder_id}", "meta_response": response.json()}
        else:
            print(f"[-] Meta CAPI rejected SO-{salesorder_id}: {response.status_code} - {resp_data}")
            log_conversion(salesorder_id, session_token or "", fbclid, total_amount, "failed_api_error", resp_data)
            return {"status": "failed", "code": response.status_code, "meta_response": resp_data}
    except Exception as e:
        print(f"[-] Network error dispatching Meta CAPI: {e}")
        log_conversion(salesorder_id, session_token or "", fbclid, total_amount, "failed_network_error", str(e))
        return {"status": "network_error", "message": str(e)}


def retry_pending_capi_conversions() -> Dict[str, Any]:
    """
    Automatically retry sending offline Purchase events for conversions that were previously logged
    with status in ('failed_missing_credentials', 'failed_api_error') once META_ACCESS_TOKEN is populated.
    """
    import os
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    if not token and "META_ACCESS_TOKEN" not in os.environ:
        from app.config import BASE_DIR
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("META_ACCESS_TOKEN="):
                            token = line.split("=", 1)[1].strip().strip("'\"")
                            if token:
                                os.environ["META_ACCESS_TOKEN"] = token
                            break
            except Exception:
                pass

    if not token:
        return {"status": "skipped", "reason": "META_ACCESS_TOKEN is not set"}

    from app.database import get_connection, save_customer_identity

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.salesorder_id, a.session_token, a.fbclid, a.total,
                   COALESCE(c.channel, 'WhatsApp') as channel,
                   COALESCE(c.brand, 'Home Cartel') as brand
            FROM conversions_audit a
            LEFT JOIN click_logs c ON a.session_token = c.session_token
            WHERE a.status IN ('failed_missing_credentials', 'failed_api_error')
        """)
        pending = [dict(r) for r in cursor.fetchall()]

    if not pending:
        return {"status": "ok", "retried": 0, "message": "No pending conversions"}

    # Pre-fetch Zoho sales orders map for phone fallback
    zoho_so_map = {}
    try:
        from app.services.zoho_creator_service import fetch_report_records, ZOHO_CREATOR_SALES_ORDERS_REPORT
        records = fetch_report_records(ZOHO_CREATOR_SALES_ORDERS_REPORT, max_records=200)
        for r in records:
            key = r.get("Sales_Order_Number") or r.get("ID")
            if key:
                zoho_so_map[str(key).strip()] = r
    except Exception:
        pass

    retried = 0
    success = 0

    for order in pending:
        so_id = order["salesorder_id"]
        st = order.get("session_token") or ""
        fb = order.get("fbclid") or ""
        amt = float(order.get("total") or 0.0)
        brand = order.get("brand") or "Home Cartel"

        phone = ""
        email = ""
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT identifier FROM customer_identities WHERE session_token = ? LIMIT 1", (st,))
            row = c.fetchone()
            if row:
                phone = row["identifier"]

        if not phone and so_id in zoho_so_map:
            from app.services.zoho_creator_service import normalize_phone
            rec = zoho_so_map[so_id]
            raw_p = rec.get("Billing_Phone") or rec.get("Shipping_Phone") or rec.get("Phone")
            phone = normalize_phone(raw_p)
            email = str(rec.get("Email") or rec.get("Customer_Email") or "").strip()
            if phone and len(phone) == 10 and phone.startswith("9"):
                save_customer_identity("phone", phone, st, brand)

        res = send_purchase_event(
            salesorder_id=so_id,
            total_amount=amt,
            email=email,
            phone=phone,
            fbclid=fb,
            brand=brand,
            access_token=token,
            session_token=st,
            force_retry=True,
        )
        retried += 1
        if res.get("status") == "success":
            success += 1
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE click_logs SET capi_status = 'sent' WHERE session_token = ?", (st,))
                c.execute("UPDATE conversions_audit SET status = 'sent' WHERE salesorder_id = ?", (so_id,))
                conn.commit()

    return {"status": "ok", "retried": retried, "success": success}

