# Zoho Books: Custom Fields & Webhook Configuration Runbook

> [!CAUTION]
> **Field Label Exact Parity Rule**: Zoho Books custom fields created in Estimates do NOT automatically transfer to Sales Orders unless the field labels **match identically character-for-character** in both modules.

---

## 1. Create Custom Fields in Estimates & Sales Orders

Path: **Settings (gear icon) → Customization → Custom Fields**.

Repeat the creation of the following **8 custom fields** in BOTH the **Estimates** module AND the **Sales Orders** module:

| Field Label (Exact) | Data Type | Character Limit | Description |
|---|---|---|---|
| **Session Token** | Text | 255 | Primary attribution key (`HC-<ts>-<rand>`). |
| **FB Click ID** | Text | 255 | Meta click identifier (`fbclid`). |
| **UTM Source** | Text | 100 | Ad traffic source (`facebook`, `instagram`). |
| **UTM Medium** | Text | 100 | Campaign medium (`paid_social`). |
| **UTM Campaign** | Text | 255 | Specific campaign name. |
| **Contact Channel** | Text | 50 | Inbound channel (`WhatsApp`, `Messenger`, `Viber`, `Email`). |
| **Zendesk Ticket ID** | Text | 50 | Cross-system reference ticket ID. |
| **Brand** | Text | 100 | Brand name (`Home Cartel`). |

---

## 2. Configure Sales Order Webhook Action

Path: **Settings (gear icon) → Automation → Workflow Actions → Webhooks → + New Webhook**.

1. **Name**: `n8n — Sales Order Created`
2. **Module**: `Sales Orders`
3. **URL**: `https://n8n.homecartel.ph/webhook/zoho-sales-order`
4. **Method**: `POST`
5. **Body**: Select **Default Payload** (sends all Sales Order data including custom fields).
6. **Security**: Check **I want to secure this webhook** and enter a secret token (12–50 alphanumeric characters).
7. Save the secret token in your n8n `.env` file as `ZOHO_WEBHOOK_SECRET`.
8. Click **Save**.

---

## 3. Create Workflow Rule to Trigger Webhook

Path: **Settings → Automation → Workflow Rules → + New Workflow Rule**.

1. **Rule Name**: `Trigger CAPI on Sales Order Creation`
2. **Module**: `Sales Orders`
3. **Workflow Type**: `Event Based`
4. **When a Sales Order is**: Select `Created`
5. **Criteria**: Keep blank (trigger on all sales orders).
6. **Immediate Actions**:
   - Click `+ Add Action` → `Type: Webhook`
   - Select the webhook created in Step 2: `n8n — Sales Order Created`
7. Click **Associate → Save**.

---

## 4. Verification Check (T4 & T9)

1. Create a test **Estimate** in Zoho Books with:
   - Session Token: `HC-TEST-99999`
   - FB Click ID: `TEST_FBCLID_VAL`
2. Click **Convert to Sales Order**.
3. Verify that `Session Token` and `FB Click ID` carried over intact on the Sales Order screen (**T9 Pass**).
4. Save the Sales Order.
5. In n8n, check the execution log for `zoho-sales-order` to confirm the webhook fired and received the custom fields (**T4 Pass**).
