"""
Executive Dashboard Template for Home Cartel Ad Attribution
Minimal, authentic engineering UI (Linear / Stripe aesthetic - no AI tropes or emojis)
"""

def get_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Cartel | Ad Attribution</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-base: #090d16;
            --bg-surface: #0f1523;
            --bg-card: #121929;
            --bg-card-hover: #162035;
            --border: #1e293b;
            --border-hover: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-cyan: #38bdf8;
            --accent-blue: #3b82f6;
            --accent-rose: #f43f5e;
            --font-main: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: var(--font-main);
            background-color: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 24px 28px 60px;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            max-width: 1440px;
            margin: 0 auto;
        }

        button:focus-visible, a:focus-visible, input:focus-visible {
            outline: 2px solid var(--accent-blue);
            outline-offset: 2px;
        }

        /* Top Minimal Header */
        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border);
            gap: 16px;
            flex-wrap: wrap;
        }

        .brand-title {
            font-size: 15px;
            font-weight: 600;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: -0.2px;
        }

        .brand-title span.sub {
            color: var(--text-muted);
            font-weight: 400;
        }

        .top-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-action {
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
            font-family: inherit;
            text-decoration: none;
        }

        .btn-action:hover {
            background: #1e293b;
            color: #fff;
            border-color: var(--border-hover);
        }

        .btn-primary {
            background: #1e293b;
            color: #f8fafc;
            border-color: #334155;
        }

        .btn-primary:hover {
            background: #334155;
            color: #fff;
        }

        /* Metric Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 110px;
            transition: border-color 0.15s ease;
        }

        .stat-card:hover {
            border-color: var(--border-hover);
        }

        .stat-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-muted);
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            letter-spacing: -0.5px;
            font-variant-numeric: tabular-nums;
            margin: 6px 0 2px;
        }

        .stat-footer {
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 4px;
        }

        /* Split Bar */
        .split-bar-wrap {
            margin: 8px 0 6px;
        }

        .split-bar {
            height: 6px;
            border-radius: 999px;
            background: #1e293b;
            overflow: hidden;
            display: flex;
        }

        .split-bar-ig {
            background: #f43f5e;
            height: 100%;
            transition: width 0.3s ease;
        }

        .split-bar-fb {
            background: #3b82f6;
            height: 100%;
            transition: width 0.3s ease;
        }

        .split-labels {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            font-weight: 500;
            margin-top: 4px;
        }

        .split-ig-text { color: #f43f5e; }
        .split-fb-text { color: #60a5fa; }

        /* Toolbar */
        .toolbar {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px 10px 0 0;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .search-wrap {
            position: relative;
            flex: 1;
            max-width: 380px;
            min-width: 240px;
        }

        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            border: 0;
        }

        .search-box {
            position: relative;
            width: 100%;
        }

        .search-box input {
            width: 100%;
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 7px 32px 7px 12px;
            color: #fff;
            font-size: 12px;
            font-family: inherit;
            transition: border-color 0.15s ease;
        }

        .search-box input:focus {
            border-color: var(--accent-blue);
            outline: none;
        }

        .search-shortcut {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 11px;
            font-family: var(--font-mono);
            pointer-events: none;
        }

        .filter-tabs {
            display: flex;
            gap: 4px;
            background: #090d16;
            padding: 3px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }

        .filter-tab {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 5px 11px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease;
            font-family: inherit;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .filter-tab:hover {
            color: #fff;
        }

        .filter-tab.active {
            background: #1e293b;
            color: #fff;
        }

        .tab-count {
            color: var(--text-muted);
            font-size: 11px;
            font-variant-numeric: tabular-nums;
        }

        .filter-tab.active .tab-count {
            color: var(--text-secondary);
        }

        /* Table Container */
        .table-wrap {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-top: none;
            border-radius: 0 0 10px 10px;
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 12px;
        }

        th {
            background: #0c121e;
            padding: 11px 16px;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(30, 41, 59, 0.6);
            vertical-align: middle;
            color: #cbd5e1;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.02);
        }

        .time-cell {
            color: var(--text-muted);
            font-family: var(--font-mono);
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
        }

        .time-relative {
            color: var(--text-secondary);
            font-weight: 500;
            display: block;
        }

        .time-exact {
            font-size: 10px;
            color: var(--text-muted);
        }

        .pill-instagram {
            background: rgba(244, 63, 94, 0.12);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.25);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .pill-facebook {
            background: rgba(59, 130, 246, 0.12);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.25);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .pill-meta {
            background: rgba(148, 163, 184, 0.1);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .product-cell {
            display: flex;
            flex-direction: column;
            gap: 3px;
            max-width: 300px;
        }

        .product-link {
            color: #f1f5f9;
            text-decoration: none;
            font-weight: 500;
            font-size: 12px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .product-link:hover {
            color: var(--accent-cyan);
            text-decoration: underline;
        }

        .ad-id-badge {
            font-family: var(--font-mono);
            font-size: 10px;
            color: #94a3b8;
            background: #090d16;
            border: 1px solid var(--border);
            padding: 1px 6px;
            border-radius: 4px;
            width: fit-content;
        }

        .copy-pill {
            font-family: var(--font-mono);
            font-size: 11px;
            background: #090d16;
            border: 1px solid var(--border);
            padding: 3px 7px;
            border-radius: 4px;
            cursor: pointer;
            transition: border-color 0.15s ease, color 0.15s ease;
            max-width: 170px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: inline-block;
            vertical-align: middle;
            color: #94a3b8;
        }

        .copy-pill:hover {
            border-color: var(--accent-cyan);
            color: #fff;
        }

        .pill-campaign {
            background: rgba(168, 85, 247, 0.1);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.2);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            max-width: 220px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: inline-block;
            vertical-align: middle;
        }

        .btn-inspect {
            background: #0f172a;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
            font-family: inherit;
        }

        .btn-inspect:hover {
            background: #1e293b;
            color: #fff;
            border-color: var(--border-hover);
        }

        .pill-ticket {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            font-family: var(--font-mono);
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .pill-estimate {
            background: rgba(168, 85, 247, 0.12);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.25);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            font-family: var(--font-mono);
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .rev-cell {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .rev-amount {
            font-weight: 700;
            color: #10b981;
            font-size: 12px;
            font-family: var(--font-mono);
        }

        .so-id {
            font-size: 10px;
            color: #94a3b8;
            font-family: var(--font-mono);
        }

        .pill-stage {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            white-space: nowrap;
        }

        .pill-stage.pill-click {
            background: rgba(100, 116, 139, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(100, 116, 139, 0.25);
        }

        .pill-stage.pill-inquiry {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .pill-stage.pill-quote {
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        .pill-stage.pill-sale {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .pill-stage.pill-success {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            border: 1px solid #10b981;
        }

        .badge-faded {
            color: #475569;
            font-size: 11px;
        }

        /* Stepper Tracker for Drawer */
        .funnel-stepper {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: 12px 0;
        }

        .stepper-step {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            position: relative;
        }

        .stepper-step:not(:last-child)::after {
            content: '';
            position: absolute;
            left: 13px;
            top: 26px;
            bottom: -8px;
            width: 2px;
            background: #1e293b;
        }

        .stepper-step.completed:not(:last-child)::after {
            background: #10b981;
        }

        .step-indicator {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #1e293b;
            border: 2px solid #334155;
            color: #94a3b8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 700;
            flex-shrink: 0;
            z-index: 1;
        }

        .stepper-step.completed .step-indicator {
            background: #064e3b;
            border-color: #10b981;
            color: #34d399;
        }

        .stepper-step.active .step-indicator {
            background: #0c4a6e;
            border-color: #38bdf8;
            color: #38bdf8;
        }

        .step-content {
            flex: 1;
        }

        .step-title {
            font-size: 12px;
            font-weight: 600;
            color: #f1f5f9;
        }

        .step-sub {
            font-size: 11px;
            color: #94a3b8;
            margin-top: 2px;
        }

        /* Slide-over Drawer */
        .drawer-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(2px);
            z-index: 900;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
        }

        .drawer-backdrop.open {
            opacity: 1;
            pointer-events: auto;
        }

        .drawer {
            position: fixed;
            top: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            max-width: 540px;
            background: #0d121f;
            border-left: 1px solid var(--border);
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .drawer.open {
            transform: translateX(0);
        }

        .drawer-header {
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #090d16;
        }

        .drawer-header h2 {
            font-size: 14px;
            font-weight: 600;
            color: #fff;
        }

        .btn-close {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.15s ease, color 0.15s ease;
        }

        .btn-close:hover {
            background: #1e293b;
            color: #fff;
        }

        .drawer-body {
            padding: 20px;
            overflow-y: auto;
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        .drawer-section {
            background: #121929;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
        }

        .drawer-section-title {
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-muted);
            margin-bottom: 10px;
        }

        .meta-kv {
            display: grid;
            grid-template-columns: 130px 1fr;
            gap: 8px;
            font-size: 12px;
            margin-bottom: 6px;
            align-items: baseline;
        }

        .meta-key {
            color: var(--text-secondary);
            font-weight: 500;
        }

        .meta-val {
            color: #f1f5f9;
            font-family: var(--font-mono);
            font-size: 11px;
            word-break: break-all;
        }

        .raw-json-box {
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 10px;
            font-family: var(--font-mono);
            font-size: 11px;
            color: #94a3b8;
            max-height: 180px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #1e293b;
            color: #fff;
            padding: 9px 14px;
            border-radius: 6px;
            border: 1px solid var(--border-hover);
            font-size: 12px;
            font-weight: 500;
            display: none;
            box-shadow: 0 8px 20px rgba(0,0,0,0.5);
            z-index: 2000;
        }

        .toast.show {
            display: block;
        }

        .empty-state {
            text-align: center;
            padding: 48px 20px;
            color: var(--text-muted);
            font-size: 13px;
        }

        @media (max-width: 768px) {
            body { padding: 16px 14px 40px; }
            .top-bar { flex-direction: column; align-items: flex-start; }
            .toolbar { flex-direction: column; align-items: stretch; }
        /* Analytics Hub & Chart Views (PDF Sec 2.5) */
        .analytics-hub {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px 22px;
            margin-bottom: 22px;
        }

        .analytics-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
            margin-bottom: 18px;
            flex-wrap: wrap;
            gap: 12px;
        }

        .analytics-title-wrap {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .analytics-title {
            font-size: 13px;
            font-weight: 700;
            color: #fff;
            letter-spacing: -0.2px;
        }

        .analytics-badge {
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.25);
            font-family: var(--font-mono);
        }

        .analytics-tabs {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .view-btn {
            background: #090d16;
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s ease;
            font-family: inherit;
        }

        .view-btn:hover {
            color: #fff;
            border-color: var(--border-hover);
        }

        .view-btn.active {
            background: #1e293b;
            color: #38bdf8;
            border-color: #0284c7;
        }

        .view-panel {
            display: none;
        }

        .view-panel.active {
            display: block;
        }

        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(440px, 1fr));
            gap: 16px;
        }

        .chart-box {
            background: #090d16;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 18px;
            display: flex;
            flex-direction: column;
        }

        .chart-box-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 14px;
        }

        .chart-box-title {
            font-size: 12px;
            font-weight: 600;
            color: #f8fafc;
        }

        .chart-box-sub {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 2px;
        }

        .chart-canvas-wrap {
            position: relative;
            height: 260px;
            width: 100%;
        }

        .metric-mini-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-top: 14px;
        }

        .metric-mini-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #0f1523;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 11px;
        }

        .metric-mini-val {
            font-weight: 700;
            font-family: var(--font-mono);
            color: #fff;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Minimal Top Bar -->
        <header class="top-bar">
            <div class="brand-title">
                Home Cartel <span class="sub">/ Ad Attribution</span>
            </div>
            <div class="top-actions">
                <button class="btn-action" onclick="fetchClicks(true)" aria-label="Refresh attribution records">
                    Refresh
                </button>
                <button class="btn-action btn-primary" onclick="exportCSV()" aria-label="Export all records as CSV">
                    Export CSV
                </button>
                <a href="https://homecartel.net" target="_blank" rel="noopener noreferrer" class="btn-action" aria-label="Open Home Cartel store">
                    Store &nearr;
                </a>
            </div>
        </header>

        <!-- Funnel Metric Cards (Complete Closed-Loop Pipeline) -->
        <section class="stats-grid" aria-label="Attribution Funnel Summary">
            <div class="stat-card">
                <div class="stat-label">Total ad clicks</div>
                <div class="stat-value" id="stat-total">0</div>
                <div class="stat-footer">Direct Meta ad landing events logged</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Channel distribution</div>
                <div class="split-labels">
                    <span class="split-ig-text">Instagram: <strong id="stat-ig-val">0</strong></span>
                    <span class="split-fb-text">Facebook: <strong id="stat-fb-val">0</strong></span>
                </div>
                <div class="split-bar-wrap">
                    <div class="split-bar">
                        <div class="split-bar-ig" id="split-bar-ig" style="width: 50%;"></div>
                        <div class="split-bar-fb" id="split-bar-fb" style="width: 50%;"></div>
                    </div>
                </div>
                <div class="stat-footer" id="stat-ratio-text">Analyzing channel split…</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Zendesk inquiries</div>
                <div class="stat-value" id="stat-inquiries" style="color: var(--accent-cyan);">0</div>
                <div class="stat-footer">Linked chats &amp; support tickets</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Zoho RFQ quotes</div>
                <div class="stat-value" id="stat-quotes" style="color: #c084fc;">0</div>
                <div class="stat-footer">Draft estimates auto-created</div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Meta Ad Spend &amp; ROAS</div>
                <div class="stat-value" id="stat-ad-spend" style="color: #f59e0b;">₱0</div>
                <div class="stat-footer" id="stat-roas-text">Blended ROAS: <strong style="color: #10b981;" id="stat-roas-val">0x</strong></div>
            </div>

            <div class="stat-card">
                <div class="stat-label">Zoho Paid Sales (Revenue)</div>
                <div class="stat-value" id="stat-sales-rev" style="color: #10b981;">₱0</div>
                <div class="stat-footer" id="stat-orders-count">0 paid orders in Zoho Creator</div>
            </div>
        </section>

        <!-- Analytics & Reporting Hub (PDF Master Handoff Views 1 to 4) -->
        <section class="analytics-hub" aria-label="Visual Analytics Hub">
            <div class="analytics-nav">
                <div class="analytics-title-wrap">
                    <span class="analytics-title">Executive Analytics Hub</span>
                    <span class="analytics-badge">PDF Handoff Sec 2.5</span>
                </div>
                <div class="analytics-tabs" role="tablist">
                    <button class="view-btn active" id="tab-v1" onclick="switchAnalyticsView('v1', this)">
                        View 1: Ad Performance
                    </button>
                    <button class="view-btn" id="tab-v2" onclick="switchAnalyticsView('v2', this)">
                        View 2: Traffic &amp; Funnel
                    </button>
                    <button class="view-btn" id="tab-v3" onclick="switchAnalyticsView('v3', this)">
                        View 3: Inquiry Health
                    </button>
                    <button class="view-btn" id="tab-v4" onclick="switchAnalyticsView('v4', this)">
                        View 4: Revenue &amp; ROAS
                    </button>
                </div>
            </div>

            <!-- View 1: Ad Performance (Sec 2.5.2) -->
            <div class="view-panel active" id="panel-v1">
                <div class="charts-grid">
                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Ad Spend by Campaign (PHP)</div>
                                <div class="chart-box-sub">Top Meta campaigns sorted by total budget spent</div>
                            </div>
                            <span class="analytics-badge" id="v1-spend-badge">₱0 Total</span>
                        </div>
                        <div class="chart-canvas-wrap">
                            <canvas id="chartSpendBar"></canvas>
                        </div>
                    </div>

                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Link CTR (%) vs CPC (PHP)</div>
                                <div class="chart-box-sub">Efficiency comparison across active campaigns</div>
                            </div>
                        </div>
                        <div class="chart-canvas-wrap">
                            <canvas id="chartCpcCtr"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- View 2: Traffic & Funnel (Sec 2.5.3) -->
            <div class="view-panel" id="panel-v2">
                <div class="charts-grid">
                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">5-Stage Closed-Loop Attribution Funnel</div>
                                <div class="chart-box-sub">Ad Clicks &rarr; Inquiries &rarr; Quotes &rarr; Paid Orders &rarr; Revenue</div>
                            </div>
                        </div>
                        <div class="chart-canvas-wrap">
                            <canvas id="chartFunnelBar"></canvas>
                        </div>
                    </div>

                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Daily Ad Traffic Trend (Last 14 Days)</div>
                                <div class="chart-box-sub">Daily tracked clicks landing on storefront</div>
                            </div>
                        </div>
                        <div class="chart-canvas-wrap">
                            <canvas id="chartDailyLine"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- View 3: Inquiry Health (Sec 2.5.4) -->
            <div class="view-panel" id="panel-v3">
                <div class="charts-grid">
                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Inquiries &amp; Clicks by Contact Channel</div>
                                <div class="chart-box-sub">WhatsApp, Facebook, Instagram, Messenger breakdown</div>
                            </div>
                        </div>
                        <div class="chart-canvas-wrap">
                            <canvas id="chartChannelsDonut"></canvas>
                        </div>
                    </div>

                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Channel Performance Breakdown</div>
                                <div class="chart-box-sub">Volume share per messaging touchpoint</div>
                            </div>
                        </div>
                        <div class="metric-mini-list" id="channel-metric-list">
                            <!-- Populated dynamically via JS -->
                        </div>
                    </div>
                </div>
            </div>

            <!-- View 4: Revenue Pipeline & ROAS (Sec 2.5.5) -->
            <div class="view-panel" id="panel-v4">
                <div class="charts-grid">
                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Ad Spend vs. Zoho Paid Revenue</div>
                                <div class="chart-box-sub">Comparison of capital deployed vs cash generated</div>
                            </div>
                            <span class="analytics-badge" style="color: #10b981; border-color: rgba(16, 185, 129, 0.3);">ROAS Leader</span>
                        </div>
                        <div class="chart-canvas-wrap">
                            <canvas id="chartRoasCompare"></canvas>
                        </div>
                    </div>

                    <div class="chart-box">
                        <div class="chart-box-header">
                            <div>
                                <div class="chart-box-title">Revenue &amp; Pipeline Conversion Health</div>
                                <div class="chart-box-sub">Key business health metrics from Zoho Creator</div>
                            </div>
                        </div>
                        <div class="metric-mini-list">
                            <div class="metric-mini-row">
                                <span style="color: #94a3b8;">Total Zoho Paid Revenue</span>
                                <span class="metric-mini-val" id="pipe-rev-val" style="color: #10b981;">₱0</span>
                            </div>
                            <div class="metric-mini-row">
                                <span style="color: #94a3b8;">Total Meta Ad Spend</span>
                                <span class="metric-mini-val" id="pipe-spend-val" style="color: #f59e0b;">₱0</span>
                            </div>
                            <div class="metric-mini-row">
                                <span style="color: #94a3b8;">Blended ROAS Multiplier</span>
                                <span class="metric-mini-val" id="pipe-roas-val" style="color: #38bdf8;">0x</span>
                            </div>
                            <div class="metric-mini-row">
                                <span style="color: #94a3b8;">Paid Sales Orders Count</span>
                                <span class="metric-mini-val" id="pipe-orders-val">0 orders</span>
                            </div>
                            <div class="metric-mini-row">
                                <span style="color: #94a3b8;">Average Order Value (AOV)</span>
                                <span class="metric-mini-val" id="pipe-aov-val" style="color: #c084fc;">₱0</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Table Toolbar & Filters -->
        <section class="toolbar">
            <div class="search-wrap">
                <label for="searchInput" class="sr-only">Search attribution records</label>
                <div class="search-box">
                    <input type="text" id="searchInput" name="search" autocomplete="off" spellcheck="false" placeholder="Search product, campaign, token, ticket, estimate…" oninput="handleSearch()">
                    <span class="search-shortcut" aria-hidden="true">/</span>
                </div>
            </div>

            <div class="filter-tabs" role="tablist">
                <button class="filter-tab active" role="tab" onclick="setFilter('all', this)">
                    All <span class="tab-count" id="count-all">0</span>
                </button>
                <button class="filter-tab" role="tab" onclick="setFilter('inquiries', this)">
                    Inquiries <span class="tab-count" id="count-inquiries">0</span>
                </button>
                <button class="filter-tab" role="tab" onclick="setFilter('quotes', this)">
                    Quotes <span class="tab-count" id="count-quotes">0</span>
                </button>
                <button class="filter-tab" role="tab" onclick="setFilter('sales', this)">
                    Sales <span class="tab-count" id="count-sales">0</span>
                </button>
                <button class="filter-tab" role="tab" onclick="setFilter('instagram', this)">
                    Instagram <span class="tab-count" id="count-ig">0</span>
                </button>
                <button class="filter-tab" role="tab" onclick="setFilter('facebook', this)">
                    Facebook <span class="tab-count" id="count-fb">0</span>
                </button>
                <button class="filter-tab" role="tab" onclick="setFilter('products', this)">
                    Products <span class="tab-count" id="count-prod">0</span>
                </button>
            </div>
        </section>

        <!-- Main Attribution Table -->
        <main class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th scope="col">Date &amp; Time</th>
                        <th scope="col">Channel</th>
                        <th scope="col">Landed Product / Creative</th>
                        <th scope="col">Session Token</th>
                        <th scope="col">Zendesk Ticket</th>
                        <th scope="col">Zoho Quote</th>
                        <th scope="col">Sale Revenue</th>
                        <th scope="col">Attribution Stage</th>
                        <th scope="col" style="text-align: right;">Action</th>
                    </tr>
                </thead>
                <tbody id="clicks-tbody">
                    <tr><td colspan="9" class="empty-state">Loading attribution records…</td></tr>
                </tbody>
            </table>
        </main>
    </div>

    <!-- Slide-over Drawer for Record Inspection -->
    <div class="drawer-backdrop" id="drawerBackdrop" onclick="closeDrawer()"></div>
    <aside class="drawer" id="inspectDrawer" aria-labelledby="drawerTitle" role="dialog" aria-modal="true">
        <header class="drawer-header">
            <h2 id="drawerTitle">Attribution Record Details</h2>
            <button class="btn-close" onclick="closeDrawer()" aria-label="Close details drawer">&times;</button>
        </header>
        <div class="drawer-body" id="drawerBody">
        </div>
    </aside>

    <!-- Global Toast Alert -->
    <div class="toast" id="toast" role="status" aria-live="polite">
        <span id="toast-msg">Copied to clipboard</span>
    </div>

    <script>
        let allClicks = [];
        let currentFilter = 'all';
        let searchQuery = '';

        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement !== document.getElementById('searchInput')) {
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }
            if (e.key === 'Escape') {
                closeDrawer();
            }
        });

        function showToast(msg) {
            const toast = document.getElementById('toast');
            document.getElementById('toast-msg').innerText = msg;
            toast.classList.add('show');
            setTimeout(() => { toast.classList.remove('show'); }, 2000);
        }

        function copyText(txt, label) {
            if (!txt) return;
            navigator.clipboard.writeText(txt).then(() => {
                showToast(`Copied ${label || 'value'}`);
            });
        }

        function parseLandingUrl(url) {
            if (!url) return { pathname: '/', productName: 'Direct Visit', params: {} };
            try {
                const u = new URL(url);
                const params = {};
                u.searchParams.forEach((v, k) => { params[k] = v; });
                
                let pathname = u.pathname;
                let productName = '';
                if (pathname.includes('/products/')) {
                    const slug = pathname.split('/products/')[1].replace(/[/?#].*$/, '');
                    productName = slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                } else if (pathname.includes('/collections/')) {
                    const slug = pathname.split('/collections/')[1].replace(/[/?#].*$/, '');
                    productName = slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') + ' Collection';
                } else if (pathname === '/' || pathname === '') {
                    productName = 'Home Cartel Storefront';
                } else {
                    productName = pathname;
                }

                return {
                    pathname,
                    productName,
                    ad_id: params.ad_id || '',
                    campaign_id: params.campaign_id || '',
                    utm_id: params.utm_id || '',
                    media_type: params.media_type || '',
                    params
                };
            } catch(e) {
                return { pathname: url, productName: url, params: {} };
            }
        }

        function formatRelativeTime(dateStr) {
            if (!dateStr) return { relative: 'Just now', exact: '' };
            try {
                const d = new Date(dateStr.replace(' ', 'T') + 'Z');
                const now = new Date();
                const diffSec = Math.floor((now - d) / 1000);
                let rel = '';
                if (diffSec < 45) rel = 'Just now';
                else if (diffSec < 3600) rel = `${Math.floor(diffSec / 60)}m ago`;
                else if (diffSec < 86400) rel = `${Math.floor(diffSec / 3600)}h ago`;
                else rel = `${Math.floor(diffSec / 86400)}d ago`;
                return { relative: rel, exact: dateStr };
            } catch(e) {
                return { relative: dateStr, exact: dateStr };
            }
        }

        function setFilter(filter, btn) {
            currentFilter = filter;
            document.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderTable();
        }

        function handleSearch() {
            searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
            renderTable();
        }

        function renderChannelBadge(ch) {
            ch = (ch || '').toLowerCase();
            if (ch.includes('instagram') || ch === 'ig') {
                return '<span class="pill-instagram">Instagram</span>';
            }
            if (ch.includes('facebook') || ch === 'fb') {
                return '<span class="pill-facebook">Facebook</span>';
            }
            return `<span class="pill-meta">${ch || 'Meta'}</span>`;
        }

        function getStageBadge(c) {
            const isSale = Boolean(c.conversion_total || c.sales_amount || c.zoho_salesorder_id);
            const isCapi = isSale && (c.conversion_capi_status === 'success' || c.capi_status === 'sent' || c.status === 'converted');
            const isQuote = Boolean(c.zoho_estimate_num || c.rfq_detected);
            const isTicket = Boolean(c.zendesk_ticket_id);

            if (isCapi) return '<span class="pill-stage pill-success">&#10003; CAPI Synced</span>';
            if (isSale) return '<span class="pill-stage pill-sale">Paid Sale</span>';
            if (isQuote) return '<span class="pill-stage pill-quote">Quoted</span>';
            if (isTicket) return '<span class="pill-stage pill-inquiry">Inquired</span>';
            return '<span class="pill-stage pill-click">Ad Click</span>';
        }

        function openDrawer(id) {
            const click = allClicks.find(c => c.id === id);
            if (!click) return;

            const urlData = parseLandingUrl(click.landing_page);
            const body = document.getElementById('drawerBody');

            const isTicket = Boolean(click.zendesk_ticket_id);
            const isQuote = Boolean(click.zoho_estimate_num || click.rfq_detected);
            const isSale = Boolean(click.conversion_total || click.sales_amount || click.zoho_salesorder_id);
            const isCapi = Boolean(click.conversion_capi_status === 'success' || click.capi_status === 'sent');
            const saleAmount = Number(click.conversion_total || click.sales_amount || 0);

            body.innerHTML = `
                <!-- Stepper Progress Tracker -->
                <div class="drawer-section">
                    <div class="drawer-section-title">Attribution Funnel Lifecycle</div>
                    <div class="funnel-stepper">
                        <div class="stepper-step completed">
                            <div class="step-indicator">&#10003;</div>
                            <div class="step-content">
                                <div class="step-title">1. Ad Landing &amp; Token Capture</div>
                                <div class="step-sub">Session token generated and saved in browser.</div>
                            </div>
                        </div>

                        <div class="stepper-step ${isTicket ? 'completed' : 'active'}">
                            <div class="step-indicator">${isTicket ? '&#10003;' : '2'}</div>
                            <div class="step-content">
                                <div class="step-title">2. Customer Message &amp; Zendesk</div>
                                <div class="step-sub">
                                    ${isTicket ? `Matched to Ticket <strong>#${click.zendesk_ticket_id}</strong>` : 'Awaiting incoming chat on WhatsApp / Messenger'}
                                </div>
                            </div>
                        </div>

                        <div class="stepper-step ${isQuote ? 'completed' : (isTicket ? 'active' : '')}">
                            <div class="step-indicator">${isQuote ? '&#10003;' : '3'}</div>
                            <div class="step-content">
                                <div class="step-title">3. RFQ Intent &amp; Zoho Estimate</div>
                                <div class="step-sub">
                                    ${isQuote ? `Draft quote created: <strong>${click.zoho_estimate_num || 'RFQ Detected'}</strong>` : 'Triggers on keywords like "quote", "magkano", "pricing"'}
                                </div>
                            </div>
                        </div>

                        <div class="stepper-step ${isSale ? 'completed' : (isQuote ? 'active' : '')}">
                            <div class="step-indicator">${isSale ? '&#10003;' : '4'}</div>
                            <div class="step-content">
                                <div class="step-title">4. Closed Sale &amp; Revenue</div>
                                <div class="step-sub">
                                    ${isSale ? `Paid order: <strong>₱${saleAmount.toLocaleString()}</strong> (${click.conversion_so_id || click.zoho_salesorder_id || 'SO'})` : 'Sales Order created in Zoho Books'}
                                </div>
                            </div>
                        </div>

                        <div class="stepper-step ${isCapi ? 'completed' : (isSale ? 'active' : '')}">
                            <div class="step-indicator">${isCapi ? '&#10003;' : '5'}</div>
                            <div class="step-content">
                                <div class="step-title">5. Meta CAPI Offline Feedback</div>
                                <div class="step-sub">
                                    ${isCapi ? 'Purchase event sent to Meta CAPI with revenue attribution' : 'Sent automatically on Sales Order creation'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="drawer-section">
                    <div class="drawer-section-title">Landed destination</div>
                    <div style="font-size:14px; font-weight:600; color:#fff; margin-bottom:8px;">
                        ${urlData.productName}
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Path</span>
                        <span class="meta-val">${urlData.pathname}</span>
                    </div>
                    ${urlData.ad_id ? `
                    <div class="meta-kv">
                        <span class="meta-key">Meta Ad ID</span>
                        <span class="meta-val" style="color:var(--accent-cyan);">
                            ${urlData.ad_id} 
                            <button class="btn-inspect" style="margin-left:8px;" onclick="copyText('${urlData.ad_id}', 'Ad ID')">Copy</button>
                        </span>
                    </div>` : ''}
                    ${urlData.campaign_id ? `
                    <div class="meta-kv">
                        <span class="meta-key">Campaign ID</span>
                        <span class="meta-val">${urlData.campaign_id}</span>
                    </div>` : ''}
                    <div style="margin-top:10px; display:flex; gap:8px;">
                        ${click.landing_page ? `
                        <a href="${click.landing_page}" target="_blank" rel="noopener noreferrer" class="btn-action btn-primary">
                            Open URL &nearr;
                        </a>
                        <button class="btn-action" onclick="copyText('${click.landing_page}', 'URL')">
                            Copy URL
                        </button>` : '<span style="color:#64748b;">No URL recorded</span>'}
                    </div>
                </div>

                <div class="drawer-section">
                    <div class="drawer-section-title">Campaign parameters</div>
                    <div class="meta-kv">
                        <span class="meta-key">Campaign</span>
                        <span class="meta-val">${click.utm_campaign || '(None)'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Creative</span>
                        <span class="meta-val">${click.utm_content || '(None)'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Channel</span>
                        <span class="meta-val">${click.channel}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Source / Medium</span>
                        <span class="meta-val">${click.utm_source || 'meta'} / ${click.utm_medium || 'paid'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Referrer</span>
                        <span class="meta-val">${click.referrer || '(Direct in-app)'}</span>
                    </div>
                </div>

                <div class="drawer-section">
                    <div class="drawer-section-title">Attribution IDs</div>
                    <div class="meta-kv">
                        <span class="meta-key">Session Token</span>
                        <span class="meta-val" style="color:var(--accent-cyan); font-weight:600;">${click.session_token}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Meta fbclid</span>
                        <span class="meta-val">${click.fbclid || '(None)'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Zendesk Ticket</span>
                        <span class="meta-val">${click.zendesk_ticket_id ? '#' + click.zendesk_ticket_id : '(Pending)'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Zoho Estimate</span>
                        <span class="meta-val">${click.zoho_estimate_num || '(Pending)'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Zoho Sales Order</span>
                        <span class="meta-val">${click.conversion_so_id || click.zoho_salesorder_id || '(Pending)'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Attributed Revenue</span>
                        <span class="meta-val" style="color:#10b981; font-weight:700;">${saleAmount > 0 ? '₱' + saleAmount.toLocaleString() : '₱0.00'}</span>
                    </div>
                    <div class="meta-kv">
                        <span class="meta-key">Timestamp</span>
                        <span class="meta-val">${click.created_at || 'Just now'}</span>
                    </div>
                    <div style="margin-top:8px; display:flex; flex-wrap:wrap; gap:6px;">
                        <button class="btn-action" onclick="copyText('${click.session_token}', 'Token')">Copy Token</button>
                        <button class="btn-action" onclick="copyText('${click.fbclid}', 'fbclid')">Copy fbclid</button>
                        ${click.zendesk_ticket_id ? `<button class="btn-action" onclick="copyText('${click.zendesk_ticket_id}', 'Ticket')">Copy Ticket ID</button>` : ''}
                    </div>
                </div>

                <div class="drawer-section">
                    <div class="drawer-section-title">Raw payload</div>
                    <pre class="raw-json-box">${JSON.stringify(click, null, 2)}</pre>
                    <button class="btn-action" style="margin-top:8px;" onclick="copyText('${encodeURIComponent(JSON.stringify(click))}', 'JSON')">Copy JSON</button>
                </div>
            `;

            document.getElementById('drawerBackdrop').classList.add('open');
            document.getElementById('inspectDrawer').classList.add('open');
        }

        function closeDrawer() {
            document.getElementById('drawerBackdrop').classList.remove('open');
            document.getElementById('inspectDrawer').classList.remove('open');
        }

        function renderTable() {
            let filtered = allClicks.filter(c => {
                const ch = (c.channel || '').toLowerCase();
                const lp = (c.landing_page || '').toLowerCase();
                
                if (currentFilter === 'inquiries' && !c.zendesk_ticket_id) return false;
                if (currentFilter === 'quotes' && (!c.rfq_detected && !c.zoho_estimate_num)) return false;
                if (currentFilter === 'sales' && (!c.conversion_total && !c.sales_amount && !c.zoho_salesorder_id)) return false;
                if (currentFilter === 'instagram' && !ch.includes('instagram')) return false;
                if (currentFilter === 'facebook' && !ch.includes('facebook')) return false;
                if (currentFilter === 'products' && !lp.includes('/products/')) return false;
                
                if (searchQuery) {
                    const text = [
                        c.fbclid, c.session_token, c.utm_campaign, c.utm_content, 
                        c.landing_page, c.channel, c.zendesk_ticket_id, 
                        c.zoho_estimate_num, c.zoho_salesorder_id, c.conversion_so_id
                    ].join(' ').toLowerCase();
                    if (!text.includes(searchQuery)) return false;
                }
                return true;
            });

            const tbody = document.getElementById('clicks-tbody');
            if (filtered.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" class="empty-state">
                            No attribution records found for current filter.
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = filtered.map(c => {
                const urlData = parseLandingUrl(c.landing_page);
                const timeInfo = formatRelativeTime(c.created_at);
                const saleRev = Number(c.conversion_total || c.sales_amount || 0);
                const soId = c.conversion_so_id || c.zoho_salesorder_id;

                return `
                <tr>
                    <td class="time-cell" title="${timeInfo.exact}">
                        <span class="time-relative">${timeInfo.relative}</span>
                        <span class="time-exact">${c.created_at ? c.created_at.split(' ')[1] : ''}</span>
                    </td>
                    <td>${renderChannelBadge(c.channel)}</td>
                    <td>
                        <div class="product-cell">
                            ${c.landing_page ? `
                            <a href="${c.landing_page}" target="_blank" rel="noopener noreferrer" class="product-link" title="${c.landing_page}">
                                ${urlData.productName} &nearr;
                            </a>
                            ` : `<span style="color:#64748b;">Storefront</span>`}
                            <div style="display:flex; gap:4px; align-items:center; flex-wrap:wrap;">
                                ${c.utm_campaign ? `<span class="pill-campaign" title="${c.utm_campaign}">${c.utm_campaign}</span>` : ''}
                                ${urlData.ad_id ? `<span class="ad-id-badge" title="Meta Ad ID: ${urlData.ad_id}">Ad #${urlData.ad_id.substring(0, 10)}…</span>` : ''}
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="copy-pill" onclick="copyText('${c.session_token}', 'Token')" style="color:var(--accent-cyan); font-weight:600;" title="Click to copy session token">
                            ${c.session_token || ''}
                        </span>
                    </td>
                    <td>
                        ${c.zendesk_ticket_id ? `
                            <span class="pill-ticket" title="Zendesk Ticket #${c.zendesk_ticket_id}">
                                #${c.zendesk_ticket_id}
                            </span>
                        ` : `<span class="badge-faded">No message</span>`}
                    </td>
                    <td>
                        ${(c.zoho_estimate_num || c.rfq_detected) ? `
                            <span class="pill-estimate" title="Zoho Books Draft Quote">
                                ${c.zoho_estimate_num ? c.zoho_estimate_num : 'RFQ Quoted'}
                            </span>
                        ` : `<span class="badge-faded">&mdash;</span>`}
                    </td>
                    <td>
                        ${(saleRev > 0 || soId) ? `
                            <div class="rev-cell">
                                <span class="rev-amount">₱${saleRev.toLocaleString()}</span>
                                <span class="so-id">${soId || 'SO Paid'}</span>
                            </div>
                        ` : `<span class="badge-faded">&mdash;</span>`}
                    </td>
                    <td>
                        ${getStageBadge(c)}
                    </td>
                    <td style="text-align: right;">
                        <button class="btn-inspect" onclick="openDrawer(${c.id})" aria-label="View click details for ID ${c.id}">
                            View
                        </button>
                    </td>
                </tr>
                `;
            }).join('');
        }

        async function fetchClicks(isManual = false) {
            try {
                const res = await fetch('/api/clicks');
                const data = await res.json();
                allClicks = data.clicks || [];

                const total = data.total_clicks || allClicks.length;
                document.getElementById('stat-total').innerText = total;
                document.getElementById('count-all').innerText = total;

                // Funnel Metrics
                const totalInquiries = data.total_inquiries || allClicks.filter(c => c.zendesk_ticket_id).length;
                const totalQuotes = data.total_quotes || allClicks.filter(c => c.rfq_detected || c.zoho_estimate_num).length;
                const totalOrders = data.total_orders || allClicks.filter(c => c.conversion_total || c.sales_amount || c.zoho_salesorder_id).length;
                const totalRev = Number(data.total_revenue || 0);

                document.getElementById('stat-inquiries').innerText = totalInquiries;
                document.getElementById('stat-quotes').innerText = totalQuotes;
                document.getElementById('stat-sales-rev').innerText = '₱' + totalRev.toLocaleString();
                document.getElementById('stat-orders-count').innerText = `${totalOrders} paid orders in Zoho Creator`;

                // Ad Spend & ROAS
                const adSpend = Math.round(Number(data.total_ad_spend || 0));
                const roas = data.blended_roas || (adSpend > 0 ? (totalRev / adSpend).toFixed(1) : 0);
                if (document.getElementById('stat-ad-spend')) {
                    document.getElementById('stat-ad-spend').innerText = '₱' + adSpend.toLocaleString();
                }
                if (document.getElementById('stat-roas-val')) {
                    document.getElementById('stat-roas-val').innerText = roas + 'x';
                }

                // Tab counts
                document.getElementById('count-inquiries').innerText = totalInquiries;
                document.getElementById('count-quotes').innerText = totalQuotes;
                document.getElementById('count-sales').innerText = totalOrders;

                const fbClicks = allClicks.filter(c => (c.channel || '').toLowerCase().includes('facebook'));
                const igClicks = allClicks.filter(c => (c.channel || '').toLowerCase().includes('instagram'));
                const prodClicks = allClicks.filter(c => (c.landing_page || '').includes('/products/'));

                document.getElementById('stat-ig-val').innerText = igClicks.length;
                document.getElementById('stat-fb-val').innerText = fbClicks.length;
                document.getElementById('count-ig').innerText = igClicks.length;
                document.getElementById('count-fb').innerText = fbClicks.length;
                document.getElementById('count-prod').innerText = prodClicks.length;

                if (total > 0) {
                    const igPercent = Math.round((igClicks.length / total) * 100);
                    const fbPercent = 100 - igPercent;
                    document.getElementById('split-bar-ig').style.width = igPercent + '%';
                    document.getElementById('split-bar-fb').style.width = fbPercent + '%';
                    document.getElementById('stat-ratio-text').innerText = `${igPercent}% Instagram · ${fbPercent}% Facebook`;
                }

                renderTable();
                renderAnalyticsCharts(data);

                if (isManual) {
                    showToast('Data refreshed');
                }
            } catch (err) {
                console.error('Error fetching clicks:', err);
            }
        }

        let chartSpendBar = null;
        let chartCpcCtr = null;
        let chartFunnelBar = null;
        let chartDailyLine = null;
        let chartChannelsDonut = null;
        let chartRoasCompare = null;
        let lastChartDataSig = '';

        function switchAnalyticsView(viewId, btn) {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const panel = document.getElementById('panel-' + viewId);
            if (panel) {
                panel.classList.add('active');
            }

            setTimeout(() => {
                [chartSpendBar, chartCpcCtr, chartFunnelBar, chartDailyLine, chartChannelsDonut, chartRoasCompare].forEach(chart => {
                    if (chart) chart.resize();
                });
            }, 60);
        }

        function renderAnalyticsCharts(data) {
            if (typeof Chart === 'undefined') return;

            const totalRev = Number(data.total_revenue || 0);
            const totalSpend = Number(data.total_ad_spend || 0);
            const totalClicks = Number(data.total_clicks || 0);
            const totalInquiries = Number(data.total_inquiries || 0);
            const totalQuotes = Number(data.total_quotes || 0);
            const totalOrders = Number(data.total_orders || 0);

            const sig = `${totalRev}_${totalSpend}_${totalClicks}_${totalOrders}_${(data.campaigns_summary||[]).length}`;
            if (sig === lastChartDataSig) return;
            lastChartDataSig = sig;

            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = "'Plus Jakarta Sans', -apple-system, sans-serif";
            Chart.defaults.borderColor = 'rgba(30, 41, 59, 0.7)';

            const campaigns = data.campaigns_summary || [];
            const channels = data.channels_summary || [];
            const daily = data.daily_trend || [];

            // Update View 1 Badge
            const v1Badge = document.getElementById('v1-spend-badge');
            if (v1Badge) v1Badge.innerText = '₱' + Math.round(totalSpend).toLocaleString() + ' Total';

            // --- CHART 1: View 1 Ad Spend by Campaign (Horizontal Bar) ---
            const spendCtx = document.getElementById('chartSpendBar');
            if (spendCtx) {
                const topSpend = campaigns.filter(c => c.amount_spent > 0).slice(0, 6);
                const labels = topSpend.map(c => c.campaign_name.length > 20 ? c.campaign_name.substring(0, 18) + '…' : c.campaign_name);
                const values = topSpend.map(c => c.amount_spent);

                if (chartSpendBar) chartSpendBar.destroy();
                chartSpendBar = new Chart(spendCtx, {
                    type: 'bar',
                    data: {
                        labels: labels.length ? labels : ['No Campaign Data'],
                        datasets: [{
                            label: 'Ad Spend (PHP)',
                            data: values.length ? values : [0],
                            backgroundColor: 'rgba(56, 189, 248, 0.8)',
                            borderColor: '#38bdf8',
                            borderWidth: 1,
                            borderRadius: 4
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ' ₱' + Number(ctx.raw).toLocaleString('en-US', { minimumFractionDigits: 2 })
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: 'rgba(30, 41, 59, 0.5)' },
                                ticks: {
                                    callback: (v) => '₱' + (v >= 1000 ? (v/1000) + 'k' : v)
                                }
                            },
                            y: { grid: { display: false } }
                        }
                    }
                });
            }

            // --- CHART 2: View 1 CTR vs CPC ---
            const cpcCtrCtx = document.getElementById('chartCpcCtr');
            if (cpcCtrCtx) {
                const activeCamps = campaigns.filter(c => c.amount_spent > 0).slice(0, 5);
                const labels = activeCamps.map(c => c.campaign_name.length > 15 ? c.campaign_name.substring(0, 13) + '…' : c.campaign_name);
                const ctrValues = activeCamps.map(c => c.ctr);
                const cpcValues = activeCamps.map(c => c.cpc);

                if (chartCpcCtr) chartCpcCtr.destroy();
                chartCpcCtr = new Chart(cpcCtrCtx, {
                    type: 'bar',
                    data: {
                        labels: labels.length ? labels : ['No Active Ads'],
                        datasets: [
                            {
                                label: 'Link CTR (%)',
                                data: ctrValues.length ? ctrValues : [0],
                                backgroundColor: 'rgba(52, 211, 153, 0.8)',
                                borderColor: '#10b981',
                                borderWidth: 1,
                                yAxisID: 'yCtr',
                                borderRadius: 4
                            },
                            {
                                label: 'Cost per Click (PHP)',
                                data: cpcValues.length ? cpcValues : [0],
                                backgroundColor: 'rgba(244, 63, 94, 0.75)',
                                borderColor: '#f43f5e',
                                borderWidth: 1,
                                yAxisID: 'yCpc',
                                borderRadius: 4
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ctx.datasetIndex === 0 ? ` CTR: ${ctx.raw}%` : ` CPC: ₱${Number(ctx.raw).toFixed(2)}`
                                }
                            }
                        },
                        scales: {
                            yCtr: {
                                type: 'linear',
                                position: 'left',
                                grid: { color: 'rgba(30, 41, 59, 0.4)' },
                                ticks: { callback: v => v + '%' }
                            },
                            yCpc: {
                                type: 'linear',
                                position: 'right',
                                grid: { display: false },
                                ticks: { callback: v => '₱' + v }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }

            // --- CHART 3: View 2 Funnel Waterfall (5 Stages) ---
            const funnelCtx = document.getElementById('chartFunnelBar');
            if (funnelCtx) {
                const funnelLabels = ['1. Ad Clicks', '2. Inquiries', '3. Quotes', '4. Paid Orders'];
                const funnelData = [totalClicks, totalInquiries, totalQuotes, totalOrders];

                if (chartFunnelBar) chartFunnelBar.destroy();
                chartFunnelBar = new Chart(funnelCtx, {
                    type: 'bar',
                    data: {
                        labels: funnelLabels,
                        datasets: [{
                            label: 'Volume',
                            data: funnelData,
                            backgroundColor: [
                                'rgba(59, 130, 246, 0.8)',
                                'rgba(56, 189, 248, 0.8)',
                                'rgba(192, 132, 252, 0.8)',
                                'rgba(16, 185, 129, 0.85)'
                            ],
                            borderColor: ['#3b82f6', '#38bdf8', '#c084fc', '#10b981'],
                            borderWidth: 1,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` Count: ${Number(ctx.raw).toLocaleString()} (${totalClicks > 0 ? ((Number(ctx.raw)/totalClicks)*100).toFixed(1) : 0}% of clicks)`
                                }
                            }
                        },
                        scales: {
                            y: {
                                type: 'logarithmic',
                                grid: { color: 'rgba(30, 41, 59, 0.5)' },
                                ticks: {
                                    callback: (v) => v === 1 || v === 10 || v === 100 || v === 1000 || v === 10000 ? v.toLocaleString() : null
                                }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }

            // --- CHART 4: View 2 Daily Line Trend ---
            const dailyCtx = document.getElementById('chartDailyLine');
            if (dailyCtx) {
                const labels = daily.map(d => d.date ? d.date.substring(5) : '');
                const counts = daily.map(d => d.count);

                if (chartDailyLine) chartDailyLine.destroy();
                chartDailyLine = new Chart(dailyCtx, {
                    type: 'line',
                    data: {
                        labels: labels.length ? labels : ['Today'],
                        datasets: [{
                            label: 'Tracked Clicks',
                            data: counts.length ? counts : [totalClicks],
                            fill: true,
                            backgroundColor: 'rgba(56, 189, 248, 0.1)',
                            borderColor: '#38bdf8',
                            borderWidth: 2,
                            tension: 0.35,
                            pointRadius: 3,
                            pointBackgroundColor: '#38bdf8'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { grid: { color: 'rgba(30, 41, 59, 0.4)' } },
                            x: { grid: { display: false } }
                        }
                    }
                });
            }

            // --- CHART 5: View 3 Channels Donut ---
            const chanCtx = document.getElementById('chartChannelsDonut');
            if (chanCtx) {
                const chanLabels = channels.map(c => c.channel);
                const chanCounts = channels.map(c => c.count);
                const colors = [
                    '#3b82f6', '#f43f5e', '#10b981', '#38bdf8', '#f59e0b', '#8b5cf6'
                ];

                if (chartChannelsDonut) chartChannelsDonut.destroy();
                chartChannelsDonut = new Chart(chanCtx, {
                    type: 'doughnut',
                    data: {
                        labels: chanLabels.length ? chanLabels : ['Meta Clicks'],
                        datasets: [{
                            data: chanCounts.length ? chanCounts : [1],
                            backgroundColor: colors.slice(0, chanLabels.length || 1),
                            borderWidth: 2,
                            borderColor: '#090d16'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '68%',
                        plugins: {
                            legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
                        }
                    }
                });

                // Populate mini list for Channel Health
                const listEl = document.getElementById('channel-metric-list');
                if (listEl) {
                    const totalChanClicks = chanCounts.reduce((a, b) => a + b, 0) || 1;
                    listEl.innerHTML = channels.map((c, i) => {
                        const pct = Math.round((c.count / totalChanClicks) * 100);
                        return `
                            <div class="metric-mini-row">
                                <span style="display:flex; align-items:center; gap:8px;">
                                    <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${colors[i % colors.length]};"></span>
                                    <span>${c.channel}</span>
                                </span>
                                <span><strong style="color:#fff;">${c.count.toLocaleString()}</strong> <span style="color:#64748b;">(${pct}%)</span></span>
                            </div>
                        `;
                    }).join('');
                }
            }

            // --- CHART 6: View 4 Revenue Pipeline & ROAS ---
            const roasCtx = document.getElementById('chartRoasCompare');
            if (roasCtx) {
                if (chartRoasCompare) chartRoasCompare.destroy();
                chartRoasCompare = new Chart(roasCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Attribution Pipeline Overview'],
                        datasets: [
                            {
                                label: 'Meta Ad Spend',
                                data: [totalSpend],
                                backgroundColor: 'rgba(245, 158, 11, 0.85)',
                                borderColor: '#f59e0b',
                                borderWidth: 1,
                                borderRadius: 6
                            },
                            {
                                label: 'Zoho Creator Paid Sales',
                                data: [totalRev],
                                backgroundColor: 'rgba(16, 185, 129, 0.85)',
                                borderColor: '#10b981',
                                borderWidth: 1,
                                borderRadius: 6
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` ${ctx.dataset.label}: ₱${Number(ctx.raw).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
                                }
                            }
                        },
                        scales: {
                            y: {
                                grid: { color: 'rgba(30, 41, 59, 0.5)' },
                                ticks: {
                                    callback: (v) => '₱' + (v >= 1000000 ? (v/1000000).toFixed(1) + 'M' : (v >= 1000 ? (v/1000) + 'k' : v))
                                }
                            },
                            x: { grid: { display: false } }
                        }
                    }
                });

                // Update View 4 Pipeline KPI numbers
                const pipeRev = document.getElementById('pipe-rev-val');
                const pipeSpend = document.getElementById('pipe-spend-val');
                const pipeRoas = document.getElementById('pipe-roas-val');
                const pipeOrders = document.getElementById('pipe-orders-val');
                const pipeAov = document.getElementById('pipe-aov-val');

                if (pipeRev) pipeRev.innerText = '₱' + Math.round(totalRev).toLocaleString();
                if (pipeSpend) pipeSpend.innerText = '₱' + Math.round(totalSpend).toLocaleString();
                if (pipeRoas) pipeRoas.innerText = (data.blended_roas || (totalSpend > 0 ? (totalRev/totalSpend).toFixed(2) : 0)) + 'x';
                if (pipeOrders) pipeOrders.innerText = totalOrders + ' paid orders';
                if (pipeAov) {
                    const aov = totalOrders > 0 ? Math.round(totalRev / totalOrders) : 0;
                    pipeAov.innerText = '₱' + aov.toLocaleString();
                }
            }
        }

        function exportCSV() {
            if (allClicks.length === 0) {
                alert('No click records to export.');
                return;
            }
            const headers = [
                'ID', 'Date_Time', 'Channel', 'Product_Destination', 'Meta_Ad_ID', 
                'Campaign_Name', 'Ad_Content', 'Meta_fbclid', 'Session_Token', 
                'Zendesk_Ticket', 'Zoho_Estimate', 'Sales_Order', 'Revenue_PHP', 
                'CAPI_Status', 'Full_Landing_URL', 'Referrer'
            ];
            const rows = allClicks.map(c => {
                const parsed = parseLandingUrl(c.landing_page);
                return [
                    c.id,
                    `"${c.created_at || ''}"`,
                    `"${c.channel || ''}"`,
                    `"${(parsed.productName || '').replace(/"/g, '""')}"`,
                    `"${parsed.ad_id || ''}"`,
                    `"${(c.utm_campaign || '').replace(/"/g, '""')}"`,
                    `"${(c.utm_content || '').replace(/"/g, '""')}"`,
                    `"${c.fbclid || ''}"`,
                    `"${c.session_token || ''}"`,
                    `"${c.zendesk_ticket_id || ''}"`,
                    `"${c.zoho_estimate_num || ''}"`,
                    `"${c.conversion_so_id || c.zoho_salesorder_id || ''}"`,
                    `"${c.conversion_total || c.sales_amount || 0}"`,
                    `"${c.conversion_capi_status || c.capi_status || 'pending'}"`,
                    `"${(c.landing_page || '').replace(/"/g, '""')}"`,
                    `"${(c.referrer || '').replace(/"/g, '""')}"`
                ];
            });

            const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\\n');
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement('a');
            link.setAttribute('href', encodedUri);
            link.setAttribute('download', 'homecartel_attribution_funnel_' + new Date().toISOString().slice(0, 10) + '.csv');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showToast('CSV downloaded');
        }

        fetchClicks();
        setInterval(fetchClicks, 10000);
    </script>
</body>
</html>
"""
