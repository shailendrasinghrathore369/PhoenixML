# PhoenixML Design System Specification (DESIGN.md)

> **Category**: Enterprise MLOps Observability & Decision-Support Control Plane
> **Aesthetic Direction**: Linear Precision × Vercel Contrast Hybrid
> **Themes Supported**: Dark (Native Default) & Light (Operational Clean)
> **Core Principle**: Extreme precision engineering, data-density without clutter, deterministic human-in-the-loop governance.

---

## 1. Visual Theme & Philosophy

PhoenixML is an operator-facing MLOps decision-support platform designed for Machine Learning Engineers, Platform Reliability Engineers (PREs), and ML Governance Operators. Its visual architecture merges the **atmospheric precision and luminance-layered depth of Linear** with the **monochrome rigor, tabular clarity, and high-contrast dual-theming of Vercel**.

### Key Aesthetic Principles

1. **Darkness as Native Medium, Lightness as High-Contrast Discipline**
   - In Dark Mode, the canvas is near-black (`#070a0f` / `#0b0f17`), and surfaces elevate through calibrated gradations of subtle opacity and luminance (`rgba(255, 255, 255, 0.03)` to `0.06`) framed by ultra-thin hairline borders (`rgba(255, 255, 255, 0.08)`).
   - In Light Mode, surfaces utilize crisp pure whites (`#ffffff`), subtle cool slate structural panels (`#f8fafc`), and razor-sharp borders (`#e2e8f0`), avoiding washed-out grays and maintaining WCAG AAA/AA legibility.

2. **Phoenix Cobalt vs. Linear Violet**
   While Linear uses violet/indigo as its sole brand accent, PhoenixML maintains its identity with **Precision Cobalt** (`#2563eb` / `#3b82f6` in dark; `#1d4ed8` in light) combined with subtle electric undertones. Brand color is treated as high-leverage ink: applied strictly to interactive focal points, active states, and system-level telemetry anchors.

3. **Strict Semantic Chromatic Hierarchy**
   Operational statuses retain PhoenixML's mandatory color contract:
   - **Healthy**: Precision Emerald (`#10b981`)
   - **Warning**: High-Visibility Amber (`#f59e0b`)
   - **Critical / Degradation**: Razor Rose (`#f43f5e` / `#ef4444`)
   - **Informational / Blue**: Sky Cobalt (`#3b82f6`)
   - **Neutral**: Slate (`#64748b`)

4. **Engineered Typography & Tabular Rigor**
   All metrics, loss functions, F1 scores, observation counts, model IDs, and timestamps use `font-variant-numeric: tabular-nums` and monospace accents to guarantee alignment across dense tables and KPI grids.

5. **Human-In-The-Loop (HITL) Prominence**
   Because PhoenixML AIMD recommendations require human authorization before any model change occurs, decision boxes and advisory banners employ distinct warm-glow ambient framing and high-contrast review callouts.

---

## 2. Dual-Theme Color Tokens (Dark & Light)

### 2.1 CSS Custom Properties Specification

```css
/* ==========================================================================
   PhoenixML Hybrid Design System Tokens: Dark (Default) & Light
   ========================================================================== */

:root,
html[data-theme="dark"] {
  /* Canvas & Base Backgrounds */
  --bg-canvas: #070a0f;                 /* Deepest workspace canvas */
  --bg-primary: #0b0f17;                /* Primary application background */
  --bg-secondary: #111827;              /* Nav, sidebar, elevated containers */
  --bg-tertiary: #172033;               /* Secondary elevated surfaces */

  /* Translucent & Layered Surfaces (Linear-style luminance stacking) */
  --surface-base: #0b0f17;
  --surface-subtle: rgba(255, 255, 255, 0.02);
  --surface-card: rgba(17, 24, 39, 0.75);
  --surface-card-hover: rgba(30, 41, 59, 0.7);
  --surface-elevated: #1e293b;
  --surface-overlay: rgba(7, 10, 15, 0.85);

  /* Hairline Borders (Vercel crispness × Linear translucency) */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-color: rgba(255, 255, 255, 0.10);
  --border-light: rgba(255, 255, 255, 0.16);
  --border-hover: rgba(255, 255, 255, 0.24);
  --border-active: #3b82f6;

  /* Typography Colors */
  --text-primary: #f8fafc;              /* Slate 50: Headings, primary KPIs */
  --text-secondary: #cbd5e1;            /* Slate 300: Body copy, active labels */
  --text-muted: #94a3b8;                /* Slate 400: Secondary metadata */
  --text-dim: #64748b;                  /* Slate 500: Micro-labels, disabled */
  --text-inverse: #070a0f;              /* Dark text on light chips */

  /* Brand / Primary Accent (Phoenix Precision Cobalt) */
  --color-primary: #3b82f6;
  --color-primary-hover: #60a5fa;
  --color-primary-active: #2563eb;
  --primary-bg-subtle: rgba(59, 130, 246, 0.10);
  --primary-border-subtle: rgba(59, 130, 246, 0.28);
  --primary-glow: rgba(59, 130, 246, 0.25);

  /* Semantic State: Healthy Emerald */
  --color-healthy: #10b981;
  --color-healthy-hover: #059669;
  --healthy-bg: rgba(16, 185, 129, 0.12);
  --healthy-border: rgba(16, 185, 129, 0.32);
  --healthy-glow: rgba(16, 185, 129, 0.25);

  /* Semantic State: Warning Amber */
  --color-warning: #f59e0b;
  --color-warning-hover: #d97706;
  --warning-bg: rgba(245, 158, 11, 0.12);
  --warning-border: rgba(245, 158, 11, 0.35);
  --warning-glow: rgba(245, 158, 11, 0.25);

  /* Semantic State: Critical Rose / Red */
  --color-critical: #f43f5e;
  --color-critical-hover: #e11d48;
  --critical-bg: rgba(244, 63, 94, 0.12);
  --critical-border: rgba(244, 63, 94, 0.35);
  --critical-glow: rgba(244, 63, 94, 0.25);

  /* Supporting Semantic Accents */
  --color-info: #38bdf8;
  --color-neutral: #64748b;

  /* Approval States */
  --badge-pending: #f59e0b;
  --badge-approved: #10b981;
  --badge-rejected: #f43f5e;

  /* Shadows & Depth */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
  --shadow-md: 0 4px 12px -2px rgba(0, 0, 0, 0.6), 0 2px 4px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 12px 24px -4px rgba(0, 0, 0, 0.7), 0 4px 8px -2px rgba(0, 0, 0, 0.5);
  --shadow-dialog: 0 24px 48px -12px rgba(0, 0, 0, 0.85), 0 0 0 1px rgba(255, 255, 255, 0.12);

  /* Focus Rings */
  --focus-ring: 0 0 0 2px #070a0f, 0 0 0 4px #3b82f6;
  --focus-ring-warning: 0 0 0 2px #070a0f, 0 0 0 4px #f59e0b;
  --focus-ring-critical: 0 0 0 2px #070a0f, 0 0 0 4px #f43f5e;
}

/* Light Mode Theme Specification (Vercel Operational Clean) */
html[data-theme="light"] {
  /* Canvas & Base Backgrounds */
  --bg-canvas: #f8fafc;                 /* Slate 50 cool background */
  --bg-primary: #ffffff;                /* Pure white primary container */
  --bg-secondary: #f1f5f9;              /* Slate 100 secondary container */
  --bg-tertiary: #e2e8f0;               /* Slate 200 elevated container */

  /* Surfaces */
  --surface-base: #ffffff;
  --surface-subtle: #f8fafc;
  --surface-card: #ffffff;
  --surface-card-hover: #f8fafc;
  --surface-elevated: #ffffff;
  --surface-overlay: rgba(15, 23, 42, 0.45);

  /* Hairline Borders */
  --border-subtle: #f1f5f9;
  --border-color: #e2e8f0;              /* Crisp 1px gray */
  --border-light: #cbd5e1;
  --border-hover: #94a3b8;
  --border-active: #2563eb;

  /* Typography Colors */
  --text-primary: #0f172a;              /* Slate 900 */
  --text-secondary: #334155;            /* Slate 700 */
  --text-muted: #64748b;                /* Slate 500 */
  --text-dim: #94a3b8;                  /* Slate 400 */
  --text-inverse: #ffffff;

  /* Brand / Primary Accent */
  --color-primary: #2563eb;             /* True Cobalt */
  --color-primary-hover: #1d4ed8;
  --color-primary-active: #1e40af;
  --primary-bg-subtle: rgba(37, 99, 235, 0.08);
  --primary-border-subtle: rgba(37, 99, 235, 0.25);
  --primary-glow: rgba(37, 99, 235, 0.15);

  /* Semantic State: Healthy Emerald */
  --color-healthy: #059669;
  --color-healthy-hover: #047857;
  --healthy-bg: rgba(16, 185, 129, 0.10);
  --healthy-border: rgba(16, 185, 129, 0.30);
  --healthy-glow: rgba(16, 185, 129, 0.15);

  /* Semantic State: Warning Amber */
  --color-warning: #d97706;
  --color-warning-hover: #b45309;
  --warning-bg: rgba(245, 158, 11, 0.10);
  --warning-border: rgba(245, 158, 11, 0.30);
  --warning-glow: rgba(245, 158, 11, 0.15);

  /* Semantic State: Critical Rose */
  --color-critical: #e11d48;
  --color-critical-hover: #be123c;
  --critical-bg: rgba(244, 63, 94, 0.08);
  --critical-border: rgba(244, 63, 94, 0.28);
  --critical-glow: rgba(244, 63, 94, 0.15);

  /* Supporting Accents */
  --color-info: #0284c7;
  --color-neutral: #475569;

  /* Approval States */
  --badge-pending: #d97706;
  --badge-approved: #059669;
  --badge-rejected: #e11d48;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.10), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
  --shadow-dialog: 0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 0 0 1px rgba(0, 0, 0, 0.05);

  /* Focus Rings */
  --focus-ring: 0 0 0 2px #ffffff, 0 0 0 4px #2563eb;
  --focus-ring-warning: 0 0 0 2px #ffffff, 0 0 0 4px #d97706;
  --focus-ring-critical: 0 0 0 2px #ffffff, 0 0 0 4px #e11d48;
}
```

---

## 3. Typography & Spacing System

### 3.1 Font Families
- **Primary Interface**: `Inter Variable`, `Inter`, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
  - OpenType features enabled: `"cv01", "ss03"` where supported for geometric legibility.
- **Monospace (Data / IDs / Code / Metrics)**: `ui-monospace`, `SFMono-Regular`, `Menlo`, `Monaco`, `Consolas`, monospace
  - Always enforce `font-variant-numeric: tabular-nums` on table numbers, timestamps, and metric scores.

### 3.2 Type Scale

| Level | Size | Weight | Line Height | Tracking | Primary Use |
|---|---|---|---|---|---|
| **Display Title** | `1.75rem` (28px) | 700 / 600 | 1.20 | `-0.025em` | Page Header primary title |
| **Section Header** | `1.25rem` (20px) | 600 | 1.30 | `-0.015em` | Card group titles, modal headers |
| **Card / Item Title** | `0.9375rem` (15px) | 600 / 510 | 1.40 | `-0.010em` | Model name, decision action title |
| **Body Standard** | `0.875rem` (14px) | 400 | 1.50 | `0` | Standard UI text, descriptions, table cells |
| **Body Medium** | `0.875rem` (14px) | 510 / 500 | 1.50 | `0` | Button labels, active tabs, table headers |
| **Metadata / Caption** | `0.75rem` (12px) | 500 | 1.40 | `+0.010em` | Timestamps, IDs, micro-badges, labels |
| **Micro Tag** | `0.6875rem` (11px) | 600 | 1.30 | `+0.020em` | Status badge text, uppercase section labels |

### 3.3 Spacing Scale
PhoenixML uses a predictable 4px / 8px incremental scale:
- `var(--space-1)`: `0.25rem` (4px) — micro gap, inner icon spacing
- `var(--space-2)`: `0.5rem` (8px) — badge padding, tight stack gap
- `var(--space-3)`: `0.75rem` (12px) — card sub-group gap, button x-padding
- `var(--space-4)`: `1.0rem` (16px) — standard card inner padding, grid gap
- `var(--space-5)`: `1.25rem` (20px) — spacious card padding, list margin
- `var(--space-6)`: `1.5rem` (24px) — section division, panel header padding
- `var(--space-8)`: `2.0rem` (32px) — major layout gutters
- `var(--space-10)`: `2.5rem` (40px) — top/bottom page padding

### 3.4 Radii Hierarchy
- **`--radius-sm` (4px)**: Micro tags, code snippets, nested toolbars
- **`--radius-md` (6px)**: Standard buttons, text inputs, status badges
- **`--radius-lg` (8px)**: Standard metric cards, table containers, popovers
- **`--radius-xl` (12px)**: Large feature containers, modal dialogs, model cards
- **`--radius-full` (9999px)**: Status dots, pill tags, rounded-full avatars

---

## 4. PhoenixML Product-Specific Module Specifications

### 4.1 Model Registry
- **Model Card Structure**:
  - Encased in `var(--surface-card)` with `1px solid var(--border-color)` and `var(--radius-xl)`.
  - Selection State: Highlighting uses `border-color: var(--color-primary)` with `box-shadow: 0 0 0 1px var(--color-primary), var(--primary-glow)`.
  - Header: Left: Lucide `Cpu` icon with model name; Right: Status pill (`ACTIVE`, `DEV`, `ARCHIVED`).
  - Metadata Line: Framework tag (`scikit-learn`, `PyTorch`) and truncated hex identifier in monospace `var(--text-dim)`.
  - Footer Action Bar: Dense icon buttons with role-based tooltips (`Evaluate AIMD`, `Ref Eval`, `Degraded Eval`).

### 4.2 Model Health Indicators
- **Health Score Meter (0 – 100)**:
  - Container: 6px tall track with `var(--bg-primary)` and subtle border.
  - Active Fill Bar: Smooth CSS transition (`width 0.4s cubic-bezier(0.4, 0, 0.2, 1)`).
  - Status Mapping:
    - **Healthy** (`>= 80%`): `var(--color-healthy)` with subtle emerald pulse if evaluation fresh.
    - **Warning** (`50% – 79%`): `var(--color-warning)` with solid amber fill.
    - **Critical** (`< 50%`): `var(--color-critical)` with rose glow.
    - **Insufficient / No Data**: `var(--text-dim)` with dashed or muted gray bar.
  - Accessibility: Must provide `role="progressbar"`, `aria-valuenow`, `aria-valuemin="0"`, `aria-valuemax="100"`.

### 4.3 Telemetry & Performance Charts
- **Chart Background**: Clear transparent or `var(--surface-subtle)` with dashed horizontal gridlines in `var(--border-subtle)`.
- **Chart Palette**:
  | Data Stream | Token / Hex | Style |
  |---|---|---|
  | **Baseline / Reference** | `#10b981` (Emerald) | Solid 2px line, subtle green area gradient (opacity 0.08) |
  | **Current Production** | `#3b82f6` (Cobalt) | Solid 2.5px line with active circular dot nodes |
  | **Shifted / Degraded Stream** | `#f43f5e` (Rose) | Dashed 2px line (`stroke-dasharray: 4 4`) with marker crosses |
  | **Drift Warning Threshold** | `#f59e0b` (Amber) | Dotted 1px horizontal threshold line |
  | **Confidence Interval Band** | `rgba(59, 130, 246, 0.12)` | Shaded bounding corridor |
- **Chart Tooltip**: Encased in `var(--bg-secondary)` with `1px solid var(--border-color)`, `var(--radius-md)`, and `var(--shadow-md)`. Monospace metrics aligned with right-aligned tabular figures.

### 4.4 Data Evaluation (Reference vs. Shifted)
- **Reference Evaluation (Baseline / Healthy)**:
  - Banner: `background: var(--healthy-bg)`, `border: 1px solid var(--healthy-border)`, text `var(--color-healthy)`.
  - Icon: Lucide `FlaskConical` (`16px`).
  - Metrics Shown: Accuracy, Precision, Recall, F1 Score formatted to 3 decimal places.
- **Shifted Evaluation (Degraded / Drifted)**:
  - Banner: `background: var(--critical-bg)`, `border: 1px solid var(--critical-border)`, text `var(--color-critical)`.
  - Icon: Lucide `TrendingDown` (`16px`).
  - Delta Indicator: Negative deltas displayed with red negative prefix (e.g. `F1: 0.620 (-0.312)`).

### 4.5 Explainability Panels
- **Rationale & Root Cause Block**:
  - Enclosed in a recessed callout box using `var(--bg-canvas)` or `rgba(0, 0, 0, 0.25)` in dark mode (`#f1f5f9` in light mode).
  - Left border: 3px solid accent line corresponding to decision severity (`var(--color-warning)` or `var(--color-critical)`).
  - Typography: `font-size: var(--text-sm)`, `line-height: 1.6`.
  - Feature Attribution List: Horizontal bar micro-charts showing positive vs negative drift contributions.

### 4.6 AIMD Recommendations & Decision Boxes
- **Decision Review Box**:
  - Position: Prominent operator focus area above model cards or within selected model drawer.
  - Visual Framing: When status is `PENDING`, frame with an amber ambient halo (`box-shadow: 0 0 24px var(--warning-glow)`).
  - Action Title: Bold display label (`RETRAIN_IMMEDIATE`, `ROLLBACK_CANDIDATE`, `CONTINUE_OBSERVATION`).
  - Priority Badge:
    - `CRITICAL`: Rose badge with animated dot.
    - `HIGH` / `MEDIUM`: Amber badge.
    - `LOW`: Muted slate badge.
  - Confidence Score: Displayed as percentage in bold tabular monospace (e.g., `87.5%`).

### 4.7 Human Approval Workflows (HITL Governance)
- **HITL Advisory Banner**:
  - Full-width region banner informing the operator that AIMD actions require deterministic human review.
  - Background: Amber subtle wash (`rgba(245, 158, 11, 0.08)`), border `1px solid var(--warning-border)`.
  - Icon: Lucide `ShieldAlert` in amber icon box.
- **Action Controls (RBAC Enforced)**:
  - **Approve Button**: Emerald variant (`var(--color-healthy)`), white text, Lucide `CheckCircle`.
  - **Reject Button**: Rose variant (`var(--color-critical)`), white text, Lucide `XCircle`.
  - **Viewer State**: Disabled buttons with tooltip `Requires ML Engineer or Admin role`, reduced opacity (0.45), cursor `not-allowed`.
- **Confirmation Modal (`ConfirmationDialog`)**:
  - Backdrop: `var(--surface-overlay)` with backdrop-filter blur (8px).
  - Modal Surface: `var(--bg-secondary)` with `var(--border-color)` and `var(--shadow-dialog)`.
  - Keyboard: `Escape` key cancels, `Enter` confirms destructive action.

### 4.8 Audit Tables & Historical Log
- **DataTable Architecture**:
  - Header Row: Sticky `top: 0`, background `var(--bg-secondary)`, subtle bottom divider. Uppercase `var(--text-dim)` tracking `+0.05em`.
  - Rows: Height `44px` (comfortable) or `36px` (compact). Hover state `background: var(--surface-card-hover)`.
  - Numeric & Timestamp Columns: Right-aligned with tabular numbers in monospace.
  - Empty State: Centered within table container; displays subtle Lucide icon (`Inbox` or `History`), bold heading, and helpful operational guidance.

---

## 5. Iconography Specification (Lucide React)

All icons use `lucide-react` with consistent optical sizing:

| Size Token | Dimensions | Stroke Width | Standard Usage |
|---|---|---|---|
| `icon-xs` | 12 × 12 px | 2.0 px | Inline status tags, micro table indicators |
| `icon-sm` | 16 × 16 px | 1.75 px | Button icons, table cell icons, breadcrumbs |
| `icon-md` | 20 × 20 px | 1.75 px | KPI card titles, section headers, modal banners |
| `icon-lg` | 24 × 24 px | 1.5 px | Empty states, confirmation dialog hero icons |
| `icon-xl` | 32 × 32 px | 1.5 px | Brand logo badge, system health summary |

### Semantic Icon Registry
- **Models / Fleet**: `Cpu`, `Layers`, `Box`
- **Telemetry / Stream**: `Activity`, `Pulse`, `Radio`
- **Health / Security**: `ShieldCheck` (Healthy), `ShieldAlert` (HITL / Advisory), `AlertTriangle` (Warning)
- **Decisions / Actions**: `CheckCircle` (Approve), `XCircle` (Reject), `History` (Audit Log), `Lock` (RBAC Protected)
- **Evaluation**: `FlaskConical` (Ref Eval), `TrendingDown` (Shifted/Degraded Eval), `Zap` (Trigger Evaluation)
- **Navigation / System**: `LayoutDashboard`, `Settings`, `LogOut`, `RefreshCw`

---

## 6. Accessibility & Interaction States

1. **Contrast Standards**:
   - Dark Mode: Text primary (`#f8fafc`) against canvas (`#070a0f`) achieves **18.2:1 contrast** (exceeds WCAG AAA).
   - Light Mode: Text primary (`#0f172a`) against surface (`#ffffff`) achieves **16.1:1 contrast** (exceeds WCAG AAA).
   - Secondary text achieves minimum **5.5:1 contrast** (WCAG AA compliant).
2. **Focus Visibility**:
   - All interactive elements (buttons, inputs, clickable rows, modal dismiss triggers) feature a high-visibility dual-layer focus ring (`var(--focus-ring)`). Outline is never set to `none` without providing `--focus-ring`.
3. **Motion & Transitions**:
   - Standard transitions use `150ms cubic-bezier(0.16, 1, 0.3, 1)` for snappy, native-feeling interactions.
   - Respect `prefers-reduced-motion: reduce`: disable non-essential pulses or transition animations.
4. **ARIA Requirements**:
   - `aria-live="polite"` on toast notifications and background polling refresh triggers.
   - Modals use `aria-modal="true"`, `role="dialog"`, with focus trap and focus restoration.
   - Status indicators include accessible text descriptions or `aria-label`.

---

## 7. Responsive Breakpoint Strategy

| Breakpoint | Range | Layout Adjustments |
|---|---|---|
| **Mobile (`sm`)** | `< 768px` | Single column KPI stack, collapsed sidebar into hamburger drawer, scrollable audit tables, full-width action buttons |
| **Tablet (`md`)** | `768px – 1023px` | 2-column KPI grid, 2-column model fleet grid, condensed table columns |
| **Desktop (`lg`)** | `1024px – 1439px` | Fixed 240px sidebar, 4-column KPI grid, multi-column decision review split |
| **Ultra-Wide (`xl`)** | `>= 1440px` | Max-width container (`1440px` or full fluid with 32px gutters), side-by-side explainability and decision preview panels |

---

## 8. Anti-Patterns & Implementation Guardrails

- ❌ **Do not use decorative rainbow gradients** across operational cards or data containers. Backgrounds must be flat, translucent, or subtle vertical luminance fades.
- ❌ **Do not introduce Next.js or Tailwind dependencies**. The project is strictly React 18 + Vite using pure CSS tokens and utility helpers.
- ❌ **Do not remove or rename existing CSS variables** (`--bg-canvas`, `--color-healthy`, etc.). All new theme tokens must alias or extend the established token schema.
- ❌ **Do not use low-contrast text on colored badges**. Status badges must maintain dark text or luminous white text with matching border opacities.
- ❌ **Do not allow autonomous action buttons** without the mandatory Human-In-The-Loop review mechanism and confirmation modal.
