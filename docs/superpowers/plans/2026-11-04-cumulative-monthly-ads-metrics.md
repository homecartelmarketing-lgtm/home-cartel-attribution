# Cumulative Monthly Ads Metrics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cumulative monthly performance record for every ad campaign with all metrics (CPC, CTR, CPM, Clicks, Spend, Impressions, Results, Landing Page Views, Frequency), expose via REST API and dashboard UI, and document in Obsidian and Graphify.

**Architecture:** Extend `meta_campaign_daily` schema, parse all columns in `import_meta_spend.py`, create a dual-engine SQL aggregation engine in `app/database.py`, add `/api/campaigns/monthly` endpoint in `app/server.py`, render a Month Selector & Cumulative KPI Table in `app/dashboard_template.py`, and link Obsidian notes & Graphify.

**Tech Stack:** Python 3.12, FastAPI, SQLite / PostgreSQL, Vanilla JS / Chart.js, Obsidian, Graphify.

**Spec:** `docs/superpowers/specs/2026-11-04-cumulative-monthly-ads-metrics-design.md`

## Global Constraints
- Mathematically accurate cumulative rates (sum of spend / sum of clicks, never average of daily rates).
- Zero division safety across all computed metrics.
- Dual-engine SQLite & PostgreSQL compatibility.
- Idempotent migration and CSV imports.

## Review Focus
- Division by zero on campaigns with 0 clicks or 0 impressions.
- Proper month bucketing across multi-month CSV date ranges.
- Graceful handling of missing optional columns in daily exports.
- Fast UI updates on month dropdown switch without page reload.
- Dual-brand isolation intact.

---

### Task 1: Schema Migration and Database Aggregation Function
**Files:**
- Modify: `app/database.py`
- Test: `tests/test_monthly_metrics.py`

- [ ] **Step 1: Write unit tests for schema expansion and monthly aggregation**
- [ ] **Step 2: Add migration columns to `meta_campaign_daily` in `init_db()`**
- [ ] **Step 3: Implement `get_cumulative_monthly_campaign_metrics(month=None)` in `app/database.py`**
- [ ] **Step 4: Verify tests pass**

### Task 2: CSV Importer Updates for All Metrics
**Files:**
- Modify: `import_meta_spend.py`
- Test: `tests/test_daily_trends.py` & `tests/test_monthly_metrics.py`

- [ ] **Step 1: Write test verifying all daily breakdown columns are parsed and stored**
- [ ] **Step 2: Update `import_daily_content()` to parse `clicks_all`, `landing_page_views`, `results`, `cost_per_result`, `cpm`, `frequency`**
- [ ] **Step 3: Update `INSERT ... ON CONFLICT DO UPDATE` query**
- [ ] **Step 4: Re-run baseline ingestion of `dailybreakdown.csv` to populate new fields**
- [ ] **Step 5: Verify tests pass**

### Task 3: REST API Endpoint
**Files:**
- Modify: `app/server.py`
- Test: `tests/test_monthly_metrics.py`

- [ ] **Step 1: Write test for `GET /api/campaigns/monthly`**
- [ ] **Step 2: Implement endpoint in `app/server.py` with authentication check and month parameter**
- [ ] **Step 3: Integrate monthly metrics summary into `/api/clicks` response for instant UI rendering**
- [ ] **Step 4: Verify tests pass**

### Task 4: Interactive Dashboard UI (Month Selector & Cumulative Table)
**Files:**
- Modify: `app/dashboard_template.py`

- [ ] **Step 1: Add "Monthly Cumulative Ads Performance" HTML structure with Month Dropdown and KPI summary cards**
- [ ] **Step 2: Add responsive table rendering all cumulative metrics (Spend, Link CPC, Link CTR, CPM, Clicks, Results, Frequency)**
- [ ] **Step 3: Add client-side JavaScript for instant month filtering, search filtering, and CSV export**
- [ ] **Step 4: Manually verify layout and responsiveness in browser**

### Task 5: Obsidian Knowledge Base, Graphify & Architecture Changelog
**Files:**
- Create: `docs/obsidian/Cumulative Ads Metrics per Month.md`
- Create: `docs/obsidian/Architecture Decision - Monthly Cumulative Aggregation.md`
- Create: `docs/obsidian/Meta Ads Performance Metrics Reference.md`
- Modify: `system_architecture_and_changelog.md`

- [ ] **Step 1: Create Obsidian notes with YAML frontmatter, tags, formulas, and `[[wikilinks]]`**
- [ ] **Step 2: Update `system_architecture_and_changelog.md` Changelog section**
- [ ] **Step 3: Re-index/update Graphify with new markdown notes and architecture documentation**
