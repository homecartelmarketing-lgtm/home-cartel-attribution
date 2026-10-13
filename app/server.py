"""
FastAPI Webhook & Attribution Server
Ad-to-Sale Attribution System (Python Native)
Replaces n8n with a high-performance, lightweight, self-hosted Python service.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import hashlib
import hmac
import json
import logging
import os

from app.database import init_db, save_click_log, get_connection, update_click_sale, seed_initial_data
from app.services.meta_capi_service import send_purchase_event
from app.services.scheduler_service import (
    start_poller_daemon,
    run_daily_attribution_audit,
)
from app.services import audit_report_service
from app.services import rfq_service
from app.config import ZOHO_WEBHOOK_SECRET, IS_POSTGRES, DATABASE_PATH
from app.auth import CurrentUser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Replaces the deprecated @app.on_event("startup") hook, which FastAPI 0.141
    no longer supports. Starts the attribution database and the background
    scheduler on startup; nothing needs tearing down on shutdown.
    """
    init_db()
    try:
        seed_initial_data()
    except Exception as e:
        print(f"[!] Seed initial data error: {e}")
    try:
        from import_meta_spend import import_spend
        import_spend()
    except Exception as e:
        print(f"[!] Optional spend import error: {e}")
    start_poller_daemon(interval_seconds=300)
    print("[+] Ad-to-Sale Attribution System initialized.")
    yield


app = FastAPI(
    title="Ad-to-Sale Attribution System",
    description="Python-native conversion attribution middleware connecting Shopify, Zendesk, Zoho Books, and Meta CAPI.",
    version="2.1.0",
    lifespan=lifespan,
)

# CORS locked down (security-and-hardening): explicit origins from env,
# never "*" with credentials. Shopify storefronts only need to POST
# /webhook/click-log without cookies, so credentials stay off.
_CORS_ORIGINS = [
    o.strip() for o in os.environ.get(
        "CORS_ORIGINS",
        "https://home-cartel.myshopify.com,"
        "https://dear-dining.myshopify.com,"
        "https://home22shop.myshopify.com,"
        "https://homecartel.net",
    ).split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Zoho-Webhook-Signature", "X-Zoho-Secret"],
)


@app.middleware("http")
async def _security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; img-src 'self' data:; "
        "frame-ancestors 'none'"
    )
    return resp


def _require_login(user: CurrentUser, request: Request):
    """HTML pages redirect to /login; API calls get 401 JSON."""
    if user:
        return user
    path = request.url.path or ""
    if path.startswith("/api/") or path.startswith("/webhook/"):
        raise HTTPException(status_code=401, detail="Authentication required")
    from fastapi.responses import RedirectResponse
    raise HTTPException(
        status_code=307,
        detail="Login required",
        headers={"Location": "/login"},
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
def root_redirect(request: Request, user: CurrentUser):
    _require_login(user, request)
    return health_check()


@app.get("/health")
def health_check():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM click_logs")
        r_c = cursor.fetchone()
        clicks = (r_c[0] if r_c else 0) or 0
        cursor.execute("SELECT COUNT(*) FROM conversions_audit")
        r_conv = cursor.fetchone()
        conversions = (r_conv[0] if r_conv else 0) or 0
        
    return {
        "status": "online",
        "engine": "Python FastAPI",
        "database": "PostgreSQL (Railway)" if IS_POSTGRES else f"SQLite ({os.path.basename(DATABASE_PATH)})",
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
def get_clicks_api(request: Request, user: CurrentUser):
    """Returns the latest click logs along with full funnel attribution data for the live dashboard."""
    _require_login(user, request)
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
        r = cursor.fetchone()
        total_clicks = (r[0] if r else 0) or 0

        cursor.execute("SELECT COUNT(*) FROM click_logs WHERE zendesk_ticket_id IS NOT NULL")
        r = cursor.fetchone()
        total_inquiries = (r[0] if r else 0) or 0

        cursor.execute("SELECT COUNT(*) FROM click_logs WHERE (rfq_detected = 1 OR (zoho_estimate_num IS NOT NULL AND zoho_estimate_num != ''))")
        r = cursor.fetchone()
        total_quotes = (r[0] if r else 0) or 0

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM conversions_audit WHERE status LIKE 'success%' OR status = 'sent'")
        conv_row = cursor.fetchone()
        attributed_orders = (conv_row[0] if conv_row else 0) or 0
        attributed_revenue = (conv_row[1] if conv_row else 0.0) or 0.0

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM conversions_audit")
        total_row = cursor.fetchone()
        total_orders = (total_row[0] if total_row else 0) or 0
        total_revenue = (total_row[1] if total_row else 0.0) or 0.0

        # Query Meta Ad Spend
        cursor.execute("SELECT COALESCE(SUM(amount_spent), 0), COALESCE(SUM(link_clicks), 0), COALESCE(SUM(impressions), 0) FROM meta_campaign_spend")
        spend_row = cursor.fetchone()
        total_ad_spend = (spend_row[0] if spend_row else 0.0) or 0.0
        total_ad_link_clicks = (spend_row[1] if spend_row else 0) or 0
        total_ad_impressions = (spend_row[2] if spend_row else 0) or 0
        blended_roas = round(total_revenue / total_ad_spend, 2) if total_ad_spend > 0 else 0.0

        cursor.execute("SELECT campaign_name, status, amount_spent, link_clicks, impressions, cpc, ctr, results, cost_per_result FROM meta_campaign_spend ORDER BY amount_spent DESC LIMIT 20")
        campaigns_summary = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT COALESCE(channel, 'Direct / Other') as channel, COUNT(*) as count 
            FROM click_logs 
            GROUP BY channel 
            ORDER BY count DESC
        """)
        channels_summary = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM click_logs 
            WHERE created_at IS NOT NULL
            GROUP BY DATE(created_at) 
            ORDER BY date DESC 
            LIMIT 14
        """)
        daily_trend = [dict(r) for r in cursor.fetchall()]
        daily_trend.reverse()

        cursor.execute("""
            SELECT 
                COALESCE(c.utm_campaign, 'Direct / Organic') as campaign_name,
                COUNT(DISTINCT a.salesorder_id) as orders_count,
                COALESCE(SUM(a.total), 0) as revenue
            FROM conversions_audit a
            LEFT JOIN click_logs c ON (a.session_token = c.session_token OR a.fbclid = c.fbclid)
            GROUP BY campaign_name
            ORDER BY revenue DESC
            LIMIT 10
        """)
        campaign_revenue = [dict(r) for r in cursor.fetchall()]

        from app.services import alert_engine
        alerts_summary = alert_engine.get_ad_evaluations_summary()

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
        "channels_summary": channels_summary,
        "daily_trend": daily_trend,
        "campaign_revenue": campaign_revenue,
        "alerts_summary": alerts_summary,
        "clicks": rows
    }

@app.get("/api/sync-zoho-creator")
@app.post("/api/sync-zoho-creator")
def trigger_zoho_creator_sync():
    """Trigger on-demand sync with Zoho Creator (Estimates + Paid Sales Orders)."""
    from app.services import zoho_creator_service
    return zoho_creator_service.run_full_zoho_creator_sync()

from app.dashboard_template import get_dashboard_html
from app.login_template import get_login_html


@app.get("/login")
def view_login(user: CurrentUser):
    from fastapi.responses import HTMLResponse, RedirectResponse
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse(content=get_login_html())


@app.post("/login")
async def do_login(request: Request):
    from fastapi.responses import HTMLResponse, RedirectResponse
    from app.auth import (
        COOKIE_NAME,
        GENERIC_LOGIN_ERROR,
        AUTH_ENABLED,
        clear_login_attempts,
        cookie_kwargs,
        create_access_token,
        is_rate_limited,
        record_failed_login,
        verify_credentials,
    )
    form = await request.form()
    username = str(form.get("username", "")).strip()[:64]
    password = str(form.get("password", ""))[:256]
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}:{username or 'empty'}"

    if is_rate_limited(key):
        logging.warning("Rate-limited login for %s from %s", username, client_ip)
        return HTMLResponse(
            content=get_login_html("Too many attempts. Try again in 5 minutes."),
            status_code=429,
        )
    if not AUTH_ENABLED or verify_credentials(username, password):
        clear_login_attempts(key)
        logging.info("Login success for user=%r from %s", username, client_ip)
        resp = RedirectResponse(url="/dashboard", status_code=303)
        resp.set_cookie(COOKIE_NAME, create_access_token(username), **cookie_kwargs())
        return resp
    record_failed_login(key)
    return HTMLResponse(content=get_login_html(GENERIC_LOGIN_ERROR), status_code=401)


@app.post("/logout")
def do_logout():
    from fastapi.responses import RedirectResponse
    from app.auth import COOKIE_NAME
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


@app.get("/api/auth-status")
def auth_status(user: CurrentUser):
    return {"authenticated": bool(user), "user": user}


@app.get("/dashboard")
def view_dashboard(request: Request, user: CurrentUser):
    """Visual Live Dashboard for Home Cartel Meta Ad Click Attribution (Executive UI)."""
    _require_login(user, request)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=get_dashboard_html())

@app.get("/audit")
def run_audit(request: Request, user: CurrentUser):
    """Trigger on-demand daily audit report."""
    _require_login(user, request)
    return run_daily_attribution_audit()


@app.post("/audit/email")
def trigger_audit_email(request: Request, user: CurrentUser):
    """Send the daily attribution audit email immediately."""
    _require_login(user, request)
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
def get_alerts(request: Request, user: CurrentUser):
    _require_login(user, request)
    """
    Return evaluated ad-performance alerts based on Section 2.6.4 of the Master Handoff PDF.
    Determines which ads are WATCH, WARNING, CRITICAL, or HEALTHY.
    """
    from app.services import alert_engine

    summary = alert_engine.get_ad_evaluations_summary()
    return {
        "status": "online",
        "counts": summary.get("counts", {}),
        "overall_status": summary.get("overall_status", "HEALTHY"),
        "alerts": summary.get("alerts", []),
        "evaluations": summary.get("evaluations", []),
        "rules_reference": summary.get("rules_reference", []),
        "evaluated_at": summary.get("evaluated_at"),
    }


@app.post("/api/upload-meta-csv")
async def upload_meta_csv(request: Request, user: CurrentUser, file: UploadFile = File(...)):
    _require_login(user, request)
    """
    Accepts CSV / TSV exports directly from Meta Ads Manager.
    Automatically detects format:
      1) Campaign Performance Spend CSV -> Ingests into meta_campaign_spend & evaluates Section 2.6.4 alerts.
      2) Bulk Ads Manager Structure TSV/CSV -> Ingests into meta_campaign_catalog for ad creative attribution.
    Returns immediate processing results and updated alert metrics for instant UI refresh.
    """
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided in upload.")

    raw_bytes = await file.read()
    if not raw_bytes or len(raw_bytes.strip()) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Guard against excessively large uploads (50 MB ceiling)
    if len(raw_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")

    # Multi-encoding decode (Meta exports may be utf-16 with BOM or utf-8)
    text = None
    for enc in ["utf-8-sig", "utf-16", "utf-16-le", "utf-8", "latin-1"]:
        try:
            candidate = raw_bytes.decode(enc)
            cand_lower = candidate.lower()
            if any(k in cand_lower for k in ["campaign", "amount spent", "ad set", "link clicks", "impressions", "reporting"]):
                text = candidate
                break
        except Exception:
            continue

    if text is None:
        try:
            text = raw_bytes.decode("utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode file text: {str(e)}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="File content decoded to empty text.")

    first_few_lines = "\n".join(text.splitlines()[:5]).lower()

    # Precise auto-detection for Meta Ads export types
    is_catalog = (
        ("ad id" in first_few_lines and "campaign id" in first_few_lines)
        or "post click item headline" in first_few_lines
        or ("ad set id" in first_few_lines and "campaign id" in first_few_lines)
    )

    is_spend = not is_catalog and (
        ("amount spent" in first_few_lines)
        or ("reporting starts" in first_few_lines)
        or ("link clicks" in first_few_lines and "impressions" in first_few_lines)
        or ("cpc" in first_few_lines and "impressions" in first_few_lines)
    )

    if is_spend:
        from import_meta_spend import import_spend_content
        res = import_spend_content(text, filename=file.filename)
        if res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res.get("message", "Error parsing spend CSV."))

        # Evaluate alerts dynamically
        from app.services import alert_engine
        alerts_summary = alert_engine.get_ad_evaluations_summary()

        return {
            "status": "success",
            "type": "campaign_spend",
            "type_label": "Meta Campaign Spend & Performance",
            "filename": file.filename,
            "run_id": res.get("run_id"),
            "rows_processed": res.get("rows_processed", 0),
            "rows_failed": res.get("rows_failed", 0),
            "total_spend": res.get("total_spend", 0.0),
            "active_campaigns": res.get("active_campaigns", 0),
            "alerts_summary": alerts_summary.get("counts", {}),
            "overall_status": alerts_summary.get("overall_status", "HEALTHY"),
            "message": f"Successfully imported {res.get('rows_processed', 0)} campaigns (PHP {res.get('total_spend', 0.0):,.2f} total spend). Alerts re-evaluated."
        }

    elif is_catalog:
        from import_campaign_catalog import import_catalog_content
        res = import_catalog_content(text, filename=file.filename)
        if res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res.get("message", "Error parsing catalog file."))

        return {
            "status": "success",
            "type": "campaign_catalog",
            "type_label": "Meta Ads Manager Bulk Catalog",
            "filename": file.filename,
            "run_id": res.get("run_id"),
            "rows_processed": res.get("rows_processed", 0),
            "rows_failed": res.get("rows_failed", 0),
            "message": f"Successfully imported {res.get('rows_processed', 0)} ad creative catalog records."
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="Unrecognized Meta export format. Expected either a Campaign Spend report (with 'Amount spent', 'Link clicks') or an Ads Manager bulk export (with 'Campaign ID', 'Ad ID')."
        )


@app.get("/api/import-history")
def get_import_history_endpoint(request: Request, user: CurrentUser, limit: int = 50):
    _require_login(user, request)
    from app.database import get_import_history
    return {
        "status": "success",
        "history": get_import_history(limit=limit)
    }


@app.get("/api/import-history/{run_id}/errors")
def get_import_errors_endpoint(run_id: str, request: Request, user: CurrentUser):
    _require_login(user, request)
    """
    Retrieve row-by-row error logs for a specific CSV import run.
    Lists line numbers, raw row snippets, and exact error reasons.
    """
    from app.database import get_import_run_errors
    errors = get_import_run_errors(run_id)
    return {
        "status": "success",
        "run_id": run_id,
        "error_count": len(errors),
        "errors": errors
    }




