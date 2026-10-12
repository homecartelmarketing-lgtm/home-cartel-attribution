"""
Zoho Books Integration Service
Ad-to-Sale Attribution System
Handles contact resolution (F3), draft estimate creation (F4) and quote
deduplication (F5).

All authentication is delegated to zoho_auth_service, which mints and caches
the per-brand OAuth access token.
"""

import requests
from typing import Dict, Any, Optional

from app.config import ZOHO_API_DOMAIN
from app.services.zoho_auth_service import (
    get_auth_headers,
    resolve_org_id,
    is_configured,
    ZohoAuthError,
)

BASE_ZOHO_URL = f"{ZOHO_API_DOMAIN}/books/v3"


def _request(
    method: str,
    path: str,
    brand: str = "Home Cartel",
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Dict[str, Any]] = None,
    timeout: int = 20,
) -> Optional[requests.Response]:
    """
    Issue an authenticated Zoho Books request, retrying once on 401.

    A 401 means the cached token was rejected (clock skew or early revocation),
    so we force a refresh and retry a single time before giving up.
    """
    for attempt in (1, 2):
        try:
            headers = get_auth_headers(brand)
        except ZohoAuthError as e:
            print(f"[-] Zoho Books auth error for brand '{brand}': {e}")
            return None

        try:
            r = requests.request(
                method,
                f"{BASE_ZOHO_URL}{path}",
                headers=headers,
                params=params,
                json=payload,
                timeout=timeout,
            )
        except Exception as e:
            print(f"[-] Network error calling Zoho Books API: {e}")
            return None

        if r.status_code == 401 and attempt == 1:
            print("[!] Zoho access token rejected (401). Forcing refresh and retrying.")
            from app.services.zoho_auth_service import get_access_token
            get_access_token(brand, force_refresh=True)
            continue

        return r

    return None


def check_existing_estimate(session_token: str, brand: str = "Home Cartel") -> bool:
    """
    Checks if an estimate with this session token already exists in Zoho Books.
    Prevents duplicate estimate creation (F5 / T22).
    """
    if not session_token or not is_configured(brand):
        return False

    try:
        org_id = resolve_org_id(brand)
    except ZohoAuthError as e:
        print(f"[-] {e}")
        return False

    params = {"organization_id": org_id, "custom_field_value": session_token}
    r = _request("GET", "/estimates", brand=brand, params=params, timeout=15)
    if r is not None and r.status_code == 200:
        estimates = r.json().get("estimates", [])
        return len(estimates) > 0
    return False


def get_or_create_contact(
    customer_name: str,
    email: str = "",
    phone: str = "",
    brand: str = "Home Cartel",
) -> Optional[str]:
    """
    Find an existing Zoho Books contact by email or phone, or create one.

    Returns the Zoho contact_id, or None if the lookup/creation failed.
    Implements Step 3 of Workflow 3 in the handoff document (section 3.9.3).
    """
    if not is_configured(brand):
        return None

    try:
        org_id = resolve_org_id(brand)
    except ZohoAuthError as e:
        print(f"[-] {e}")
        return None

    # 1. Search for an existing contact by email, falling back to phone.
    search_params: Dict[str, Any] = {"organization_id": org_id}
    if email:
        search_params["email"] = email
    elif phone:
        search_params["phone"] = phone

    if email or phone:
        r = _request("GET", "/contacts", brand=brand, params=search_params, timeout=15)
        if r is not None and r.status_code == 200:
            contacts = r.json().get("contacts", [])
            if contacts:
                contact_id = contacts[0].get("contact_id")
                if contact_id:
                    return str(contact_id)

    # 2. Not found - create a minimal contact shell.
    if not customer_name:
        customer_name = "Valued Customer"

    name_parts = str(customer_name).strip().split(" ", 1)
    contact_payload: Dict[str, Any] = {
        "contact_name": customer_name,
        "first_name": name_parts[0],
        "last_name": name_parts[1] if len(name_parts) > 1 else "",
        "contact_type": "customer",
    }
    if email:
        contact_payload["email"] = email
    if phone:
        contact_payload["phone"] = phone

    r = _request(
        "POST",
        "/contacts",
        brand=brand,
        params={"organization_id": org_id},
        payload=contact_payload,
        timeout=20,
    )
    if r is not None and r.status_code in (200, 201):
        contact = r.json().get("contact", {})
        contact_id = contact.get("contact_id")
        if contact_id:
            print(f"[+] Created Zoho Books contact {contact_id} for '{customer_name}'.")
            return str(contact_id)

    if r is not None:
        print(f"[-] Zoho contact creation failed: {r.status_code} - {r.text[:300]}")
    return None

def create_draft_estimate(
    customer_name: str,
    tracking_fields: Dict[str, Any],
    contact_id: Optional[str] = None,
    brand: str = "Home Cartel",
) -> Dict[str, Any]:
    """
    Creates a pre-populated draft estimate shell in Zoho Books (F4).
    Populates all 8 custom tracking fields.
    """
    if not is_configured(brand):
        return {"status": "error", "message": "Zoho Books not configured for this brand"}

    try:
        org_id = resolve_org_id(brand)
    except ZohoAuthError as e:
        return {"status": "error", "message": str(e)}

    ticket_id = tracking_fields.get("ticket_id")

    # Resolve the customer contact when the caller did not supply one.
    if not contact_id:
        contact_id = get_or_create_contact(
            customer_name=customer_name,
            email=tracking_fields.get("customer_email", ""),
            phone=tracking_fields.get("customer_phone", ""),
            brand=brand,
        )

    if not contact_id:
        return {"status": "error", "message": "Could not resolve Zoho Books contact"}

    # Field labels must match the Zoho Books custom fields character-for-character
    # (see docs/zoho_books_webhook_and_fields.md) so values inherit on conversion.
    custom_fields = [
        {"label": "Session Token", "value": tracking_fields.get("session_token", "")},
        {"label": "FB Click ID", "value": tracking_fields.get("fbclid", "")},
        {"label": "UTM Source", "value": tracking_fields.get("utm_source", "")},
        {"label": "UTM Medium", "value": tracking_fields.get("utm_medium", "")},
        {"label": "UTM Campaign", "value": tracking_fields.get("utm_campaign", "")},
        {"label": "Contact Channel", "value": tracking_fields.get("channel", "WhatsApp")},
        {"label": "Zendesk Ticket ID", "value": str(ticket_id or "")},
        {"label": "Brand", "value": tracking_fields.get("brand", brand)},
    ]

    payload = {
        "customer_id": contact_id,
        "status": "draft",
        "custom_fields": custom_fields,
        "notes": f"Auto-created from Zendesk inquiry #{ticket_id}. Agent: Please add products and send quotation.",
        "line_items": [],
    }

    r = _request(
        "POST",
        "/estimates",
        brand=brand,
        params={"organization_id": org_id},
        payload=payload,
        timeout=20,
    )

    if r is None:
        return {"status": "error", "message": "Zoho Books request failed"}

    if r.status_code in (200, 201):
        est = r.json().get("estimate", {})
        print(
            f"[+] Created Zoho Books Draft Estimate #{est.get('estimate_number')} "
            f"for ticket #{ticket_id}"
        )
        return {"status": "success", "estimate": est}

    print(f"[-] Zoho Books API estimate creation failed: {r.status_code} - {r.text[:300]}")
    return {"status": "failed", "code": r.status_code, "response": r.text}
