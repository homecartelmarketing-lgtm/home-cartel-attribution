"""
Zendesk Integration Service
Ad-to-Sale Attribution System
Handles ticket querying, custom field enrichment, non-destructive tagging, and email parsing.
"""

import requests
import re
from typing import Dict, Any, List, Optional
from app.config import ZD_SUBDOMAIN, ZD_EMAIL, ZD_TOKEN

def get_base_url() -> str:
    return f"https://{ZD_SUBDOMAIN}.zendesk.com/api/v2"

def get_auth():
    if not ZD_EMAIL or not ZD_TOKEN:
        return None
    return (f"{ZD_EMAIL}/token", ZD_TOKEN)

def search_recent_tickets(query: str = "type:ticket status:open", limit: int = 25) -> List[Dict[str, Any]]:
    auth = get_auth()
    if not auth:
        return []
    url = f"{get_base_url()}/search.json"
    params = {"query": query, "sort_by": "created_at", "sort_order": "desc"}
    try:
        r = requests.get(url, auth=auth, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("results", [])[:limit]
    except Exception as e:
        print(f"[-] Zendesk API search error: {e}")
        return []

def get_user_details(user_id: int) -> Dict[str, Any]:
    auth = get_auth()
    if not auth or not user_id:
        return {}
    try:
        r = requests.get(f"{get_base_url()}/users/{user_id}.json", auth=auth, timeout=10)
        return r.json().get("user", {}) if r.status_code == 200 else {}
    except Exception:
        return {}

def enrich_ticket_tracking(ticket_id: int, fields: Dict[str, Any]) -> bool:
    """
    Update Zendesk ticket custom fields with attribution tracking values.
    Uses custom fields dictionary.
    """
    auth = get_auth()
    if not auth:
        print("[-] Zendesk credentials not configured. Skipping ticket update.")
        return False
        
    custom_field_payload = []
    for k, v in fields.items():
        if v:
            custom_field_payload.append({"id": k, "value": v})
            
    payload = {
        "ticket": {
            "custom_fields": custom_field_payload
        }
    }
    
    url = f"{get_base_url()}/tickets/{ticket_id}.json"
    try:
        r = requests.put(url, auth=auth, json=payload, timeout=15)
        if r.status_code == 200:
            print(f"[+] Successfully enriched Zendesk Ticket #{ticket_id} with attribution fields.")
            return True
        else:
            print(f"[-] Failed to enrich Zendesk ticket #{ticket_id}: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"[-] Network error updating Zendesk ticket: {e}")
        return False

def add_internal_note(ticket_id: int, note_text: str) -> bool:
    auth = get_auth()
    if not auth: return False
    url = f"{get_base_url()}/tickets/{ticket_id}.json"
    payload = {
        "ticket": {
            "comment": {
                "body": note_text,
                "public": False
            }
        }
    }
    try:
        r = requests.put(url, auth=auth, json=payload, timeout=15)
        return r.status_code == 200
    except Exception:
        return False

def add_ticket_tags(ticket_id: int, new_tags: List[str]) -> bool:
    """
    Safely adds tags to a Zendesk ticket without replacing existing tags (T10).
    Uses the dedicated /tickets/{id}/tags.json POST endpoint.
    """
    auth = get_auth()
    if not auth: return False
    url = f"{get_base_url()}/tickets/{ticket_id}/tags.json"
    try:
        r = requests.post(url, auth=auth, json={"tags": new_tags}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

def get_ticket_comments(ticket_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch a ticket's comment thread.

    Used to extract the session token from inbound email bodies, where the
    token lives in the message text rather than a custom field.
    """
    auth = get_auth()
    if not auth or not ticket_id:
        return []
    try:
        r = requests.get(
            f"{get_base_url()}/tickets/{ticket_id}/comments.json",
            auth=auth,
            params={"sort_order": "asc"},
            timeout=15,
        )
        if r.status_code == 200:
            return (r.json().get("comments") or [])[:limit]
    except Exception as e:
        print(f"[-] Zendesk API comments error: {e}")
    return []


def get_ticket_details(ticket_id: int) -> Dict[str, Any]:
    """Fetch a single ticket with its custom fields."""
    auth = get_auth()
    if not auth or not ticket_id:
        return {}
    try:
        r = requests.get(f"{get_base_url()}/tickets/{ticket_id}.json", auth=auth, timeout=15)
        return r.json().get("ticket", {}) if r.status_code == 200 else {}
    except Exception as e:
        print(f"[-] Zendesk API ticket fetch error: {e}")
        return {}


def get_requester_identities(user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch a user's channel identities (PSID, Viber ID, WhatsApp number).

    Powers repeat-customer matching: an identity maps a person back to the
    session token from their most recent ad click (F10).
    """
    auth = get_auth()
    if not auth or not user_id:
        return []
    try:
        r = requests.get(
            f"{get_base_url()}/users/{user_id}/identities.json", auth=auth, timeout=15
        )
        if r.status_code == 200:
            return r.json().get("identities") or []
    except Exception as e:
        print(f"[-] Zendesk API identities error: {e}")
    return []


def classify_channel_identity(identities: List[Dict[str, Any]]) -> Optional[str]:
    """
    Return the messaging identifier for a Zendesk user, or None.

    Prefers a Messenger PSID (most reliable), then Viber, then falls back to
    None so the caller can use time-window matching.
    """
    for identity in identities or []:
        id_type = str(identity.get("type", "")).lower()
        value = str(identity.get("value", ""))
        if not value:
            continue
        if id_type in ("facebook", "messaging", "messenger"):
            return value
        if "viber" in id_type or "viber" in value.lower():
            return value
    return None


def extract_token_from_email_text(text: str) -> Optional[str]:
    """Extracts Ref: HC-<timestamp>-<rand> from email description or body."""
    if not text:
        return None
    match = re.search(r"Ref:\s*(HC-[0-9]+-[0-9]+)", text, re.IGNORECASE)
    return match.group(1) if match else None
