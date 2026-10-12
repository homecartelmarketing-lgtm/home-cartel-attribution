"""
Meta Conversions API (CAPI) Offline Conversion Tester
Validates POC Tests:
  - T5: Meta CAPI Purchase event formatting & transmission
  - T31: Correct fbc parameter construction (fb.1.<timestamp_ms>.<fbclid>)
Supports test_event_code to verify events inside Meta Events Manager > Test Events.
"""

import os
import sys
import time
import hashlib
import json
import argparse
import requests

def normalize_email(email: str) -> str:
    """Trim whitespace and convert to lowercase."""
    if not email:
        return ""
    return email.strip().lower()

def normalize_phone(phone: str) -> str:
    """
    Format phone to E.164 standard (+63 for Philippines).
    Accepts formats like: '09171234567', '+63 917 123 4567', '9171234567'.
    Returns '+639XXXXXXXXX' without spaces or dashes.
    """
    if not phone:
        return ""
    digits = "".join(ch for ch in phone if ch.isdigit())
    if digits.startswith("63"):
        clean = "+" + digits
    elif digits.startswith("09"):
        clean = "+63" + digits[1:]
    elif digits.startswith("9") and len(digits) == 10:
        clean = "+63" + digits
    elif digits.startswith("0") and len(digits) > 7:
        clean = "+63" + digits[1:]
    else:
        clean = "+" + digits
    return clean

def hash_sha256(value: str) -> str:
    """Hash string using SHA-256 and return hex string."""
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def build_fbc(fbclid: str, timestamp_ms: int = None) -> str:
    """
    Construct fbc cookie format: fb.1.<creation_time_ms>.<fbclid>
    Per POC Test T31, timestamp must be in milliseconds.
    """
    if not fbclid:
        return ""
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    return f"fb.1.{timestamp_ms}.{fbclid}"

def build_capi_payload(
    dataset_id: str,
    salesorder_id: str,
    total_amount: float,
    email: str,
    phone: str,
    fbclid: str,
    test_event_code: str = None
) -> dict:
    norm_email = normalize_email(email)
    norm_phone = normalize_phone(phone)
    hashed_email = hash_sha256(norm_email)
    hashed_phone = hash_sha256(norm_phone)
    
    event_time = int(time.time())
    fbc = build_fbc(fbclid)
    
    user_data = {}
    if hashed_email:
        user_data["em"] = [hashed_email]
    if hashed_phone:
        user_data["ph"] = [hashed_phone]
    if fbc:
        user_data["fbc"] = fbc
        
    event = {
        "event_name": "Purchase",
        "event_time": event_time,
        "action_source": "system_generated",
        "event_id": f"SO-{salesorder_id}",
        "user_data": user_data,
        "custom_data": {
            "value": total_amount,
            "currency": "PHP"
        }
    }
    
    payload = {
        "data": [event]
    }
    if test_event_code:
        payload["test_event_code"] = test_event_code
        
    return payload

def main():
    parser = argparse.ArgumentParser(description="Meta CAPI Offline Purchase Event Tester (T5, T31)")
    parser.add_argument("--dataset-id", default=os.environ.get("META_DATASET_ID"),
                        help="Meta Dataset ID (or env META_DATASET_ID)")
    parser.add_argument("--access-token", default=os.environ.get("META_ACCESS_TOKEN"),
                        help="Meta CAPI Access Token (or env META_ACCESS_TOKEN)")
    parser.add_argument("--test-code", default=os.environ.get("META_TEST_EVENT_CODE"),
                        help="Meta Test Event Code (from Events Manager > Test Events tab)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print payload and normalization results without sending HTTP request")
    
    args = parser.parse_args()
    
    sample_email = " Juan.DelaCruz@Example.com "
    sample_phone = "0917-888-9999"
    sample_fbclid = "IwAR3xSampleFbclidForPOCAttributionTest"
    sample_so = "TEST-SO-1001"
    sample_val = 18500.00
    
    print("=" * 70)
    print(" META CONVERSIONS API (CAPI) TEST SUITE (T5, T31)")
    print("=" * 70)
    
    # 1. Normalization & Hashing Verification
    norm_em = normalize_email(sample_email)
    norm_ph = normalize_phone(sample_phone)
    hash_em = hash_sha256(norm_em)
    hash_ph = hash_sha256(norm_ph)
    fbc_val = build_fbc(sample_fbclid)
    
    print(f"[*] Input Email: {sample_email!r} -> Normalized: {norm_em!r}")
    print(f"[*] Hashed Email (SHA256): {hash_em}")
    print(f"[*] Input Phone: {sample_phone!r} -> Normalized: {norm_ph!r}")
    print(f"[*] Hashed Phone (SHA256): {hash_ph}")
    print(f"[*] Constructed fbc (T31): {fbc_val}")
    
    assert fbc_val.startswith("fb.1."), "fbc must start with fb.1."
    assert norm_ph.startswith("+639"), "Philippine mobile number must start with +639"
    assert norm_em == "juan.delacruz@example.com", "Email must be lowercased and stripped"
    print("\n[PASS] T31: Phone normalization and fbc format check passed.")
    
    payload = build_capi_payload(
        dataset_id=args.dataset_id or "MOCK_DATASET_ID",
        salesorder_id=sample_so,
        total_amount=sample_val,
        email=sample_email,
        phone=sample_phone,
        fbclid=sample_fbclid,
        test_event_code=args.test_code
    )
    
    print("\n[*] Constructed Meta CAPI Payload:")
    print(json.dumps(payload, indent=2))
    
    if args.dry_run or not args.dataset_id or not args.access_token:
        print("\n" + "=" * 70)
        print(" [!] DRY RUN COMPLETE / CREDENTIALS OMITTED")
        print("     To send a live event to Meta Events Manager:")
        print("       python scripts/poc/test_meta_capi.py \\")
        print("         --dataset-id <YOUR_DATASET_ID> \\")
        print("         --access-token <YOUR_CAPI_TOKEN> \\")
        print("         --test-code <TEST_EVENT_CODE>")
        print("=" * 70)
        return

    endpoint = f"https://graph.facebook.com/v19.0/{args.dataset_id}/events"
    params = {"access_token": args.access_token}
    
    print(f"\n[+] Dispatching Purchase event to Meta Graph API: {endpoint}...")
    try:
        resp = requests.post(endpoint, params=params, json=payload, timeout=20)
        print(f"[*] HTTP Status Code: {resp.status_code}")
        print(f"[*] Response Body: {resp.text}")
        
        if resp.status_code == 200:
            print("\n[PASS] T5: Meta CAPI Purchase event received successfully!")
            print("Check Meta Events Manager > Test Events to confirm EMQ >= 6.0.")
        else:
            print(f"\n[-] Meta API rejected event: {resp.status_code}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"\n[-] Network error sending CAPI request: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
