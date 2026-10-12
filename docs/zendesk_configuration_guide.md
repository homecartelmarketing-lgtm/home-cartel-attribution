# Zendesk Configuration Runbook

This guide details the exact steps for configuring **Zendesk Admin Center** for Home Cartel ([homecartelhelp.zendesk.com](https://homecartelhelp.zendesk.com)).

---

## 1. Create the 10 Tracking Custom Ticket Fields

Navigate to: **Admin Center → Objects and rules → Tickets → Fields → Add field**.

| Field Display Name | Field Type | Field ID (Live) | Field Key / Identifier | Purpose |
|---|---|---|---|---|
| **Session Token** | Text | `17953452223503` | `hc_session_token` | Primary tracking identifier (`HC-<ts>-<rand>`). Never overwrite if populated. |
| **FB Click ID** | Text | `17953492031119` | `hc_fbclid` | Meta click ID captured from URL. |
| **UTM Campaign** | Text | `17953470092687` | `hc_utm_campaign` | Campaign name. |
| **UTM Source - Name of Ads** | Text | `17953470454671` | `hc_utm_source` | Ad source and creative name. |
| **Contact Channel** | Drop-down | `17953481428751` | `hc_contact_channel` | Channel used (`WhatsApp`, `Messenger`, `Viber`, `Email`, `Instagram`). |
| **UTM Medium** | Text | *(Optional)* | `hc_utm_medium` | Medium (e.g. `paid_social`). |
| **UTM Content** | Text | *(Optional)* | `hc_utm_content` | Specific ad creative or format. |
| **Product Name** | Text | *(Optional)* | `hc_product_name` | Product inquirer showed interest in. |
| **Product SKU** | Text | *(Optional)* | `hc_product_sku` | Product SKU code. |
| **Attribution Confidence** | Text | *(Optional)* | `hc_attribution_confidence` | Confidence indicator (`high_channel_match`, `time_window_fallback`). |

> [!NOTE]
> Make these fields viewable by agents on the ticket sidebar for transparency. Agents must NOT edit these fields manually.

---

## 2. Create the Brand Dropdown Field

1. Go to **Admin Center → Objects and rules → Tickets → Fields → Add field**.
2. Select **Dropdown**.
3. Field display name: `Brand`.
4. Values:
   - `Home Cartel` (Primary Brand)
   - Add sister brands as needed.
5. Under **Agent permissions**: Check **Required to solve ticket**.
6. Click **Save**.

---

## 3. Brand Auto-Tagging Triggers

Create one trigger per brand per incoming channel:

### Primary Brand WhatsApp Trigger
- **Path**: Admin Center → Objects and rules → Triggers → Add Trigger.
- **Trigger Name**: `Auto-tag Brand — Home Cartel — WhatsApp`
- **Conditions (Meet ALL)**:
  - `Ticket > Is > Created`
  - `Ticket > Channel > Is > WhatsApp`
- **Actions**:
  - `Ticket > Brand > Home Cartel`
  - `Ticket > Add tags > brand_home_cartel`

### Primary Brand Facebook Messenger Trigger
- **Trigger Name**: `Auto-tag Brand — Home Cartel — Messenger`
- **Conditions (Meet ALL)**:
  - `Ticket > Is > Created`
  - `Ticket > Channel > Is > Facebook Messenger`
- **Actions**:
  - `Ticket > Brand > Home Cartel`
  - `Ticket > Add tags > brand_home_cartel`

---

## 4. RFQ Detection Trigger (Customer Inquiries Only)

This trigger detects purchase intent, tags the ticket with `rfq_detected`, and triggers the n8n Workflow 3 estimate generator.

- **Trigger Name**: `RFQ Detection — Customer Intent`
- **Conditions (Meet ALL)**:
  - `Ticket > Current user > Is not > (Agent)` *(Crucial: Prevents firing on agent replies)*
  - `Ticket > Tags > Does not contain > rfq_detected`
- **Conditions (Meet ANY)**:
  - `Ticket > Comment text > Contains > quote`
  - `Ticket > Comment text > Contains > quotation`
  - `Ticket > Comment text > Contains > rfq`
  - `Ticket > Comment text > Contains > estimate`
  - `Ticket > Comment text > Contains > pricing`
  - `Ticket > Comment text > Contains > how much`
  - `Ticket > Comment text > Contains > magkano`
  - `Ticket > Subject > Contains > quote`
  - `Ticket > Subject > Contains > quotation`
- **Actions**:
  - `Ticket > Add tags > rfq_detected`
  - `Ticket > Status > Open`
  - *(Optional)* Trigger Webhook to: `https://n8n.homecartel.ph/webhook/zendesk-rfq`

---

## 5. Generate Zendesk API Token for Scripting & n8n

1. Go to **Admin Center → Apps and integrations → APIs → Zendesk API**.
2. Enable **Token Access**.
3. Under **Active API Tokens**, click **Add API token**.
4. Description: `Ad-to-Sale Attribution System n8n & CLI`.
5. Copy the generated token immediately.
6. Configure in your environment:
   ```powershell
   $env:ZD_SUBDOMAIN = "homecartelhelp"
   $env:ZD_EMAIL = "admin@homecartel.ph"
   $env:ZD_TOKEN = "<COPIED_TOKEN>"
   ```
