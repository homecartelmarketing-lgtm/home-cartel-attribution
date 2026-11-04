# Design Spec: Dashboard UI/UX Pro Redesign with Live Theme Switcher

## 1. Overview & Motivation
The Home Cartel Ads Management & Attribution Dashboard currently uses a functional single-page layout. To elevate it to enterprise SaaS standards (Linear/Stripe-level aesthetics), we are applying the **`ui-ux-pro-max`** Data-Dense Dashboard design intelligence.

To guarantee zero regression risk and respect the user's preference for safe reversibility, the redesign will be built on a **Scoped Dual-Theme Architecture**:
- **Modern Pro Theme (`data-theme="modern-pro"`)**: The elevated, high-contrast, data-dense modern aesthetic.
- **Classic Theme (`data-theme="classic"`)**: The exact existing UI.
- **Live Switcher**: A segmented control in the top navigation bar allowing one-click instant toggling between "Modern Pro" and "Classic", persisted in `localStorage`.

---

## 2. Design System Tokens (`ui-ux-pro-max`)

### A. Color Palette
| Token | Hex Value | Purpose |
| :--- | :--- | :--- |
| `--color-primary` | `#1E40AF` | Deep royal blue for primary active tabs, brand accents |
| `--color-secondary` | `#3B82F6` | Electric blue for interactive links, charts, active pills |
| `--color-accent` | `#D97706` | Amber/gold for warnings, badges, and ROAS alerts |
| `--color-success` | `#059669` | Emerald green for healthy status, positive ROAS |
| `--color-danger` | `#DC2626` | Crimson for high-fatigue ads, 0-lead anomalies |
| `--color-bg` | `#F8FAFC` | Clean slate background (reduces eye strain) |
| `--color-surface` | `#FFFFFF` | Crisp white cards with 1px subtle slate borders |
| `--color-border` | `#E2E8F0` | Subtle clean boundary between widgets |
| `--color-text` | `#0F172A` | Slate-900 (ultra-readable, 12.8:1 contrast on white) |
| `--color-muted` | `#64748B` | Slate-500 for secondary labels and hints |

### B. Typography & Layout
- **Font Stack**: `Plus Jakarta Sans`, `Inter`, -apple-system, system-ui, sans-serif.
- **Tabular Figures**: `font-variant-numeric: tabular-nums;` on all financial, CPC, CTR, and count metrics to align numbers cleanly.
- **Grid & Spacing**: 8-point spatial rhythm (`8px`, `16px`, `24px`, `32px`).
- **Cards & Elevation**: `box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05);` with crisp `1px solid var(--color-border)`.

---

## 3. Architecture & Implementation Plan

### A. Non-Destructive Scoped Styling
- The entire redesign will live under scoped CSS rules (`body[data-theme="modern-pro"] ...` or `.theme-modern-pro ...`).
- When `data-theme="classic"` (or no theme class), the CSS falls back 100% to the original styling without touching existing selectors.

### B. Interactive Theme Switcher Component
- In the top header bar (near the brand title and freshness indicator):
  ```html
  <div class="theme-switch-container">
    <button class="theme-btn active" id="btn-theme-modern" onclick="switchDashboardTheme('modern-pro')">
      ✦ Modern Pro
    </button>
    <button class="theme-btn" id="btn-theme-classic" onclick="switchDashboardTheme('classic')">
      ⟲ Classic
    </button>
  </div>
  ```
- Backed by JavaScript:
  ```javascript
  function switchDashboardTheme(themeName) {
      document.body.setAttribute('data-theme', themeName);
      localStorage.setItem('hc_dashboard_theme', themeName);
      updateThemeButtonStates(themeName);
  }
  ```

### C. Redesigned Dashboard Sections
1. **Header & Sidebar**:
   - Polished sidebar with clean icon-text spacing, active pill badges, and refined logout button.
   - Top banner with sync status, brand selector, and the new Live Theme Switcher.
2. **KPI Summary Cards**:
   - Crisp modern metrics with sparkline-style micro-badges, clean titles, and tabular figures.
3. **Analytics Hub & Monthly Panel**:
   - Modern tab bar with animated indicator line / pill background.
   - Refined tables: subtle zebra borders, sticky header, hover highlight, and high-contrast status chips.
4. **Ad Health Monitor & Alerts**:
   - Modernized alert banner cards with color-coded severity bars (Green / Amber / Red).

---

## 4. Verification & Testing
- **Theme Switch Test**: Clicking "Classic" restores original layout 100%; clicking "Modern Pro" enables the new design.
- **Persistence Test**: Refreshing the browser preserves the chosen theme via `localStorage`.
- **Automated Test Suite**: Run `pytest tests/` to confirm all 91 tests continue passing.
