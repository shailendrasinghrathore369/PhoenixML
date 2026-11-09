# PhoenixML Design System Mapping & Architecture Review

This document details the mapping between the proposed **PhoenixML Design System (`DESIGN.md`)**, the existing React 18 + Vite component tree, and the design tokens in `frontend/src/lib/tokens.js` and `frontend/styles/dashboard.css`.

---

## 1. Component Mapping Matrix

| Design Specification Module | Existing Component(s) | Existing CSS Selectors / Tokens | Status & Compatibility |
|---|---|---|---|
| **Shell & Navigation** | `AppHeader.jsx`<br>`AppSidebar.jsx`<br>`DashboardLayout.jsx` | `.navbar`, `.sidebar`, `.sidebar-nav`, `.brand`, `.brand-icon`<br>`--bg-secondary`, `--border-color`, `--color-primary` | ✅ **100% Compatible**. Matches layout structure, 240px sidebar width, sticky header, and profile badge. |
| **KPI & Fleet Metrics** | `KPIGrid.jsx`<br>`MetricCard.jsx` | `.kpi-grid`, `.kpi-card`, `.kpi-value`, `.kpi-icon-box`<br>`--surface-card`, `--shadow-sm`, `font-mono` | ✅ **100% Compatible**. Uses tabular figures for numbers and semantic status badge slots. |
| **Model Registry** | `ModelCard.jsx` | `.model-card`, `.model-card-top`, `.model-name`, `.metric-item`<br>`--surface-card`, `--radius-xl`, `--border-color` | ✅ **100% Compatible**. Selection rings match `--primary-glow`, and inline metric grids follow the 3-column micro-layout. |
| **Health Indicators** | `HealthIndicator.jsx` | `.health-indicator`, `.health-meter-bar`, `.health-meter-fill`<br>`--color-healthy`, `--color-warning`, `--color-critical` | ✅ **100% Compatible**. Employs ARIA progressbar roles and emerald/amber/rose color transitions. |
| **HITL Governance** | `HITLBanner.jsx`<br>`ConfirmationDialog.jsx` | `.hitl-banner`, `.hitl-pill`, `.dialog-overlay`, `.dialog-content`<br>`--warning-bg`, `--warning-border`, `--shadow-dialog` | ✅ **100% Compatible**. Amber advisory region and accessible modal confirmation dialog with Escape keyboard support. |
| **AIMD Recommendations & Review** | `DecisionReviewBox.jsx` | `.decision-box`, `.decision-header`, `.decision-rationale`, `.decision-details-grid`<br>`--warning-glow`, `--badge-pending`, `--surface-elevated` | ✅ **100% Compatible**. Highlight framing for pending status, severity callout cards, and confidence metric displays. |
| **Data Evaluation (Ref vs. Shifted)** | `ModelCard.jsx` (eval banner)<br>`useDashboard.js` | `bg-emerald-950/20`, `bg-rose-950/20`<br>`--color-healthy`, `--color-critical` | ✅ **100% Compatible**. References `FlaskConical` for baseline evaluation and `TrendingDown` for degraded shifted evaluation. |
| **Audit Trails & Tables** | `DataTable.jsx`<br>`RecentDecisionsTable.jsx` | `table`, `thead`, `tbody`, `tr`, `th`, `td`<br>`--bg-secondary`, `--surface-card-hover`, `--border-color` | ✅ **100% Compatible**. Tabular alignment (text left, numbers right), sticky headers, and empty-state fallbacks. |
| **Semantic Badges** | `StatusBadge.jsx` | `.status-badge`, `.status-dot`, `.status-badge-sm`<br>`--color-healthy`, `--color-warning`, `--color-critical` | ✅ **100% Compatible**. Pill styling with 9999px radius and optional live pulse indicator. |
| **System States & Feedback** | `LoadingState.jsx`<br>`EmptyState.jsx`<br>`ErrorState.jsx`<br>`Toast.jsx` | `.loading-state`, `.empty-state`, `.error-state`, `.toast-container`<br>`--focus-ring`, `--shadow-md` | ✅ **100% Compatible**. Fully accessible system states with aria-live support. |

---

## 2. CSS Custom Properties & Token Mapping

The proposed `DESIGN.md` explicitly preserves all existing CSS token names:

```
Existing Tokens in dashboard.css & tokens.js ──> Proposed DESIGN.md Mapping
--------------------------------------------------------------------------
--bg-canvas                                 ──> Preserved (#070a0f / #f8fafc)
--bg-primary                                ──> Preserved (#0b0f17 / #ffffff)
--bg-secondary                              ──> Preserved (#111827 / #f1f5f9)
--surface-card                              ──> Preserved (translucent / clean white)
--border-color                              ──> Preserved (hairline rgba / crisp gray)
--color-primary                             ──> Preserved (Phoenix Precision Cobalt)
--color-healthy                             ──> Preserved (Emerald #10b981)
--color-warning                             ──> Preserved (Amber #f59e0b)
--color-critical                            ──> Preserved (Rose #f43f5e)
--radius-sm / md / lg / xl / full           ──> Preserved (4px / 6px / 8px / 12px / 9999px)
--shadow-sm / md / lg                       ──> Preserved (Linear-style ambient elevation)
--focus-ring / warning / critical           ──> Preserved (Dual-ring accessible contrast)
```

---

## 3. Frontend Architecture Conflict Analysis

| Potential Conflict Area | Risk Level | Assessment & Resolution |
|---|---|---|
| **Framework Lock-in (Next.js / SSR)** | **NONE** | The design specification strictly avoids Next.js assumptions. All token delivery, font stacks, and component layout conventions operate inside the client-side React 18 + Vite SPA architecture. |
| **CSS Methodology (Tailwind migration)** | **NONE** | No Tailwind migration is mandated or required. The specification uses CSS custom properties (`:root` / `[data-theme]`) and class-based utility combinations (`clsx` + `tailwind-merge` in `utils.js`), fully compatible with current CSS. |
| **Theme Switching Mechanism** | **LOW / PLANNED** | Currently `dashboard.css` declares `html { color-scheme: dark; }`. In Phase 2, theme switching will simply set `data-theme="dark"` or `data-theme="light"` on `document.documentElement` without modifying component templates. |
| **Font Dependencies** | **LOW** | `DESIGN.md` designates `Inter Variable` as primary with system font fallbacks (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto`). The application will render cleanly using standard OS system fonts without forcing heavy external webfont downloads. |
| **Backend & RBAC Contracts** | **NONE** | Zero API contract modifications. Viewer, ML Engineer, and Admin roles continue to dictate action button states seamlessly. |
| **Existing Test Suite** | **NONE** | All 26 existing Vitest tests (`tokens.test.js` and `components.test.jsx`) validate the exact token names and component interfaces specified in this design system. |
