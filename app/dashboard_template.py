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
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }

        @media (min-width: 1200px) {
            .stats-grid {
                grid-template-columns: repeat(5, 1fr);
            }
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
        }

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
            grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
            gap: 18px;
        }

        .chart-box {
            background: linear-gradient(180deg, #0d1322 0%, #080c16 100%);
            border: 1px solid rgba(51, 65, 85, 0.45);
            border-radius: 12px;
            padding: 18px 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.45);
            transition: border-color 0.2s ease, transform 0.2s ease;
        }

        .chart-box:hover {
            border-color: rgba(56, 189, 248, 0.35);
        }

        .chart-box-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 14px;
        }

        .chart-box-title {
            font-size: 13px;
            font-weight: 600;
            color: #f8fafc;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chart-box-sub {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 3px;
        }

        .chart-canvas-wrap {
            position: relative;
            height: 285px;
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

        /* Ad Health Monitor (PDF Sec 2.5.2 & 2.6) */
        .health-hub {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px 22px;
            margin-bottom: 22px;
        }
        .health-updated {
            font-size: 11px;
            color: var(--text-muted);
            font-family: var(--font-mono);
        }
        .health-kpis {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(220px, 100%), 1fr));
            gap: 14px;
            margin-bottom: 18px;
        }
        .health-kpi {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
        }
        .health-kpi-label {
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .health-kpi-value {
            font-size: 22px;
            font-weight: 700;
            color: #fff;
            font-family: var(--font-mono);
            min-height: 30px;
            display: flex;
            align-items: center;
        }
        .health-kpi-sub {
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 6px;
        }
        .health-charts {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(340px, 100%), 1fr));
            gap: 18px;
            margin-bottom: 18px;
        }
        .health-canvas {
            height: 380px;
        }
        .health-charts[hidden] { display: none; }
        .health-empty {
            padding: 28px;
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
            background: #0d1322;
            border: 1px dashed var(--border-hover);
            border-radius: 10px;
            margin-bottom: 18px;
        }
        .health-attention {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }
        .health-attention-title {
            font-size: 12px;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 10px;
        }
        .health-attention-hint {
            font-weight: 500;
            font-size: 11px;
            color: var(--text-muted);
            margin-left: 8px;
        }
        .health-attn-row {
            display: grid;
            grid-template-columns: 96px minmax(0, 1fr) minmax(0, 1.2fr);
            gap: 14px;
            align-items: center;
            width: 100%;
            text-align: left;
            background: transparent;
            border: 0;
            border-top: 1px solid rgba(30, 41, 59, 0.6);
            padding: 10px 4px;
            color: inherit;
            font-family: inherit;
            cursor: pointer;
        }
        .health-attn { border-top: 1px solid rgba(30, 41, 59, 0.6); }
        .health-attn:first-child { border-top: 0; }
        .health-attn .health-attn-row { border-top: 0; }
        .health-sop {
            margin: 0 4px 10px 110px;
            font-size: 11px;
            color: var(--text-secondary);
        }
        .health-sop summary { cursor: pointer; color: var(--accent-cyan); font-weight: 600; }
        .health-sop ol { margin: 8px 0 0 18px; line-height: 1.7; }
        .health-attn-row:hover { background: rgba(30, 41, 59, 0.25); }
        .health-attn-row:focus-visible { outline: 2px solid var(--accent-cyan); outline-offset: -2px; }
        .health-attn-name {
            font-size: 12px;
            font-weight: 600;
            color: #f8fafc;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .health-attn-metrics {
            font-size: 10px;
            color: var(--text-muted);
            font-family: var(--font-mono);
            margin-top: 2px;
        }
        .health-attn-ok {
            font-size: 12px;
            color: #34d399;
            padding: 4px 0;
        }
        .health-coverage {
            font-size: 11px;
            color: var(--text-muted);
            background: #0a0e19;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px 14px;
        }
        .health-coverage summary {
            cursor: pointer;
            font-weight: 600;
            color: var(--text-secondary);
        }
        .health-coverage ul {
            margin: 10px 0 8px 18px;
            line-height: 1.7;
        }
        .health-coverage strong { color: #cbd5e1; }
        .health-coverage p { margin: 0; }
        @media (max-width: 720px) {
            .health-attn-row { grid-template-columns: 1fr; gap: 6px; }
            .health-sop { margin-left: 4px; }
        }

        /* Ad health pop-up */
        .health-modal-backdrop {
            position: fixed;
            inset: 0;
            z-index: 3000;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(3px);
        }
        .health-modal-backdrop[hidden] { display: none; }
        .health-modal-card {
            width: 100%;
            max-width: 640px;
            max-height: 86vh;
            display: flex;
            flex-direction: column;
            background: #0d121f;
            border: 1px solid var(--border-hover);
            border-radius: 12px;
            box-shadow: 0 24px 60px rgba(0, 0, 0, 0.6);
        }
        .health-modal-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
        }
        .health-modal-title { font-size: 15px; font-weight: 700; color: #fff; }
        .health-modal-sub { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
        .health-modal-body { padding: 14px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .health-modal-item {
            background: #0a0e19;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
        }
        .health-modal-item-name { font-size: 12px; font-weight: 600; color: #f8fafc; margin: 6px 0 2px; }
        .health-modal-item-metrics { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 8px; }
        .health-modal-note {
            font-size: 11px;
            color: var(--text-secondary);
            background: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 6px;
            padding: 8px 10px;
        }
        .health-modal-note.warn {
            background: rgba(245, 158, 11, 0.1);
            border-color: rgba(245, 158, 11, 0.35);
            color: #fde68a;
        }
        .health-modal-foot {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 12px 20px;
            border-top: 1px solid var(--border);
        }

        /* Section 2.6.4 Alert Center Styles */
        .alert-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }
        .alert-status-pill.watch {
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: #38bdf8;
        }
        .alert-status-pill.watch:hover {
            background: rgba(56, 189, 248, 0.22);
            border-color: #38bdf8;
        }
        .alert-status-pill.critical {
            background: rgba(244, 63, 94, 0.15);
            border: 1px solid rgba(244, 63, 94, 0.4);
            color: #fb7185;
        }
        .alert-status-pill.warning {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #fbbf24;
        }
        .alert-status-pill.healthy {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34d399;
        }
        .alert-pulse-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 8px currentColor;
            animation: alertPulse 2s infinite ease-in-out;
        }
        @keyframes alertPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.45; transform: scale(0.85); }
        }

        .tab-alert-count {
            background: #0284c7;
            color: #fff;
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 700;
            margin-left: 5px;
        }

        .v1-alert-banner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 11px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .v1-alert-banner.watch {
            background: rgba(12, 74, 110, 0.28);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: #e0f2fe;
        }
        .v1-alert-banner.watch:hover {
            background: rgba(12, 74, 110, 0.45);
            border-color: #38bdf8;
        }
        .v1-alert-banner-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .v1-alert-banner-title {
            font-weight: 700;
            color: #38bdf8;
        }
        .v1-alert-banner-cta {
            font-weight: 600;
            color: #38bdf8;
            font-size: 11px;
            white-space: nowrap;
        }

        .alert-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }
        .alert-stat-card {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .alert-stat-card:hover {
            border-color: var(--border-hover);
            transform: translateY(-1px);
        }
        .alert-stat-card.critical { border-left: 3px solid #f43f5e; }
        .alert-stat-card.warning { border-left: 3px solid #f59e0b; }
        .alert-stat-card.watch { border-left: 3px solid #38bdf8; }
        .alert-stat-card.healthy { border-left: 3px solid #10b981; }

        .alert-stat-header {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 6px;
        }
        .alert-stat-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            display: inline-block;
        }
        .alert-stat-dot.red { background: #f43f5e; box-shadow: 0 0 6px #f43f5e; }
        .alert-stat-dot.yellow { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; }
        .alert-stat-dot.blue { background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }
        .alert-stat-dot.green { background: #10b981; box-shadow: 0 0 6px #10b981; }

        .alert-stat-title {
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.6px;
            color: var(--text-muted);
        }
        .alert-stat-num {
            font-size: 26px;
            font-weight: 700;
            font-family: var(--font-mono);
            color: #fff;
            line-height: 1.1;
            margin-bottom: 4px;
        }
        .alert-stat-desc {
            font-size: 11px;
            color: var(--text-secondary);
        }

        .alert-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }
        .alert-filter-pills {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        .alert-filter-pill {
            background: #0f1523;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }
        .alert-filter-pill:hover {
            color: #fff;
            border-color: var(--border-hover);
        }
        .alert-filter-pill.active {
            background: #1e293b;
            border-color: #38bdf8;
            color: #38bdf8;
        }
        .alert-meta-note {
            font-size: 11px;
            color: var(--text-muted);
        }
        .alert-meta-note code {
            font-family: var(--font-mono);
            color: #cbd5e1;
            background: #1e293b;
            padding: 1px 5px;
            border-radius: 3px;
        }

        .alert-table-wrap {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow-x: auto;
            margin-bottom: 20px;
        }
        .alert-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            text-align: left;
        }
        .alert-table th {
            padding: 10px 14px;
            background: #0a0e19;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        .alert-table td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(30, 41, 59, 0.5);
            color: var(--text-secondary);
            vertical-align: middle;
        }
        .alert-table tr:hover td {
            background: rgba(30, 41, 59, 0.25);
        }

        .badge-alert {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            font-family: var(--font-mono);
        }
        .badge-alert.critical {
            background: rgba(244, 63, 94, 0.15);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.35);
        }
        .badge-alert.warning {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }
        .badge-alert.watch {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.35);
        }
        .badge-alert.healthy {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }

        .metric-val-alert {
            font-family: var(--font-mono);
            font-weight: 600;
            color: #f1f5f9;
        }
        .metric-val-alert.breached {
            color: #38bdf8;
            background: rgba(56, 189, 248, 0.1);
            padding: 2px 5px;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        .action-box {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(51, 65, 85, 0.5);
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 11px;
            color: #e2e8f0;
            line-height: 1.4;
        }
        .action-box.watch {
            border-color: rgba(56, 189, 248, 0.35);
            background: rgba(12, 74, 110, 0.15);
            color: #bae6fd;
        }
        .action-box.critical {
            border-color: rgba(244, 63, 94, 0.4);
            background: rgba(136, 19, 55, 0.2);
            color: #fecdd3;
            font-weight: 600;
        }
        .action-box.warning {
            border-color: rgba(245, 158, 11, 0.4);
            background: rgba(120, 53, 15, 0.2);
            color: #fde68a;
        }
        .action-box.healthy {
            border-color: rgba(16, 185, 129, 0.25);
            color: #94a3b8;
        }

        .routing-tag {
            font-size: 10px;
            font-family: var(--font-mono);
            color: var(--text-muted);
            background: #0f1523;
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
        }

        .rules-reference-card {
            background: #0d1322;
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-top: 14px;
        }
        .rules-ref-header {
            padding: 12px 18px;
            font-size: 12px;
            font-weight: 600;
            color: #cbd5e1;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }
        .rules-ref-header:hover {
            color: #fff;
        }
        .rules-ref-content {
            padding: 0 18px 18px;
            border-top: 1px solid var(--border);
        }
        .rules-table-wrap {
            overflow-x: auto;
            margin-top: 12px;
        }
        .rules-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }
        .rules-table th {
            padding: 8px 10px;
            background: #0a0e19;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            text-align: left;
            font-weight: 600;
        }
        .rules-table td {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(30, 41, 59, 0.4);
            color: var(--text-secondary);
        }

        /* Responsive Import Modal & Dropzone */
        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(4, 7, 15, 0.82);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 16px;
            opacity: 0;
            transition: opacity 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .modal-backdrop.active {
            display: flex;
            opacity: 1;
        }

        .modal-card {
            width: 100%;
            max-width: 520px;
            background: #0b0f19;
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.04);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            max-height: 90vh;
            transform: scale(0.96) translateY(8px);
            transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .modal-backdrop.active .modal-card {
            transform: scale(1) translateY(0);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 18px 22px 14px;
            border-bottom: 1px solid rgba(30, 41, 59, 0.6);
            background: rgba(15, 23, 42, 0.3);
        }

        .modal-title-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .modal-title {
            font-size: 15px;
            font-weight: 600;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: -0.2px;
        }

        .modal-title-badge {
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        .modal-subtitle {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.4;
        }

        .modal-close-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 22px;
            line-height: 1;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
            transition: color 0.15s, background 0.15s;
        }

        .modal-close-btn:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }

        .modal-body {
            padding: 20px 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            overflow-y: auto;
        }

        /* Responsive Drop Zone */
        .dropzone {
            border: 2px dashed #334155;
            border-radius: 12px;
            padding: 26px 18px;
            text-align: center;
            cursor: pointer;
            background: rgba(15, 23, 42, 0.35);
            transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .dropzone:hover {
            border-color: #475569;
            background: rgba(15, 23, 42, 0.6);
        }

        .dropzone.dragover {
            border-color: #38bdf8;
            background: rgba(56, 189, 248, 0.08);
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.15);
            transform: scale(1.01);
        }

        .dropzone-prompt {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }

        .dropzone-icon {
            width: 42px;
            height: 42px;
            border-radius: 10px;
            background: rgba(30, 41, 59, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #38bdf8;
            margin-bottom: 2px;
            transition: transform 0.2s;
        }

        .dropzone:hover .dropzone-icon, .dropzone.dragover .dropzone-icon {
            transform: translateY(-2px);
        }

        .dropzone-main-text {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
        }

        .dropzone-main-text span.browse-link {
            color: #38bdf8;
            text-decoration: underline;
            text-underline-offset: 3px;
        }

        .dropzone-hint {
            font-size: 11px;
            color: var(--text-muted);
        }

        /* Selected File Preview Card */
        .file-selected-card {
            display: none;
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 10px;
            padding: 14px 16px;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .file-info-group {
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 0;
        }

        .file-icon-wrap {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .file-text-meta {
            display: flex;
            flex-direction: column;
            gap: 3px;
            min-width: 0;
        }

        .file-name {
            font-size: 13px;
            font-weight: 600;
            color: #fff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 250px;
        }

        .file-sub-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
        }

        .file-size {
            color: var(--text-muted);
        }

        .format-badge {
            padding: 1px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
            background: #1e293b;
            color: var(--text-secondary);
        }

        .format-badge.spend {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .format-badge.catalog {
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        .btn-remove-file {
            background: transparent;
            border: 1px solid #334155;
            color: var(--text-muted);
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 11px;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.15s;
        }

        .btn-remove-file:hover {
            background: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.4);
            color: #f87171;
        }

        /* Guidance Cards */
        .guidance-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .guidance-box {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(30, 41, 59, 0.6);
            border-radius: 8px;
            padding: 10px 12px;
        }

        .guidance-label {
            font-size: 11px;
            font-weight: 600;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }

        .guidance-desc {
            font-size: 11px;
            color: var(--text-muted);
            line-height: 1.35;
        }

        /* Responsive Status & Feedback */
        .import-status-box {
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 12px;
            line-height: 1.45;
            display: none;
            animation: fadeIn 0.15s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .import-status-box.loading {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #38bdf8;
        }

        .import-status-box.error {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
        }

        .import-status-box.success {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #6ee7b7;
        }

        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(56, 189, 248, 0.25);
            border-top-color: #38bdf8;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            display: inline-block;
            vertical-align: middle;
            flex-shrink: 0;
        }

        .modal-footer {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 10px;
            padding: 14px 22px 18px;
            border-top: 1px solid rgba(30, 41, 59, 0.6);
            background: rgba(7, 10, 18, 0.6);
        }

        @media (max-width: 600px) {
            .modal-card {
                width: 95vw;
                max-height: 94vh;
            }
            .guidance-grid {
                grid-template-columns: 1fr;
            }
            .modal-footer {
                flex-direction: column-reverse;
                gap: 8px;
            }
            .modal-footer button {
                width: 100%;
                justify-content: center;
            }
            .file-selected-card {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            .file-info-group {
                width: 100%;
            }
            .file-name {
                max-width: 200px;
            }
            .btn-remove-file {
                align-self: flex-end;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Minimal Top Bar -->
        <header class="top-bar">
            <div class="brand-title">
                Home Cartel <span class="sub">/ Ad Attribution</span>
                <div id="header-alert-pill" class="alert-status-pill watch" onclick="switchToAlertView()" title="Section 2.6.4 Alert Monitor: Click to inspect ads" role="button" tabindex="0">
                    <span class="alert-pulse-dot"></span>
                    <span id="header-alert-text">1 Ad to WATCH</span>
                </div>
            </div>
            <div class="top-actions">
                <button class="btn-action" id="btn-open-import" onclick="openImportModal()" aria-label="Import Meta Ads CSV" title="Import Meta Campaign Spend or Ads Catalog">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 2px;">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="17 8 12 3 7 8"></polyline>
                        <line x1="12" y1="3" x2="12" y2="15"></line>
                    </svg>
                    Import Meta CSV
                </button>
                <button class="btn-action" onclick="fetchClicks(true)" aria-label="Refresh attribution records">
                    Refresh
                </button>
                <button class="btn-action btn-primary" onclick="exportCSV()" aria-label="Export all records as CSV">
                    Export CSV
                </button>
                <a href="https://homecartel.net" target="_blank" rel="noopener noreferrer" class="btn-action" aria-label="Open Home Cartel store">
                    Store &nearr;
                </a>
                <form method="post" action="/logout" style="display:inline;">
                    <button class="btn-action" type="submit" aria-label="Sign out">Sign out</button>
                </form>
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
                <div class="stat-label">Meta Ad Spend</div>
                <div class="stat-value" id="stat-ad-spend" style="color: #f59e0b;">₱0</div>
                <div class="stat-footer" id="stat-ad-spend-footer">Analyzing campaign volume…</div>
            </div>
        </section>

        <!-- Analytics & Reporting Hub (PDF Master Handoff Views 1 to 5) -->
        <section class="analytics-hub" aria-label="Visual Analytics Hub">
            <div class="analytics-nav">
                <div class="analytics-title-wrap">
                    <span class="analytics-title">Executive Analytics Hub</span>
                    <span class="analytics-badge">PDF Handoff Sec 2.5 &amp; 2.6</span>
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
                    <button class="view-btn alert-tab-btn" id="tab-v5" onclick="switchAnalyticsView('v5', this)">
                        Alert Center (Sec 2.6.4) <span class="tab-alert-count" id="tab-alert-badge">1</span>
                    </button>
                </div>
            </div>

            <!-- View 1: Ad Performance (Sec 2.5.2) -->
            <div class="view-panel active" id="panel-v1">
                <div id="v1-alert-banner" class="v1-alert-banner watch" onclick="switchToAlertView()">
                    <div class="v1-alert-banner-left">
                        <span class="alert-pulse-dot"></span>
                        <span class="v1-alert-banner-title">Alert Center Notice:</span>
                        <span id="v1-alert-banner-text">1 Active Campaign flagged in WATCH status (IG - Interests Targeting - VC - Magnetic Track Lights &mdash; Frequency: 2.96x &gt; 2.5)</span>
                    </div>
                    <div class="v1-alert-banner-cta">Inspect Alert SOP &rarr;</div>
                </div>
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

            <!-- View 5: Alert Center (Sec 2.6.4 Master Table & Health Monitor) -->
            <div class="view-panel" id="panel-v5">
                <!-- Executive Alert Summary Grid -->
                <div class="alert-summary-grid">
                    <div class="alert-stat-card critical" onclick="filterAlertsByLevel('CRITICAL', document.getElementById('pill-filter-crit'))">
                        <div class="alert-stat-header">
                            <span class="alert-stat-dot red"></span>
                            <span class="alert-stat-title">CRITICAL ALERTS</span>
                        </div>
                        <div class="alert-stat-num" id="alert-count-critical">0</div>
                        <div class="alert-stat-desc">Pause ad immediately · Rotate creative same day</div>
                    </div>
                    <div class="alert-stat-card warning" onclick="filterAlertsByLevel('WARNING', document.getElementById('pill-filter-warn'))">
                        <div class="alert-stat-header">
                            <span class="alert-stat-dot yellow"></span>
                            <span class="alert-stat-title">WARNING ALERTS</span>
                        </div>
                        <div class="alert-stat-num" id="alert-count-warning">0</div>
                        <div class="alert-stat-desc">Review creative · Plan rotation in 3 days</div>
                    </div>
                    <div class="alert-stat-card watch" onclick="filterAlertsByLevel('WATCH', document.getElementById('pill-filter-watch'))">
                        <div class="alert-stat-header">
                            <span class="alert-stat-dot blue"></span>
                            <span class="alert-stat-title">WATCH ALERTS</span>
                        </div>
                        <div class="alert-stat-num" id="alert-count-watch">1</div>
                        <div class="alert-stat-desc">Monitor closely · Note adset / campaign name</div>
                    </div>
                    <div class="alert-stat-card healthy" onclick="filterAlertsByLevel('HEALTHY', document.getElementById('pill-filter-healthy'))">
                        <div class="alert-stat-header">
                            <span class="alert-stat-dot green"></span>
                            <span class="alert-stat-title">HEALTHY ADS</span>
                        </div>
                        <div class="alert-stat-num" id="alert-count-healthy">7</div>
                        <div class="alert-stat-desc">Optimal delivery · Metrics within safe thresholds</div>
                    </div>
                </div>

                <!-- Alert Filter Toolbar -->
                <div class="alert-toolbar">
                    <div class="alert-filter-pills" role="tablist">
                        <button class="alert-filter-pill active" id="pill-filter-all" onclick="filterAlertsByLevel('ALL', this)">All Evaluated Ads (<span id="pill-all-count">8</span>)</button>
                        <button class="alert-filter-pill" id="pill-filter-crit" onclick="filterAlertsByLevel('CRITICAL', this)">Critical (<span id="pill-crit-count">0</span>)</button>
                        <button class="alert-filter-pill" id="pill-filter-warn" onclick="filterAlertsByLevel('WARNING', this)">Warning (<span id="pill-warn-count">0</span>)</button>
                        <button class="alert-filter-pill" id="pill-filter-watch" onclick="filterAlertsByLevel('WATCH', this)">Watch (<span id="pill-watch-count">1</span>)</button>
                        <button class="alert-filter-pill" id="pill-filter-healthy" onclick="filterAlertsByLevel('HEALTHY', this)">Healthy (<span id="pill-healthy-count">7</span>)</button>
                    </div>
                    <div class="alert-meta-note">
                        <span>Mandatory exclusion filter applied: <code>campaign_name NOT LIKE '%FR Stores%'</code> (PDF Sec 2.6.1)</span>
                    </div>
                </div>

                <!-- Active Evaluations Table -->
                <div class="alert-table-wrap">
                    <table class="alert-table" aria-label="Ad Performance Alert Evaluation Table">
                        <thead>
                            <tr>
                                <th style="width: 100px;">Level</th>
                                <th>Campaign / Performance Ad</th>
                                <th style="width: 150px;">Parameter</th>
                                <th style="width: 100px;">Frequency</th>
                                <th style="width: 90px;">CTR</th>
                                <th style="width: 100px;">CPC</th>
                                <th style="width: 110px;">Spend</th>
                                <th>Required Action (SOP 2.6.4)</th>
                                <th style="width: 160px;">Email Routing</th>
                            </tr>
                        </thead>
                        <tbody id="alert-table-body">
                            <!-- Populated dynamically via JS -->
                        </tbody>
                    </table>
                </div>

                <!-- Section 2.6.4 Reference Configuration Collapsible -->
                <details class="rules-reference-card">
                    <summary class="rules-ref-header">
                        <span>View Complete 11 Alert Rule Configuration Matrix (PDF Section 2.6.4)</span>
                        <span class="rules-toggle-icon">&darr;</span>
                    </summary>
                    <div class="rules-ref-content">
                        <div class="rules-table-wrap">
                            <table class="rules-table">
                                <thead>
                                    <tr>
                                        <th style="width: 80px;">Level</th>
                                        <th style="width: 150px;">Parameter</th>
                                        <th>Trigger Condition</th>
                                        <th>Required Action</th>
                                        <th style="width: 110px;">Data Source</th>
                                        <th style="width: 170px;">Recipients Routing</th>
                                    </tr>
                                </thead>
                                <tbody id="rules-ref-body">
                                    <!-- Populated with all 11 exact rules from Section 2.6.4 -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </details>
            </div>
        </section>

        <!-- Ad Health Monitor (PDF Sec 2.5.2 & 2.6) -->
        <section class="health-hub" id="adHealthHub" aria-label="Ad Health Monitor">
            <div class="analytics-nav">
                <div class="analytics-title-wrap">
                    <span class="analytics-title">Ad Health Monitor</span>
                    <span class="analytics-badge">PDF Sec 2.5.2 &amp; 2.6</span>
                </div>
                <span class="health-updated" id="health-updated" title="This view reads the campaign-level Meta CSV import, not the Meta API">Awaiting data&hellip;</span>
            </div>

            <div class="health-kpis">
                <div class="health-kpi">
                    <div class="health-kpi-label">Overall status</div>
                    <div class="health-kpi-value" id="health-kpi-status"><span class="badge-alert healthy">&mdash;</span></div>
                    <div class="health-kpi-sub" id="health-kpi-status-sub">No campaigns evaluated yet</div>
                </div>
                <div class="health-kpi">
                    <div class="health-kpi-label">Campaigns needing attention</div>
                    <div class="health-kpi-value" id="health-kpi-attn">0 / 0</div>
                    <div class="health-kpi-sub" id="health-kpi-attn-sub">Critical + Warning + Watch</div>
                </div>
                <div class="health-kpi">
                    <div class="health-kpi-label">Spend at risk</div>
                    <div class="health-kpi-value" id="health-kpi-risk">&#8369;0</div>
                    <div class="health-kpi-sub" id="health-kpi-risk-sub">0% of evaluated spend</div>
                </div>
                <div class="health-kpi">
                    <div class="health-kpi-label">Portfolio frequency</div>
                    <div class="health-kpi-value" id="health-kpi-freq">&mdash;</div>
                    <div class="health-kpi-sub">Impressions &divide; reach &middot; Watch above 2.5&times;</div>
                </div>
            </div>

            <div class="health-empty" id="health-empty" hidden>
                No active campaigns to evaluate. Import Meta Ads data to start monitoring (FR Stores Reach campaigns are excluded per PDF Sec 2.6.1).
            </div>

            <div class="health-charts" id="health-charts">
                <div class="chart-box">
                    <div class="chart-box-header">
                        <div>
                            <div class="chart-box-title">Audience Saturation &mdash; Frequency</div>
                            <div class="chart-box-sub">Watch &gt; 2.5 &middot; Warning &gt; 3.5 &middot; Critical &gt; 4.5</div>
                        </div>
                    </div>
                    <div class="chart-canvas-wrap health-canvas"><canvas id="chartHealthFreq" role="img" aria-label="Frequency by campaign against alert thresholds"></canvas></div>
                </div>
                <div class="chart-box">
                    <div class="chart-box-header">
                        <div>
                            <div class="chart-box-title">Underperforming Ads &mdash; Link CTR (%)</div>
                            <div class="chart-box-sub">Lowest first &middot; Warning &lt; 0.67% &middot; Critical &lt; 0.43%</div>
                        </div>
                    </div>
                    <div class="chart-canvas-wrap health-canvas"><canvas id="chartHealthCtr" role="img" aria-label="Link CTR by campaign against alert thresholds"></canvas></div>
                </div>
                <div class="chart-box">
                    <div class="chart-box-header">
                        <div>
                            <div class="chart-box-title">Cost per Link Click (PHP) &mdash; reference only</div>
                            <div class="chart-box-sub">Highest first &middot; no fixed alert line: Expensive Ads fires on +30% / +50% vs an ad&rsquo;s own 30-day average</div>
                        </div>
                    </div>
                    <div class="chart-canvas-wrap health-canvas"><canvas id="chartHealthCpc" role="img" aria-label="Cost per link click by campaign against alert thresholds"></canvas></div>
                </div>
            </div>

            <div class="health-attention">
                <div class="health-attention-title">Needs attention <span class="health-attention-hint">Click a row to open the Alert Center</span></div>
                <div id="health-attention-list"></div>
            </div>

            <details class="health-coverage">
                <summary>PDF checks not yet monitored (6)</summary>
                <ul>
                    <li><strong>Creative Fatigue</strong> &mdash; CTR vs prior 7 days per ad (Query Table A)</li>
                    <li><strong>Expensive Ads vs own average</strong> &mdash; CPC vs the ad&rsquo;s 30-day average (Query Table B); CPC is shown for reference only and raises no alert here</li>
                    <li><strong>Delivery Problem</strong> &mdash; impressions &minus;25% WoW while spend falls &lt;10% (Query Table C)</li>
                    <li><strong>CTR / CPC 30-day trend lines</strong> (Sec 2.5.2)</li>
                    <li><strong>Top 10 / Bottom 10 ads by CTR</strong> (Sec 2.5.2); this view is campaign-level</li>
                    <li><strong>Adset-level frequency</strong> &mdash; frequency here is campaign impressions &divide; reach</li>
                </ul>
                <p>These need daily ad / adset data. The current source is the campaign-level Meta CSV import; connect the Meta Insights API (ads_read) to enable them.</p>
            </details>
        </section>
    </div>

    <!-- Responsive Meta Ads CSV/TSV Import Modal -->
    <div class="modal-backdrop" id="importModal" role="dialog" aria-modal="true" aria-labelledby="modalTitle" onclick="handleBackdropClick(event)">
        <div class="modal-card">
            <div class="modal-header">
                <div class="modal-title-group">
                    <div class="modal-title" id="modalTitle">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #38bdf8;">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        Import Meta Ads Data
                        <span class="modal-title-badge">Live Sync</span>
                    </div>
                    <div class="modal-subtitle">
                        Direct ingestion for Meta Campaign Spend Reports &amp; Ads Manager Bulk Exports.
                    </div>
                </div>
                <button class="modal-close-btn" onclick="closeImportModal()" aria-label="Close dialog">&times;</button>
            </div>

            <div class="modal-body">
                <!-- Interactive Drag & Drop Zone -->
                <div class="dropzone" id="dropZone" onclick="triggerFileInput()">
                    <input type="file" id="metaFileInput" accept=".csv,.tsv,.txt" style="display: none;" onchange="handleFileSelect(this.files)">
                    
                    <div class="dropzone-prompt" id="dropZonePrompt">
                        <div class="dropzone-icon">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"></path>
                                <path d="M12 12v9"></path>
                                <path d="m16 16-4-4-4 4"></path>
                            </svg>
                        </div>
                        <div class="dropzone-main-text">
                            Drag &amp; drop Meta export here, or <span class="browse-link">browse</span>
                        </div>
                        <div class="dropzone-hint">
                            Accepts .csv or .tsv exported from Meta Ads Manager (up to 50MB)
                        </div>
                    </div>

                    <!-- Selected File Preview Card -->
                    <div class="file-selected-card" id="fileSelectedCard" onclick="event.stopPropagation()">
                        <div class="file-info-group">
                            <div class="file-icon-wrap">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                                    <polyline points="14 2 14 8 20 8"></polyline>
                                    <line x1="16" y1="13" x2="8" y2="13"></line>
                                    <line x1="16" y1="17" x2="8" y2="17"></line>
                                </svg>
                            </div>
                            <div class="file-text-meta">
                                <div class="file-name" id="fileCardName">filename.csv</div>
                                <div class="file-sub-meta">
                                    <span class="file-size" id="fileCardSize">0 KB</span>
                                    <span class="format-badge" id="fileCardBadge">Auto-Detect on Upload</span>
                                </div>
                            </div>
                        </div>
                        <button class="btn-remove-file" onclick="clearSelectedFile(event)" type="button" aria-label="Change file">
                            Change File
                        </button>
                    </div>
                </div>

                <!-- Guidance Cards for Auto-Detection -->
                <div class="guidance-grid">
                    <div class="guidance-box">
                        <div class="guidance-label">
                            <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#34d399;"></span>
                            Spend &amp; Performance
                        </div>
                        <div class="guidance-desc">
                            Table export with Amount Spent, CPC, CTR, Impressions &amp; Link Clicks. Updates Views 1, 4 &amp; Alert Center.
                        </div>
                    </div>
                    <div class="guidance-box">
                        <div class="guidance-label">
                            <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:#c084fc;"></span>
                            Ads Bulk Catalog
                        </div>
                        <div class="guidance-desc">
                            Ads Manager export with Campaign ID, Ad Set ID, Ad ID &amp; Post Headlines. Powers ad creative attribution.
                        </div>
                    </div>
                </div>

                <!-- Dynamic Real-Time Status / Feedback Banner -->
                <div class="import-status-box" id="importStatusBox">
                    <div id="importStatusContent"></div>
                </div>
            </div>

            <div class="modal-footer">
                <button class="btn-action" id="btn-cancel-import" onclick="closeImportModal()" type="button">
                    Cancel
                </button>
                <button class="btn-action btn-primary" id="btn-submit-upload" onclick="submitMetaImport()" type="button" disabled>
                    Upload &amp; Sync Dashboard
                </button>
            </div>
        </div>
    </div>

    <!-- Ad health pop-up: Critical / Warning campaigns on load and after a CSV import -->
    <div class="health-modal-backdrop" id="healthModal" role="dialog" aria-modal="true" aria-labelledby="healthModalTitle" hidden onclick="if (event.target === this) closeHealthModal()">
        <div class="health-modal-card">
            <div class="health-modal-head">
                <div>
                    <div class="health-modal-title" id="healthModalTitle">Ad health alert</div>
                    <div class="health-modal-sub" id="healthModalSub"></div>
                </div>
                <button type="button" class="modal-close-btn" onclick="closeHealthModal()" aria-label="Close alert pop-up">&times;</button>
            </div>
            <div class="health-modal-body" id="healthModalBody"></div>
            <div class="health-modal-foot">
                <button type="button" class="btn-action" id="healthModalDismiss" onclick="closeHealthModal()">Dismiss</button>
                <button type="button" class="btn-action btn-primary" onclick="closeHealthModal(); switchToAlertView()">Open Alert Center</button>
            </div>
        </div>
    </div>

    <!-- Global Toast Alert -->
    <div class="toast" id="toast" role="status" aria-live="polite">
        <span id="toast-msg">Copied to clipboard</span>
    </div>

    <script>
        let allClicks = [];
        let selectedMetaFile = null;

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeHealthModal();
                closeImportModal();
            }
        });

        // Import Modal & Drag-Drop Handlers
        function openImportModal() {
            const modal = document.getElementById('importModal');
            if (!modal) return;
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            hideImportStatus();
        }

        function closeImportModal() {
            const modal = document.getElementById('importModal');
            if (!modal) return;
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }

        function handleBackdropClick(e) {
            if (e.target && e.target.id === 'importModal') {
                closeImportModal();
            }
        }

        function triggerFileInput() {
            const input = document.getElementById('metaFileInput');
            if (input) input.click();
        }

        function clearSelectedFile(e) {
            if (e) e.stopPropagation();
            selectedMetaFile = null;
            const input = document.getElementById('metaFileInput');
            if (input) input.value = '';
            document.getElementById('dropZonePrompt').style.display = 'flex';
            document.getElementById('fileSelectedCard').style.display = 'none';
            document.getElementById('btn-submit-upload').disabled = true;
            hideImportStatus();
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        function handleFileSelect(files) {
            if (!files || files.length === 0) return;
            const file = files[0];
            selectedMetaFile = file;

            document.getElementById('fileCardName').innerText = file.name;
            document.getElementById('fileCardSize').innerText = formatBytes(file.size);

            const badge = document.getElementById('fileCardBadge');
            badge.innerText = 'Detecting format…';
            badge.className = 'format-badge';

            // Client-side quick inspection of the first 2KB for responsive preview
            const reader = new FileReader();
            reader.onload = function(evt) {
                const sample = (evt.target.result || '').toLowerCase();
                const isSpend = sample.includes('amount spent') || sample.includes('link clicks') || sample.includes('impressions');
                const isCatalog = sample.includes('campaign id') || sample.includes('ad id') || sample.includes('ad set id') || sample.includes('headline');

                if (isSpend) {
                    badge.innerText = 'Spend & Performance Report';
                    badge.className = 'format-badge spend';
                } else if (isCatalog) {
                    badge.innerText = 'Ads Manager Bulk Catalog';
                    badge.className = 'format-badge catalog';
                } else {
                    badge.innerText = 'Auto-Detect on Upload';
                    badge.className = 'format-badge';
                }
            };
            reader.onerror = function() {
                badge.innerText = 'Auto-Detect on Upload';
                badge.className = 'format-badge';
            };
            reader.readAsText(file.slice(0, 2048));

            document.getElementById('dropZonePrompt').style.display = 'none';
            document.getElementById('fileSelectedCard').style.display = 'flex';
            document.getElementById('btn-submit-upload').disabled = false;
            hideImportStatus();
        }

        function showImportLoading(msg) {
            const box = document.getElementById('importStatusBox');
            const content = document.getElementById('importStatusContent');
            box.className = 'import-status-box loading';
            content.innerHTML = `<span class="spinner"></span> <span>${msg}</span>`;
            box.style.display = 'flex';
        }

        function showImportError(msg) {
            const box = document.getElementById('importStatusBox');
            const content = document.getElementById('importStatusContent');
            box.className = 'import-status-box error';
            content.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:1px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> <div><strong>Import failed:</strong> ${msg}</div>`;
            box.style.display = 'flex';
        }

        function showImportSuccess(msg, details = '') {
            const box = document.getElementById('importStatusBox');
            const content = document.getElementById('importStatusContent');
            box.className = 'import-status-box success';
            content.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:1px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> <div><strong>Success:</strong> ${msg} ${details ? `<div style="margin-top:2px;font-size:11px;opacity:0.9;">${details}</div>` : ''}</div>`;
            box.style.display = 'flex';
        }

        function hideImportStatus() {
            const box = document.getElementById('importStatusBox');
            if (box) box.style.display = 'none';
        }

        async function submitMetaImport() {
            if (!selectedMetaFile) {
                showImportError('Please choose a CSV or TSV file to import.');
                return;
            }

            const btnSubmit = document.getElementById('btn-submit-upload');
            const btnCancel = document.getElementById('btn-cancel-import');
            btnSubmit.disabled = true;
            btnCancel.disabled = true;
            btnSubmit.innerHTML = '<span class="spinner"></span> Syncing Meta Data…';

            showImportLoading('Uploading and parsing Meta Ads records in memory…');

            const formData = new FormData();
            formData.append('file', selectedMetaFile);

            try {
                const response = await fetch('/api/upload-meta-csv', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || data.message || 'Import failed with server error.');
                }

                const detailsText = data.type === 'campaign_spend'
                    ? `Total Spend: ₱${Number(data.total_spend || 0).toLocaleString()} · Section 2.6.4 Status: ${data.overall_status || 'HEALTHY'}`
                    : `Catalog Records: ${data.rows_processed || 0}`;

                showImportSuccess(data.message, detailsText);
                showToast(data.message || 'Meta data synced successfully!');

                // Instantly re-fetch and re-render all dashboard KPIs, charts, and alerts!
                // The import pop-up replaces the on-load one for this refresh.
                healthPopupSuppress = true;
                const refreshed = fetchClicks(true);

                setTimeout(async () => {
                    closeImportModal();
                    clearSelectedFile();
                    btnSubmit.innerHTML = 'Upload &amp; Sync Dashboard';
                    btnSubmit.disabled = false;
                    btnCancel.disabled = false;
                    await refreshed;
                    healthPopupSuppress = false;
                    if (data.type === 'campaign_spend') showImportAlerts(data);
                }, 1300);

            } catch (err) {
                showImportError(err.message || 'Network error while uploading file.');
                btnSubmit.innerHTML = 'Upload &amp; Sync Dashboard';
                btnSubmit.disabled = false;
                btnCancel.disabled = false;
            }
        }

        // Setup drag and drop events on document load
        window.addEventListener('DOMContentLoaded', () => {
            const dropZone = document.getElementById('dropZone');
            if (!dropZone) return;

            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropZone.classList.add('dragover');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropZone.classList.remove('dragover');
                }, false);
            });

            dropZone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                if (dt && dt.files && dt.files.length > 0) {
                    handleFileSelect(dt.files);
                }
            }, false);
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

        async function fetchClicks(isManual = false) {
            try {
                const res = await fetch('/api/clicks');
                if (res.status === 401) { window.location.href = '/login'; return; }
                const data = await res.json();
                allClicks = data.clicks || [];

                const total = data.total_clicks || allClicks.length;
                document.getElementById('stat-total').innerText = total;

                // Funnel Metrics
                const totalInquiries = data.total_inquiries || allClicks.filter(c => c.zendesk_ticket_id).length;
                const totalQuotes = data.total_quotes || allClicks.filter(c => c.rfq_detected || c.zoho_estimate_num).length;
                const totalOrders = data.total_orders || allClicks.filter(c => c.conversion_total || c.sales_amount || c.zoho_salesorder_id).length;
                const totalRev = Number(data.total_revenue || 0);

                document.getElementById('stat-inquiries').innerText = totalInquiries;
                document.getElementById('stat-quotes').innerText = totalQuotes;

                // Meta Ad Spend & Campaign Volume
                const adSpend = Math.round(Number(data.total_ad_spend || 0));
                if (document.getElementById('stat-ad-spend')) {
                    document.getElementById('stat-ad-spend').innerText = '₱' + adSpend.toLocaleString();
                }
                const adSpendFooter = document.getElementById('stat-ad-spend-footer');
                if (adSpendFooter) {
                    const impr = Number(data.total_ad_impressions || 0).toLocaleString();
                    const clicks = Number(data.total_ad_link_clicks || 0).toLocaleString();
                    adSpendFooter.innerText = `${impr} impressions · ${clicks} link clicks`;
                }

                const fbClicks = allClicks.filter(c => (c.channel || '').toLowerCase().includes('facebook'));
                const igClicks = allClicks.filter(c => (c.channel || '').toLowerCase().includes('instagram'));

                document.getElementById('stat-ig-val').innerText = igClicks.length;
                document.getElementById('stat-fb-val').innerText = fbClicks.length;

                if (total > 0) {
                    const igPercent = Math.round((igClicks.length / total) * 100);
                    const fbPercent = 100 - igPercent;
                    document.getElementById('split-bar-ig').style.width = igPercent + '%';
                    document.getElementById('split-bar-fb').style.width = fbPercent + '%';
                    document.getElementById('stat-ratio-text').innerText = `${igPercent}% Instagram · ${fbPercent}% Facebook`;
                }

                renderAnalyticsCharts(data);
                renderAdHealth(data.alerts_summary);
                if (data.alerts_summary) {
                    renderAlertCenter(data.alerts_summary);
                }

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

        let currentAlertFilter = 'ALL';
        let allAlertEvaluations = [];
        let allAlertRules = [];

        function switchToAlertView() {
            const tab = document.getElementById('tab-v5');
            switchAnalyticsView('v5', tab);
            const hub = document.querySelector('.analytics-hub');
            if (hub) hub.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function filterAlertsByLevel(level, btn) {
            currentAlertFilter = level;
            document.querySelectorAll('.alert-filter-pill').forEach(p => p.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderAlertTableRows();
        }

        // --- Ad Health Monitor (PDF Sec 2.5.2 & 2.6): threshold-aware campaign charts ---
        let chartHealthFreq = null;
        let chartHealthCtr = null;
        let chartHealthCpc = null;
        let lastHealthSig = '';

        const HEALTH_COLORS = { critical: '#f43f5e', warning: '#f59e0b', watch: '#38bdf8', healthy: '#10b981' };

        const healthThresholdPlugin = {
            id: 'healthThresholdLines',
            afterDatasetsDraw(chart, args, opts) {
                const lines = (opts && opts.lines) || [];
                const xScale = chart.scales.x;
                const area = chart.chartArea;
                const ctx = chart.ctx;
                lines.forEach(l => {
                    const px = xScale.getPixelForValue(l.value);
                    if (px < area.left || px > area.right) return;
                    ctx.save();
                    ctx.beginPath();
                    ctx.setLineDash([5, 4]);
                    ctx.lineWidth = 1.25;
                    ctx.strokeStyle = l.color;
                    ctx.moveTo(px, area.top);
                    ctx.lineTo(px, area.bottom);
                    ctx.stroke();
                    ctx.setLineDash([]);
                    ctx.fillStyle = l.color;
                    ctx.font = "600 9px 'JetBrains Mono', monospace";
                    ctx.textAlign = l.align || 'center';
                    ctx.fillText(l.label, px, area.top - 4);
                    ctx.restore();
                });
            }
        };

        function healthEsc(s) {
            return String(s == null ? '' : s).replace(/[&<>"']/g, ch => (
                { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]
            ));
        }

        // Two-line axis label (campaign names share long prefixes, so keep the distinguishing tail)
        function healthShortName(name) {
            const n = String(name || 'Unknown');
            const max = 30;
            if (n.length <= max) return n;
            let cut = n.lastIndexOf(' ', max);
            if (cut < 10) cut = max;
            const first = n.slice(0, cut).trim();
            const rest = n.slice(cut).trim();
            return [first, rest.length > max ? '…' + rest.slice(rest.length - (max - 1)) : rest];
        }

        function buildHealthChart(canvasId, prev, items, cfg) {
            if (prev) prev.destroy();
            const canvas = document.getElementById(canvasId);
            if (!canvas || items.length === 0) return null;
            const maxVal = Math.max(0, ...items.map(i => i.value), ...cfg.lines.map(l => l.value));
            return new Chart(canvas.getContext('2d'), {
                type: 'bar',
                plugins: [healthThresholdPlugin],
                data: {
                    labels: items.map(i => healthShortName(i.name)),
                    datasets: [{
                        data: items.map(i => i.value),
                        backgroundColor: items.map(i => cfg.color(i.value)),
                        borderRadius: 4,
                        barThickness: 12
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: { padding: { top: 14, right: 10 } },
                    scales: {
                        x: { beginAtZero: true, suggestedMax: maxVal * 1.1, ticks: { callback: v => cfg.tick(v) } },
                        y: { grid: { display: false }, ticks: { font: { size: 10 } } }
                    },
                    plugins: {
                        legend: { display: false },
                        healthThresholdLines: { lines: cfg.lines },
                        tooltip: {
                            callbacks: {
                                title: ctxs => items[ctxs[0].dataIndex].name,
                                label: c => ' ' + cfg.label(items[c.dataIndex].value)
                            }
                        }
                    }
                }
            });
        }

        function renderAdHealth(summary) {
            const hub = document.getElementById('adHealthHub');
            if (!hub || typeof Chart === 'undefined') return;

            const evals = (summary && summary.evaluations) || [];
            const th = (summary && summary.thresholds) || {};
            const sig = JSON.stringify([evals.map(e => [e.campaign_name, e.level, e.frequency, e.ctr, e.cpc, e.spend]), th]);
            if (sig === lastHealthSig) return;
            lastHealthSig = sig;

            const counts = (summary && summary.counts) || { critical: 0, warning: 0, watch: 0, healthy: 0, total: 0 };
            const overall = (summary && summary.overall_status) || 'HEALTHY';
            const total = counts.total || evals.length;
            const attn = (counts.critical || 0) + (counts.warning || 0) + (counts.watch || 0);

            const atRisk = evals.filter(e => e.level !== 'HEALTHY').reduce((s, e) => s + Number(e.spend || 0), 0);
            const totalSpend = evals.reduce((s, e) => s + Number(e.spend || 0), 0);
            const sumImp = evals.reduce((s, e) => s + Number(e.impressions || 0), 0);
            const sumReach = evals.reduce((s, e) => s + Number(e.reach || 0), 0);
            const portfolioFreq = sumReach > 0 ? sumImp / sumReach : null;

            const lvlClass = overall.toLowerCase();
            document.getElementById('health-kpi-status').innerHTML =
                `<span class="badge-alert ${healthEsc(lvlClass)}">${healthEsc(overall)}</span>`;
            document.getElementById('health-kpi-status-sub').innerText = total
                ? `${counts.critical || 0} critical · ${counts.warning || 0} warning · ${counts.watch || 0} watch · ${counts.healthy || 0} healthy`
                : 'No campaigns evaluated yet';
            document.getElementById('health-kpi-attn').innerText = `${attn} / ${total}`;
            document.getElementById('health-kpi-risk').innerText = '₱' + Math.round(atRisk).toLocaleString();
            document.getElementById('health-kpi-risk-sub').innerText =
                `${totalSpend > 0 ? Math.round((atRisk / totalSpend) * 100) : 0}% of evaluated spend`;
            const freqEl = document.getElementById('health-kpi-freq');
            freqEl.innerText = portfolioFreq === null ? '—' : portfolioFreq.toFixed(2) + '×';
            const freqWatch = th.frequency ? th.frequency.watch : null;
            freqEl.style.color = (portfolioFreq !== null && freqWatch !== null && portfolioFreq > freqWatch) ? HEALTH_COLORS.watch : '#fff';

            const stamp = document.getElementById('health-updated');
            if (summary && summary.data_as_of) {
                const w = summary.window || {};
                stamp.innerText = `CSV import · data as of ${summary.data_as_of}` + (w.start && w.end ? ` · window ${w.start} to ${w.end}` : '');
            } else {
                stamp.innerText = 'CSV import · no data imported yet';
            }

            const empty = document.getElementById('health-empty');
            const chartsWrap = document.getElementById('health-charts');
            empty.hidden = evals.length > 0;
            chartsWrap.hidden = evals.length === 0;

            const fq = th.frequency || {};
            const ct = th.ctr || {};
            const top10 = arr => arr.slice(0, 10);
            const rows = evals.map(e => ({ name: e.campaign_name, freq: Number(e.frequency || 0), ctr: Number(e.ctr || 0), cpc: Number(e.cpc || 0) }));

            chartHealthFreq = buildHealthChart('chartHealthFreq', chartHealthFreq,
                top10(rows.slice().sort((a, b) => b.freq - a.freq)).map(r => ({ name: r.name, value: r.freq })), {
                    lines: [
                        { value: fq.watch, color: HEALTH_COLORS.watch, label: String(fq.watch) },
                        { value: fq.warning, color: HEALTH_COLORS.warning, label: String(fq.warning) },
                        { value: fq.critical, color: HEALTH_COLORS.critical, label: String(fq.critical) }
                    ].filter(l => l.value != null),
                    color: v => v > fq.critical ? HEALTH_COLORS.critical : v > fq.warning ? HEALTH_COLORS.warning : v > fq.watch ? HEALTH_COLORS.watch : HEALTH_COLORS.healthy,
                    tick: v => v + '×',
                    label: v => 'Frequency: ' + v.toFixed(2) + '×'
                });

            chartHealthCtr = buildHealthChart('chartHealthCtr', chartHealthCtr,
                top10(rows.slice().sort((a, b) => a.ctr - b.ctr)).map(r => ({ name: r.name, value: r.ctr })), {
                    lines: [
                        { value: ct.warning, color: HEALTH_COLORS.warning, label: ct.warning + '%', align: 'left' },
                        { value: ct.critical, color: HEALTH_COLORS.critical, label: ct.critical + '%', align: 'right' }
                    ].filter(l => l.value != null),
                    color: v => v < ct.critical ? HEALTH_COLORS.critical : v < ct.warning ? HEALTH_COLORS.warning : HEALTH_COLORS.healthy,
                    tick: v => v + '%',
                    label: v => 'Link CTR: ' + v.toFixed(2) + '%'
                });

            chartHealthCpc = buildHealthChart('chartHealthCpc', chartHealthCpc,
                top10(rows.slice().sort((a, b) => b.cpc - a.cpc)).map(r => ({ name: r.name, value: r.cpc })), {
                    lines: [],
                    color: () => HEALTH_COLORS.watch,
                    tick: v => '₱' + v,
                    label: v => 'CPC: ₱' + v.toFixed(2)
                });

            // Needs-attention list, most severe first
            const rank = { CRITICAL: 0, WARNING: 1, WATCH: 2 };
            const flagged = evals
                .filter(e => e.level in rank)
                .sort((a, b) => rank[a.level] - rank[b.level] || Number(b.spend || 0) - Number(a.spend || 0));
            const list = document.getElementById('health-attention-list');
            if (evals.length === 0) {
                list.innerHTML = '';
            } else if (flagged.length === 0) {
                list.innerHTML = '<div class="health-attn-ok">All campaigns are inside the safe thresholds.</div>';
            } else {
                list.innerHTML = flagged.map(e => {
                    const cls = e.level.toLowerCase();
                    const sop = e.sop && e.sop.steps && e.sop.steps.length
                        ? `<details class="health-sop"><summary>What to do &mdash; ${healthEsc(e.sop.title)}</summary><ol>${e.sop.steps.map(s => `<li>${healthEsc(s)}</li>`).join('')}</ol></details>`
                        : '';
                    return `
                      <div class="health-attn">
                        <button type="button" class="health-attn-row" onclick="switchToAlertView()">
                            <span class="badge-alert ${cls}">${healthEsc(e.level)}</span>
                            <div>
                                <div class="health-attn-name" title="${healthEsc(e.campaign_name)}">${healthEsc(e.campaign_name)}</div>
                                <div class="health-attn-metrics">${healthEsc(e.primary_parameter)} · Freq ${Number(e.frequency || 0).toFixed(2)}× · CTR ${Number(e.ctr || 0).toFixed(2)}% · CPC ₱${Number(e.cpc || 0).toFixed(2)} · ₱${Math.round(e.spend || 0).toLocaleString()}</div>
                            </div>
                            <div class="action-box ${cls}">${healthEsc(e.primary_action)}</div>
                        </button>
                        ${sop}
                      </div>`;
                }).join('');
            }

            maybeShowHealthPopupOnLoad(evals);
        }

        // --- Ad health pop-up (Critical / Warning) ---
        let healthPopupSuppress = false;
        let healthModalOpener = null;

        function openHealthModal(title, sub, items, note, noteIsWarning) {
            const modal = document.getElementById('healthModal');
            if (!modal || !items.length) return;
            document.getElementById('healthModalTitle').innerText = title;
            document.getElementById('healthModalSub').innerText = sub;
            document.getElementById('healthModalBody').innerHTML = items.map(i => {
                const cls = String(i.level || '').toLowerCase();
                const sop = i.sop && i.sop.steps && i.sop.steps.length
                    ? `<details class="health-sop" style="margin:8px 0 0 0;"><summary>What to do &mdash; ${healthEsc(i.sop.title)}</summary><ol>${i.sop.steps.map(s => `<li>${healthEsc(s)}</li>`).join('')}</ol></details>`
                    : '';
                return `
                    <div class="health-modal-item">
                        <span class="badge-alert ${healthEsc(cls)}">${healthEsc(i.level)}</span>
                        <div class="health-modal-item-name">${healthEsc(i.name)}</div>
                        <div class="health-modal-item-metrics">${healthEsc(i.metrics)}</div>
                        <div class="action-box ${healthEsc(cls)}">${healthEsc(i.action)}</div>
                        ${sop}
                    </div>`;
            }).join('') + (note ? `<div class="health-modal-note ${noteIsWarning ? 'warn' : ''}">${healthEsc(note)}</div>` : '');
            healthModalOpener = document.activeElement;
            modal.hidden = false;
            const dismiss = document.getElementById('healthModalDismiss');
            if (dismiss) dismiss.focus();
        }

        function closeHealthModal() {
            const modal = document.getElementById('healthModal');
            if (!modal || modal.hidden) return;
            modal.hidden = true;
            if (healthModalOpener && healthModalOpener.focus) healthModalOpener.focus();
        }

        function maybeShowHealthPopupOnLoad(evals) {
            const sevRank = { CRITICAL: 0, WARNING: 1 };
            const flagged = evals.filter(e => e.level in sevRank)
                .sort((a, b) => sevRank[a.level] - sevRank[b.level]);
            if (!flagged.length) return;
            if (healthPopupSuppress) return;
            const key = flagged.map(e => e.campaign_name + ':' + e.level).sort().join('|');
            try {
                if (sessionStorage.getItem('hc_health_popup') === key) return;
                sessionStorage.setItem('hc_health_popup', key);
            } catch (err) { /* storage blocked: show it every load */ }
            const crit = flagged.filter(e => e.level === 'CRITICAL').length;
            openHealthModal(
                crit ? `${crit} campaign${crit > 1 ? 's' : ''} in CRITICAL status` : `${flagged.length} campaign${flagged.length > 1 ? 's' : ''} need review`,
                'Current Meta CSV data \u00B7 FR Stores Reach campaigns excluded',
                flagged.map(e => ({
                    level: e.level,
                    name: e.campaign_name,
                    metrics: `${e.primary_parameter} \u00B7 Freq ${Number(e.frequency || 0).toFixed(2)}\u00D7 \u00B7 CTR ${Number(e.ctr || 0).toFixed(2)}% \u00B7 \u20B1${Math.round(e.spend || 0).toLocaleString()}`,
                    action: e.primary_action,
                    sop: e.sop
                }))
            );
        }

        // After a CSV import: pop up Critical / Warning changes, toast the Watch ones.
        function showImportAlerts(data) {
            const alerts = data.new_alerts || [];
            if (!alerts.length) return;
            const urgent = alerts.filter(a => a.level === 'CRITICAL' || a.level === 'WARNING')
                .sort((a, b) => (a.level === 'CRITICAL' ? 0 : 1) - (b.level === 'CRITICAL' ? 0 : 1));
            const watch = alerts.filter(a => a.level === 'WATCH');
            if (watch.length) {
                showToast(`${watch.length} campaign${watch.length > 1 ? 's' : ''} flagged WATCH: ${watch.map(a => a.campaign_name).join(', ')}`);
            }
            if (!urgent.length) return;
            const byStatus = s => alerts.filter(a => a.email_status === s).length;
            let note = '';
            let warn = false;
            if (byStatus('sent') === alerts.length) {
                note = `Email sent for ${alerts.length} alert${alerts.length > 1 ? 's' : ''}.`;
            } else if (byStatus('skipped')) {
                note = 'Email not sent: no recipients configured (set ALERT_RECIPIENTS and the SMTP_* settings).';
                warn = true;
            } else if (byStatus('failed')) {
                const f = alerts.find(a => a.email_status === 'failed');
                note = 'Email failed: ' + (f && f.email_detail ? f.email_detail : 'see server log') + '.';
                warn = true;
            } else if (byStatus('sent')) {
                note = `Email sent for ${byStatus('sent')} of ${alerts.length} alerts.`;
                warn = true;
            }
            openHealthModal(
                `${urgent.length} campaign${urgent.length > 1 ? 's' : ''} newly flagged after import`,
                'New or escalated since the last import',
                urgent.map(a => ({
                    level: a.level,
                    name: a.campaign_name,
                    metrics: `${a.parameter} \u00B7 ${a.metric_name} ${a.metric_value} (threshold ${a.threshold}) \u00B7 was ${a.previous_level}`,
                    action: a.required_action,
                    sop: a.sop
                })),
                note,
                warn
            );
        }

        function renderAlertCenter(summary) {
            if (!summary) return;
            allAlertEvaluations = summary.evaluations || [];
            allAlertRules = summary.rules_reference || [];
            const counts = summary.counts || { critical: 0, warning: 0, watch: 0, healthy: 0, total: 0 };
            const overall = summary.overall_status || 'HEALTHY';

            // 1. Header Alert Pill
            const headerPill = document.getElementById('header-alert-pill');
            const headerText = document.getElementById('header-alert-text');
            if (headerPill && headerText) {
                headerPill.className = 'alert-status-pill ' + overall.toLowerCase();
                if (overall === 'CRITICAL') {
                    headerText.innerText = `${counts.critical} CRITICAL ALERT${counts.critical > 1 ? 'S' : ''}`;
                } else if (overall === 'WARNING') {
                    headerText.innerText = `${counts.warning} WARNING ALERT${counts.warning > 1 ? 'S' : ''}`;
                } else if (overall === 'WATCH') {
                    headerText.innerText = `${counts.watch} Ad to WATCH`;
                } else {
                    headerText.innerText = 'All Ads Healthy';
                }
            }

            // 2. Tab Badge
            const tabBadge = document.getElementById('tab-alert-badge');
            if (tabBadge) {
                const totalAlerts = (counts.critical || 0) + (counts.warning || 0) + (counts.watch || 0);
                tabBadge.innerText = totalAlerts;
                tabBadge.style.background = counts.critical > 0 ? '#f43f5e' : (counts.warning > 0 ? '#f59e0b' : '#0284c7');
            }

            // 3. View 1 Notice Banner
            const v1Banner = document.getElementById('v1-alert-banner');
            const v1Text = document.getElementById('v1-alert-banner-text');
            if (v1Banner && v1Text) {
                v1Banner.className = 'v1-alert-banner ' + overall.toLowerCase();
                if (counts.critical > 0) {
                    v1Text.innerHTML = `<strong>CRITICAL:</strong> ${counts.critical} active ad(s) breached critical performance thresholds &mdash; immediate pause required.`;
                } else if (counts.warning > 0) {
                    v1Text.innerHTML = `<strong>WARNING:</strong> ${counts.warning} active ad(s) underperforming &mdash; review creative and plan rotation in 3 days.`;
                } else if (counts.watch > 0) {
                    const watchAd = (summary.alerts || []).find(a => a.level === 'WATCH') || {};
                    v1Text.innerHTML = `1 Active Campaign flagged in WATCH status (<strong>${watchAd.campaign_name || 'Active Campaign'}</strong> &mdash; ${watchAd.metric_name}: ${watchAd.metric_value} vs threshold ${watchAd.threshold || '> 2.5'}).`;
                } else {
                    v1Text.innerText = `All ${counts.healthy} active campaigns are running within safe historical performance thresholds.`;
                }
            }

            // 4. Summary card numbers
            const cCrit = document.getElementById('alert-count-critical');
            const cWarn = document.getElementById('alert-count-warning');
            const cWatch = document.getElementById('alert-count-watch');
            const cHealth = document.getElementById('alert-count-healthy');
            if (cCrit) cCrit.innerText = counts.critical || 0;
            if (cWarn) cWarn.innerText = counts.warning || 0;
            if (cWatch) cWatch.innerText = counts.watch || 0;
            if (cHealth) cHealth.innerText = counts.healthy || 0;

            // 5. Filter pill counts
            const pAll = document.getElementById('pill-all-count');
            const pCrit = document.getElementById('pill-crit-count');
            const pWarn = document.getElementById('pill-warn-count');
            const pWatch = document.getElementById('pill-watch-count');
            const pHealth = document.getElementById('pill-healthy-count');
            if (pAll) pAll.innerText = counts.total || allAlertEvaluations.length;
            if (pCrit) pCrit.innerText = counts.critical || 0;
            if (pWarn) pWarn.innerText = counts.warning || 0;
            if (pWatch) pWatch.innerText = counts.watch || 0;
            if (pHealth) pHealth.innerText = counts.healthy || 0;

            // 6. Render table rows
            renderAlertTableRows();

            // 7. Render 11 Rules Matrix
            renderRulesReferenceTable();
        }

        function renderAlertTableRows() {
            const tbody = document.getElementById('alert-table-body');
            if (!tbody) return;

            let filtered = allAlertEvaluations;
            if (currentAlertFilter !== 'ALL') {
                filtered = allAlertEvaluations.filter(e => e.level === currentAlertFilter);
            }

            if (filtered.length === 0) {
                tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 28px; color: #64748b;">No ads found matching filter "${currentAlertFilter}".</td></tr>`;
                return;
            }

            tbody.innerHTML = filtered.map(item => {
                const lvl = item.level || 'HEALTHY';
                const isWatch = lvl === 'WATCH';
                const isWarn = lvl === 'WARNING';
                const isCrit = lvl === 'CRITICAL';
                const isHealthy = lvl === 'HEALTHY';

                const badgeClass = isCrit ? 'critical' : (isWarn ? 'warning' : (isWatch ? 'watch' : 'healthy'));
                const actionBoxClass = badgeClass;

                const freqBreached = item.frequency > 2.5;
                const ctrBreached = item.ctr < 0.67;

                const routing = isCrit 
                    ? 'monitoring person + brand team + business owner'
                    : (isWarn 
                        ? 'monitoring person + brand marketing team' 
                        : (isWatch ? 'monitoring person only' : 'None'));

                return `
                    <tr>
                        <td>
                            <span class="badge-alert ${badgeClass}">
                                <span class="alert-stat-dot ${isCrit ? 'red' : (isWarn ? 'yellow' : (isWatch ? 'blue' : 'green'))}"></span>
                                ${lvl}
                            </span>
                        </td>
                        <td>
                            <div style="font-weight: 600; color: #f8fafc; font-size: 12px; margin-bottom: 2px;">
                                ${item.campaign_name}
                            </div>
                            <div style="font-size: 10px; color: #64748b; font-family: var(--font-mono);">
                                Imp: ${Number(item.impressions||0).toLocaleString()} · Reach: ${Number(item.reach||0).toLocaleString()} · Clicks: ${Number(item.link_clicks||0).toLocaleString()}
                            </div>
                        </td>
                        <td>
                            <span style="font-weight: 500; color: ${isHealthy ? '#94a3b8' : '#e2e8f0'};">
                                ${item.primary_parameter || 'Optimal Delivery'}
                            </span>
                        </td>
                        <td>
                            <span class="metric-val-alert ${freqBreached ? 'breached' : ''}">
                                ${item.frequency ? item.frequency.toFixed(2) + 'x' : '&mdash;'}
                            </span>
                            ${freqBreached ? '<span style="display:block; font-size:9px; color:#38bdf8; font-weight:600;">&gt; 2.5 Watch</span>' : ''}
                        </td>
                        <td>
                            <span class="metric-val-alert ${ctrBreached ? 'breached' : ''}">
                                ${item.ctr ? item.ctr.toFixed(2) + '%' : '&mdash;'}
                            </span>
                        </td>
                        <td>
                            <span class="metric-val-alert">
                                ₱${item.cpc ? item.cpc.toFixed(2) : '0.00'}
                            </span>
                        </td>
                        <td>
                            <span style="font-family: var(--font-mono); font-weight: 600; color: #cbd5e1;">
                                ₱${Math.round(item.spend||0).toLocaleString()}
                            </span>
                        </td>
                        <td>
                            <div class="action-box ${actionBoxClass}">
                                ${item.primary_action || 'Optimal delivery - all metrics within safe thresholds.'}
                            </div>
                        </td>
                        <td>
                            <span class="routing-tag">${routing}</span>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function renderRulesReferenceTable() {
            const tbody = document.getElementById('rules-ref-body');
            if (!tbody || !allAlertRules || allAlertRules.length === 0) return;

            tbody.innerHTML = allAlertRules.map(r => {
                const badgeClass = r.level === 'CRITICAL' ? 'critical' : (r.level === 'WARNING' ? 'warning' : 'watch');
                return `
                    <tr>
                        <td><span class="badge-alert ${badgeClass}">${r.level}</span></td>
                        <td style="font-weight: 600; color: #f1f5f9;">${r.parameter}</td>
                        <td style="color: #cbd5e1; font-family: var(--font-mono); font-size: 10px;">${r.trigger_condition}</td>
                        <td style="color: #e2e8f0;">${r.required_action}</td>
                        <td style="color: #94a3b8; font-family: var(--font-mono); font-size: 10px;">${r.source}</td>
                        <td style="color: #94a3b8; font-size: 10px;">${r.routing}</td>
                    </tr>
                `;
            }).join('');
        }

        function switchAnalyticsView(viewId, btn) {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
            
            if (btn) btn.classList.add('active');
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

            // Global Chart.js styling tokens aligned with chart-designer principles
            Chart.defaults.color = '#94a3b8';
            Chart.defaults.font.family = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
            Chart.defaults.font.size = 11;
            Chart.defaults.borderColor = 'rgba(30, 41, 59, 0.45)';
            Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(9, 13, 22, 0.96)';
            Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
            Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
            Chart.defaults.plugins.tooltip.borderColor = 'rgba(56, 189, 248, 0.25)';
            Chart.defaults.plugins.tooltip.borderWidth = 1;
            Chart.defaults.plugins.tooltip.padding = 10;
            Chart.defaults.plugins.tooltip.cornerRadius = 8;
            Chart.defaults.plugins.tooltip.boxPadding = 6;
            Chart.defaults.plugins.tooltip.usePointStyle = true;

            const campaigns = data.campaigns_summary || [];
            const channels = data.channels_summary || [];
            const daily = data.daily_trend || [];

            // Update View 1 Badge
            const v1Badge = document.getElementById('v1-spend-badge');
            if (v1Badge) v1Badge.innerText = '₱' + Math.round(totalSpend).toLocaleString() + ' Total';

            // --- CHART 1: View 1 Ad Spend by Campaign (Horizontal Bar with Gradient) ---
            const spendCanvas = document.getElementById('chartSpendBar');
            if (spendCanvas) {
                const spendCtx = spendCanvas.getContext('2d');
                const topSpend = campaigns
                    .filter(c => c.amount_spent > 0)
                    .sort((a, b) => b.amount_spent - a.amount_spent)
                    .slice(0, 6);
                
                const labels = topSpend.map(c => c.campaign_name.length > 22 ? c.campaign_name.substring(0, 20) + '…' : c.campaign_name);
                const values = topSpend.map(c => c.amount_spent);

                // Horizontal gradient: Deep Cyan to Vibrant Sky Blue
                const hGrad = spendCtx.createLinearGradient(0, 0, spendCanvas.width || 400, 0);
                hGrad.addColorStop(0, '#0284c7');
                hGrad.addColorStop(1, '#38bdf8');

                if (chartSpendBar) chartSpendBar.destroy();
                chartSpendBar = new Chart(spendCtx, {
                    type: 'bar',
                    data: {
                        labels: labels.length ? labels : ['No Campaign Data'],
                        datasets: [{
                            label: 'Ad Spend (PHP)',
                            data: values.length ? values : [0],
                            backgroundColor: hGrad,
                            borderColor: '#38bdf8',
                            borderWidth: 1,
                            borderRadius: 6,
                            borderSkipped: false
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 600, easing: 'easeOutQuart' },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => {
                                        const val = Number(ctx.raw);
                                        const pct = totalSpend > 0 ? ((val / totalSpend) * 100).toFixed(1) : 0;
                                        return ` Spend: ₱${val.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${pct}% of total)`;
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: 'rgba(30, 41, 59, 0.4)' },
                                ticks: {
                                    callback: (v) => '₱' + (v >= 1000 ? (v/1000) + 'k' : v)
                                }
                            },
                            y: { 
                                grid: { display: false },
                                ticks: { color: '#cbd5e1', font: { weight: '500' } }
                            }
                        }
                    }
                });
            }

            // --- CHART 2: View 1 CTR vs CPC (Dual-Axis with High-Contrast Palettes) ---
            const cpcCtrCanvas = document.getElementById('chartCpcCtr');
            if (cpcCtrCanvas) {
                const cpcCtrCtx = cpcCtrCanvas.getContext('2d');
                const activeCamps = campaigns
                    .filter(c => c.amount_spent > 0)
                    .sort((a, b) => b.amount_spent - a.amount_spent)
                    .slice(0, 5);
                
                const labels = activeCamps.map(c => c.campaign_name.length > 15 ? c.campaign_name.substring(0, 13) + '…' : c.campaign_name);
                const ctrValues = activeCamps.map(c => c.ctr);
                const cpcValues = activeCamps.map(c => c.cpc);

                // Emerald gradient for CTR (Efficiency)
                const ctrGrad = cpcCtrCtx.createLinearGradient(0, 0, 0, 260);
                ctrGrad.addColorStop(0, 'rgba(52, 211, 153, 0.9)');
                ctrGrad.addColorStop(1, 'rgba(5, 150, 105, 0.5)');

                // Rose gradient for CPC (Cost)
                const cpcGrad = cpcCtrCtx.createLinearGradient(0, 0, 0, 260);
                cpcGrad.addColorStop(0, 'rgba(251, 113, 133, 0.9)');
                cpcGrad.addColorStop(1, 'rgba(225, 29, 72, 0.5)');

                if (chartCpcCtr) chartCpcCtr.destroy();
                chartCpcCtr = new Chart(cpcCtrCtx, {
                    type: 'bar',
                    data: {
                        labels: labels.length ? labels : ['No Active Ads'],
                        datasets: [
                            {
                                label: 'Link CTR (%) [Left]',
                                data: ctrValues.length ? ctrValues : [0],
                                backgroundColor: ctrGrad,
                                borderColor: '#10b981',
                                borderWidth: 1,
                                yAxisID: 'yCtr',
                                borderRadius: 5
                            },
                            {
                                label: 'Cost per Click (PHP) [Right]',
                                data: cpcValues.length ? cpcValues : [0],
                                backgroundColor: cpcGrad,
                                borderColor: '#f43f5e',
                                borderWidth: 1,
                                yAxisID: 'yCpc',
                                borderRadius: 5
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 600, easing: 'easeOutQuart' },
                        plugins: {
                            legend: { 
                                position: 'top', 
                                labels: { 
                                    boxWidth: 10, 
                                    font: { size: 11, weight: '500' },
                                    color: '#cbd5e1'
                                } 
                            },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ctx.datasetIndex === 0 
                                        ? ` Link CTR: ${Number(ctx.raw).toFixed(2)}%` 
                                        : ` Cost Per Click: ₱${Number(ctx.raw).toFixed(2)} PHP`
                                }
                            }
                        },
                        scales: {
                            yCtr: {
                                type: 'linear',
                                position: 'left',
                                grid: { color: 'rgba(30, 41, 59, 0.35)' },
                                ticks: { 
                                    color: '#34d399',
                                    callback: v => v + '%' 
                                },
                                title: { display: true, text: 'CTR %', color: '#34d399', font: { size: 10 } }
                            },
                            yCpc: {
                                type: 'linear',
                                position: 'right',
                                grid: { display: false },
                                ticks: { 
                                    color: '#fb7185',
                                    callback: v => '₱' + v 
                                },
                                title: { display: true, text: 'CPC (PHP)', color: '#fb7185', font: { size: 10 } }
                            },
                            x: { 
                                grid: { display: false },
                                ticks: { color: '#cbd5e1' }
                            }
                        }
                    }
                });
            }

            // --- CHART 3: View 2 Funnel Waterfall (5-Stage Visual Conversion Journey) ---
            const funnelCanvas = document.getElementById('chartFunnelBar');
            if (funnelCanvas) {
                const funnelCtx = funnelCanvas.getContext('2d');
                const funnelLabels = ['1. Ad Clicks', '2. Inquiries', '3. Quotes Issued', '4. Paid Orders'];
                const funnelData = [totalClicks, totalInquiries, totalQuotes, totalOrders];

                // 4 Semantic Stage Gradients
                const g1 = funnelCtx.createLinearGradient(0, 0, 0, 260);
                g1.addColorStop(0, '#60a5fa'); g1.addColorStop(1, '#2563eb');

                const g2 = funnelCtx.createLinearGradient(0, 0, 0, 260);
                g2.addColorStop(0, '#22d3ee'); g2.addColorStop(1, '#0891b2');

                const g3 = funnelCtx.createLinearGradient(0, 0, 0, 260);
                g3.addColorStop(0, '#c084fc'); g3.addColorStop(1, '#7c3aed');

                const g4 = funnelCtx.createLinearGradient(0, 0, 0, 260);
                g4.addColorStop(0, '#34d399'); g4.addColorStop(1, '#059669');

                if (chartFunnelBar) chartFunnelBar.destroy();
                chartFunnelBar = new Chart(funnelCtx, {
                    type: 'bar',
                    data: {
                        labels: funnelLabels,
                        datasets: [{
                            label: 'Volume',
                            data: funnelData,
                            backgroundColor: [g1, g2, g3, g4],
                            borderColor: ['#3b82f6', '#06b6d4', '#a855f7', '#10b981'],
                            borderWidth: 1,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 650, easing: 'easeOutQuart' },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => {
                                        const count = Number(ctx.raw);
                                        const ofTop = totalClicks > 0 ? ((count / totalClicks) * 100).toFixed(2) : 0;
                                        return ` Count: ${count.toLocaleString()} (${ofTop}% of initial clicks)`;
                                    },
                                    afterLabel: (ctx) => {
                                        if (ctx.dataIndex === 1 && totalClicks > 0) {
                                            return ` Lead Conversion: ${((totalInquiries/totalClicks)*100).toFixed(2)}%`;
                                        }
                                        if (ctx.dataIndex === 2 && totalInquiries > 0) {
                                            return ` Quote Rate: ${((totalQuotes/totalInquiries)*100).toFixed(1)}% of inquiries`;
                                        }
                                        if (ctx.dataIndex === 3) {
                                            return ` Closed Revenue: ₱${Math.round(totalRev).toLocaleString()} PHP`;
                                        }
                                        return '';
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                type: 'logarithmic',
                                grid: { color: 'rgba(30, 41, 59, 0.4)' },
                                ticks: {
                                    color: '#94a3b8',
                                    callback: (v) => v === 1 || v === 10 || v === 100 || v === 1000 || v === 10000 ? v.toLocaleString() : null
                                }
                            },
                            x: { 
                                grid: { display: false },
                                ticks: { color: '#e2e8f0', font: { weight: '600' } }
                            }
                        }
                    }
                });
            }

            // --- CHART 4: View 2 Daily Line Trend (Curved with Vertical Area Glow) ---
            const dailyCanvas = document.getElementById('chartDailyLine');
            if (dailyCanvas) {
                const dailyCtx = dailyCanvas.getContext('2d');
                const labels = daily.map(d => d.date ? d.date.substring(5) : '');
                const counts = daily.map(d => d.count);

                // Area Fill Gradient: Soft cyan glow fading downward
                const areaGrad = dailyCtx.createLinearGradient(0, 0, 0, 260);
                areaGrad.addColorStop(0, 'rgba(56, 189, 248, 0.32)');
                areaGrad.addColorStop(0.7, 'rgba(56, 189, 248, 0.08)');
                areaGrad.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

                if (chartDailyLine) chartDailyLine.destroy();
                chartDailyLine = new Chart(dailyCtx, {
                    type: 'line',
                    data: {
                        labels: labels.length ? labels : ['Today'],
                        datasets: [{
                            label: 'Tracked Clicks',
                            data: counts.length ? counts : [totalClicks],
                            fill: true,
                            backgroundColor: areaGrad,
                            borderColor: '#38bdf8',
                            borderWidth: 2.5,
                            tension: 0.38,
                            pointRadius: 3.5,
                            pointHoverRadius: 6.5,
                            pointBackgroundColor: '#fff',
                            pointBorderColor: '#0284c7',
                            pointBorderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 650, easing: 'easeOutQuart' },
                        plugins: { 
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` Ad Clicks: ${Number(ctx.raw).toLocaleString()} events`
                                }
                            }
                        },
                        scales: {
                            y: { 
                                grid: { color: 'rgba(30, 41, 59, 0.35)' },
                                ticks: { color: '#94a3b8' }
                            },
                            x: { 
                                grid: { display: false },
                                ticks: { color: '#cbd5e1' }
                            }
                        }
                    }
                });
            }

            // --- CHART 5: View 3 Channels Donut (Accessible Curated Palette) ---
            const chanCanvas = document.getElementById('chartChannelsDonut');
            if (chanCanvas) {
                const chanCtx = chanCanvas.getContext('2d');
                const chanLabels = channels.map(c => c.channel);
                const chanCounts = channels.map(c => c.count);
                
                // Color palette recommended by chart-designer
                const colors = [
                    '#38bdf8', '#f43f5e', '#10b981', '#f59e0b', '#8b5cf6', '#64748b'
                ];

                if (chartChannelsDonut) chartChannelsDonut.destroy();
                chartChannelsDonut = new Chart(chanCtx, {
                    type: 'doughnut',
                    data: {
                        labels: chanLabels.length ? chanLabels : ['Meta Clicks'],
                        datasets: [{
                            data: chanCounts.length ? chanCounts : [1],
                            backgroundColor: colors.slice(0, chanLabels.length || 1),
                            borderWidth: 2.5,
                            borderColor: '#090d16',
                            hoverOffset: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 600, easing: 'easeOutQuart' },
                        cutout: '72%',
                        plugins: {
                            legend: { 
                                position: 'right', 
                                labels: { 
                                    boxWidth: 10, 
                                    font: { size: 11, weight: '500' },
                                    color: '#cbd5e1',
                                    padding: 12
                                } 
                            },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => {
                                        const count = Number(ctx.raw);
                                        const sum = chanCounts.reduce((a, b) => a + b, 0) || 1;
                                        const pct = Math.round((count / sum) * 100);
                                        return ` ${ctx.label}: ${count.toLocaleString()} clicks (${pct}%)`;
                                    }
                                }
                            }
                        }
                    }
                });

                // Populate mini list for Channel Health with visual mini progress bars
                const listEl = document.getElementById('channel-metric-list');
                if (listEl) {
                    const totalChanClicks = chanCounts.reduce((a, b) => a + b, 0) || 1;
                    listEl.innerHTML = channels.map((c, i) => {
                        const pct = Math.round((c.count / totalChanClicks) * 100);
                        const clr = colors[i % colors.length];
                        return `
                            <div class="metric-mini-row" style="flex-direction: column; align-items: stretch; gap: 6px;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <span style="display:flex; align-items:center; gap:8px;">
                                        <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${clr};"></span>
                                        <span style="color:#e2e8f0; font-weight:500;">${c.channel}</span>
                                    </span>
                                    <span><strong style="color:#fff;">${c.count.toLocaleString()}</strong> <span style="color:#94a3b8;">(${pct}%)</span></span>
                                </div>
                                <div style="width:100%; height:4px; background:#1e293b; border-radius:999px; overflow:hidden;">
                                    <div style="width:${pct}%; height:100%; background:${clr}; border-radius:999px;"></div>
                                </div>
                            </div>
                        `;
                    }).join('');
                }
            }

            // --- CHART 6: View 4 Revenue Pipeline & ROAS (Financial Multi-Bar) ---
            const roasCanvas = document.getElementById('chartRoasCompare');
            if (roasCanvas) {
                const roasCtx = roasCanvas.getContext('2d');
                const netProfit = Math.max(0, totalRev - totalSpend);

                // Gradients for Capital vs Revenue vs Net Spread
                const spendGrad = roasCtx.createLinearGradient(0, 0, 0, 260);
                spendGrad.addColorStop(0, '#fbbf24'); spendGrad.addColorStop(1, '#d97706');

                const revGrad = roasCtx.createLinearGradient(0, 0, 0, 260);
                revGrad.addColorStop(0, '#34d399'); revGrad.addColorStop(1, '#059669');

                const netGrad = roasCtx.createLinearGradient(0, 0, 0, 260);
                netGrad.addColorStop(0, '#38bdf8'); netGrad.addColorStop(1, '#0284c7');

                if (chartRoasCompare) chartRoasCompare.destroy();
                chartRoasCompare = new Chart(roasCtx, {
                    type: 'bar',
                    data: {
                        labels: ['Executive Financial Summary'],
                        datasets: [
                            {
                                label: 'Meta Ad Spend',
                                data: [totalSpend],
                                backgroundColor: spendGrad,
                                borderColor: '#f59e0b',
                                borderWidth: 1,
                                borderRadius: 6
                            },
                            {
                                label: 'Zoho Creator Paid Sales',
                                data: [totalRev],
                                backgroundColor: revGrad,
                                borderColor: '#10b981',
                                borderWidth: 1,
                                borderRadius: 6
                            },
                            {
                                label: 'Net Profit Spread',
                                data: [netProfit],
                                backgroundColor: netGrad,
                                borderColor: '#0284c7',
                                borderWidth: 1,
                                borderRadius: 6
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: { duration: 650, easing: 'easeOutQuart' },
                        plugins: {
                            legend: { 
                                position: 'top', 
                                labels: { 
                                    boxWidth: 10, 
                                    font: { size: 11, weight: '500' },
                                    color: '#cbd5e1'
                                } 
                            },
                            tooltip: {
                                callbacks: {
                                    label: (ctx) => ` ${ctx.dataset.label}: ₱${Number(ctx.raw).toLocaleString('en-US', { minimumFractionDigits: 2 })} PHP`
                                }
                            }
                        },
                        scales: {
                            y: {
                                grid: { color: 'rgba(30, 41, 59, 0.4)' },
                                ticks: {
                                    color: '#94a3b8',
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
