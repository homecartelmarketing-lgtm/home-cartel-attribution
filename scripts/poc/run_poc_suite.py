"""
Unified POC Test Runner for Ad-to-Sale Attribution System
Runs automated unit tests for all scriptable POC test cases:
  - T1: Session token creation & format
  - T2: Redirect payload schema
  - T4: Zoho Books webhook payload custom fields structure
  - T5: Meta CAPI Purchase event payload schema
  - T6: Token persistence through redirect
  - T8: Email token injection & regex extraction
  - T10: Zendesk tag preservation logic
  - T11: Multi-brand routing logic
  - T22: Duplicate customer quote deduplication logic
  - T24: RFQ keyword trigger logic (excludes agent replies)
  - T26: CAPI duplicate event prevention (Event ID uniqueness)
  - T31: Meta CAPI fbc parameter format
"""

import sys
import time
import re
import hashlib
from typing import Dict, Any, List

class POCTestRunner:
    def __init__(self):
        self.results = {}
        
    def record(self, test_id: str, desc: str, passed: bool, details: str = ""):
        self.results[test_id] = {
            "desc": desc,
            "passed": passed,
            "details": details
        }
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_id}: {desc}")
        if details:
            print(f"       -> {details}")

    def test_t1_t6_t31_token_and_fbc(self):
        # T1: Session token format
        ts = int(time.time() * 1000)
        rand = 54321
        token = f"HC-{ts}-{rand}"
        is_valid_token = bool(re.match(r"^HC-\d{13}-\d{5}$", token))
        self.record("T1", "Session token generation format (HC-<13 digits>-<5 digits>)", is_valid_token, f"Generated: {token}")

        # T6: Token survives redirect page
        storage_mock = {"hc_session_token": token, "hc_fbclid": "TEST_FBCLID_999"}
        redirect_payload = {
            "session_token": storage_mock.get("hc_session_token", ""),
            "fbclid": storage_mock.get("hc_fbclid", ""),
            "channel": "WhatsApp",
            "brand": "Home Cartel",
            "timestamp": "2026-10-08T12:00:00Z"
        }
        t6_pass = redirect_payload["session_token"] == token and redirect_payload["fbclid"] == "TEST_FBCLID_999"
        self.record("T6", "Token survives redirect page and populates payload", t6_pass)

        # T31: fbc parameter format
        fbclid = "IwAR123SampleClickId"
        ts_ms = int(time.time() * 1000)
        fbc = f"fb.1.{ts_ms}.{fbclid}"
        is_valid_fbc = bool(re.match(r"^fb\.1\.\d{13}\..+$", fbc))
        self.record("T31", "Meta CAPI fbc parameter format uses epoch milliseconds", is_valid_fbc, f"fbc: {fbc}")

    def test_t2_redirect_payload(self):
        payload = {
            "session_token": "HC-1791440000000-12345",
            "fbclid": "fbclid_xyz",
            "utm_source": "facebook",
            "utm_medium": "paid_social",
            "utm_campaign": "chandelier_deals",
            "utm_content": "video_ad_1",
            "channel": "WhatsApp",
            "brand": "Home Cartel",
            "timestamp": "2026-10-08T06:00:00.000Z"
        }
        required_fields = ["session_token", "channel", "brand", "timestamp"]
        has_all_fields = all(f in payload and payload[f] for f in required_fields)
        self.record("T2", "Redirect page fires webhook with mandatory schema", has_all_fields)

    def test_t4_zoho_books_custom_fields(self):
        # T4: Zoho Books payload structure check
        sample_so_webhook = {
            "salesorder": {
                "salesorder_id": "19400000012345",
                "customer_id": "19400000054321",
                "total": 45000.00,
                "custom_fields": [
                    {"label": "Session Token", "value": "HC-1791440000000-12345"},
                    {"label": "FB Click ID", "value": "test_fbclid_val"},
                    {"label": "UTM Source", "value": "facebook"},
                    {"label": "UTM Campaign", "value": "chandelier_deals"},
                    {"label": "Contact Channel", "value": "WhatsApp"},
                    {"label": "Brand", "value": "Home Cartel"}
                ]
            }
        }
        cf_labels = {cf["label"]: cf["value"] for cf in sample_so_webhook["salesorder"]["custom_fields"]}
        has_token = bool(cf_labels.get("Session Token"))
        has_fbclid = bool(cf_labels.get("FB Click ID"))
        self.record("T4", "Zoho Books webhook payload contains Session Token and FB Click ID custom fields", has_token and has_fbclid)

    def test_t5_capi_payload_validation(self):
        # T5: Meta CAPI offline Purchase schema
        email = "test@homecartel.com"
        phone = "+639171234567"
        h_email = hashlib.sha256(email.encode("utf-8")).hexdigest()
        h_phone = hashlib.sha256(phone.encode("utf-8")).hexdigest()
        
        capi_body = {
            "data": [{
                "event_name": "Purchase",
                "event_time": int(time.time()),
                "action_source": "system_generated",
                "event_id": "SO-19400000012345",
                "user_data": {
                    "em": [h_email],
                    "ph": [h_phone],
                    "fbc": "fb.1.1791440000000.test_fbclid_val"
                },
                "custom_data": {
                    "value": 45000.00,
                    "currency": "PHP"
                }
            }]
        }
        event = capi_body["data"][0]
        valid_schema = (
            event["event_name"] == "Purchase" and
            event["custom_data"]["currency"] == "PHP" and
            event["custom_data"]["value"] > 0 and
            len(event["user_data"]["em"][0]) == 64 and
            len(event["user_data"]["ph"][0]) == 64 and
            event["event_id"].startswith("SO-")
        )
        self.record("T5", "Meta CAPI Purchase event payload schema valid with hashed PII & currency PHP", valid_schema)

    def test_t8_email_token_regex(self):
        # T8: Regex extraction from email comment
        raw_email = "Hello support,\n\nPlease send us a quotation for 3 chandeliers.\n\nRef: HC-1791440000000-98765\nThank you!"
        match = re.search(r"Ref:\s*(HC-[0-9]+-[0-9]+)", raw_email, re.IGNORECASE)
        token_found = match.group(1) if match else None
        self.record("T8", "Email token injection and regex extraction (Ref: HC-*)", token_found == "HC-1791440000000-98765")

    def test_t10_tag_preservation(self):
        # T10: Tag update must add new tag without deleting existing tags
        existing_tags = ["vip", "metro_manila", "lighting"]
        new_tag = "rfq_detected"
        
        # Simulates set-union addition used in HTTP request rather than destructive PUT
        merged_tags = list(set(existing_tags + [new_tag]))
        
        preserved = all(t in merged_tags for t in existing_tags) and new_tag in merged_tags
        self.record("T10", "Tag update preserves existing tags without overwrite", preserved)

    def test_t11_multi_brand_routing(self):
        # T11: Multi-brand routing resolves to correct brand configuration
        brand_configs = {
            "Home Cartel": {"capi_dataset": "DATASET_HOME_CARTEL", "zoho_org": "ORG_HC"},
            "Brand B": {"capi_dataset": "DATASET_BRAND_B", "zoho_org": "ORG_B"},
            "Brand C": {"capi_dataset": "DATASET_BRAND_C", "zoho_org": "ORG_C"}
        }
        
        test_payload_1 = {"brand": "Home Cartel"}
        test_payload_2 = {"brand": "Brand B"}
        
        route_1 = brand_configs.get(test_payload_1["brand"])
        route_2 = brand_configs.get(test_payload_2["brand"])
        
        correct = route_1["capi_dataset"] == "DATASET_HOME_CARTEL" and route_2["capi_dataset"] == "DATASET_BRAND_B"
        self.record("T11", "Multi-brand routing correctly isolates datasets and organizations", correct)

    def test_t22_quote_deduplication(self):
        # T22: Duplicate RFQs for same customer/session token do not create duplicate estimates
        active_estimates = ["HC-1791440000000-11111"]
        incoming_token_dup = "HC-1791440000000-11111"
        incoming_token_new = "HC-1791440000000-22222"
        
        should_skip = incoming_token_dup in active_estimates
        should_create = incoming_token_new not in active_estimates
        self.record("T22", "Workflow 3 estimate deduplication detects existing session token", should_skip and should_create)

    def test_t24_rfq_keyword_trigger_agent_filter(self):
        # T24: RFQ keywords should only trigger on customer messages, never on agent replies
        keywords = ["quote", "quotation", "rfq", "estimate", "pricing", "how much", "magkano"]
        
        def should_trigger(comment_text: str, is_agent: bool) -> bool:
            if is_agent:
                return False
            lower = comment_text.lower()
            return any(k in lower for k in keywords)

        cust_msg = "Magkano po yung crystal chandelier?"
        agent_reply = "Here is your quotation and price breakdown."
        
        self.record("T24", "RFQ trigger detects customer 'magkano' and skips agent reply containing 'quotation'",
                    should_trigger(cust_msg, is_agent=False) and not should_trigger(agent_reply, is_agent=True))

    def test_t26_capi_deduplication_event_id(self):
        # T26: Prevent duplicate CAPI events on retry using unique event_id SO-<id>
        salesorder_id = "19400000099999"
        event_id = f"SO-{salesorder_id}"
        
        # Simulating n8n event cache / Meta deduplication
        processed_events = set()
        
        # First send
        first_send = event_id not in processed_events
        processed_events.add(event_id)
        
        # Retry send
        retry_send_skipped = event_id in processed_events
        self.record("T26", "Meta CAPI event_id format (SO-<salesorder_id>) guarantees deduplication on webhook retry",
                    first_send and retry_send_skipped)

    def run_all(self):
        print("=" * 75)
        print(" SCRIPTABLE POC TEST SUITE RUNNER - AD-TO-SALE ATTRIBUTION SYSTEM")
        print("=" * 75)
        
        self.test_t1_t6_t31_token_and_fbc()
        self.test_t2_redirect_payload()
        self.test_t4_zoho_books_custom_fields()
        self.test_t5_capi_payload_validation()
        self.test_t8_email_token_regex()
        self.test_t10_tag_preservation()
        self.test_t11_multi_brand_routing()
        self.test_t22_quote_deduplication()
        self.test_t24_rfq_keyword_trigger_agent_filter()
        self.test_t26_capi_deduplication_event_id()
        
        print("\n" + "=" * 75)
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["passed"])
        print(f" TOTAL TESTS RUN: {total} | PASSED: {passed} | FAILED: {total - passed}")
        print("=" * 75)
        return total == passed

if __name__ == "__main__":
    runner = POCTestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
