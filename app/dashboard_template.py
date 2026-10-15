"""
Executive Dashboard Template for Home Cartel Ad Attribution
Minimal, authentic engineering UI (Linear / Stripe aesthetic - no AI tropes or emojis)
"""

import base64
from pathlib import Path


def _brand_logo_html(brand: str, css_class: str, width: int = 168, height: int = 36) -> str:
    """Inline base64 image logo for the specified brand, or fallback text wordmark."""
    assets_dir = Path(__file__).parent / "assets"
    if brand == "roomandstyle":
        for fname in ["roomandstyle_logo.jpg", "room-and-style-logo.webp", "roomandstyle_logo.webp"]:
            p = assets_dir / fname
            if not p.exists() and "room-and-style-logo.webp" in fname:
                p = Path(__file__).parent.parent / "room-and-style-logo.webp"
            if p.exists():
                try:
                    raw = p.read_bytes()
                    mime = "image/webp" if fname.endswith(".webp") else "image/jpeg"
                    uri = f"data:{mime};base64," + base64.b64encode(raw).decode("ascii")
                    return f'<img class="logo-img brand-logo-rs {css_class}" src="{uri}" alt="Room and Style" width="{width}" height="{height}">'
                except OSError:
                    pass
        return '<span class="logo-text">Room &amp; Style</span>'
    else:
        try:
            raw = (assets_dir / "homecartel_logo.jpg").read_bytes()
            uri = "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")
            return f'<img class="logo-img brand-logo-hc {css_class}" src="{uri}" alt="Home Cartel" width="{width}" height="{height}">'
        except OSError:
            return '<span class="logo-text">Home Cartel</span>'


def _logo_html(css_class: str) -> str:
    """Home Cartel logo as an inline image, or a text wordmark if the file is missing."""
    return _brand_logo_html("homecartel", css_class)


def _rs_logo_html(css_class: str, width: int = 168, height: int = 36) -> str:
    """Room and Style logo as an inline image, or a text wordmark if the file is missing."""
    return _brand_logo_html("roomandstyle", css_class, width=width, height=height)



def get_dashboard_html() -> str:
    html = """<!DOCTYPE html>
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
            --bg-base: #f1f5f9;
            --bg-surface: #ffffff;
            --bg-card: #ffffff;
            --bg-card-hover: #f8fafc;
            --border: #e2e8f0;
            --border-hover: #cbd5e1;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --accent-cyan: #0284c7;
            --accent-blue: #2563eb;
            --accent-rose: #e11d48;
            --font-main: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-size: 15px;
            line-height: 1.5;
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
            color: #0f172a;
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
            background: #ffffff;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
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
            background: #e2e8f0;
            color: #0f172a;
            border-color: var(--border-hover);
        }

        .btn-primary {
            background: #e2e8f0;
            color: #0f172a;
            border-color: #cbd5e1;
        }

        .btn-primary:hover {
            background: #cbd5e1;
            color: #0f172a;
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

        .stats-grid.stats-grid-single {
            grid-template-columns: 1fr;
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
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--text-muted);
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.5px;
            font-variant-numeric: tabular-nums;
            margin: 6px 0 2px;
        }

        .stat-footer {
            font-size: 13px;
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
            background: #e2e8f0;
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
            font-size: 12px;
            font-weight: 500;
            margin-top: 4px;
        }

        .split-ig-text { color: #be123c; }
        .split-fb-text { color: #1d4ed8; }

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
            font-size: 13px;
        }

        th {
            background: #f1f5f9;
            padding: 11px 16px;
            color: var(--text-muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }

        td {
            padding: 12px 16px;
            border-bottom: 1px solid rgba(15,23,42,0.10);
            vertical-align: middle;
            color: #334155;
        }

        tr:hover td {
            background: rgba(15,23,42,0.03);
        }

        .pill-instagram {
            background: rgba(244, 63, 94, 0.12);
            color: #be123c;
            border: 1px solid rgba(244, 63, 94, 0.25);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .pill-facebook {
            background: rgba(59, 130, 246, 0.12);
            color: #1d4ed8;
            border: 1px solid rgba(59, 130, 246, 0.25);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .pill-meta {
            background: rgba(148, 163, 184, 0.1);
            color: #475569;
            border: 1px solid rgba(148, 163, 184, 0.2);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
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
            color: #0f172a;
            text-decoration: none;
            font-weight: 500;
            font-size: 13px;
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
            font-size: 12px;
            color: #475569;
            background: #f8fafc;
            border: 1px solid var(--border);
            padding: 1px 6px;
            border-radius: 4px;
            width: fit-content;
        }

        .copy-pill {
            font-family: var(--font-mono);
            font-size: 12px;
            background: #f8fafc;
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
            color: #475569;
        }

        .copy-pill:hover {
            border-color: var(--accent-cyan);
            color: #0f172a;
        }

        .pill-campaign {
            background: rgba(168, 85, 247, 0.1);
            color: #7e22ce;
            border: 1px solid rgba(168, 85, 247, 0.2);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
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
            color: #0369a1;
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            font-family: var(--font-mono);
            display: inline-flex;
            align-items: center;
            white-space: nowrap;
        }

        .pill-estimate {
            background: rgba(168, 85, 247, 0.12);
            color: #7e22ce;
            border: 1px solid rgba(168, 85, 247, 0.25);
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 12px;
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
            color: #047857;
            font-size: 13px;
            font-family: var(--font-mono);
        }

        .so-id {
            font-size: 12px;
            color: #475569;
            font-family: var(--font-mono);
        }

        .pill-stage {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
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
            color: #475569;
            border: 1px solid rgba(100, 116, 139, 0.25);
        }

        .pill-stage.pill-inquiry {
            background: rgba(56, 189, 248, 0.15);
            color: #0369a1;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .pill-stage.pill-quote {
            background: rgba(168, 85, 247, 0.15);
            color: #7e22ce;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        .pill-stage.pill-sale {
            background: rgba(16, 185, 129, 0.15);
            color: #047857;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .pill-stage.pill-success {
            background: rgba(16, 185, 129, 0.2);
            color: #047857;
            border: 1px solid #10b981;
        }

        .badge-faded {
            color: #64748b;
            font-size: 12px;
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
            background: #e2e8f0;
        }

        .stepper-step.completed:not(:last-child)::after {
            background: #10b981;
        }

        .step-indicator {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #e2e8f0;
            border: 2px solid #cbd5e1;
            color: #475569;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 700;
            flex-shrink: 0;
            z-index: 1;
        }

        .stepper-step.completed .step-indicator {
            background: #d1fae5;
            border-color: #10b981;
            color: #047857;
        }

        .stepper-step.active .step-indicator {
            background: #e0f2fe;
            border-color: #38bdf8;
            color: #0369a1;
        }

        .step-content {
            flex: 1;
        }

        .step-title {
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
        }

        .step-sub {
            font-size: 12px;
            color: #475569;
            margin-top: 2px;
        }

        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #0f172a;
            color: #fff;
            padding: 9px 14px;
            border-radius: 6px;
            border: 1px solid var(--border-hover);
            font-size: 13px;
            font-weight: 500;
            display: none;
            box-shadow: 0 8px 20px rgba(15,23,42,0.12);
            z-index: 2000;
        }

        .toast.show {
            display: block;
        }

        .empty-state {
            text-align: center;
            padding: 48px 20px;
            color: var(--text-muted);
            font-size: 14px;
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
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.2px;
        }

        .analytics-badge {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.12);
            color: #0369a1;
            border: 1px solid rgba(56, 189, 248, 0.25);
            font-family: var(--font-mono);
        }

        .analytics-tabs {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }

        .view-btn {
            background: #f8fafc;
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.15s ease;
            font-family: inherit;
        }

        .view-btn:hover {
            color: #0f172a;
            border-color: var(--border-hover);
        }

        .view-btn.active {
            background: #e2e8f0;
            color: #0369a1;
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
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(15,23,42,0.12);
            border-radius: 12px;
            padding: 18px 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 24px -2px rgba(15,23,42,0.10);
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
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chart-box-sub {
            font-size: 12px;
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
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 6px;
            font-size: 12px;
        }

        .metric-mini-val {
            font-weight: 700;
            font-family: var(--font-mono);
            color: #0f172a;
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
            font-size: 12px;
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
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
        }
        .health-kpi-label {
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .health-kpi-value {
            font-size: 22px;
            font-weight: 700;
            color: #0f172a;
            font-family: var(--font-mono);
            min-height: 30px;
            display: flex;
            align-items: center;
        }
        .health-kpi-sub {
            font-size: 12px;
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
            font-size: 13px;
            background: #ffffff;
            border: 1px dashed var(--border-hover);
            border-radius: 10px;
            margin-bottom: 18px;
        }
        .health-attention {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 16px;
            margin-bottom: 14px;
        }
        .health-attention-title {
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 10px;
        }
        .health-attention-hint {
            font-weight: 500;
            font-size: 12px;
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
            border-top: 1px solid rgba(15,23,42,0.10);
            padding: 10px 4px;
            color: inherit;
            font-family: inherit;
            cursor: pointer;
        }
        .health-attn { border-top: 1px solid rgba(15,23,42,0.10); }
        .health-attn:first-child { border-top: 0; }
        .health-attn .health-attn-row { border-top: 0; }
        .health-sop {
            margin: 0 4px 10px 110px;
            font-size: 12px;
            color: var(--text-secondary);
        }
        .health-sop summary { cursor: pointer; color: var(--accent-cyan); font-weight: 600; }
        .health-sop ol { margin: 8px 0 0 18px; line-height: 1.7; }
        .health-attn-row:hover { background: rgba(15,23,42,0.04); }
        .health-attn-row:focus-visible { outline: 2px solid var(--accent-cyan); outline-offset: -2px; }
        .health-attn-name {
            font-size: 13px;
            font-weight: 600;
            color: #0f172a;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .health-attn-metrics {
            font-size: 12px;
            color: var(--text-muted);
            font-family: var(--font-mono);
            margin-top: 2px;
        }
        .health-attn-ok {
            font-size: 13px;
            color: #047857;
            padding: 4px 0;
        }
        .health-coverage {
            font-size: 12px;
            color: var(--text-muted);
            background: #f1f5f9;
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
        .health-coverage strong { color: #334155; }
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
            background: rgba(15,23,42,0.5);
            backdrop-filter: blur(3px);
        }
        .health-modal-backdrop[hidden] { display: none; }
        .health-modal-card {
            width: 100%;
            max-width: 640px;
            max-height: 86vh;
            display: flex;
            flex-direction: column;
            background: #ffffff;
            border: 1px solid var(--border-hover);
            border-radius: 12px;
            box-shadow: 0 24px 60px rgba(15,23,42,0.5);
        }
        .health-modal-head {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
        }
        .health-modal-title { font-size: 15px; font-weight: 700; color: #0f172a; }
        .health-modal-sub { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
        .health-modal-body { padding: 14px 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .health-modal-item {
            background: #f1f5f9;
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 14px;
        }
        .health-modal-item-name { font-size: 13px; font-weight: 600; color: #0f172a; margin: 6px 0 2px; }
        .health-modal-item-metrics { font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); margin-bottom: 8px; }
        .health-modal-note {
            font-size: 12px;
            color: var(--text-secondary);
            background: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 6px;
            padding: 8px 10px;
        }
        .health-modal-note.warn {
            background: rgba(245, 158, 11, 0.1);
            border-color: rgba(245, 158, 11, 0.35);
            color: #78350f;
        }
        .health-modal-foot {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 12px 20px;
            border-top: 1px solid var(--border);
        }

        /* ===== Friendly ad health layout (light theme) ===== */
        .top-bar { align-items: flex-start; padding-bottom: 18px; margin-bottom: 22px; }
        .brand-block { display: flex; flex-direction: column; gap: 10px; }
        .brand-title { font-size: 24px; font-weight: 700; letter-spacing: -0.4px; }
        .brand-title .sub { color: var(--accent-cyan); font-weight: 700; }
        .top-actions { flex-wrap: wrap; justify-content: flex-end; }

        .btn-action { min-height: 40px; padding: 8px 14px; font-size: 14px; border-radius: 8px; background: #ffffff; color: var(--text-secondary); border-color: var(--border-hover); }
        .btn-action:hover { background: #f1f5f9; color: var(--text-primary); }
        .btn-action.btn-primary { background: #0369a1; color: #ffffff; border-color: #0369a1; font-weight: 600; }
        .btn-action.btn-primary:hover { background: #075985; color: #ffffff; }
        .btn-action.btn-primary:disabled { background: #94a3b8; border-color: #94a3b8; cursor: not-allowed; }
        .btn-lg { min-height: 44px; padding: 10px 18px; font-size: 15px; }
        .badge-alert { font-family: var(--font-main); text-transform: none; letter-spacing: 0; font-size: 13px; font-weight: 700; padding: 4px 10px; border-radius: 999px; white-space: nowrap; }
        .help-q { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 50%; background: #e0f2fe; color: #0369a1; font-weight: 700; font-size: 13px; }

        .freshness { display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap; font-size: 14px; font-weight: 600; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--border-hover); background: #ffffff; color: var(--text-secondary); width: fit-content; }
        .fresh-dot { width: 10px; height: 10px; border-radius: 50%; background: #94a3b8; flex-shrink: 0; }
        .fresh-period { font-weight: 500; color: var(--text-muted); }
        .freshness.fresh { border-color: #6ee7b7; background: #ecfdf5; color: #047857; }
        .freshness.fresh .fresh-dot { background: #10b981; }
        .freshness.aging { border-color: #fcd34d; background: #fffbeb; color: #b45309; }
        .freshness.aging .fresh-dot { background: #f59e0b; }
        .freshness.old { border-color: #fca5a5; background: #fef2f2; color: #b91c1c; }
        .freshness.old .fresh-dot { background: #ef4444; }

        .analytics-hub { overflow-x: auto; }
        .health-hub { background: transparent; border: 0; padding: 0; margin-bottom: 26px; }

        .status-banner { display: flex; align-items: center; gap: 18px; padding: 20px 24px; border-radius: 14px; border: 1px solid var(--border-hover); border-left-width: 8px; background: #ffffff; margin-bottom: 18px; }
        .status-banner.healthy { background: #ecfdf5; border-color: #6ee7b7; border-left-color: #10b981; }
        .status-banner.watch { background: #eff6ff; border-color: #93c5fd; border-left-color: #3b82f6; }
        .status-banner.warning { background: #fffbeb; border-color: #fcd34d; border-left-color: #f59e0b; }
        .status-banner.critical { background: #fef2f2; border-color: #fca5a5; border-left-color: #ef4444; }
        .status-banner.neutral { border-left-color: #94a3b8; }
        .status-icon { width: 48px; height: 48px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #ffffff; border: 2px solid currentColor; }
        .status-banner.healthy .status-icon { color: #047857; }
        .status-banner.watch .status-icon { color: #1d4ed8; }
        .status-banner.warning .status-icon { color: #b45309; }
        .status-banner.critical .status-icon { color: #b91c1c; }
        .status-banner.neutral .status-icon { color: #64748b; }
        .status-text { flex: 1; min-width: 0; }
        .status-title { font-size: 22px; font-weight: 700; color: var(--text-primary); letter-spacing: -0.3px; }
        .status-sub { font-size: 15px; color: var(--text-secondary); margin-top: 4px; }

        .health-kpis { margin-bottom: 26px; }
        .health-kpi { background: #ffffff; padding: 16px 18px; }
        .health-kpi-label { font-size: 13px; letter-spacing: 0.3px; text-transform: none; font-weight: 700; color: var(--text-secondary); }
        .health-kpi-value { font-size: 28px; color: var(--text-primary); }
        .tip { display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px; margin-left: 4px; border-radius: 50%; background: #e2e8f0; color: #475569; font-size: 12px; font-weight: 700; cursor: help; vertical-align: middle; }

        .sect-title { font-size: 19px; font-weight: 700; color: var(--text-primary); margin: 0 0 12px; letter-spacing: -0.2px; }
        .sect-hint { font-size: 14px; font-weight: 500; color: var(--text-muted); margin-left: 10px; }
        #health-attention-wrap, #health-campaigns-wrap { margin-bottom: 26px; }

        .attn-list { display: grid; gap: 14px; }
        .attn-card { background: #ffffff; border: 1px solid var(--border-hover); border-left-width: 6px; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); }
        .attn-card.critical { border-left-color: #ef4444; }
        .attn-card.warning { border-left-color: #f59e0b; }
        .attn-card.watch { border-left-color: #3b82f6; }
        .attn-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
        .attn-name { font-size: 17px; font-weight: 700; color: var(--text-primary); word-break: break-word; }
        .attn-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 14px; }
        .attn-metric { background: #f8fafc; border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
        .attn-metric.bad { background: #fff7ed; border-color: #fdba74; }
        .m-val { font-size: 24px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
        .attn-metric.bad .m-val { color: #c2410c; }
        .m-lab { font-size: 14px; color: var(--text-secondary); line-height: 1.35; }
        .m-lab span { display: block; font-size: 13px; color: var(--text-muted); }
        .attn-action { font-size: 15px; color: var(--text-primary); margin: 4px 0 10px; }
        .attn-card .health-sop { margin: 6px 0 10px; font-size: 14px; }
        .attn-card .health-sop summary { font-size: 14px; }
        .btn-link { background: none; border: 0; padding: 6px 0; color: #0369a1; font-weight: 600; font-size: 14px; cursor: pointer; font-family: inherit; }
        .btn-link:hover { text-decoration: underline; }
        .all-good { background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 12px; padding: 16px 20px; color: #047857; font-size: 16px; font-weight: 600; }

        .camp-list { background: #ffffff; border: 1px solid var(--border-hover); border-radius: 12px; overflow: hidden; }
        .camp-head, .camp-row { display: grid; grid-template-columns: 130px minmax(0, 1.5fr) minmax(0, 1fr) minmax(0, 1fr) 110px; gap: 16px; align-items: center; padding: 12px 18px; }
        .camp-head { background: #f1f5f9; font-size: 13px; font-weight: 700; color: var(--text-secondary); border-bottom: 1px solid var(--border-hover); }
        .camp-row { border-bottom: 1px solid var(--border); font-size: 15px; }
        .camp-row:last-child { border-bottom: 0; }
        .camp-row.critical { background: #fef2f2; }
        .camp-row.warning { background: #fffbeb; }
        .camp-name { font-weight: 600; color: var(--text-primary); word-break: break-word; }
        .camp-cell b, .camp-spend b { font-variant-numeric: tabular-nums; color: var(--text-primary); }
        .camp-cell span, .camp-spend span { font-size: 13px; color: var(--text-muted); margin-left: 4px; }
        .camp-spend { text-align: right; }
        .mbar { position: relative; height: 10px; border-radius: 999px; background: #e2e8f0; margin-top: 6px; }
        .mfill { height: 100%; border-radius: 999px; }
        .mbar .mark { position: absolute; top: -3px; bottom: -3px; width: 2px; background: #475569; opacity: 0.55; }

        .health-more { background: #ffffff; border: 1px solid var(--border-hover); border-radius: 12px; padding: 4px 18px; }
        .health-more > summary { cursor: pointer; padding: 14px 0; font-size: 16px; font-weight: 700; color: var(--text-primary); }
        .health-more .health-charts { margin-top: 6px; }
        .health-coverage-note { font-size: 14px; color: var(--text-secondary); background: #f8fafc; border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; margin: 4px 0 16px; line-height: 1.5; }

        .get-started { background: #ffffff; border: 2px dashed #93c5fd; border-radius: 14px; padding: 24px 26px; margin-bottom: 26px; }
        .get-started-title { font-size: 20px; font-weight: 700; margin-bottom: 10px; }
        .get-started ol { margin: 0 0 16px 22px; font-size: 16px; line-height: 1.7; color: var(--text-secondary); }

        .help-block { margin-bottom: 16px; }
        .help-block h3 { font-size: 16px; margin-bottom: 8px; color: var(--text-primary); }
        .help-block p { font-size: 15px; color: var(--text-secondary); margin-bottom: 8px; line-height: 1.55; }
        .help-row { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 8px; font-size: 15px; color: var(--text-secondary); }
        .help-row .badge-alert { min-width: 84px; justify-content: center; flex-shrink: 0; }
        .import-steps { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
        .import-step { flex: 1; min-width: 150px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px; padding: 10px 12px; font-size: 14px; color: #0c4a6e; }
        .import-step b { display: block; margin-bottom: 2px; }

        @media (max-width: 900px) {
            .camp-head { display: none; }
            .camp-row { grid-template-columns: 1fr 1fr; gap: 10px 14px; }
            .camp-status, .camp-name { grid-column: 1 / -1; }
            .camp-spend { text-align: left; }
            .status-banner { flex-wrap: wrap; padding: 16px; }
            .status-title { font-size: 19px; }
            .sect-hint { display: block; margin: 4px 0 0; }
            .top-actions { justify-content: flex-start; }
        }
        @media (max-width: 520px) {
            .health-kpis { grid-template-columns: 1fr 1fr; }
            .health-kpi-value { font-size: 22px; }
            .brand-title { font-size: 20px; }
            .btn-lg { width: 100%; justify-content: center; }
            .status-banner .btn-lg { width: 100%; }
        }

        /* Section 2.6.4 Alert Center Styles */
        .alert-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }
        .alert-status-pill.watch {
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: #0369a1;
        }
        .alert-status-pill.watch:hover {
            background: rgba(56, 189, 248, 0.22);
            border-color: #38bdf8;
        }
        .alert-status-pill.critical {
            background: rgba(244, 63, 94, 0.15);
            border: 1px solid rgba(244, 63, 94, 0.4);
            color: #be123c;
        }
        .alert-status-pill.warning {
            background: rgba(245, 158, 11, 0.15);
            border: 1px solid rgba(245, 158, 11, 0.4);
            color: #b45309;
        }
        .alert-status-pill.healthy {
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #047857;
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
            font-size: 12px;
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
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .v1-alert-banner.watch {
            background: rgba(56,189,248,0.14);
            border: 1px solid rgba(56, 189, 248, 0.35);
            color: #0c4a6e;
        }
        .v1-alert-banner.watch:hover {
            background: rgba(56,189,248,0.18);
            border-color: #38bdf8;
        }
        .v1-alert-banner-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .v1-alert-banner-title {
            font-weight: 700;
            color: #0369a1;
        }
        .v1-alert-banner-cta {
            font-weight: 600;
            color: #0369a1;
            font-size: 12px;
            white-space: nowrap;
        }

        .alert-summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }
        .alert-stat-card {
            background: #ffffff;
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
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.6px;
            color: var(--text-muted);
        }
        .alert-stat-num {
            font-size: 26px;
            font-weight: 700;
            font-family: var(--font-mono);
            color: #0f172a;
            line-height: 1.1;
            margin-bottom: 4px;
        }
        .alert-stat-desc {
            font-size: 12px;
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
            background: #f8fafc;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }
        .alert-filter-pill:hover {
            color: #0f172a;
            border-color: var(--border-hover);
        }
        .alert-filter-pill.active {
            background: #e2e8f0;
            border-color: #38bdf8;
            color: #0369a1;
        }
        .alert-meta-note {
            font-size: 12px;
            color: var(--text-muted);
        }
        .alert-meta-note code {
            font-family: var(--font-mono);
            color: #334155;
            background: #e2e8f0;
            padding: 1px 5px;
            border-radius: 3px;
        }

        .alert-table-wrap {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow-x: auto;
            margin-bottom: 20px;
        }
        .alert-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }
        .alert-table th {
            padding: 10px 14px;
            background: #f1f5f9;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        .alert-table td {
            padding: 12px 14px;
            border-bottom: 1px solid rgba(15,23,42,0.10);
            color: var(--text-secondary);
            vertical-align: middle;
        }
        .alert-table tr:hover td {
            background: rgba(15,23,42,0.04);
        }

        .badge-alert {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            font-family: var(--font-mono);
        }
        .badge-alert.critical {
            background: rgba(244, 63, 94, 0.15);
            color: #be123c;
            border: 1px solid rgba(244, 63, 94, 0.35);
        }
        .badge-alert.warning {
            background: rgba(245, 158, 11, 0.15);
            color: #b45309;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }
        .badge-alert.watch {
            background: rgba(56, 189, 248, 0.15);
            color: #0369a1;
            border: 1px solid rgba(56, 189, 248, 0.35);
        }
        .badge-alert.healthy {
            background: rgba(16, 185, 129, 0.15);
            color: #047857;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }

        .metric-val-alert {
            font-family: var(--font-mono);
            font-weight: 600;
            color: #0f172a;
        }
        .metric-val-alert.breached {
            color: #0369a1;
            background: rgba(56, 189, 248, 0.1);
            padding: 2px 5px;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        .action-box {
            background: rgba(15,23,42,0.04);
            border: 1px solid rgba(15,23,42,0.12);
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            color: #1e293b;
            line-height: 1.4;
        }
        .action-box.watch {
            border-color: rgba(56, 189, 248, 0.35);
            background: rgba(56,189,248,0.10);
            color: #0c4a6e;
        }
        .action-box.critical {
            border-color: rgba(244, 63, 94, 0.4);
            background: rgba(244,63,94,0.10);
            color: #881337;
            font-weight: 600;
        }
        .action-box.warning {
            border-color: rgba(245, 158, 11, 0.4);
            background: rgba(245,158,11,0.12);
            color: #78350f;
        }
        .action-box.healthy {
            border-color: rgba(16, 185, 129, 0.25);
            color: #475569;
        }

        .routing-tag {
            font-size: 12px;
            font-family: var(--font-mono);
            color: var(--text-muted);
            background: #f8fafc;
            border: 1px solid var(--border);
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
        }

        .rules-reference-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-top: 14px;
        }
        .rules-ref-header {
            padding: 12px 18px;
            font-size: 13px;
            font-weight: 600;
            color: #334155;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }
        .rules-ref-header:hover {
            color: #0f172a;
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
            font-size: 12px;
        }
        .rules-table th {
            padding: 8px 10px;
            background: #f1f5f9;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            text-align: left;
            font-weight: 600;
        }
        .rules-table td {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(15,23,42,0.06);
            color: var(--text-secondary);
        }

        /* Responsive Import Modal & Dropzone */
        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(15,23,42,0.55);
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
            background: #f8fafc;
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 25px 60px -15px rgba(15,23,42,0.55), 0 0 0 1px rgba(15,23,42,0.04);
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
            border-bottom: 1px solid rgba(15,23,42,0.10);
            background: rgba(15,23,42,0.04);
        }

        .modal-title-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .modal-title {
            font-size: 15px;
            font-weight: 600;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 8px;
            letter-spacing: -0.2px;
        }

        .modal-title-badge {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 2px 7px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.12);
            color: #0369a1;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }

        .modal-subtitle {
            font-size: 13px;
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
            color: #0f172a;
            background: rgba(15,23,42,0.06);
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
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 26px 18px;
            text-align: center;
            cursor: pointer;
            background: rgba(15,23,42,0.04);
            transition: border-color 0.18s ease, background-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .dropzone:hover {
            border-color: #475569;
            background: rgba(15,23,42,0.04);
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
            background: rgba(15,23,42,0.10);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #0369a1;
            margin-bottom: 2px;
            transition: transform 0.2s;
        }

        .dropzone:hover .dropzone-icon, .dropzone.dragover .dropzone-icon {
            transform: translateY(-2px);
        }

        .dropzone-main-text {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
        }

        .dropzone-main-text span.browse-link {
            color: #0369a1;
            text-decoration: underline;
            text-underline-offset: 3px;
        }

        .dropzone-hint {
            font-size: 12px;
            color: var(--text-muted);
        }

        /* Selected File Preview Card */
        .file-selected-card {
            display: none;
            width: 100%;
            background: rgba(15,23,42,0.5);
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
            color: #0369a1;
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
            font-size: 14px;
            font-weight: 600;
            color: #0f172a;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 250px;
        }

        .file-sub-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
        }

        .file-size {
            color: var(--text-muted);
        }

        .format-badge {
            padding: 1px 6px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
            background: #e2e8f0;
            color: var(--text-secondary);
        }

        .format-badge.spend {
            background: rgba(16, 185, 129, 0.15);
            color: #047857;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .format-badge.catalog {
            background: rgba(168, 85, 247, 0.15);
            color: #7e22ce;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        .btn-remove-file {
            background: transparent;
            border: 1px solid #cbd5e1;
            color: var(--text-muted);
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            flex-shrink: 0;
            transition: all 0.15s;
        }

        .btn-remove-file:hover {
            background: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.4);
            color: #b91c1c;
        }

        /* Guidance Cards */
        .guidance-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .guidance-box {
            background: rgba(15,23,42,0.04);
            border: 1px solid rgba(15,23,42,0.10);
            border-radius: 8px;
            padding: 10px 12px;
        }

        .guidance-label {
            font-size: 12px;
            font-weight: 600;
            color: #0f172a;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 4px;
        }

        .guidance-desc {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.35;
        }

        /* Responsive Status & Feedback */
        .import-status-box {
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 13px;
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
            color: #0369a1;
        }

        .import-status-box.error {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #b91c1c;
        }

        .import-status-box.success {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #047857;
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
            border-top: 1px solid rgba(15,23,42,0.10);
            background: rgba(15,23,42,0.45);
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

        /* ===== Friendly overrides (must come last) ===== */
        [hidden] { display: none !important; }
        .modal-footer { background: #f8fafc; }
        .badge-alert { font-family: var(--font-main); text-transform: none; letter-spacing: 0; font-size: 13px; font-weight: 700; padding: 4px 12px; border-radius: 999px; white-space: nowrap; }
        .health-modal-item-metrics { font-family: var(--font-main); font-size: 14px; color: var(--text-secondary); margin-bottom: 10px; }
        .health-modal-item-name { font-size: 16px; font-weight: 700; }
        .health-modal-title { font-size: 19px; }
        .health-modal-sub { font-size: 14px; }
        .health-modal-card { max-width: 680px; }
        .action-box { font-size: 14px; line-height: 1.5; padding: 10px 12px; }
        .health-modal-note { font-size: 14px; }

        /* ===== App shell: sidebar layout like the reference design ===== */
        :root { --bg-base: #f5f6fb; --brand: #1f2a8c; --brand-dark: #171f6b; --line: #eceef7; --card-shadow: 0 1px 2px rgba(20, 28, 80, 0.05), 0 10px 28px rgba(20, 28, 80, 0.07); }
        body { padding: 0; background: var(--bg-base); }
        .app-shell { display: grid; grid-template-columns: 250px minmax(0, 1fr); min-height: 100vh; }
        .app-main { padding: 28px 36px 64px; min-width: 0; }
        .page, .top-bar { max-width: 1800px; }

        .app-sidebar { position: sticky; top: 0; align-self: start; height: 100vh; background: #fafbff; border-right: 1px solid var(--line); display: flex; flex-direction: column; padding: 28px 16px 20px; z-index: 40; overflow-y: auto; }
        .side-brand-header { padding: 2px 4px 22px; position: relative; }
        .side-logo { padding: 0 0 12px; min-height: 40px; display: flex; align-items: center; }
        .brand-logo-panel { width: 100%; }
        .logo-img { display: block; width: 100%; max-width: 168px; height: auto; mix-blend-mode: multiply; }
        .logo-text { font-weight: 800; font-size: 22px; color: #0f172a; letter-spacing: -0.5px; }
        .side-mono { display: none; width: 44px; height: 44px; border-radius: 12px; background: #0f172a; color: #ffffff; font-weight: 800; font-size: 16px; align-items: center; justify-content: center; }
        .side-mono.rs { background: #d97706; }

        /* Brand Switcher in Sidebar */
        .brand-switcher { position: relative; width: 100%; }
        .brand-switcher-trigger {
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            padding: 8px 12px;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
            cursor: pointer;
            font-family: inherit;
            transition: all 0.15s ease;
        }
        .brand-switcher-trigger:hover {
            border-color: #cbd5e1;
            background: #f8fafc;
        }
        .brand-current-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
        }
        .brand-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .brand-status-dot.dot-live {
            background: #10b981;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
        }
        .brand-status-dot.dot-standby {
            background: #f59e0b;
            box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.25);
        }
        .brand-chevron {
            color: #94a3b8;
            transition: transform 0.2s ease;
            flex-shrink: 0;
        }
        .brand-switcher.open .brand-chevron {
            transform: rotate(180deg);
        }
        .brand-dropdown-menu {
            position: absolute;
            top: calc(100% + 6px);
            left: 0;
            right: 0;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 14px;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12), 0 8px 10px -6px rgba(15, 23, 42, 0.05);
            padding: 6px;
            z-index: 80;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .brand-dropdown-title {
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.08em;
            color: #94a3b8;
            padding: 6px 10px 4px;
            text-transform: uppercase;
        }
        .brand-menu-item {
            display: flex;
            align-items: center;
            gap: 10px;
            width: 100%;
            padding: 9px 10px;
            border: 0;
            border-radius: 10px;
            background: transparent;
            cursor: pointer;
            text-align: left;
            font-family: inherit;
            transition: background 0.15s ease;
        }
        .brand-menu-item:hover {
            background: #f1f5f9;
        }
        .brand-menu-item.active {
            background: #eef2ff;
        }
        .brand-menu-mono {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: #0f172a;
            color: #ffffff;
            font-size: 12px;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .brand-menu-mono.rs {
            background: #d97706;
        }
        .brand-menu-text {
            flex: 1;
            min-width: 0;
            display: flex;
            flex-direction: column;
        }
        .brand-menu-name {
            font-size: 13px;
            font-weight: 700;
            color: #0f172a;
            line-height: 1.2;
        }
        .brand-menu-status {
            font-size: 11px;
            font-weight: 500;
            color: #64748b;
            margin-top: 2px;
        }
        .brand-menu-status.live {
            color: #059669;
        }
        .brand-menu-status.standby {
            color: #d97706;
        }
        .brand-menu-check {
            color: var(--brand);
            display: none;
            flex-shrink: 0;
        }
        .brand-menu-item.active .brand-menu-check {
            display: block;
        }

        /* Top Bar quick switcher pill */
        .brand-pill-toggle {
            display: inline-flex;
            align-items: center;
            background: #f1f3fb;
            border-radius: 12px;
            padding: 3px;
            gap: 2px;
        }
        .brand-pill-btn {
            border: 0;
            background: transparent;
            padding: 7px 12px;
            min-height: 34px;
            border-radius: 9px;
            font-family: inherit;
            font-size: 13px;
            font-weight: 700;
            color: #475569;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 7px;
            transition: all 0.15s ease;
        }
        .brand-pill-btn:hover {
            color: #0f172a;
        }
        .brand-pill-btn.active {
            background: #ffffff;
            color: var(--brand);
            box-shadow: 0 1px 4px rgba(20, 28, 80, 0.12);
        }
        .mini-standby-tag {
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            padding: 2px 6px;
            border-radius: 6px;
            background: #fef3c7;
            color: #b45309;
        }

        /* Mobile bar brand switch */
        .mobile-brand-pill {
            border: 1px solid var(--line);
            background: #ffffff;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            color: #0f172a;
            font-family: inherit;
        }

        /* Room and Style Standby Page */
        .standby-freshness-chip {
            background: #fffbeb;
            border: 1px solid #fde68a;
            color: #b45309;
        }
        .standby-hero-card {
            background: linear-gradient(180deg, #ffffff 0%, #fafbff 100%);
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05);
            padding: 48px 32px 40px;
            margin-bottom: 24px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .standby-hero-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #d97706, #f59e0b, #fbbf24);
        }
        .standby-hero-inner {
            max-width: 580px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .standby-logo-display {
            margin-bottom: 20px;
            padding: 18px 32px;
            background: #ffffff;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.04);
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .standby-logo-display .logo-hero {
            display: block;
            max-width: 250px;
            height: auto;
            mix-blend-mode: multiply;
        }
        .standby-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 4px 12px;
            border-radius: 999px;
            background: #fffbeb;
            border: 1px solid #fde68a;
            color: #b45309;
            font-size: 12.5px;
            font-weight: 700;
            margin-bottom: 14px;
        }
        .pulse-dot-amber {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #d97706;
            box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.2);
            animation: amberPulse 2.4s infinite ease-in-out;
        }
        @keyframes amberPulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.15); }
        }
        .standby-headline {
            font-size: 25px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.4px;
            margin-bottom: 10px;
            line-height: 1.25;
        }
        .standby-description {
            font-size: 14.5px;
            color: #64748b;
            line-height: 1.6;
            margin-bottom: 24px;
            max-width: 520px;
        }
        .standby-actions-group {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        /* Activation pathway */
        .standby-pathway {
            list-style: none;
            margin: 16px 0 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .pathway-step {
            display: flex;
            align-items: flex-start;
            gap: 14px;
            padding: 12px 14px;
            background: #f8fafc;
            border: 1px solid #f1f5f9;
            border-radius: 12px;
        }
        .step-num {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            color: #475569;
            font-size: 12px;
            font-weight: 800;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            margin-top: 2px;
        }
        .step-body { flex: 1; min-width: 0; }
        .step-title { font-size: 14px; font-weight: 700; color: #0f172a; }
        .step-desc { font-size: 12.5px; color: #64748b; margin-top: 2px; }
        .step-status {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            margin-top: 4px;
        }
        .status-chip-standby {
            font-size: 11.5px;
            font-weight: 700;
            color: #b45309;
            background: #fef3c7;
            padding: 3px 9px;
            border-radius: 6px;
            white-space: nowrap;
        }
        .brand-summary-box {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 14px;
        }
        .brand-summary-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            font-size: 13.5px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--line);
        }
        .brand-summary-row:last-child { border-bottom: 0; }
        .bs-label { color: #64748b; font-weight: 500; }
        .bs-val { font-weight: 700; color: #0f172a; }
        .bs-val.badge-amber {
            background: #fef3c7;
            color: #b45309;
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 12px;
        }
        .standby-note {
            margin-top: 20px;
            padding: 14px;
            background: #f8fafc;
            border-left: 3px solid #d97706;
            border-radius: 0 10px 10px 0;
            font-size: 13px;
            color: #475569;
            line-height: 1.5;
        }

        .side-nav { display: flex; flex-direction: column; gap: 6px; }
        .nav-item { display: flex; align-items: center; gap: 14px; width: 100%; min-height: 48px; padding: 12px 14px; border: 0; border-radius: 14px; background: transparent; color: #475569; font-family: inherit; font-size: 15px; font-weight: 600; text-decoration: none; cursor: pointer; position: relative; }
        .nav-item:hover { background: #eef0fb; color: var(--brand); }
        .nav-item.active { background: #ffffff; color: var(--brand); box-shadow: 0 2px 14px rgba(31, 42, 140, 0.13); }
        .nav-item:focus-visible, .icon-btn:focus-visible, .seg-btn:focus-visible, .chip-btn:focus-visible, .more-item:focus-visible { outline: 3px solid #93c5fd; outline-offset: 2px; }
        .nav-badge { margin-left: auto; min-width: 22px; height: 22px; padding: 0 6px; border-radius: 11px; background: #ef4444; color: #ffffff; font-size: 12px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
        .side-foot { margin-top: auto; border-top: 1px solid var(--line); padding-top: 14px; }
        .nav-signout { color: #64748b; }
        .attn-trend { margin: 10px 0 0; padding: 10px 12px; border-radius: 10px; background: #f1f3fb; font-size: 13px; color: #334155; }
        .attn-trend ul { margin: 4px 0 0; padding-left: 18px; }
        .signout-form { margin: 0; display: inline-flex; }
        .btn-signout { display: inline-flex; align-items: center; gap: 6px; }

        .nav-backdrop { display: none; }
        .mobile-bar { display: none; }

        .top-bar { border: 0; padding: 0; margin: 0 0 24px; align-items: flex-start; justify-content: space-between; gap: 18px; }
        .greet-title { font-size: 30px; font-weight: 800; letter-spacing: -0.6px; color: #0f172a; line-height: 1.2; }
        .greet-sub { color: #64748b; font-size: 15px; margin: 4px 0 12px; }
        .top-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
        .icon-btn { position: relative; width: 46px; height: 46px; border-radius: 50%; border: 1px solid var(--line); background: #ffffff; color: #334155; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
        .icon-btn:hover { background: #eef0fb; color: var(--brand); }
        .bell-count { position: absolute; top: -4px; right: -4px; min-width: 20px; height: 20px; padding: 0 5px; border-radius: 10px; background: #ef4444; color: #ffffff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
        .more-menu { position: relative; }
        .more-list { position: absolute; right: 0; top: calc(100% + 6px); min-width: 190px; background: #ffffff; border: 1px solid var(--line); border-radius: 12px; box-shadow: var(--card-shadow); padding: 6px; z-index: 60; }
        .more-item { display: block; width: 100%; text-align: left; padding: 11px 12px; border: 0; border-radius: 8px; background: none; color: #334155; font-family: inherit; font-size: 14px; font-weight: 600; text-decoration: none; cursor: pointer; }
        .more-item:hover { background: #eef0fb; }

        .btn-action.btn-primary { background: var(--brand); border-color: var(--brand); color: #ffffff; }
        .btn-action.btn-primary:hover { background: var(--brand-dark); border-color: var(--brand-dark); color: #ffffff; }
        .btn-action.btn-primary:disabled { background: #a5aad6; border-color: #a5aad6; }
        .help-q { background: #eef0fb; color: var(--brand); }
        .brand-title .sub { color: var(--brand); }

        .card { background: #ffffff; border: 1px solid #f0f1f8; border-radius: 18px; box-shadow: var(--card-shadow); padding: 22px 24px; min-width: 0; }
        .card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
        .card-title { font-size: 19px; font-weight: 800; color: #0f172a; letter-spacing: -0.2px; }
        .card-sub { font-size: 14px; color: #64748b; margin-bottom: 12px; }
        .seg { display: inline-flex; background: #f1f3fb; border-radius: 10px; padding: 3px; gap: 2px; }
        .seg-btn { border: 0; background: transparent; padding: 7px 12px; min-height: 36px; border-radius: 8px; font-family: inherit; font-size: 13px; font-weight: 700; color: #475569; cursor: pointer; }
        .seg-btn.active { background: #ffffff; color: var(--brand); box-shadow: 0 1px 4px rgba(20, 28, 80, 0.14); }
        .chip-btn { background: #eef0fb; color: var(--brand); border: 0; border-radius: 8px; padding: 9px 14px; font-family: inherit; font-size: 13px; font-weight: 700; cursor: pointer; }
        .chip-btn:hover { background: #e2e6fa; }
        .grid-2 { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 22px; margin-bottom: 22px; }
        #health-chart-card .health-canvas { height: 340px; }

        .kpi-card { padding: 8px 0; margin-bottom: 22px; }
        .kpi-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 0; margin: 0; }
        .kpi-strip .health-kpi { border: 0; border-left: 1px solid var(--line); border-radius: 0; background: transparent; box-shadow: none; padding: 14px 24px; }
        .kpi-strip .health-kpi:first-child { border-left: 0; }
        .kpi-strip .health-kpi-label { font-size: 14px; font-weight: 600; color: #475569; }
        .kpi-strip .health-kpi-value { font-size: 28px; font-weight: 800; color: var(--brand); }
        .kpi-valrow { display: flex; align-items: center; gap: 10px; }
        .kpi-chip { display: inline-block; font-size: 12px; font-weight: 700; padding: 2px 8px; margin-left: 4px; border-radius: 999px; background: #fee2e2; color: #b91c1c; }
        .kpi-chip.ok { background: #d1fae5; color: #047857; }

        .sum-list, .top-list { list-style: none; margin: 16px 0 0; padding: 0; display: flex; flex-direction: column; gap: 16px; }
        .sum-list li, .top-item { display: flex; align-items: center; gap: 12px; }
        .sum-ico { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .sum-ico.healthy { background: #d1fae5; color: #047857; }
        .sum-ico.watch { background: #dbeafe; color: #1d4ed8; }
        .sum-ico.warning { background: #fef3c7; color: #b45309; }
        .sum-ico.critical { background: #fee2e2; color: #b91c1c; }
        .sum-name { font-weight: 600; color: #334155; font-size: 15px; }
        .sum-num { margin-left: auto; font-size: 20px; color: var(--brand); font-variant-numeric: tabular-nums; }
        .top-badge { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #ffffff; font-weight: 800; font-size: 14px; flex-shrink: 0; }
        .top-badge.healthy { background: #10b981; }
        .top-badge.watch { background: #3b82f6; }
        .top-badge.warning { background: #f59e0b; }
        .top-badge.critical { background: #ef4444; }
        .top-name { flex: 1; min-width: 0; font-weight: 700; font-size: 14px; color: #0f172a; line-height: 1.3; word-break: break-word; }
        .top-spend { font-weight: 800; color: var(--brand); font-size: 15px; white-space: nowrap; font-variant-numeric: tabular-nums; }

        /* campaign table inside the card */
        .camp-list { border: 0; border-radius: 0; box-shadow: none; background: transparent; overflow: visible; }
        .camp-head, .camp-row { grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr) minmax(0, 1fr) 92px; gap: 16px; padding: 12px 4px; }
        .camp-head { background: transparent; border-bottom: 1px solid var(--line); font-size: 13px; color: #64748b; }
        .camp-row { border-bottom: 1px solid var(--line); }
        .camp-row.critical, .camp-row.warning { background: transparent; }
        .camp-main { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; min-width: 0; }
        .camp-name { font-size: 15px; }
        .camp-spend { text-align: right; }

        .analytics-hub { border-radius: 18px; border: 1px solid #f0f1f8; box-shadow: var(--card-shadow); margin-top: 22px; }
        .health-more { border-radius: 18px; border: 1px solid #f0f1f8; box-shadow: var(--card-shadow); margin-bottom: 22px; }

        .logo-img { mix-blend-mode: multiply; }
        .modal-brand { padding: 18px 22px 12px; }
        .modal-brand .logo-img { height: 30px; width: auto; max-width: none; }
        .mobile-logo .logo-img { height: 28px; width: auto; max-width: none; }
        .mobile-logo .logo-text { font-size: 20px; }

        /* ---- tablets: icon rail ---- */
        @media (max-width: 1099px) and (min-width: 900px) {
            .app-shell { grid-template-columns: 78px minmax(0, 1fr); }
            .app-sidebar { padding: 22px 10px 16px; align-items: center; }
            .side-brand-header { padding: 0 0 22px; width: 100%; display: flex; flex-direction: column; align-items: center; }
            .side-logo { padding: 0; min-height: 0; }
            .side-logo .brand-logo-panel, .side-logo .logo-img, .side-logo .logo-text { display: none !important; }
            .brand-switcher { display: none; }
            .side-mono { display: flex; }
            .nav-item { justify-content: center; padding: 12px 0; }
            .nav-label { display: none; }
            .nav-badge { position: absolute; top: 2px; right: 2px; min-width: 18px; height: 18px; font-size: 11px; padding: 0 4px; }
            .app-main { padding: 24px 24px 56px; }
        }
        @media (max-width: 1099px) {
            .grid-2 { grid-template-columns: minmax(0, 1fr); }
            .kpi-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .kpi-strip .health-kpi:nth-child(3) { border-left: 0; }
            .kpi-strip .health-kpi:nth-child(n+3) { border-top: 1px solid var(--line); }
        }

        /* ---- phones and small tablets: drawer menu ---- */
        @media (max-width: 899px) {
            .app-shell { display: block; }
            .app-sidebar { position: fixed; left: 0; top: 0; bottom: 0; width: 276px; height: 100%; transform: translateX(-102%); transition: transform 0.25s ease; z-index: 3500; box-shadow: none; }
            body.nav-open .app-sidebar { transform: none; box-shadow: 0 0 40px rgba(15, 23, 42, 0.35); }
            .nav-backdrop { display: block; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); opacity: 0; pointer-events: none; transition: opacity 0.2s ease; z-index: 3400; }
            body.nav-open .nav-backdrop { opacity: 1; pointer-events: auto; }
            body.nav-open { overflow: hidden; }
            .mobile-bar { position: sticky; top: 0; z-index: 50; display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 0 -16px 18px; padding: 10px 16px; background: rgba(245, 246, 251, 0.96); backdrop-filter: blur(6px); border-bottom: 1px solid var(--line); }
            .app-main { padding: 0 16px 48px; }
            .bell-desktop { display: none; }
            .top-bar { flex-direction: column; align-items: stretch; gap: 14px; }
            .greet-title { font-size: 24px; }
            .top-actions { justify-content: flex-start; }
        }

        /* ---- phones ---- */
        @media (max-width: 700px) {
            .card { padding: 18px 16px; border-radius: 16px; }
            .kpi-strip .health-kpi { padding: 12px 14px; }
            .kpi-strip .health-kpi-value { font-size: 22px; }
            .camp-head { display: none; }
            .camp-row { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 10px 14px; padding: 14px 2px; }
            .camp-main { grid-column: 1 / -1; }
            .camp-spend { grid-column: 1 / -1; text-align: left; }
            .attn-metrics { grid-template-columns: minmax(0, 1fr); }
            #health-chart-card .health-canvas { height: 300px; }
            .seg { width: 100%; }
            .seg-btn { flex: 1; padding: 7px 6px; }
            .top-actions .btn-lg { flex: 1 1 100%; justify-content: center; }
        }
        @media (max-width: 420px) {
            .kpi-strip { grid-template-columns: minmax(0, 1fr); }
            .kpi-strip .health-kpi { border-left: 0; border-top: 1px solid var(--line); }
            .kpi-strip .health-kpi:first-child { border-top: 0; }
            .greet-title { font-size: 22px; }
            .freshness { font-size: 13px; }
        }
        @media (prefers-reduced-motion: reduce) {
            .app-sidebar, .nav-backdrop { transition: none; }
        }
    </style>
</head>
<body>
    <div class="app-shell" id="appShell">
        <div class="nav-backdrop" id="navBackdrop" onclick="closeNav()"></div>

        <!-- Left sidebar: logo and menu (no profile section) -->
        <aside class="app-sidebar" id="app-sidebar" aria-label="Sidebar">
            <div class="side-brand-header">
                <div class="side-logo" id="side-logo-wrap">
                    <div id="side-logo-hc" class="brand-logo-panel">__HC_LOGO_SIDEBAR__</div>
                    <div id="side-logo-rs" class="brand-logo-panel" style="display: none;">__RS_LOGO_SIDEBAR__</div>
                    <span class="side-mono" id="side-mono" aria-hidden="true">HC</span>
                </div>
                <div class="brand-switcher" id="sidebarBrandSwitcher">
                    <button type="button" class="brand-switcher-trigger" id="brandSwitcherTrigger" onclick="toggleBrandDropdown(event)" aria-haspopup="true" aria-expanded="false" title="Switch brand">
                        <span class="brand-current-pill">
                            <span class="brand-status-dot dot-live" id="sidebarBrandDot"></span>
                            <span class="brand-current-name" id="sidebarBrandName">Home Cartel</span>
                        </span>
                        <svg class="brand-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="m6 9 6 6 6-6"/></svg>
                    </button>
                    <div class="brand-dropdown-menu" id="brandDropdownMenu" hidden>
                        <div class="brand-dropdown-title">Switch brand</div>
                        <button type="button" class="brand-menu-item active" id="brand-item-homecartel" onclick="selectBrand('homecartel')">
                            <span class="brand-menu-mono">HC</span>
                            <div class="brand-menu-text">
                                <span class="brand-menu-name">Home Cartel</span>
                                <span class="brand-menu-status live">Live attribution</span>
                            </div>
                            <svg class="brand-menu-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        </button>
                        <button type="button" class="brand-menu-item" id="brand-item-roomandstyle" onclick="selectBrand('roomandstyle')">
                            <span class="brand-menu-mono rs">RS</span>
                            <div class="brand-menu-text">
                                <span class="brand-menu-name">Room and Style</span>
                                <span class="brand-menu-status standby">Standby</span>
                            </div>
                            <svg class="brand-menu-check" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        </button>
                    </div>
                </div>
            </div>
            <nav class="side-nav" aria-label="Main menu">
                <a href="#sec-dashboard" class="nav-item active" id="nav-dashboard" aria-current="page" onclick="navGo(event, 'dashboard')">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7.5" height="9" rx="2"></rect><rect x="13.5" y="3" width="7.5" height="5.5" rx="2"></rect><rect x="13.5" y="12" width="7.5" height="9" rx="2"></rect><rect x="3" y="15.5" width="7.5" height="5.5" rx="2"></rect></svg>
                    <span class="nav-label">Dashboard</span>
                </a>
                <a href="#sec-campaigns" class="nav-item" id="nav-campaigns" onclick="navGo(event, 'campaigns')">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 11v2a1 1 0 0 0 1 1h2l5 4V6L6 10H4a1 1 0 0 0-1 1z"></path><path d="M15.5 9a4 4 0 0 1 0 6"></path><path d="M18 6.5a8 8 0 0 1 0 11"></path></svg>
                    <span class="nav-label">Campaigns</span>
                </a>
                <a href="#sec-analytics" class="nav-item" id="nav-alerts" onclick="navGo(event, 'alerts')">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path></svg>
                    <span class="nav-label">Alerts</span>
                    <span class="nav-badge" id="nav-alert-count" hidden>0</span>
                </a>
                <a href="#sec-analytics" class="nav-item" id="nav-analytics" onclick="navGo(event, 'analytics')">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18"></path><path d="m7 15 4-4 3 3 5-6"></path></svg>
                    <span class="nav-label">Analytics</span>
                </a>
                <a href="#help" class="nav-item" id="nav-help" onclick="navGo(event, 'help')">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9.5"></circle><path d="M9.5 9.2a2.6 2.6 0 0 1 5 .9c0 1.7-2.5 2.2-2.5 3.7"></path><circle cx="12" cy="17.4" r="0.5"></circle></svg>
                    <span class="nav-label">Help</span>
                </a>
            </nav>
            <form class="side-foot" method="post" action="/logout">
                <button class="nav-item nav-signout" type="submit" aria-label="Sign out">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><path d="m16 17 5-5-5-5"></path><path d="M21 12H9"></path></svg>
                    <span class="nav-label">Sign out</span>
                </button>
            </form>
        </aside>

        <div class="app-main">
            <!-- Phone / tablet top bar -->
            <div class="mobile-bar">
                <button type="button" class="icon-btn" id="navToggle" onclick="toggleNav()" aria-label="Open menu" aria-expanded="false" aria-controls="app-sidebar">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><line x1="4" y1="7" x2="20" y2="7"></line><line x1="4" y1="12" x2="20" y2="12"></line><line x1="4" y1="17" x2="20" y2="17"></line></svg>
                </button>
                <div class="mobile-logo">
                    <div id="mobile-logo-hc" class="brand-logo-panel">__HC_LOGO_MOBILE__</div>
                    <div id="mobile-logo-rs" class="brand-logo-panel" style="display: none;">__RS_LOGO_MOBILE__</div>
                </div>
                <button type="button" class="mobile-brand-pill" onclick="toggleBrandDropdown(event)" aria-label="Switch brand">
                    <span id="mobileBrandLabel">HC</span>
                    <span class="brand-status-dot dot-live" id="mobileBrandDot"></span>
                </button>
                <button type="button" class="icon-btn bell" onclick="switchToAlertView()" aria-label="Open alerts">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path></svg>
                    <span class="bell-count" id="bell-count-m" hidden>0</span>
                </button>
            </div>

            <!-- Home Cartel Brand View -->
            <div id="brand-content-homecartel" class="brand-view-panel">
                <header class="top-bar" id="sec-dashboard">
                    <div class="greet">
                        <h1 class="greet-title" id="greet-title">Good morning!</h1>
                        <p class="greet-sub">Here is how your Meta ads are doing.</p>
                        <div class="freshness stale-none" id="freshness-chip" title="Shows how recent the last uploaded Meta report is">
                            <span class="fresh-dot" aria-hidden="true"></span>
                            <span id="freshness-text">Checking your data&hellip;</span>
                            <span class="fresh-period" id="freshness-period"></span>
                        </div>
                    </div>
                    <div class="top-actions">
                        <div class="brand-pill-toggle" role="tablist" aria-label="Brand switcher">
                            <button type="button" class="brand-pill-btn active" id="pill-hc" onclick="selectBrand('homecartel')" role="tab" aria-selected="true" title="Switch to Home Cartel">
                                <span class="brand-status-dot dot-live"></span>
                                <span>Home Cartel</span>
                            </button>
                            <button type="button" class="brand-pill-btn" id="pill-rs" onclick="selectBrand('roomandstyle')" role="tab" aria-selected="false" title="Switch to Room and Style (Standby)">
                                <span class="brand-status-dot dot-standby"></span>
                                <span>Room and Style</span>
                                <span class="mini-standby-tag">Standby</span>
                            </button>
                        </div>
                        <button type="button" class="icon-btn bell bell-desktop" onclick="switchToAlertView()" aria-label="Open alerts" title="Alerts">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"></path></svg>
                            <span class="bell-count" id="bell-count" hidden>0</span>
                        </button>
                    <button class="btn-action btn-primary btn-lg" id="btn-open-import" onclick="openImportModal()" aria-label="Import a new Meta report" title="Upload your latest Meta Ads Manager report">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        Import new report
                    </button>
                    <button class="btn-action" onclick="fetchClicks(true)" aria-label="Refresh the page data">Refresh</button>
                    <form class="signout-form" method="post" action="/logout">
                        <button type="submit" class="btn-action btn-signout" aria-label="Sign out of the dashboard" title="Sign out">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><path d="m16 17 5-5-5-5"></path><path d="M21 12H9"></path></svg>
                            Sign out
                        </button>
                    </form>
                    <div class="more-menu">
                        <button type="button" class="btn-action" id="moreBtn" onclick="toggleMore(event)" aria-haspopup="true" aria-expanded="false" aria-controls="moreMenu">More &#9662;</button>
                        <div class="more-list" id="moreMenu" hidden>
                            <button type="button" class="more-item" onclick="exportCSV(); closeMore()">Export CSV</button>
                            <a class="more-item" href="https://homecartel.net" target="_blank" rel="noopener noreferrer">Open store &nearr;</a>
                        </div>
                    </div>
                </div>
            </header>

            <main class="page" id="adHealthHub">
                <div class="status-banner neutral" id="health-banner" role="status" aria-live="polite">
                    <div class="status-icon" id="health-banner-icon" aria-hidden="true"></div>
                    <div class="status-text">
                        <div class="status-title" id="health-banner-title">Checking your campaigns&hellip;</div>
                        <div class="status-sub" id="health-banner-sub"></div>
                    </div>
                    <button type="button" class="btn-action btn-primary btn-lg" id="health-banner-cta" onclick="scrollToAttention()" hidden>See what to do</button>
                </div>

                <section class="card kpi-card" aria-label="Key numbers">
                    <div class="health-kpis kpi-strip">
                        <div class="health-kpi">
                            <div class="health-kpi-label">Ad spend <span class="tip" tabindex="0" title="Total money spent on your Meta ads in the period covered by the report.">?</span></div>
                            <div class="health-kpi-value" id="stat-ad-spend">&#8369;0</div>
                            <div class="health-kpi-sub" id="stat-ad-spend-footer">Waiting for your report&hellip;</div>
                        </div>
                        <div class="health-kpi">
                            <div class="health-kpi-label">Spend that needs attention <span class="tip" tabindex="0" title="Money spent on campaigns that are not healthy (Watch, Act soon or Act now).">?</span></div>
                            <div class="kpi-valrow"><div class="health-kpi-value" id="health-kpi-risk">&#8369;0</div><span class="kpi-chip" id="kpi-chip-risk" hidden></span></div>
                            <div class="health-kpi-sub" id="health-kpi-risk-sub">0% of your ad spend</div>
                        </div>
                        <div class="health-kpi">
                            <div class="health-kpi-label">Campaigns to review <span class="tip" tabindex="0" title="How many of your running campaigns are flagged, out of all running campaigns.">?</span></div>
                            <div class="health-kpi-value" id="health-kpi-attn">0 / 0</div>
                            <div class="health-kpi-sub" id="health-kpi-attn-sub">Flagged out of running campaigns</div>
                        </div>
                        <div class="health-kpi">
                            <div class="health-kpi-label">Times people saw your ads <span class="tip" tabindex="0" title="Average number of times one person saw your ads (called frequency). Above 2.5 people may start to get tired of them.">?</span></div>
                            <div class="kpi-valrow"><div class="health-kpi-value" id="health-kpi-freq">&mdash;</div><span class="kpi-chip" id="kpi-chip-freq" hidden></span></div>
                            <div class="health-kpi-sub">On average per person &middot; aim for under 2.5</div>
                        </div>
                    </div>
                </section>

                <div class="get-started" id="health-empty" hidden>
                    <div class="get-started-title">Let&rsquo;s get your first report in</div>
                    <ol>
                        <li>In <b>Meta Ads Manager</b>, open the <b>Campaigns</b> tab and export the table as a <b>.csv</b> file.</li>
                        <li>Click <b>Import new report</b> at the top of this page and choose that file.</li>
                        <li>Press <b>Upload &amp; Sync</b>. Your campaigns appear here with a colour for each one.</li>
                    </ol>
                    <button type="button" class="btn-action btn-primary btn-lg" onclick="openImportModal()">Import new report</button>
                </div>

                <section id="health-attention-wrap">
                    <h2 class="sect-title">Needs your attention</h2>
                    <div id="health-attention-list" class="attn-list"></div>
                </section>

                <div id="sec-campaigns" class="grid-2" aria-label="Campaigns">
                    <section class="card" id="health-chart-card">
                        <div class="card-head">
                            <h2 class="card-title">Campaign health</h2>
                            <div class="seg" role="group" aria-label="Choose what the chart shows">
                                <button type="button" class="seg-btn active" id="seg-freq" aria-pressed="true" onclick="setHealthMetric('freq')">Times seen</button>
                                <button type="button" class="seg-btn" id="seg-ctr" aria-pressed="false" onclick="setHealthMetric('ctr')">Clicks</button>
                                <button type="button" class="seg-btn" id="seg-cpc" aria-pressed="false" onclick="setHealthMetric('cpc')">Cost per click</button>
                            </div>
                        </div>
                        <p class="card-sub" id="health-chart-sub">Dotted lines show where Watch, Act soon and Act now start.</p>
                        <div class="chart-canvas-wrap health-canvas" id="health-charts"><canvas id="chartHealthMain" role="img" aria-label="Campaign health chart"></canvas></div>
                    </section>
                    <section class="card side-card" aria-label="Status summary">
                        <h2 class="card-title">Status summary</h2>
                        <ul class="sum-list">
                            <li><span class="sum-ico healthy" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="5 12.5 10 17.5 19 7.5"></polyline></svg></span><span class="sum-name">Healthy</span><b class="sum-num" id="sum-healthy">0</b></li>
                            <li><span class="sum-ico watch" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"></path><circle cx="12" cy="12" r="3"></circle></svg></span><span class="sum-name">Watch</span><b class="sum-num" id="sum-watch">0</b></li>
                            <li><span class="sum-ico warning" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5 22 20.5H2z"></path><line x1="12" y1="10" x2="12" y2="14.5"></line></svg></span><span class="sum-name">Act soon</span><b class="sum-num" id="sum-warning">0</b></li>
                            <li><span class="sum-ico critical" aria-hidden="true"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.5"></circle><line x1="12" y1="7" x2="12" y2="13"></line></svg></span><span class="sum-name">Act now</span><b class="sum-num" id="sum-critical">0</b></li>
                        </ul>
                    </section>
                </div>

                <div class="grid-2" id="health-campaigns-wrap">
                    <section class="card">
                        <div class="card-head">
                            <h2 class="card-title">Campaign performance</h2>
                            <button type="button" class="chip-btn" onclick="switchToAlertView()">See all</button>
                        </div>
                        <div id="health-campaigns" class="camp-list"></div>
                    </section>
                    <section class="card side-card" aria-label="Top campaigns by spend">
                        <h2 class="card-title">Top campaigns by spend</h2>
                        <ul class="top-list" id="top-spend-list"></ul>
                    </section>
                </div>

                <details class="health-more" id="health-more">
                    <summary>What is not checked yet</summary>
                    <div class="health-coverage-note">
                        <strong>Not checked yet:</strong> day-by-day trends, single-ad rankings, and the three alerts that compare an ad with its own past
                        (Creative Fatigue, Expensive Ads, Delivery Problem). They need daily data from Meta, which is not connected yet.
                        Campaigns whose name contains &ldquo;FR Stores&rdquo; (Reach campaigns) and paused campaigns are left out on purpose.
                    </div>
                </details>

                <section id="sec-analytics" aria-label="Analytics and alerts">
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

                </section>
            </main>
        </div><!-- end #brand-content-homecartel -->

        <!-- Room and Style Brand View (Standby) -->
        <div id="brand-content-roomandstyle" class="brand-view-panel" style="display: none;">
            <header class="top-bar">
                <div class="greet">
                    <h1 class="greet-title">Room and Style</h1>
                    <p class="greet-sub">Ad attribution and sales reconciliation pipeline.</p>
                    <div class="freshness standby-freshness-chip">
                        <span class="fresh-dot dot-standby" aria-hidden="true"></span>
                        <span>System Status: <strong>Standby</strong></span>
                    </div>
                </div>
                <div class="top-actions">
                    <div class="brand-pill-toggle" role="tablist" aria-label="Brand switcher">
                        <button type="button" class="brand-pill-btn" onclick="selectBrand('homecartel')" role="tab" aria-selected="false" title="Switch to Home Cartel">
                            <span class="brand-status-dot dot-live"></span>
                            <span>Home Cartel</span>
                        </button>
                        <button type="button" class="brand-pill-btn active" onclick="selectBrand('roomandstyle')" role="tab" aria-selected="true" title="Room and Style (Standby)">
                            <span class="brand-status-dot dot-standby"></span>
                            <span>Room and Style</span>
                            <span class="mini-standby-tag">Standby</span>
                        </button>
                    </div>
                    <form class="signout-form" method="post" action="/logout">
                        <button type="submit" class="btn-action btn-signout" aria-label="Sign out">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><path d="m16 17 5-5-5-5"></path><path d="M21 12H9"></path></svg>
                            Sign out
                        </button>
                    </form>
                </div>
            </header>

            <main class="page">
                <!-- Standby Hero Banner -->
                <section class="card standby-hero-card">
                    <div class="standby-hero-inner">
                        <div class="standby-logo-display">
                            __RS_LOGO_HERO__
                        </div>
                        <div class="standby-status-pill" aria-label="STANDBY">
                            <span class="pulse-dot-amber"></span>
                            <span>STANDBY</span>
                        </div>
                        <h2 class="standby-headline">Room and Style is currently on Standby</h2>
                        <p class="standby-description">
                            The attribution pipeline and marketing intelligence system for Room and Style are in standby. Tracking endpoints, Meta ad datasets, and order reconciliation are queued for activation.
                        </p>
                        <div class="standby-actions-group">
                            <button type="button" class="btn-action btn-primary btn-lg" onclick="selectBrand('homecartel')">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
                                Switch to Home Cartel
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Standby Activation Pathway & Overview -->
                <div class="grid-2">
                    <section class="card">
                        <div class="card-head">
                            <h3 class="card-title">Activation pathway</h3>
                            <span class="status-chip-standby">Standby</span>
                        </div>
                        <p class="card-sub">Three sequential milestones to connect Room and Style to live attribution:</p>
                        <ol class="standby-pathway">
                            <li class="pathway-step">
                                <span class="step-num">1</span>
                                <div class="step-body">
                                    <div class="step-title">Storefront tracking script</div>
                                    <div class="step-desc">Embed click tracking tag on roomandstyle.ph to capture UTM tags and generate click session tokens.</div>
                                    <span class="step-status">Endpoint prepared &middot; Pending snippet placement</span>
                                </div>
                            </li>
                            <li class="pathway-step">
                                <span class="step-num">2</span>
                                <div class="step-body">
                                    <div class="step-title">Meta Ads daily spend dataset</div>
                                    <div class="step-desc">Connect Room and Style ad account ID in multi-brand schema to import daily breakdown reports.</div>
                                    <span class="step-status">Database schema ready &middot; Awaiting ad account ID</span>
                                </div>
                            </li>
                            <li class="pathway-step">
                                <span class="step-num">3</span>
                                <div class="step-body">
                                    <div class="step-title">Zoho Creator orders &amp; CAPI feedback</div>
                                    <div class="step-desc">Route sales order webhooks by brand tag to close the loop with Meta Conversions API.</div>
                                    <span class="step-status">Webhook receiver active &middot; Brand filter unassigned</span>
                                </div>
                            </li>
                        </ol>
                    </section>

                    <section class="card side-card">
                        <div class="card-head">
                            <h3 class="card-title">Brand status</h3>
                        </div>
                        <div class="brand-summary-box">
                            <div class="brand-summary-row">
                                <span class="bs-label">Active workspace</span>
                                <span class="bs-val">Room and Style</span>
                            </div>
                            <div class="brand-summary-row">
                                <span class="bs-label">Pipeline state</span>
                                <span class="bs-val badge-amber">Standby</span>
                            </div>
                            <div class="brand-summary-row">
                                <span class="bs-label">Database partition</span>
                                <span class="bs-val">Multi-brand schema ready</span>
                            </div>
                            <div class="brand-summary-row">
                                <span class="bs-label">Target domain</span>
                                <span class="bs-val">roomandstyle.ph</span>
                            </div>
                        </div>
                        <div class="standby-note">
                            To view live campaigns, spend alerts, and attributed revenue, switch to <strong>Home Cartel</strong>.
                        </div>
                    </section>
                </div>
            </main>
        </div><!-- end #brand-content-roomandstyle -->
    </div>
</div>

    <!-- Responsive Meta Ads CSV/TSV Import Modal -->
    <div class="modal-backdrop" id="importModal" role="dialog" aria-modal="true" aria-labelledby="modalTitle" onclick="handleBackdropClick(event)">
        <div class="modal-card">
            <div class="modal-brand">__HC_LOGO_MODAL__</div>
            <div class="modal-header">
                <div class="modal-title-group">
                    <div class="modal-title" id="modalTitle">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #0369a1;">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="17 8 12 3 7 8"></polyline>
                            <line x1="12" y1="3" x2="12" y2="15"></line>
                        </svg>
                        Import new report
                        <span class="modal-title-badge">CSV</span>
                    </div>
                    <div class="modal-subtitle">
                        Upload your Meta Ads Manager campaign report to update this page.
                    </div>
                </div>
                <button class="modal-close-btn" onclick="closeImportModal()" aria-label="Close dialog">&times;</button>
            </div>

            <div class="modal-body">
                <div class="import-steps">
                    <div class="import-step"><b>1. Export from Meta</b>Ads Manager &rarr; Campaigns tab &rarr; Export table data (.csv). Upload the summary report and the daily report (Breakdown &rarr; By Time &rarr; Day), one at a time</div>
                    <div class="import-step"><b>2. Choose the file</b>Drop it in the box below</div>
                    <div class="import-step"><b>3. Upload</b>Press the blue button. The page updates by itself</div>
                </div>

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
                            Table export with Amount Spent, CPC, CTR, Impressions &amp; Link Clicks. Updates the charts, colours and alerts.
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

    <!-- Help panel: how to read this page, in plain words -->
    <div class="health-modal-backdrop" id="helpModal" role="dialog" aria-modal="true" aria-labelledby="helpModalTitle" hidden onclick="if (event.target === this) closeHelp()">
        <div class="health-modal-card">
            <div class="health-modal-head">
                <div>
                    <div class="health-modal-title" id="helpModalTitle">How to read this page</div>
                    <div class="health-modal-sub">A quick guide, no technical knowledge needed</div>
                </div>
                <button type="button" class="modal-close-btn" onclick="closeHelp()" aria-label="Close help">&times;</button>
            </div>
            <div class="health-modal-body">
                <div class="help-block">
                    <h3>The colours</h3>
                    <div class="help-row"><span class="badge-alert healthy">Healthy</span><span>Nothing to do. This campaign is inside the safe range.</span></div>
                    <div class="help-row"><span class="badge-alert watch">Watch</span><span>People have seen the ads more than 2.5 times each. Keep an eye on it.</span></div>
                    <div class="help-row"><span class="badge-alert warning">Act soon</span><span>Seen more than 3.5 times, or fewer than 0.67% of viewers click. Change the audience or the ad within a few days.</span></div>
                    <div class="help-row"><span class="badge-alert critical">Act now</span><span>Seen more than 4.5 times, or fewer than 0.43% click. Pause the ad set or ad that is wasting money, then replace it.</span></div>
                </div>
                <div class="help-block">
                    <h3>The words</h3>
                    <p><b>Times seen (frequency):</b> how many times the same person saw your ad. Too many and people get tired of it.</p>
                    <p><b>Clicks (Link CTR):</b> out of 100 people who saw the ad, how many clicked the link. Higher is better.</p>
                    <p><b>Spend that needs attention:</b> the money spent on campaigns that are not healthy.</p>
                </div>
                <div class="help-block">
                    <h3>Keeping it up to date</h3>
                    <p>This page is not live. It shows the last report you uploaded (see the date at the top). To refresh it, export your <b>Campaigns</b> table from Meta Ads Manager as a .csv file, click <b>Import new report</b>, and upload it. Pop-ups and emails go out when a campaign gets worse.</p>
                </div>
            </div>
            <div class="health-modal-foot">
                <button type="button" class="btn-action btn-primary" onclick="closeHelp()">Got it</button>
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
                closeNav();
                closeMore();
                closeHelp();
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

                const dataLine = (evt.target.result || '').split(String.fromCharCode(10)).slice(1, 2)[0] || '';
                const dataCols = dataLine.split(',');
                const isDaily = isSpend && dataCols.length > 2 && dataCols[0].length === 10 && dataCols[0] === dataCols[1];

                if (isDaily) {
                    badge.innerText = 'Daily Breakdown Report';
                    badge.className = 'format-badge spend';
                } else if (isSpend) {
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
            content.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:1px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> <div><strong>Success:</strong> ${msg} ${details ? `<div style="margin-top:2px;font-size: 12px;opacity:0.9;">${details}</div>` : ''}</div>`;
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

                const isSpendType = data.type === 'campaign_spend' || data.type === 'campaign_daily';
                const detailsText = data.type === 'campaign_daily'
                    ? `Daily report: ${data.rows_processed || 0} rows · Status now: ${data.overall_status || 'HEALTHY'}`
                    : (data.type === 'campaign_spend'
                        ? `Total Spend: ₱${Number(data.total_spend || 0).toLocaleString()} · Section 2.6.4 Status: ${data.overall_status || 'HEALTHY'}`
                        : `Catalog Records: ${data.rows_processed || 0}`);

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
                    if (isSpendType) showImportAlerts(data);
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
                let lastChartDataSig = '';

        let currentAlertFilter = 'ALL';
        let allAlertEvaluations = [];
        let allAlertRules = [];

        function switchToAlertView() {
            const tab = document.getElementById('tab-v5');
            switchAnalyticsView('v5', tab);
            setActiveNav('alerts');
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
            if (typeof Chart === 'undefined' || !canvas || items.length === 0) return null;
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
                        y: { grid: { display: false }, ticks: { font: { size: 12 } } }
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

        // --- Friendly ad health view: banner, freshness, cards and campaign rows ---
        const LEVEL_TEXT = { CRITICAL: 'Act now', WARNING: 'Act soon', WATCH: 'Watch', HEALTHY: 'Healthy' };
        const LEVEL_RANK = { CRITICAL: 0, WARNING: 1, WATCH: 2, HEALTHY: 3 };

        const ICON_OK = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="5 12.5 10 17.5 19 7.5"></polyline></svg>';
        const ICON_EYE = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
        const ICON_WARN = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5 22 20.5H2z"></path><line x1="12" y1="10" x2="12" y2="14.5"></line><circle cx="12" cy="17.5" r="0.6"></circle></svg>';
        const ICON_STOP = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.5"></circle><line x1="12" y1="7" x2="12" y2="13"></line><circle cx="12" cy="16.6" r="0.6"></circle></svg>';
        const ICON_INFO = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.5"></circle><line x1="12" y1="11" x2="12" y2="17"></line><circle cx="12" cy="7.6" r="0.6"></circle></svg>';

        function plural(n, one, many) { return n === 1 ? one : many; }

        function reportAgeDays(str) {
            if (!str) return null;
            let s = String(str).trim().replace(' ', 'T');
            if (!/[zZ]$|[+-][0-9]{2}:?[0-9]{2}$/.test(s)) s += 'Z';
            const d = new Date(s);
            if (isNaN(d.getTime())) return null;
            return Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000));
        }

        function formatShortDate(iso) {
            if (!iso) return '';
            const d = new Date(String(iso).slice(0, 10) + 'T00:00:00');
            if (isNaN(d.getTime())) return String(iso);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }

        function renderFreshness(summary) {
            const chip = document.getElementById('freshness-chip');
            const text = document.getElementById('freshness-text');
            const period = document.getElementById('freshness-period');
            if (!chip || !text) return;
            const days = reportAgeDays(summary && summary.data_as_of);
            chip.classList.remove('fresh', 'aging', 'old', 'stale-none');
            if (days === null) {
                chip.classList.add('stale-none');
                text.innerText = 'No report uploaded yet';
                if (period) period.innerText = '';
                chip.title = 'Import a Meta report to start';
                return;
            }
            const when = days === 0 ? 'today' : (days === 1 ? 'yesterday' : days + ' days ago');
            if (days <= 2) { chip.classList.add('fresh'); text.innerText = 'Report updated ' + when; }
            else if (days <= 6) { chip.classList.add('aging'); text.innerText = 'Report updated ' + when + ' · consider importing a new one'; }
            else { chip.classList.add('old'); text.innerText = 'Report is out of date (' + when + ') · import a new one'; }
            const w = (summary && summary.window) || {};
            if (period) period.innerText = (w.start && w.end) ? 'Covers ' + formatShortDate(w.start) + ' – ' + formatShortDate(w.end) : '';
            const dw = summary.daily_window || {};
            chip.title = 'Last uploaded: ' + summary.data_as_of + ' (source: Meta CSV import)' +
                (dw.start ? '. Daily report: ' + dw.start + ' to ' + dw.end + ' (' + dw.days + ' days)' : '. No daily report yet, so trend checks are off');
        }

        function renderHealthBanner(counts, total, attn, atRisk, totalSpend) {
            const banner = document.getElementById('health-banner');
            if (!banner) return;
            const icon = document.getElementById('health-banner-icon');
            const title = document.getElementById('health-banner-title');
            const sub = document.getElementById('health-banner-sub');
            const cta = document.getElementById('health-banner-cta');
            const crit = counts.critical || 0, warn = counts.warning || 0, watch = counts.watch || 0;
            banner.classList.remove('healthy', 'watch', 'warning', 'critical', 'neutral');
            const pct = totalSpend > 0 ? Math.round((atRisk / totalSpend) * 100) : 0;
            const money = '₱' + Math.round(atRisk).toLocaleString();
            if (!total) {
                banner.classList.add('neutral'); icon.innerHTML = ICON_INFO;
                title.innerText = 'No campaign data yet';
                sub.innerText = 'Import your Meta report to see how your ads are doing.';
                cta.hidden = true;
                return;
            }
            if (crit > 0) {
                banner.classList.add('critical'); icon.innerHTML = ICON_STOP;
                title.innerText = crit + ' ' + plural(crit, 'campaign needs', 'campaigns need') + ' action now';
            } else if (warn > 0) {
                banner.classList.add('warning'); icon.innerHTML = ICON_WARN;
                title.innerText = warn + ' ' + plural(warn, 'campaign needs', 'campaigns need') + ' action soon';
            } else if (watch > 0) {
                banner.classList.add('watch'); icon.innerHTML = ICON_EYE;
                title.innerText = watch + ' ' + plural(watch, 'campaign needs', 'campaigns need') + ' a look';
            } else {
                banner.classList.add('healthy'); icon.innerHTML = ICON_OK;
                title.innerText = 'All ' + total + ' running ' + plural(total, 'campaign is', 'campaigns are') + ' healthy';
            }
            if (attn > 0) {
                sub.innerText = (total - attn) + ' of ' + total + ' are healthy. ' + money + ' (' + pct + '%) of your ad spend is in campaigns that need attention.';
                cta.hidden = false;
            } else {
                sub.innerText = 'Nothing needs your attention right now.';
                cta.hidden = true;
            }
        }

        function scrollToAttention() {
            const el = document.getElementById('health-attention-wrap');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function miniBar(value, max, marks, color) {
            const pct = Math.max(2, Math.min(100, (value / max) * 100));
            const m = marks.map(x => '<i class="mark" style="left:' + Math.min(100, (x.at / max) * 100) + '%" title="' + healthEsc(x.title) + '"></i>').join('');
            return '<div class="mbar"><div class="mfill" style="width:' + pct + '%;background:' + color + '"></div>' + m + '</div>';
        }

        function renderAttentionCards(flagged, th) {
            const fq = th.frequency || {};
            const ct = th.ctr || {};
            return flagged.map(e => {
                const cls = e.level.toLowerCase();
                const freq = Number(e.frequency || 0);
                const ctr = Number(e.ctr || 0);
                const freqBad = fq.watch != null && freq > fq.watch;
                const ctrBad = ct.warning != null && ctr < ct.warning;
                const sop = e.sop && e.sop.steps && e.sop.steps.length
                    ? '<details class="health-sop"><summary>Step-by-step: ' + healthEsc(e.sop.title) + '</summary><ol>' + e.sop.steps.map(s => '<li>' + healthEsc(s) + '</li>').join('') + '</ol></details>'
                    : '';
                const trendLines = (e.alerts || []).filter(a => a.detail)
                    .map(a => '<li>' + healthEsc(a.detail) + '</li>').join('');
                const trendBox = trendLines
                    ? '<div class="attn-trend"><strong>Compared with earlier days</strong><ul>' + trendLines + '</ul></div>'
                    : '';
                return '<article class="attn-card ' + cls + '">' +
                    '<div class="attn-head"><span class="badge-alert ' + cls + '">' + healthEsc(LEVEL_TEXT[e.level] || e.level) + '</span>' +
                    '<h3 class="attn-name">' + healthEsc(e.campaign_name) + '</h3></div>' +
                    '<div class="attn-metrics">' +
                    '<div class="attn-metric' + (freqBad ? ' bad' : '') + '"><div class="m-val">' + freq.toFixed(2) + '×</div><div class="m-lab">times each person saw your ad' + (fq.watch != null ? '<span>aim for under ' + fq.watch + '</span>' : '') + '</div></div>' +
                    '<div class="attn-metric' + (ctrBad ? ' bad' : '') + '"><div class="m-val">' + ctr.toFixed(2) + '%</div><div class="m-lab">of viewers clicked' + (ct.warning != null ? '<span>aim for over ' + ct.warning + '%</span>' : '') + '</div></div>' +
                    '<div class="attn-metric"><div class="m-val">₱' + Math.round(e.spend || 0).toLocaleString() + '</div><div class="m-lab">spent in this report</div></div>' +
                    '</div>' +
                    trendBox +
                    '<p class="attn-action"><strong>What to do:</strong> ' + healthEsc(e.primary_action) + '</p>' +
                    sop +
                    '<button type="button" class="btn-link" onclick="switchToAlertView()">Open in Alert Center →</button>' +
                    '</article>';
            }).join('');
        }

        function renderCampaignRows(evals, th) {
            const fq = th.frequency || {};
            const ct = th.ctr || {};
            const colorFor = lvl => lvl === 'CRITICAL' ? HEALTH_COLORS.critical : lvl === 'WARNING' ? HEALTH_COLORS.warning : lvl === 'WATCH' ? HEALTH_COLORS.watch : HEALTH_COLORS.healthy;
            const rows = evals.slice().sort((a, b) => (LEVEL_RANK[a.level] - LEVEL_RANK[b.level]) || (Number(b.spend || 0) - Number(a.spend || 0)));
            const freqMarks = [fq.watch, fq.warning, fq.critical].filter(v => v != null).map(v => ({ at: v, title: 'Limit ' + v + '×' }));
            const ctrMarks = [ct.critical, ct.warning].filter(v => v != null).map(v => ({ at: v, title: 'Limit ' + v + '%' }));
            const head = '<div class="camp-head"><div>Campaign</div><div>Times seen (under ' + (fq.watch != null ? fq.watch : 2.5) + ')</div><div>Clicks (over ' + (ct.warning != null ? ct.warning : 0.67) + '%)</div><div style="text-align:right">Spent</div></div>';
            return head + rows.map(e => {
                const cls = e.level.toLowerCase();
                const freq = Number(e.frequency || 0);
                const ctr = Number(e.ctr || 0);
                return '<div class="camp-row ' + cls + '">' +
                    '<div class="camp-main"><div class="camp-name" title="' + healthEsc(e.campaign_name) + '">' + healthEsc(e.campaign_name) + '</div>' +
                    '<span class="badge-alert ' + cls + '">' + healthEsc(LEVEL_TEXT[e.level] || e.level) + '</span></div>' +
                    '<div class="camp-cell"><b>' + freq.toFixed(2) + '×</b><span>seen per person</span>' + miniBar(freq, 5.5, freqMarks, freq > (fq.watch != null ? fq.watch : 99) ? colorFor(e.level) : HEALTH_COLORS.healthy) + '</div>' +
                    '<div class="camp-cell"><b>' + ctr.toFixed(2) + '%</b><span>click</span>' + miniBar(ctr, 3, ctrMarks, ctr < (ct.warning != null ? ct.warning : 0) ? colorFor(e.level) : HEALTH_COLORS.healthy) + '</div>' +
                    '<div class="camp-spend"><b>₱' + Math.round(e.spend || 0).toLocaleString() + '</b></div>' +
                    '</div>';
            }).join('');
        }

        function openHelp() {
            const m = document.getElementById('helpModal');
            if (!m) return;
            healthModalOpener = document.activeElement;
            m.hidden = false;
        }

        function closeHelp() {
            const m = document.getElementById('helpModal');
            if (!m || m.hidden) return;
            m.hidden = true;
            if (healthModalOpener && healthModalOpener.focus) healthModalOpener.focus();
        }

        // --- App shell: greeting, side menu, main chart and side cards ---
        let chartHealthMain = null;
        let healthMetric = 'freq';
        let healthChartData = null;
        let navReturnFocus = null;

        function setGreeting() {
            const el = document.getElementById('greet-title');
            if (!el) return;
            const h = new Date().getHours();
            el.innerText = h < 12 ? 'Good morning!' : (h < 18 ? 'Good afternoon!' : 'Good evening!');
        }

        function openNav() {
            document.body.classList.add('nav-open');
            const b = document.getElementById('navToggle');
            if (b) b.setAttribute('aria-expanded', 'true');
            navReturnFocus = document.activeElement;
            const first = document.querySelector('#app-sidebar .nav-item');
            if (first) first.focus();
        }

        function closeNav() {
            if (!document.body.classList.contains('nav-open')) return;
            document.body.classList.remove('nav-open');
            const b = document.getElementById('navToggle');
            if (b) b.setAttribute('aria-expanded', 'false');
            if (navReturnFocus && navReturnFocus.focus) navReturnFocus.focus();
        }

        function toggleNav() {
            if (document.body.classList.contains('nav-open')) closeNav(); else openNav();
        }

        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab' || !document.body.classList.contains('nav-open')) return;
            const items = Array.from(document.querySelectorAll('#app-sidebar .nav-item'));
            if (!items.length) return;
            const first = items[0];
            const last = items[items.length - 1];
            if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
            else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
        });

        function setActiveNav(key) {
            ['dashboard', 'campaigns', 'alerts', 'analytics'].forEach(k => {
                const a = document.getElementById('nav-' + k);
                if (!a) return;
                a.classList.toggle('active', k === key);
                if (k === key) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
            });
        }

        function scrollToEl(id) {
            const el = document.getElementById(id);
            if (el && !el.hidden) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function toggleBrandDropdown(ev) {
            if (ev) ev.stopPropagation();
            const menu = document.getElementById('brandDropdownMenu');
            const trigger = document.getElementById('brandSwitcherTrigger');
            const switcher = document.getElementById('sidebarBrandSwitcher');
            if (!menu) return;
            const willOpen = menu.hidden;
            menu.hidden = !willOpen;
            if (switcher) switcher.classList.toggle('open', willOpen);
            if (trigger) trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        }

        function closeBrandMenu() {
            const menu = document.getElementById('brandDropdownMenu');
            const trigger = document.getElementById('brandSwitcherTrigger');
            const switcher = document.getElementById('sidebarBrandSwitcher');
            if (menu) menu.hidden = true;
            if (switcher) switcher.classList.remove('open');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }

        function selectBrand(brand) {
            if (brand !== 'homecartel' && brand !== 'roomandstyle') brand = 'homecartel';
            try {
                localStorage.setItem('active_brand_choice', brand);
            } catch(e) {}

            const isRS = (brand === 'roomandstyle');

            const hcSide = document.getElementById('side-logo-hc');
            const rsSide = document.getElementById('side-logo-rs');
            const hcMob = document.getElementById('mobile-logo-hc');
            const rsMob = document.getElementById('mobile-logo-rs');
            const sideMono = document.getElementById('side-mono');

            if (hcSide) hcSide.style.display = isRS ? 'none' : 'block';
            if (rsSide) rsSide.style.display = isRS ? 'block' : 'none';
            if (hcMob) hcMob.style.display = isRS ? 'none' : 'block';
            if (rsMob) rsMob.style.display = isRS ? 'block' : 'none';
            if (sideMono) {
                sideMono.innerText = isRS ? 'RS' : 'HC';
                sideMono.classList.toggle('rs', isRS);
            }

            const nameEl = document.getElementById('sidebarBrandName');
            const dotEl = document.getElementById('sidebarBrandDot');
            if (nameEl) nameEl.innerText = isRS ? 'Room and Style' : 'Home Cartel';
            if (dotEl) {
                dotEl.classList.toggle('dot-standby', isRS);
                dotEl.classList.toggle('dot-live', !isRS);
            }

            const itemHC = document.getElementById('brand-item-homecartel');
            const itemRS = document.getElementById('brand-item-roomandstyle');
            if (itemHC) itemHC.classList.toggle('active', !isRS);
            if (itemRS) itemRS.classList.toggle('active', isRS);

            const pillHC = document.getElementById('pill-hc');
            const pillRS = document.getElementById('pill-rs');
            if (pillHC) {
                pillHC.classList.toggle('active', !isRS);
                pillHC.setAttribute('aria-selected', !isRS ? 'true' : 'false');
            }
            if (pillRS) {
                pillRS.classList.toggle('active', isRS);
                pillRS.setAttribute('aria-selected', isRS ? 'true' : 'false');
            }

            const mobLabel = document.getElementById('mobileBrandLabel');
            const mobDot = document.getElementById('mobileBrandDot');
            if (mobLabel) mobLabel.innerText = isRS ? 'RS' : 'HC';
            if (mobDot) {
                mobDot.classList.toggle('dot-standby', isRS);
                mobDot.classList.toggle('dot-live', !isRS);
            }

            const hcContent = document.getElementById('brand-content-homecartel');
            const rsContent = document.getElementById('brand-content-roomandstyle');
            if (hcContent) hcContent.style.display = isRS ? 'none' : 'block';
            if (rsContent) rsContent.style.display = isRS ? 'block' : 'none';

            document.title = isRS ? 'Room and Style | Standby' : 'Home Cartel | Ad Attribution';
            closeBrandMenu();

            if (isRS) {
                setActiveNav('dashboard');
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }

        function navGo(ev, key) {
            if (ev) ev.preventDefault();
            closeNav();
            if (key === 'help') { openHelp(); return; }
            const activeBrand = (function() {
                try { return localStorage.getItem('active_brand_choice') || 'homecartel'; }
                catch(e) { return 'homecartel'; }
            })();
            if (activeBrand === 'roomandstyle' && key !== 'dashboard') {
                selectBrand('homecartel');
                showToast('Switched to Home Cartel to view ' + key);
            }
            setActiveNav(key);
            if (key === 'dashboard') { window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
            if (key === 'campaigns') {
                const sec = document.getElementById('sec-campaigns');
                scrollToEl(sec && !sec.hidden ? 'sec-campaigns' : 'sec-analytics');
                return;
            }
            if (key === 'alerts') { switchToAlertView(); return; }
            if (key === 'analytics') {
                switchAnalyticsView('v1', document.getElementById('tab-v1'));
                scrollToEl('sec-analytics');
            }
        }

        function toggleMore(ev) {
            if (ev) ev.stopPropagation();
            const m = document.getElementById('moreMenu');
            const b = document.getElementById('moreBtn');
            if (!m || !b) return;
            const willOpen = m.hidden;
            menu_open = willOpen;
            m.hidden = !willOpen;
            b.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        }

        function closeMore() {
            const m = document.getElementById('moreMenu');
            const b = document.getElementById('moreBtn');
            if (m) m.hidden = true;
            if (b) b.setAttribute('aria-expanded', 'false');
        }

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.more-menu')) closeMore();
            if (!e.target.closest('#sidebarBrandSwitcher') && !e.target.closest('.mobile-brand-pill')) closeBrandMenu();
        });

        let scrollTick = false;
        function updateNavFromScroll() {
            scrollTick = false;
            const activeBrand = (function() {
                try { return localStorage.getItem('active_brand_choice') || 'homecartel'; }
                catch(e) { return 'homecartel'; }
            })();
            if (activeBrand === 'roomandstyle') {
                setActiveNav('dashboard');
                return;
            }
            const line = window.innerHeight * 0.35;
            const hubTab = document.getElementById('tab-v5');
            const hubKey = hubTab && hubTab.classList.contains('active') ? 'alerts' : 'analytics';
            let cur = 'dashboard';
            [['sec-campaigns', 'campaigns'], ['sec-analytics', hubKey]].forEach(p => {
                const el = document.getElementById(p[0]);
                if (el && !el.hidden && el.getBoundingClientRect().top <= line) cur = p[1];
            });
            setActiveNav(cur);
        }
        window.addEventListener('scroll', () => {
            if (!scrollTick) { scrollTick = true; window.requestAnimationFrame(updateNavFromScroll); }
        }, { passive: true });

        function healthChartConfig(metric, rows, th) {
            const fq = th.frequency || {};
            const ct = th.ctr || {};
            const top10 = arr => arr.slice(0, 10);
            if (metric === 'ctr') {
                return {
                    sub: 'Lowest first. Dotted lines: below ' + (ct.warning != null ? ct.warning : '0.67') + '% is Act soon, below ' + (ct.critical != null ? ct.critical : '0.43') + '% is Act now.',
                    items: top10(rows.slice().sort((a, b) => a.ctr - b.ctr)).map(r => ({ name: r.name, value: r.ctr })),
                    cfg: {
                        lines: [
                            { value: ct.warning, color: HEALTH_COLORS.warning, label: ct.warning + '%', align: 'left' },
                            { value: ct.critical, color: HEALTH_COLORS.critical, label: ct.critical + '%', align: 'right' }
                        ].filter(l => l.value != null),
                        color: v => v < ct.critical ? HEALTH_COLORS.critical : v < ct.warning ? HEALTH_COLORS.warning : HEALTH_COLORS.healthy,
                        tick: v => v + '%',
                        label: v => 'Link CTR: ' + v.toFixed(2) + '%'
                    }
                };
            }
            if (metric === 'cpc') {
                return {
                    sub: 'Highest first, for comparison only. There is no alert line because cost only matters when compared with the past cost of the same ad.',
                    items: top10(rows.slice().sort((a, b) => b.cpc - a.cpc)).map(r => ({ name: r.name, value: r.cpc })),
                    cfg: { lines: [], color: () => HEALTH_COLORS.watch, tick: v => '₱' + v, label: v => 'Cost per click: ₱' + v.toFixed(2) }
                };
            }
            return {
                sub: 'Highest first. Dotted lines: ' + fq.watch + ' Watch, ' + fq.warning + ' Act soon, ' + fq.critical + ' Act now.',
                items: top10(rows.slice().sort((a, b) => b.freq - a.freq)).map(r => ({ name: r.name, value: r.freq })),
                cfg: {
                    lines: [
                        { value: fq.watch, color: HEALTH_COLORS.watch, label: String(fq.watch) },
                        { value: fq.warning, color: HEALTH_COLORS.warning, label: String(fq.warning) },
                        { value: fq.critical, color: HEALTH_COLORS.critical, label: String(fq.critical) }
                    ].filter(l => l.value != null),
                    color: v => v > fq.critical ? HEALTH_COLORS.critical : v > fq.warning ? HEALTH_COLORS.warning : v > fq.watch ? HEALTH_COLORS.watch : HEALTH_COLORS.healthy,
                    tick: v => v + '×',
                    label: v => 'Times seen: ' + v.toFixed(2) + '×'
                }
            };
        }

        function renderHealthMainChart() {
            if (!healthChartData) return;
            const c = healthChartConfig(healthMetric, healthChartData.rows, healthChartData.th);
            const sub = document.getElementById('health-chart-sub');
            if (sub) sub.innerText = c.sub;
            chartHealthMain = buildHealthChart('chartHealthMain', chartHealthMain, c.items, c.cfg);
        }

        function setHealthMetric(m) {
            healthMetric = m;
            ['freq', 'ctr', 'cpc'].forEach(k => {
                const b = document.getElementById('seg-' + k);
                if (!b) return;
                b.classList.toggle('active', k === m);
                b.setAttribute('aria-pressed', k === m ? 'true' : 'false');
            });
            renderHealthMainChart();
        }

        function renderSideCards(evals, counts) {
            ['healthy', 'watch', 'warning', 'critical'].forEach(k => {
                const el = document.getElementById('sum-' + k);
                if (el) el.innerText = counts[k] || 0;
            });
            const list = document.getElementById('top-spend-list');
            if (!list) return;
            const top = evals.slice().sort((a, b) => Number(b.spend || 0) - Number(a.spend || 0)).slice(0, 3);
            list.innerHTML = top.map(e => {
                const cls = e.level.toLowerCase();
                const ini = String(e.campaign_name || '?').split(/[^A-Za-z0-9]+/)[0].slice(0, 2).toUpperCase() || '?';
                return '<li class="top-item"><span class="top-badge ' + cls + '" aria-hidden="true">' + healthEsc(ini) + '</span>' +
                    '<span class="top-name" title="' + healthEsc(e.campaign_name) + '">' + healthEsc(e.campaign_name) + '</span>' +
                    '<span class="top-spend">₱' + Math.round(e.spend || 0).toLocaleString() + '</span></li>';
            }).join('');
        }

        function setAlertCounts(n) {
            ['bell-count', 'bell-count-m', 'nav-alert-count'].forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                el.innerText = n;
                el.hidden = !(n > 0);
            });
        }

        document.addEventListener('DOMContentLoaded', () => {
            setGreeting();
            updateNavFromScroll();
        });

        function renderAdHealth(summary) {
            const hub = document.getElementById('adHealthHub');
            if (!hub) return;

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

            const pctAtRisk = totalSpend > 0 ? Math.round((atRisk / totalSpend) * 100) : 0;
            document.getElementById('health-kpi-attn').innerText = `${attn} / ${total}`;
            document.getElementById('health-kpi-attn-sub').innerText = total
                ? `${counts.critical || 0} act now · ${counts.warning || 0} act soon · ${counts.watch || 0} watch`
                : 'No running campaigns yet';
            document.getElementById('health-kpi-risk').innerText = '₱' + Math.round(atRisk).toLocaleString();
            document.getElementById('health-kpi-risk-sub').innerText = `${pctAtRisk}% of your ad spend`;
            const freqEl = document.getElementById('health-kpi-freq');
            freqEl.innerText = portfolioFreq === null ? '—' : portfolioFreq.toFixed(2) + '×';
            const freqWatch = th.frequency ? th.frequency.watch : null;
            const freqHigh = portfolioFreq !== null && freqWatch !== null && portfolioFreq > freqWatch;
            freqEl.style.color = freqHigh ? '#b45309' : '';
            const chipRisk = document.getElementById('kpi-chip-risk');
            const chipFreq = document.getElementById('kpi-chip-freq');
            if (chipRisk) {
                chipRisk.hidden = !total;
                chipRisk.className = 'kpi-chip' + (attn ? '' : ' ok');
                chipRisk.innerText = attn ? pctAtRisk + '%' : 'OK';
            }
            if (chipFreq) {
                chipFreq.hidden = portfolioFreq === null;
                chipFreq.className = 'kpi-chip' + (freqHigh ? '' : ' ok');
                chipFreq.innerText = freqHigh ? 'High' : 'OK';
            }
            setAlertCounts(attn);

            renderFreshness(summary);
            renderHealthBanner(counts, total, attn, atRisk, totalSpend);

            const empty = document.getElementById('health-empty');
            const chartsWrap = document.getElementById('health-charts');
            empty.hidden = evals.length > 0;
            chartsWrap.hidden = evals.length === 0;

            const rows = evals.map(e => ({ name: e.campaign_name, freq: Number(e.frequency || 0), ctr: Number(e.ctr || 0), cpc: Number(e.cpc || 0) }));
            healthChartData = { rows: rows, th: th };
            renderHealthMainChart();
            renderSideCards(evals, counts);

            // Needs-attention cards (worst first) and the all-campaigns list
            const rank = { CRITICAL: 0, WARNING: 1, WATCH: 2 };
            const flagged = evals
                .filter(e => e.level in rank)
                .sort((a, b) => rank[a.level] - rank[b.level] || Number(b.spend || 0) - Number(a.spend || 0));
            const list = document.getElementById('health-attention-list');
            const attnWrap = document.getElementById('health-attention-wrap');
            const campWrap = document.getElementById('health-campaigns-wrap');
            const secCamps = document.getElementById('sec-campaigns');
            const campList = document.getElementById('health-campaigns');
            attnWrap.hidden = evals.length === 0;
            campWrap.hidden = evals.length === 0;
            if (secCamps) secCamps.hidden = evals.length === 0;
            if (evals.length === 0) {
                list.innerHTML = '';
                campList.innerHTML = '';
            } else {
                list.innerHTML = flagged.length === 0
                    ? '<div class="all-good">Good news: every running campaign is inside the safe limits.</div>'
                    : renderAttentionCards(flagged, th);
                campList.innerHTML = renderCampaignRows(evals, th);
            }

            maybeShowHealthPopupOnLoad(evals);
            updateNavFromScroll();
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
                        <span class="badge-alert ${healthEsc(cls)}">${healthEsc(LEVEL_TEXT[i.level] || i.level)}</span>
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
                crit ? `${crit} ${plural(crit, 'campaign needs', 'campaigns need')} action now` : `${flagged.length} ${plural(flagged.length, 'campaign needs', 'campaigns need')} action soon`,
                'Based on your latest Meta report',
                flagged.map(e => ({
                    level: e.level,
                    name: e.campaign_name,
                    metrics: `Seen ${Number(e.frequency || 0).toFixed(2)} times per person \u00B7 ${Number(e.ctr || 0).toFixed(2)}% of viewers click \u00B7 \u20B1${Math.round(e.spend || 0).toLocaleString()} spent`,
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
                `${urgent.length} ${plural(urgent.length, 'campaign needs', 'campaigns need')} attention after this report`,
                'New problems or campaigns that got worse since the last report',
                urgent.map(a => ({
                    level: a.level,
                    name: a.campaign_name,
                    metrics: `${a.metric_name} is ${a.metric_value} (limit ${a.threshold}) \u00B7 was ${LEVEL_TEXT[a.previous_level] || a.previous_level}`,
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
                            <div style="font-weight: 600; color: #0f172a; font-size: 13px; margin-bottom: 2px;">
                                ${item.campaign_name}
                            </div>
                            <div style="font-size: 12px; color: #64748b; font-family: var(--font-mono);">
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
                            ${freqBreached ? '<span style="display:block; font-size: 12px; color:#0369a1; font-weight:600;">&gt; 2.5 Watch</span>' : ''}
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
                            <span style="font-family: var(--font-mono); font-weight: 600; color: #334155;">
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
                        <td style="font-weight: 600; color: #0f172a;">${r.parameter}</td>
                        <td style="color: #334155; font-family: var(--font-mono); font-size: 12px;">${r.trigger_condition}</td>
                        <td style="color: #1e293b;">${r.required_action}</td>
                        <td style="color: #475569; font-family: var(--font-mono); font-size: 12px;">${r.source}</td>
                        <td style="color: #475569; font-size: 12px;">${r.routing}</td>
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
                [chartSpendBar, chartCpcCtr].forEach(chart => {
                    if (chart) chart.resize();
                });
            }, 60);
        }

        function renderAnalyticsCharts(data) {
            if (typeof Chart === 'undefined') return;

            const totalRev = Number(data.total_revenue || 0);
            const totalSpend = Number(data.total_ad_spend || 0);
            const totalClicks = Number(data.total_clicks || 0);
            const totalOrders = Number(data.total_orders || 0);

            const sig = `${totalRev}_${totalSpend}_${totalClicks}_${totalOrders}_${(data.campaigns_summary||[]).length}`;
            if (sig === lastChartDataSig) return;
            lastChartDataSig = sig;

            // Global Chart.js styling tokens aligned with chart-designer principles
            Chart.defaults.color = '#475569';
            Chart.defaults.font.family = "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
            Chart.defaults.font.size = 12;
            Chart.defaults.borderColor = 'rgba(15,23,42,0.08)';
            Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(255,255,255,0.98)';
            Chart.defaults.plugins.tooltip.titleColor = '#0f172a';
            Chart.defaults.plugins.tooltip.bodyColor = '#334155';
            Chart.defaults.plugins.tooltip.borderColor = 'rgba(56, 189, 248, 0.25)';
            Chart.defaults.plugins.tooltip.borderWidth = 1;
            Chart.defaults.plugins.tooltip.padding = 10;
            Chart.defaults.plugins.tooltip.cornerRadius = 8;
            Chart.defaults.plugins.tooltip.boxPadding = 6;
            Chart.defaults.plugins.tooltip.usePointStyle = true;

            const campaigns = data.campaigns_summary || [];

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
                                grid: { color: 'rgba(15,23,42,0.06)' },
                                ticks: {
                                    callback: (v) => '₱' + (v >= 1000 ? (v/1000) + 'k' : v)
                                }
                            },
                            y: { 
                                grid: { display: false },
                                ticks: { color: '#334155', font: { weight: '500' } }
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
                                    font: { size: 12, weight: '500' },
                                    color: '#334155'
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
                                grid: { color: 'rgba(15,23,42,0.06)' },
                                ticks: { 
                                    color: '#047857',
                                    callback: v => v + '%' 
                                },
                                title: { display: true, text: 'CTR %', color: '#047857', font: { size: 12 } }
                            },
                            yCpc: {
                                type: 'linear',
                                position: 'right',
                                grid: { display: false },
                                ticks: { 
                                    color: '#be123c',
                                    callback: v => '₱' + v 
                                },
                                title: { display: true, text: 'CPC (PHP)', color: '#be123c', font: { size: 12 } }
                            },
                            x: { 
                                grid: { display: false },
                                ticks: { color: '#334155' }
                            }
                        }
                    }
                });
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
        const savedBrand = (function() {
            try { return localStorage.getItem('active_brand_choice') || 'homecartel'; }
            catch(e) { return 'homecartel'; }
        })();
        selectBrand(savedBrand);
    </script>
</body>
</html>
"""
    return (
        html.replace("__HC_LOGO_SIDEBAR__", _logo_html("logo-sidebar"))
        .replace("__HC_LOGO_MOBILE__", _logo_html("logo-mobile"))
        .replace("__HC_LOGO_MODAL__", _logo_html("logo-modal"))
        .replace("__RS_LOGO_SIDEBAR__", _rs_logo_html("logo-sidebar"))
        .replace("__RS_LOGO_MOBILE__", _rs_logo_html("logo-mobile"))
        .replace("__RS_LOGO_HERO__", _rs_logo_html("logo-hero", width=280, height=64))
    )
