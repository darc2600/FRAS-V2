# FRAS Design System

This design system extracts the shared visual language and reusable component plan from the FRAS mockups:

- `fras-professor-landing-mockup.html`
- `fras-monitor-page-mockup.html`
- `fras-attendance-session-history-mockup.html`
- `fras-post-session-review-mockup.html`
- `fras-session-detail-view-mockup.html`

The goal is to keep the revised FRAS experience consistent while supporting the finalized professor workflow:

```text
Today's Classes -> Live Session -> Session Review -> Student Evidence
Today's Classes -> Session History -> Session Review -> Student Evidence
```

## 1. Color Tokens

Use these as canonical product tokens. Some mockups used very close maroon variants (`#8a0030`, `#87002f`); standardize on `#87002f` for implementation.

| Token | Value | Usage |
|---|---:|---|
| `--color-primary-maroon` | `#87002f` | Primary actions, active nav, key status emphasis |
| `--color-primary-maroon-alt` | `#8a0030` | Legacy/mockup alias only |
| `--color-maroon-dark` | `#650023` | Page titles, strong brand text, dark maroon states |
| `--color-maroon-dark-alt` | `#690024` | Legacy/mockup alias only |
| `--color-sidebar` | `#191919` | Sidebar background |
| `--color-sidebar-alt` | `#181818` | Legacy/mockup alias only |
| `--color-page-bg` | `#f7f7f8` | Main application background |
| `--color-surface` | `#ffffff` | Cards, panels, tables, topbar |
| `--color-text` | `#1f171b` | Primary text |
| `--color-text-strong` | `#090909` | Large metrics and high-emphasis values |
| `--color-text-muted` | `#675d62` | Secondary text, helper labels |
| `--color-text-subtle` | `#5b4f54` | Table headers and metadata |
| `--color-border` | `#e7dfe3` | Default borders |
| `--color-border-maroon-soft` | `#e3bfc7` | Review tables, important panels |
| `--color-border-action` | `#d8aab4` | Secondary action button borders |
| `--color-success` | `#16804a` | Present, valid presence, successful sync |
| `--color-warning` | `#8a6500` | Late, attendance warning, caution states |
| `--color-danger` | `#b4232f` | Absent, requires review, excessive breaks |
| `--color-info` | `#315b93` | Break states, informational presence events |
| `--color-accent-yellow` | `#f3c400` | Sidebar active indicator, Mapua accent |
| `--color-neutral` | `#777777` | Disabled, absent-muted, inactive states |

### Soft Badge Backgrounds

| Token | Value | Usage |
|---|---:|---|
| `--color-primary-soft` | `#f7e9ee` | Maroon-tinted selected rows/panels |
| `--color-success-soft` | `#e8f7ee` | Present, valid presence badges |
| `--color-warning-soft` | `#fff2c8` | Late, attendance warning badges |
| `--color-danger-soft` | `#fde8e8` | Absent, requires review badges |
| `--color-info-soft` | `#e9f0fb` | On break, break event badges |
| `--color-neutral-soft` | `#f1f1f1` | Absent muted, disabled, empty states |
| `--color-excused-soft` | `#f0edf5` | Excused badges |
| `--color-excused` | `#594777` | Excused text |

### Status Color Rules

| Status | Text | Background |
|---|---:|---:|
| `Present`, `Valid Presence`, `Completed`, `Synced` | `--color-success` | `--color-success-soft` |
| `Late`, `Attendance Warning`, `In Progress` | `--color-warning` | `--color-warning-soft` |
| `Absent`, `Requires Review`, `Needs Review`, `Sync Failed` | `--color-danger` | `--color-danger-soft` |
| `On Break`, `Break Out`, `Break In` | `--color-info` | `--color-info-soft` |
| `Excused` | `--color-excused` | `--color-excused-soft` |

## 2. Typography

### Font Family

```css
font-family: Inter, "Segoe UI", Arial, sans-serif;
```

Use `Inter` if available. `Segoe UI` keeps the interface native-feeling on Windows.

### Type Scale

| Token | Size | Usage |
|---|---:|---|
| `--font-size-display` | `30px` | Landing page main heading, major student name |
| `--font-size-page-title` | `27px` | Session History page title |
| `--font-size-section-title` | `21px` | Review page title in topbar |
| `--font-size-panel-title` | `18px` | Panel headings, suite title |
| `--font-size-card-title` | `16px` | Activity panel titles |
| `--font-size-body` | `13px` | Default row/body text |
| `--font-size-body-sm` | `12px` | Metadata, topbar labels, helper text |
| `--font-size-label` | `11px` | Form labels, metric labels |
| `--font-size-table-label` | `10px` | Dense table headers and small badges |

### Metric Sizes

| Token | Size | Usage |
|---|---:|---|
| `--font-size-metric-lg` | `30px` | Live session timer |
| `--font-size-metric` | `27px` | Summary cards and evidence metrics |
| `--font-size-metric-sm` | `24px` | Compact roster summary counts |

### Font Weights

| Token | Weight | Usage |
|---|---:|---|
| `--font-weight-regular` | `400` | Rare, long body copy only |
| `--font-weight-medium` | `650` | Course names and medium emphasis |
| `--font-weight-semibold` | `700` | Secondary labels |
| `--font-weight-bold` | `800` | Navigation, metadata, table values |
| `--font-weight-heavy` | `900` | Buttons, labels, statuses |
| `--font-weight-black` | `950` | Metrics, high-emphasis headings |

### Typography Rules

- Use uppercase labels for metric labels, table headers, and compact metadata labels.
- Use tabular numbers for timers, durations, counts, and percentages.
- Do not use negative letter spacing.
- Keep letter spacing subtle: `0.02em` for buttons, `0.04em-0.06em` for uppercase labels.

## 3. Spacing System

Use a compact operational layout. FRAS is a classroom tool, not a marketing site.

| Token | Value | Usage |
|---|---:|---|
| `--space-1` | `4px` | Tiny label gaps |
| `--space-2` | `8px` | Inline gaps, table inner details |
| `--space-3` | `10px` | Button groups, compact row gaps |
| `--space-4` | `12px` | Small card padding, metadata gaps |
| `--space-5` | `14px` | Table tools, activity panels |
| `--space-6` | `16px` | Standard card padding |
| `--space-7` | `18px` | Panel/sidebar user card padding |
| `--space-8` | `20px` | Session card padding |
| `--space-9` | `22px` | Feature card/student card padding |
| `--space-10` | `24px` | Major sections, topbar side padding |
| `--space-11` | `26px` | Session history page padding |
| `--space-12` | `28px` | Standard app page padding |
| `--space-13` | `30px` | Landing page top padding |
| `--space-14` | `34px` | Wide landing page content padding |
| `--space-15` | `44px` | Large bottom page padding |

### Layout Spacing Rules

| Pattern | Value |
|---|---:|
| Page padding, dense pages | `26px-28px` |
| Landing page padding | `30px 34px 44px` |
| Monitor page padding | `24px 28px 34px` |
| Card padding | `15px-22px` |
| Panel padding | `14px-18px` |
| Grid gaps | `12px`, `14px`, `18px`, `20px` |
| Section spacing | `18px-24px` |
| Table header padding | `13px 12px` |
| Table body padding | `15px-16px 12px` |
| Sidebar brand padding | `28px-30px 22px-28px` |
| Nav item height | `54px-56px` |
| Topbar height | `58px-64px` |

## 4. Border Radius System

Keep corners restrained. Most FRAS UI should feel institutional, precise, and operational.

| Token | Value | Usage |
|---|---:|---|
| `--radius-none` | `0` | Grid/table internal edges |
| `--radius-xs` | `2px` | Dense buttons, table shells |
| `--radius-sm` | `3px` | Inputs, action buttons, panels |
| `--radius-md` | `4px` | Student cards, camera chips |
| `--radius-lg` | `6px` | Buttons, side user card, hover rows |
| `--radius-xl` | `8px` | Major cards, panels, session cards |
| `--radius-pill` | `999px` | Badges, status pills, progress bars |
| `--radius-circle` | `50%` | Avatars, timeline nodes |

### Radius Rules

- Cards: `3px-8px`, depending on density.
- Buttons: `2px-6px`; primary workflow buttons use `6px` on operational pages and `2px-3px` in dense review/history tables.
- Badges: always `999px`.
- Inputs: `3px-4px`.
- Tables: outer shell `2px-3px`; rows do not need rounded corners.
- Drawer/modal: `0` on viewport edge, with shadow rather than rounded chrome.

## 5. Shadows

| Token | Value | Usage |
|---|---|---|
| `--shadow-topbar` | `0 1px 8px rgba(20,20,20,.04)` | Topbar |
| `--shadow-card` | `0 7px 18px rgba(29,21,24,.04)` | Dense cards, history/review cards |
| `--shadow-card-lg` | `0 10px 26px rgba(29,21,24,.06)` | Monitor panels and major cards |
| `--shadow-card-xl` | `0 10px 28px rgba(29,21,24,.06)` | Landing priority cards |
| `--shadow-primary-action` | `0 8px 18px rgba(138,0,48,.18)` | Primary maroon button |
| `--shadow-primary-action-strong` | `0 9px 18px rgba(138,0,48,.22)` | Prominent `Start Monitoring` |
| `--shadow-drawer` | `-20px 0 44px rgba(25,16,20,.16)` | Student detail drawer |
| `--shadow-inset-brand` | `inset 0 0 0 1px rgba(255,255,255,.14)` | Brand seal/visual mark |

### Shadow Rules

- Use soft shadows for hierarchy, not decoration.
- Tables should primarily use borders; shadows should be subtle.
- Drawers should use a strong directional shadow to show layered context.

## 6. Reusable UI Components

Build these components before implementing full pages.

## Sidebar

### Purpose

Primary application navigation and role context for professors.

### Props / Inputs

```ts
type SidebarItem = {
  label: string;
  icon?: string;
  href?: string;
  active?: boolean;
};

type SidebarProps = {
  brandName: string;
  productName: string;
  items: SidebarItem[];
  userName?: string;
  userRole?: string;
  userInitials?: string;
};
```

### Where Used

- Today's Classes
- Live Session
- Session History
- Session Review
- Student Evidence

### Styling Rules

- Width: `250px-260px`; standardize to `255px`.
- Background: `--color-sidebar`.
- Active item: `--color-primary-maroon` with `4px` yellow left indicator.
- Nav item height: `54px-56px`.
- User card anchored to bottom.

### Example Usage

```html
<Sidebar
  brandName="Mapua University"
  productName="Attendance Suite"
  activeItem="Session History"
  userName="Prof. Brown"
  userRole="Course Monitor"
/>
```

## Topbar

### Purpose

Provides product context, search, utility icons, and current user avatar.

### Props / Inputs

```ts
type TopbarProps = {
  title?: string;
  tabs?: { label: string; active?: boolean; href?: string }[];
  searchPlaceholder?: string;
  statusLabel?: string;
  avatarInitials?: string;
};
```

### Where Used

- All pages.
- Live Session uses `statusLabel="Live Session Active"`.
- Session History uses tabs/search.

### Styling Rules

- Height: `58px-64px`.
- Background: `--color-surface`.
- Border-bottom: `1px solid --color-border`.
- Shadow: `--shadow-topbar`.
- Utility icons aligned right.

### Example Usage

```html
<Topbar
  title="Attendance Suite"
  searchPlaceholder="Search sessions..."
  avatarInitials="MB"
/>
```

## Page Header

### Purpose

Introduces the current page or workflow step with metadata and primary page action.

### Props / Inputs

```ts
type PageHeaderProps = {
  title: string;
  subtitle?: string;
  metadata?: string[];
  primaryAction?: { label: string; onClick?: () => void };
};
```

### Where Used

- Today's Classes
- Session History
- Session Review
- Student Evidence

### Styling Rules

- Title sizes: `27px-30px` for page content headers.
- Metadata uses `12px-14px`, weight `750-800`.
- Primary page action aligns right.

### Example Usage

```html
<PageHeader
  title="Attendance Session History"
  metadata={["IT114L - Web Systems and Technologies", "Section A41", "Room ZM2"]}
  primaryAction={{ label: "Export Full History" }}
/>
```

## Class Card

### Purpose

Displays one assigned class and its next available action.

### Props / Inputs

```ts
type ClassCardProps = {
  courseCode: string;
  courseName: string;
  room: string;
  schedule: string;
  studentCount: number;
  status: "upcoming" | "ongoing" | "completed" | "needs_review";
  primaryActionLabel: string;
  secondaryActions?: string[];
};
```

### Where Used

- Today's Classes card view.

### Styling Rules

- Use blackboard-inspired header: dark green/charcoal surface.
- Status badge top-right.
- Primary action maroon for ongoing/startable classes.
- Completed cards may use reduced opacity.

### Example Usage

```html
<ClassCard
  courseCode="CS126-8"
  courseName="Software Engineering"
  room="ZM2"
  schedule="02:00 PM - 03:10 PM"
  studentCount={38}
  status="ongoing"
  primaryActionLabel="Start Monitoring"
/>
```

## Stat Card

### Purpose

Shows compact metrics for sessions, presence validation, rosters, and history.

### Props / Inputs

```ts
type StatCardProps = {
  label: string;
  value: string | number;
  helperText?: string;
  tone?: "default" | "success" | "warning" | "danger" | "info" | "review";
};
```

### Where Used

- Live Session roster summary.
- Session Review summary.
- Student Evidence summary.
- Session History summary.

### Styling Rules

- Background: `--color-surface`.
- Border: `1px solid --color-border`.
- Padding: `15px-16px`.
- Metric value: `24px-30px`, weight `950`.
- Review tone may use inset maroon left border.

### Example Usage

```html
<StatCard label="Students Requiring Review" value="04" tone="review" />
```

## Status Badge

### Purpose

Displays status, assessment, or sync state consistently.

### Props / Inputs

```ts
type StatusBadgeProps = {
  label: string;
  tone: "success" | "warning" | "danger" | "info" | "neutral" | "excused" | "primary";
};
```

### Where Used

- Student roster.
- Session Review table.
- Session History table.
- Class cards.

### Styling Rules

- Border radius: `--radius-pill`.
- Padding: `5px 9px` or `6px 10px`.
- Font size: `10px-11px`.
- Uppercase for system states; title case acceptable for student status.

### Example Usage

```html
<StatusBadge label="Requires Review" tone="danger" />
```

## Action Button

### Purpose

Standardizes primary, secondary, outline, and dense table actions.

### Props / Inputs

```ts
type ActionButtonProps = {
  label: string;
  variant?: "primary" | "outline" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  icon?: string;
  disabled?: boolean;
};
```

### Where Used

- Start Monitoring.
- End Session.
- View Session Summary.
- Mark Excused.
- Override Status.
- Confirm Attendance.
- Finalize Attendance.
- Sync to Blackboard.

### Styling Rules

- Primary: maroon background, white text.
- Outline: white background, maroon border/text.
- Dense table actions: height `32px`, font `11px`, radius `2px`.
- Main workflow actions: height `42px-48px`, radius `3px-6px`.

### Example Usage

```html
<ActionButton label="Finalize Attendance" variant="outline" />
<ActionButton label="Sync to Blackboard" variant="primary" />
```

## Data Table

### Purpose

Displays structured review/history records while preserving FRAS's table-based workflow.

### Props / Inputs

```ts
type DataTableProps<T> = {
  columns: {
    key: keyof T | string;
    label: string;
    align?: "left" | "right" | "center";
    width?: string;
  }[];
  rows: T[];
  rowTone?: (row: T) => "default" | "warning" | "review" | "muted";
  actions?: (row: T) => React.ReactNode;
  expandableContent?: (row: T) => React.ReactNode;
};
```

### Where Used

- Session History.
- Session Review.
- Future roster tables.

### Styling Rules

- Header background: `#eeeeef` or `#f2f2f3`.
- Header text: uppercase, `10px-11px`, weight `950`.
- Header padding: `13px 12px`.
- Body padding: `15px-16px 12px`.
- Review rows use soft danger or soft maroon background.
- Action column aligns right.

### Example Usage

```html
<DataTable
  columns={sessionColumns}
  rows={sessions}
  actions={(session) => <ActionButton label="View Session Summary" variant="primary" size="sm" />}
/>
```

## Search / Filter Bar

### Purpose

Supports discoverability without turning pages into analytics dashboards.

### Props / Inputs

```ts
type FilterField = {
  label: string;
  type: "search" | "select" | "date-range";
  value?: string;
  options?: string[];
};

type SearchFilterBarProps = {
  fields: FilterField[];
  onApply?: () => void;
  onSearch?: (value: string) => void;
};
```

### Where Used

- Session History.
- Session Review.
- Live Session roster search.

### Styling Rules

- Background: `--color-surface`.
- Border: `1px solid --color-border`.
- Padding: `14px`.
- Inputs height: `36px-38px`.
- Apply button black or maroon depending on context.

### Example Usage

```html
<SearchFilterBar
  fields={[
    { label: "Date Range", type: "date-range", value: "Oct 01, 2023 - Oct 31, 2023" },
    { label: "Session Status", type: "select", value: "All Statuses" }
  ]}
/>
```

## Student Detail Drawer

### Purpose

Shows student evidence without navigating away from Live Session or Session Review.

### Props / Inputs

```ts
type StudentDetailDrawerProps = {
  open: boolean;
  studentName: string;
  studentNumber: string;
  currentStatus: string;
  timeIn?: string;
  presenceDuration?: string;
  outsideDuration?: string;
  breakOutHistory?: string[];
  breakInHistory?: string[];
  actions?: React.ReactNode;
};
```

### Where Used

- Live Session student roster.
- Session Review student evidence quick view.

### Styling Rules

- Position fixed to right.
- Width: `386px`.
- Height: `100vh`.
- Background: `--color-surface`.
- Shadow: `--shadow-drawer`.
- Padding: `22px`.
- Use detail cards in `2-column` grid.

### Example Usage

```html
<StudentDetailDrawer
  open
  studentName="John Doe"
  studentNumber="2020-00123"
  currentStatus="On Break"
  timeIn="07:18 AM"
  presenceDuration="58m"
  outsideDuration="11m"
/>
```

## Timeline Component

### Purpose

Displays chronological evidence for Time In, Break Out, Break In, and Time Out.

### Props / Inputs

```ts
type TimelineEvent = {
  time: string;
  type: "time_in" | "break_out" | "break_in" | "time_out" | "warning";
  title: string;
  description?: string;
  evidenceLabel?: string;
};

type TimelineProps = {
  events: TimelineEvent[];
  compact?: boolean;
};
```

### Where Used

- Student Evidence page.
- Session Review expandable rows.
- Student Detail Drawer, compact form.

### Styling Rules

- Use vertical line with circular nodes for full detail view.
- Use card grid timeline for compact table expansion.
- Time column uses tabular numbers and weight `950`.
- Break events use info color.
- Warning/review events use warning or danger color.

### Example Usage

```html
<Timeline
  events={[
    { time: "09:04 AM", type: "time_in", title: "Time In", evidenceLabel: "Verified face" },
    { time: "09:29 AM", type: "break_out", title: "Break Out", evidenceLabel: "Exit detected" },
    { time: "09:43 AM", type: "break_in", title: "Break In", evidenceLabel: "Entry detected" },
    { time: "10:28 AM", type: "time_out", title: "Time Out", evidenceLabel: "Verified face" }
  ]}
/>
```

## Presence Ratio Bar

### Purpose

Shows how much of the session a student spent inside vs outside the classroom.

### Props / Inputs

```ts
type PresenceRatioBarProps = {
  insideSeconds: number;
  outsideSeconds: number;
  untrackedSeconds?: number;
  sessionSeconds: number;
  showLegend?: boolean;
};
```

### Where Used

- Student Evidence page.
- Session Review expanded student detail.

### Styling Rules

- Height: `14px`.
- Radius: `--radius-pill`.
- Inside segment: success.
- Outside segment: danger.
- Untracked segment: neutral.
- Always include numeric labels nearby; do not rely on color alone.

### Example Usage

```html
<PresenceRatioBar
  insideSeconds={3300}
  outsideSeconds={1920}
  untrackedSeconds={180}
  sessionSeconds={5400}
  showLegend
/>
```

## Implementation Notes

- Build tokens first, then components, then pages.
- Keep professor navigation role-based. Admin-only pages should not appear in the professor sidebar.
- Use `Session History`, `Session Review`, and `Student Evidence` consistently. Avoid reintroducing ambiguous labels like `Attendance Logs` for multiple concepts.
- Every attendance decision should expose evidence: event timeline, presence duration, outside duration, assessment, and professor action.
- Blackboard synchronization should remain a final step after professor validation.
