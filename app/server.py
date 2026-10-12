"""
FastAPI Webhook & Attribution Server
Ad-to-Sale Attribution System (Python Native)
Replaces n8n with a high-performance, lightweight, self-hosted Python service.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import hashlib
import hmac
import json
import logging

from app.database import init_db, save_click_log, get_connection, update_click_sale
from app.services.meta_capi_service import send_purchase_event
from app.services.scheduler_service import (
    start_poller_daemon,
    run_daily_attribution_audit,
)
from app.services import audit_report_service
from app.services import rfq_service
from app.config import ZOHO_WEBHOOK_SECRET


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Replaces the deprecated @app.on_event("startup") hook, which FastAPI 0.141
    no longer supports. Starts the attribution database and the background
    scheduler on startup; nothing needs tearing down on shutdown.
    """
    init_db()
    start_poller_daemon(interval_seconds=300)
    print("[+] Ad-to-Sale Attribution System initialized.")
    yield


app = FastAPI(
    title="Ad-to-Sale Attribution System",
    description="Python-native conversion attribution middleware connecting Shopify, Zendesk, Zoho Books, and Meta CAPI.",
    version="2.1.0",
    lifespan=lifespan,
)

# Enable CORS for Shopify storefronts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _verify_zoho_signature(raw_body: bytes, request: Request) -> bool:
    """
    Validate the Zoho Books webhook signature.

    Zoho sends X-Zoho-Webhook-Signature = HMAC-SHA256(secret, raw_body) as a
    lowercase hex digest. When a secret is configured a missing or malformed
    signature is rejected outright - the previous implementation silently
    accepted unsigned requests.

    Two verification paths are supported:
      * HMAC signature (preferred, per handoff section 3.10.2)
      * a plain shared secret in X-Zoho-Secret, kept for older integrations

    Returns True when verification passes or when no secret is configured at
    all (local development).
    """
    if not ZOHO_WEBHOOK_SECRET:
        return True

    signature = request.headers.get("X-Zoho-Webhook-Signature", "")
    if signature:
        expected = hmac.new(
            ZOHO_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        # Zoho may prefix the digest with the algorithm.
        provided = signature.strip().lower()
        if provided.startswith("sha256="):
            provided = provided[len("sha256="):]
        return hmac.compare_digest(expected, provided)

    # Legacy fallback: plain shared secret header or query parameter.
    legacy = request.headers.get("X-Zoho-Secret") or request.query_params.get("secret") or ""
    if legacy:
        return hmac.compare_digest(ZOHO_WEBHOOK_SECRET, legacy)

    # A secret is configured but nothing verifiable was supplied: reject.
    logging.warning("Zoho webhook rejected: secret configured but no signature provided.")
    return False


class ClickLogPayload(BaseModel):
    session_token: str
    fbclid: Optional[str] = ""
    fbclid_ts: Optional[int] = None
    utm_source: Optional[str] = ""
    utm_medium: Optional[str] = ""
    utm_campaign: Optional[str] = ""
    utm_content: Optional[str] = ""
    channel: str = "WhatsApp"
    brand: str = "Home Cartel"
    landing_page: Optional[str] = ""
    referrer: Optional[str] = ""
    timestamp: Optional[str] = None

@app.get("/")
@app.get("/health")
def health_check():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM click_logs")
        clicks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM conversions_audit")
        conversions = cursor.fetchone()[0]
        
    return {
        "status": "online",
        "engine": "Python FastAPI",
        "database": "SQLite (attribution.db)",
        "total_clicks_recorded": clicks,
        "total_conversions_recorded": conversions
    }

@app.post("/webhook/click-log")
async def handle_click_log(payload: ClickLogPayload):
    """
    Ingests click logs from Shopify redirect pages (/wa-go, /msgr-go, /viber-go).
    Replaces n8n Workflow 1 (F1).
    """
    data = payload.model_dump()
    success = save_click_log(data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to record click log")
        
    return {
        "status": "success",
        "session_token": payload.session_token,
        "channel": payload.channel,
        "brand": payload.brand
    }

@app.post("/webhook/zoho-sales-order")
async def handle_zoho_sales_order(request: Request, background_tasks: BackgroundTasks):
    """
    Receives Sales Order webhook from Zoho Books upon order creation (F6).
    Validates custom tracking fields and triggers Meta CAPI offline Purchase event (F7/F8).
    Replaces n8n Workflow 4.
    """
    body_bytes = await request.body()

    # Verify authenticity before parsing anything (handoff section 3.10.2).
    if not _verify_zoho_signature(body_bytes, request):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        body = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        # Zoho sometimes sends form-url-encoded or raw JSON
        form = await request.form()
        json_data = form.get("JSONString")
        body = json.loads(json_data) if json_data else dict(form)

    so = body.get("salesorder", body)
    salesorder_id = str(so.get("salesorder_id") or so.get("salesorder_number") or "")
    total = float(so.get("total") or 0.0)
    customer_email = so.get("email") or ""
    customer_phone = so.get("phone") or ""

    # Extract custom fields
    custom_fields = so.get("custom_fields", [])
    cf_map = { (cf.get("label") or cf.get("customfield_name")): cf.get("value") for cf in custom_fields }
    
    session_token = cf_map.get("Session Token") or ""
    fbclid = cf_map.get("FB Click ID") or ""
    brand = cf_map.get("Brand") or "Home Cartel"

    if not session_token:
        print(f"[!] Sales Order #{salesorder_id} has no Session Token. Skipping ad attribution.")
        return {"status": "skipped", "reason": "No Session Token"}

    if total <= 0:
        return {"status": "skipped", "reason": "Zero or negative total"}

    print(f"[+] Processing Sales Order #{salesorder_id} (PHP {total:,.2f}) for CAPI attribution...")

    # Run CAPI dispatch asynchronously in background
    background_tasks.add_task(
        send_purchase_event,
        salesorder_id=salesorder_id,
        total_amount=total,
        email=customer_email,
        phone=customer_phone,
        fbclid=fbclid,
        brand=brand,
        session_token=session_token
    )

    # Update click log with conversion details
    update_click_sale(session_token, salesorder_id, total, "sent")

    return {
        "status": "accepted",
        "salesorder_id": salesorder_id,
        "session_token": session_token,
        "amount": total
    }

@app.get("/api/clicks")
def get_clicks_api():
    """Returns the latest click logs along with full funnel attribution data for the live dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()
        # Conversions are aggregated in a subquery so a session token matching
        # several audit rows cannot fan out and duplicate click rows.
        cursor.execute("""
            SELECT
                c.id, c.session_token, c.fbclid, c.utm_source, c.utm_medium,
                c.utm_campaign, c.utm_content, c.channel, c.brand, c.status,
                c.zendesk_ticket_id, c.rfq_detected, c.zoho_estimate_num,
                c.zoho_salesorder_id, c.sales_amount, c.capi_status,
                c.landing_page, c.referrer, c.created_at,
                COALESCE(conv_t.total_agg, conv_f.total_agg)   AS conversion_total,
                COALESCE(conv_t.so_agg, conv_f.so_agg)         AS conversion_so_id,
                COALESCE(conv_t.status_agg, conv_f.status_agg) AS conversion_capi_status
            FROM click_logs c
            -- Two independent single-key joins keep exactly one row per click:
            -- a match-key can fan rows out only when a click joins to many
            -- audit rows, never when audits are pre-aggregated per key.
            LEFT JOIN (
                SELECT session_token AS match_key,
                       MAX(total)         AS total_agg,
                       MAX(salesorder_id) AS so_agg,
                       MAX(status)        AS status_agg
                FROM conversions_audit
                WHERE session_token IS NOT NULL AND session_token != ''
                GROUP BY session_token
            ) conv_t ON conv_t.match_key = c.session_token
            LEFT JOIN (
                SELECT fbclid AS match_key,
                       MAX(total)         AS total_agg,
                       MAX(salesorder_id) AS so_agg,
                       MAX(status)        AS status_agg
                FROM conversions_audit
                WHERE fbclid IS NOT NULL AND fbclid != ''
                GROUP BY fbclid
            ) conv_f ON conv_f.match_key = c.fbclid
            ORDER BY c.id DESC LIMIT 100
        """)
        rows = [dict(r) for r in cursor.fetchall()]

        # Query summary funnel metrics
        cursor.execute("SELECT COUNT(*) FROM click_logs")
        total_clicks = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM click_logs WHERE zendesk_ticket_id IS NOT NULL AND zendesk_ticket_id != ''")
        total_inquiries = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM click_logs WHERE (rfq_detected = 1 OR (zoho_estimate_num IS NOT NULL AND zoho_estimate_num != ''))")
        total_quotes = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM conversions_audit WHERE status LIKE 'success%' OR status = 'sent'")
        conv_row = cursor.fetchone()
        attributed_orders = conv_row[0] or 0
        attributed_revenue = conv_row[1] or 0.0

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM conversions_audit")
        total_row = cursor.fetchone()
        total_orders = total_row[0] or 0
        total_revenue = total_row[1] or 0.0

        # Query Meta Ad Spend
        cursor.execute("SELECT COALESCE(SUM(amount_spent), 0), COALESCE(SUM(link_clicks), 0), COALESCE(SUM(impressions), 0) FROM meta_campaign_spend")
        spend_row = cursor.fetchone()
        total_ad_spend = spend_row[0] or 0.0
        total_ad_link_clicks = spend_row[1] or 0
        total_ad_impressions = spend_row[2] or 0
        blended_roas = round(total_revenue / total_ad_spend, 2) if total_ad_spend > 0 else 0.0

        cursor.execute("SELECT campaign_name, status, amount_spent, link_clicks, impressions, cpc, ctr, results, cost_per_result FROM meta_campaign_spend ORDER BY amount_spent DESC LIMIT 20")
        campaigns_summary = [dict(r) for r in cursor.fetchall()]

    return {
        "total": len(rows),
        "total_clicks": total_clicks,
        "total_inquiries": total_inquiries,
        "total_quotes": total_quotes,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "attributed_orders": attributed_orders,
        "attributed_revenue": attributed_revenue,
        "total_ad_spend": total_ad_spend,
        "total_ad_link_clicks": total_ad_link_clicks,
        "total_ad_impressions": total_ad_impressions,
        "blended_roas": blended_roas,
        "campaigns_summary": campaigns_summary,
        "clicks": rows
    }

@app.get("/api/sync-zoho-creator")
@app.post("/api/sync-zoho-creator")
def trigger_zoho_creator_sync():
    """Trigger on-demand sync with Zoho Creator (Estimates + Paid Sales Orders)."""
    from app.services import zoho_creator_service
    return zoho_creator_service.run_full_zoho_creator_sync()

from app.dashboard_template import get_dashboard_html

@app.get("/dashboard")
def view_dashboard():
    """Visual Live Dashboard for Home Cartel Meta Ad Click Attribution (Executive UI)."""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=get_dashboard_html())

@app.get("/audit")
def run_audit():
    """Trigger on-demand daily audit report."""
    return run_daily_attribution_audit()


@app.post("/audit/email")
def trigger_audit_email():
    """Send the daily attribution audit email immediately."""
    return audit_report_service.send_daily_audit_email()


@app.post("/webhook/zendesk-rfq")
async def handle_zendesk_rfq(request: Request):
    """
    Optional Zendesk trigger target for RFQ detection.

    docs/zendesk_configuration_guide.md section 4 documents an optional webhook
    action on the RFQ trigger. When present, this endpoint runs the estimate
    sweep immediately instead of waiting for the next poller tick.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    ticket = body.get("ticket", body) or {}
    if ticket.get("id"):
        return {"status": "ok", "result": rfq_service.process_rfq_ticket(ticket)}

    # No specific ticket supplied: sweep recent rfq_detected tickets.
    return {"status": "ok", "results": rfq_service.process_rfq_tickets()}


@app.post("/webhook/analytics-sync")
async def handle_analytics_sync(request: Request):
    """
    Accept GA4 / Zoho Analytics session counts for cross-platform alerts.

    Alert #11 (Anomaly Spend with No Leads) needs session and inquiry counts
    from GA4. Rather than requiring a Google service-account key inside this
    service, the analytics side pushes its counts here and the alert engine
    reads them back.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    from app.services import analytics_store

    brand = body.get("brand") or "Home Cartel"
    recorded = analytics_store.record_sessions(
        brand=brand,
        date_str=body.get("date"),
        sessions=int(body.get("sessions") or 0),
        inquiries=int(body.get("inquiries") or 0),
    )
    return {"status": "success", "recorded": recorded}


@app.get("/api/alerts")
def get_alerts():
    """Return the most recently evaluated ad-performance alerts."""
    from app.services import alert_engine

    return {"status": "online", "alerts": alert_engine.get_recent_alerts()}


