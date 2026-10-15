# Ads Management System — Architecture, Context & Changelog

> **Note for Developers and AI Coding Agents:**
>
> This document serves as the Single Source of Truth for the system architecture, data flow, and changelog. Before making any code modifications, review the system flow below and update the **Changelog** section after every update.

## 1. End-to-End System Flow (System Architecture)

The **Ads Management System** connects Meta ad clicks to customer inquiries in Zendesk and finalized sales orders in Zoho Creator to measure true Return on Ad Spend (ROAS) and send conversion signals back to the Meta Conversions API (CAPI).

### Step 1: Storefront & Website Traffic Capture

The frontend script captures tracking parameters (`session_token`, `fbclid`, `utm_campaign`, `utm_source`, and `contact_channel`) from the following allowed origins (`CORS_ORIGINS`):

* `https://home-cartel.myshopify.com`
* `https://dear-dining.myshopify.com`
* `https://home22shop.myshopify.com`
* `https://homecartel.net`

### Step 2: Zendesk Lead & Inquiry Ingestion

When a customer submits an inquiry, tracking metadata is stored in Zendesk (`homecartelhelp` subdomain) using specific Custom Ticket Field IDs:

* **Session Token (`ZD_FIELD_SESSION_TOKEN`):** `17953452223503`
* **Facebook Click ID (`ZD_FIELD_FBCLID`):** `17953492031119`
* **UTM Campaign (`ZD_FIELD_UTM_CAMPAIGN`):** `17953470092687`
* **UTM Source (`ZD_FIELD_UTM_SOURCE`):** `17953470454671`
* **Contact Channel (`ZD_FIELD_CONTACT_CHANNEL`):** `17953481428751`

### Step 3: Zoho Creator Sales Order Matching

The system retrieves confirmed sales orders from Zoho Creator using the OAuth 2.0 Refresh Token flow:

* **Account Owner (`ZOHO_ACCOUNT_OWNER`):** `homecartel`
* **App Name (`ZOHO_APP_NAME`):** `cms`
* **Report Name (`ZOHO_REPORT_NAME`):** `Sales_Orders_Report`
* **Endpoints:** `https://accounts.zoho.com` (Accounts) and `https://www.zohoapis.com` (API Base)

### Step 4: Local Database & Ad Spend Reconciliation

Retrieved inquiry, order, and campaign spend data are merged and processed in local storage:

* **SQLite Database (`DB_PATH`):** `attribution.db`
* **Campaign Spend CSV (`SPEND_CSV_PATH`):** `meta_campaign_spend.csv`

### Step 5: Meta Conversions API (CAPI) Feedback Loop

Attributed sales (Purchase events) are sent back to Meta to optimize ad delivery and attribution:

* **Meta Dataset / Pixel ID (`META_DATASET_ID`):** `236624173955711`
* **Graph API Version (`META_API_VERSION`):** `v19.0`

### Step 6: Dashboard & Security (JWT Cookie Auth)

The attribution dashboard is protected using JWT cookie authentication:

* **Auth Toggle:** `AUTH_ENABLED=true`
* **Session Duration:** `TOKEN_EXPIRE_MINUTES=720` (12 hours)
* **Credentials:** Uses `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` (bcrypt), and `AUTH_SECRET_KEY`.

## 2. Environment Variables Reference (`.env` Status)

| Category | Variable Name | Configuration Status | Notes / Value Reference | 
| ----- | ----- | ----- | ----- | 
| **App / Server** | `DB_PATH` | Configured | `attribution.db` | 
| **App / Server** | `SPEND_CSV_PATH` | Configured | `meta_campaign_spend.csv` | 
| **App / Server** | `CORS_ORIGINS` | Configured | 3 Shopify domains + `homecartel.net` | 
| **Zendesk** | `ZD_SUBDOMAIN` | Configured | `homecartelhelp` | 
| **Zendesk** | `ZD_EMAIL` | Configured | `homecartelzendesk@gmail.com` | 
| **Zendesk** | `ZD_TOKEN` | Configured | Stored securely in local `.env` | 
| **Zendesk** | `ZD_FIELD_*` | Configured | 5 Live Custom Ticket Field IDs mapped | 
| **Zoho Creator** | `ZOHO_CLIENT_ID` | Configured | Stored securely in local `.env` | 
| **Zoho Creator** | `ZOHO_CLIENT_SECRET` | Configured | Stored securely in local `.env` | 
| **Zoho Creator** | `ZOHO_REFRESH_TOKEN` | Configured | Stored securely in local `.env` | 
| **Zoho Creator** | `ZOHO_ACCOUNT_OWNER` | Configured | `homecartel` | 
| **Zoho Creator** | `ZOHO_APP_NAME` | Configured | `cms` | 
| **Zoho Creator** | `ZOHO_REPORT_NAME` | Configured | `Sales_Orders_Report` | 
| **Meta CAPI** | `META_DATASET_ID` | Configured | `236624173955711` | 
| **Meta CAPI** | `META_API_VERSION` | Configured | `v19.0` | 
| **Meta CAPI** | `META_ACCESS_TOKEN` | Configured | Stored securely in local `.env` | 
| **Meta CAPI** | `META_TEST_EVENT_CODE` | Optional | Set in `.env` if verifying in Meta Test Events tool | 
| **Dashboard Auth** | `AUTH_ENABLED` | **PENDING IN `.env`** | Present in `.env.example`; needs to be added to live `.env` | 
| **Dashboard Auth** | `ADMIN_USERNAME` | **PENDING IN `.env`** | Default: `admin` | 
| **Dashboard Auth** | `ADMIN_PASSWORD_HASH` | **PENDING IN `.env`** | Generate via `python generate_password.py` | 
| **Dashboard Auth** | `AUTH_SECRET_KEY` | **PENDING IN `.env`** | Generate via `secrets.token_hex(32)` | 

## 3. AI Coding Agent Guidelines (AI Agent Rules)

1. **Never Expose Secrets:** Never hardcode actual API tokens or secrets (`ZD_TOKEN`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`, `META_ACCESS_TOKEN`, `AUTH_SECRET_KEY`) in the source code or in this documentation. Always load them via `os.getenv()`.
2. **Preserve Custom Field Mapping:** The Zendesk custom ticket field IDs are mapped to the live production environment of `homecartelhelp`. Do not modify default IDs without explicit instruction.
3. **Ignore Local Data and PDFs in Docker/Git:** `.gitignore` and `.dockerignore` are configured to exclude `.env`, `*.db`, `meta_campaign_spend.csv`, and `*.pdf`. Keep these exclusions intact.
4. **Log Every Change:** Whenever a feature is added, a bug is fixed, or a script is modified, add a corresponding entry under the **Changelog** section below.

## 4. Changelog

### [Unreleased] - 2026-10-15

#### Added & Configured

* **Dual-Brand Switcher & Room and Style Standby:**
  - Added brand switcher in sidebar, top header, and mobile navigation allowing instant switching between **Home Cartel** and **Room and Style**.
  - Embedded official Room and Style logo (`roomandstyle_logo.jpg` / `room-and-style-logo.webp`) with seamless multi-blend mode.
  - Implemented executive-grade **Standby** dashboard view for Room and Style using the `frontend-design` design system: eliminated generic AI card templates in favor of an architectural 3-step activation pathway (storefront script, Meta spend datasets, Zoho CAPI feedback) and sentence-case typography.
  - Added Room and Style configuration mapping in `app/config.py` with isolated standby routing.
* **Unified CSV Importer (Daily Breakdown & Summary Reports):**
  - Implemented automatic file type detection (`detect_report_kind`) in `import_meta_spend.py` routing either summary spend or daily breakdown through the single "Import new report" button.
  - Created `meta_campaign_daily` SQLite/PostgreSQL table with idempotent upserts (`ON CONFLICT(campaign_name, report_date) DO UPDATE`).
  - Added week-over-week trend monitoring in `app/services/alert_engine.py`:
    - *Creative Fatigue:* CTR drops of 20%, 30%, or 45% trigger Watch, Act soon, and Act now alerts.
    - *Expensive Ads:* CPC up 30% or 50% above ad's 30-day baseline triggers Act soon and Act now alerts.
    - *Delivery Problem:* Impressions drop >= 25% while spend drops < 10% triggers Act now.
  - Integrated trend notes ("Compared with earlier days") into campaign cards, alerts center, and freshness tooltips.
  - Test suite expanded to 85 passing tests including comprehensive daily trend and multi-brand switcher test cases.

### [Unreleased] - 2026-10-14

#### Added & Configured

* Configured `META_ACCESS_TOKEN` in `.env` and executed live Meta CAPI dispatch. Successfully dispatched 24 historical conversions with HTTP 200 response from Meta Graph API (`v19.0`), marking them as `sent` in `click_logs` and `conversions_audit`.
* Implemented automatic CAPI retry queue (`retry_pending_capi_conversions`) with Zoho sales order phone/email fallback in both background poller and sync routines.
* Implemented deep Zendesk ticket backfill and quote ingestion (`QUO-` / `EST-`), expanding `click_logs` to 78 and upgrading 23 historical Zoho orders from `unattributed` to attributed.
* Hardened Philippine phone number normalization across all contact channels in `customer_identities`.
* Configured `CORS_ORIGINS` for `home-cartel.myshopify.com`, `dear-dining.myshopify.com`, `home22shop.myshopify.com`, and `homecartel.net`.
* Set up live Zendesk API connection (`homecartelhelp`) along with 5 custom ticket field IDs for attribution tracking.
* Configured Zoho Creator OAuth2 credentials for `homecartel` / `cms` (`Sales_Orders_Report`).
* Added Meta Dataset ID (`236624173955711`) for Meta Conversions API (`v19.0`).
* Created `CHANGELOG.md` as the central system documentation and reference guide for developers and AI coding agents.

#### Pending / To-Do

* [x] Generate `META_ACCESS_TOKEN` from Meta Events Manager (Dataset ID `236624173955711`) and add it to `.env`.
* [ ] Copy Dashboard Authentication variables (`AUTH_ENABLED`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `AUTH_SECRET_KEY`, `TOKEN_EXPIRE_MINUTES`) from `.env.example` into the live `.env` file and generate a production password hash and secret key.