"""
Zendesk T3 Channel Inspector
Automates POC Test T3 against Zendesk API (e.g., homecartelhelp.zendesk.com).
Inspects the last 20-50 tickets across WhatsApp, Viber, Messenger, and Email
to verify requester identities, phone formatting (+63), email capture, and custom fields.
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, List

def parse_args():
    parser = argparse.ArgumentParser(description="Zendesk T3 Channel Inspector")
    parser.add_argument("--subdomain", default=os.environ.get("ZD_SUBDOMAIN", "homecartelhelp"),
                        help="Zendesk subdomain (default: homecartelhelp or env ZD_SUBDOMAIN)")
    parser.add_argument("--email", default=os.environ.get("ZD_EMAIL"),
                        help="Zendesk admin/agent email (or env ZD_EMAIL)")
    parser.add_argument("--token", default=os.environ.get("ZD_TOKEN"),
                        help="Zendesk API token (or env ZD_TOKEN)")
    parser.add_argument("--limit", type=int, default=25,
                        help="Number of tickets to inspect (default: 25)")
    return parser.parse_args()

def inspect_channel_ticket(ticket: Dict[str, Any], user: Dict[str, Any], identities: List[Dict[str, Any]]) -> Dict[str, Any]:
    channel = ticket.get("via", {}).get("channel", "unknown")
    phone = user.get("phone") or ""
    email = user.get("email") or ""
    
    identity_summary = [{"type": i.get("type"), "value": i.get("value")} for i in identities]
    has_psid = any(i.get("type") in ["facebook", "messaging"] for i in identities)
    has_viber = any("viber" in str(i.get("type", "")).lower() or "viber" in str(i.get("value", "")).lower() for i in identities)
    
    result = {
        "id": ticket.get("id"),
        "channel": channel,
        "subject": ticket.get("subject"),
        "created_at": ticket.get("created_at"),
        "phone": phone,
        "email": email,
        "identities": identity_summary,
        "tags": ticket.get("tags", []),
        "pass_t3": False,
        "channel_type": "Other",
        "notes": ""
    }
    
    chan_lower = channel.lower()
    if "whatsapp" in chan_lower:
        result["channel_type"] = "WhatsApp"
        # Pass if phone exists and has +63 or valid format
        clean_phone = "".join(filter(str.isdigit, phone))
        if phone.startswith("+63") or (clean_phone.startswith("63") and len(clean_phone) >= 11) or (clean_phone.startswith("09") and len(clean_phone) == 11):
            result["pass_t3"] = True
            result["notes"] = "Valid WhatsApp phone identifier detected."
        else:
            result["notes"] = f"Phone '{phone}' missing or not in standard PH format."
    elif "facebook" in chan_lower or "messenger" in chan_lower:
        result["channel_type"] = "Messenger"
        if has_psid:
            result["pass_t3"] = True
            result["notes"] = "Messenger PSID / messaging identity present."
        else:
            result["notes"] = "Missing messaging identity (PSID)."
    elif "instagram" in chan_lower or "ig" in chan_lower:
        result["channel_type"] = "Instagram"
        has_ig = any("instagram" in str(i.get("type", "")).lower() for i in identities)
        if has_ig or user.get("name"):
            result["pass_t3"] = True
            result["notes"] = "Instagram identity / handle detected."
        else:
            result["notes"] = "No Instagram identity found (requires time-window matching)."
    elif "viber" in chan_lower:
        result["channel_type"] = "Viber"
        if has_viber or phone:
            result["pass_t3"] = True
            result["notes"] = "Viber user identifier or phone present."
        else:
            result["notes"] = "No Viber ID or phone found (requires time-window matching)."
    elif "email" in chan_lower or "mail" in chan_lower or "web" in chan_lower:
        result["channel_type"] = "Email/Web"
        if email and "@" in email:
            result["pass_t3"] = True
            result["notes"] = "Valid email address present."
        else:
            result["notes"] = "Email address missing."
    else:
        result["pass_t3"] = bool(phone or email)
        result["notes"] = f"Unmapped channel '{channel}'."
        
    return result

def main():
    args = parse_args()
    
    print("=" * 70)
    print(" AD-TO-SALE ATTRIBUTION SYSTEM - ZENDESK T3 INSPECTOR")
    print(f" Target Subdomain: https://{args.subdomain}.zendesk.com")
    print("=" * 70)
    
    if not args.email or not args.token:
        print("\n[!] CREDENTIALS MISSING:")
        print("    Zendesk API requires an email and API token.")
        print("    To run this against live Zendesk tickets:")
        print("      Windows (PowerShell):")
        print(f"        $env:ZD_SUBDOMAIN='{args.subdomain}'")
        print("        $env:ZD_EMAIL='admin@yourdomain.com'")
        print("        $env:ZD_TOKEN='your_api_token'")
        print("        python scripts/poc/zendesk_t3_check.py")
        print("\n    To generate a token:")
        print(f"      1. Go to https://{args.subdomain}.zendesk.com/admin/apps-integrations/apis/zendesk-api")
        print("      2. Enable Token Access, click 'Add API token', and copy the generated token.")
        print("=" * 70)
        sys.exit(2)
        
    base_url = f"https://{args.subdomain}.zendesk.com/api/v2"
    auth = (f"{args.email}/token", args.token)
    
    try:
        print(f"\n[+] Connecting to {base_url}...")
        resp = requests.get(f"{base_url}/users/me.json", auth=auth, timeout=15)
        if resp.status_code == 401:
            print("[-] Authentication Failed (HTTP 401). Please verify ZD_EMAIL and ZD_TOKEN.")
            sys.exit(1)
        resp.raise_for_status()
        me = resp.json().get("user", {})
        print(f"[+] Authenticated successfully as: {me.get('name')} <{me.get('email')}> (Role: {me.get('role')})")
        
        # Search recent tickets
        print(f"[+] Fetching last {args.limit} tickets...")
        tickets_resp = requests.get(
            f"{base_url}/search.json",
            auth=auth,
            params={"query": "type:ticket", "sort_by": "created_at", "sort_order": "desc"},
            timeout=30
        )
        tickets_resp.raise_for_status()
        tickets = tickets_resp.json().get("results", [])[:args.limit]
        
        if not tickets:
            print("[-] No tickets found in Zendesk search.")
            return

        print(f"[+] Inspecting {len(tickets)} tickets across communication channels...\n")
        
        channel_counts = {}
        pass_counts = {}
        
        for idx, t in enumerate(tickets, 1):
            uid = t.get("requester_id")
            user = {}
            identities = []
            if uid:
                try:
                    u_resp = requests.get(f"{base_url}/users/{uid}.json", auth=auth, timeout=10)
                    if u_resp.status_code == 200:
                        user = u_resp.json().get("user", {})
                    i_resp = requests.get(f"{base_url}/users/{uid}/identities.json", auth=auth, timeout=10)
                    if i_resp.status_code == 200:
                        identities = i_resp.json().get("identities", [])
                except Exception as e:
                    pass

            analysis = inspect_channel_ticket(t, user, identities)
            ch = analysis["channel_type"]
            channel_counts[ch] = channel_counts.get(ch, 0) + 1
            if analysis["pass_t3"]:
                pass_counts[ch] = pass_counts.get(ch, 0) + 1

            status_icon = "PASS [OK]" if analysis["pass_t3"] else "FAIL [WARN]"
            print(f"[{idx:02d}] Ticket #{analysis['id']} | {analysis['channel_type']} (via={analysis['channel']}) -> {status_icon}")
            print(f"     Subject: {analysis['subject']!r}")
            print(f"     Phone: {analysis['phone'] or '(None)'} | Email: {analysis['email'] or '(None)'}")
            print(f"     Identities: {analysis['identities']}")
            print(f"     Tags: {analysis['tags']}")
            print(f"     Notes: {analysis['notes']}")
            print("-" * 65)

        print("\n" + "=" * 70)
        print(" T3 SUMMARY RESULTS BY CHANNEL")
        print("=" * 70)
        for ch, total in channel_counts.items():
            passed = pass_counts.get(ch, 0)
            pct = (passed / total) * 100 if total > 0 else 0
            print(f"  {ch:<15}: {passed}/{total} Passed ({pct:.1f}%)")
        print("=" * 70)

    except requests.exceptions.RequestException as e:
        print(f"\n[-] Network/API Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
