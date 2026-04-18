# EDITEASE Admin Page — Full Audit & Redesign Plan

> **Reviewer persona:** Senior Product Designer + Frontend Engineer + SaaS UX Strategist.  
> **Scope:** `Dashboard.jsx` (AdminOverview), `UserManagement.jsx`, `JobMonitor.jsx`, `AppShell.jsx`, `admin.py`, `index.css`.

---

## A. Overall Verdict

The admin section is **partially complete and structurally sound, but it is not production-ready and is not presentation-ready in its current form.** The foundation is good — you have a solid design token system, real data, GSAP animations, and a glassmorphism shell. However, the admin-specific pages suffer from a pattern of *functional correctness at the expense of information architecture*. What exists reads like a developer's first pass at a UI — the data is there, but it is never organized into a coherent control-center narrative.

**Rating before improvements: 5.5/10**  
Strong bones, but the admin pages betray the quality of the shell around them.

---

## B. Biggest Problems (Ranked by Severity)

### 🔴 Critical (Will fail in presentation / real use)

1. **No system health narrative on the Overview.** The admin Dashboard has stats but no "system is healthy / degraded / critical" verdict. An examiner looking at it has no idea at a glance whether the system is okay. There is no alerting hierarchy — 5 failed tasks and 2 uncertain clips look the same as everything being perfect.

2. **Role change has zero confirmation.** In `UserManagement.jsx`, a `<select>` dropdown directly calls `handleRoleChange` on `onChange`. There is no "Are you sure you want to make this user an Admin?" gate. This is a trust-and-safety catastrophe. In any real product, this would be a P0 bug. For an academic presentation, an examiner with SaaS knowledge will call this out immediately.

3. **User deactivation has zero confirmation.** Same issue. `handleStatusChange` fires immediately on button click with a destructive action (deactivating a user). No modal, no warning, no undo.

4. **The UserManagement page has no search or filter.** With 15+ users per page, you cannot search by name, email, or filter by role or status. This makes it useless at scale and looks remarkably unfinished next to job filters that already exist in `JobMonitor.jsx`.

5. **The Job Monitor has no retry/cancel action.** You can see a failed job. You cannot do anything about it from the UI. There's no "Retry", no "Cancel", no "Copy Task ID", no "View full error". The `error_message` field is truncated into the cell with no expand mechanism.

6. **The Job Monitor "Timing" column shows only created-at time, not duration.** An admin monitoring jobs cares about *how long* something took, not *when* it was created. There is no `started_at`, `completed_at`, or computed `duration` shown.

### 🟠 Major (Hurts usability and professionalism)

7. **The Admin Overview is missing a "Recent Activity" feed.** You have `recent_organized_uploads` in the API response but it is completely ignored by the frontend. This is rich, alive data being thrown away.

8. **Pagination on UserManagement does not show current page number.** "Prev / Next" buttons with no page indicator is a UX regression. The user cannot tell they are on page 3 of 8.

9. **The "Quick Actions" bento card is filler.** Three links in a 2-column spanning card is weak use of prime dashboard real estate. It works as a widget in a prototype but not in a product presentation.

10. **No system-level alerts / banner system.** If `tasks_failed > 0`, the dashboard should show a prominent, dismissable banner at the top: "⚠ 3 tasks failed — Review now." Currently the only signal is a small colored number inside a bento card.

11. **No "last login" or "last active" data shown.** The User Management table shows "Joined" date but not "Last Seen" — the most operationally useful signal for an admin managing platform access.

12. **The `AdminOverview` has no refresh button.** Stats are fetched once on mount and never again unless the page reloads. For a live system with Celery tasks, this is insufficient.

13. **Invite Modal has no role description tooltips.** The role dropdown says "Admin (Full Access)" but an admin reviewing a presentation would ask: what *exactly* can each role do? No help text, no description.

14. **The `JobMonitor` auto-refresh logic is subtly broken.** It checks `jobs.some(j => j.status === 'PENDING' || j.status === 'STARTED')` inside the interval, but `jobs` inside the closure is stale (captured from the render that set up `setInterval`). This is a classic React stale closure bug. It could stop polling prematurely or never stop.

### 🟡 Moderate (Polish and professionalism gaps)

15. **Badge system is incomplete on UserManagement.** The `role` badge for non-admin roles has no semantic color — it renders as a plain grey badge. Editor should be green, Reviewer should be amber, Admin should be blue.

16. **`Status` column in the user table uses text+icon but no badge.** Active/Inactive is shown as raw colored `<span>` text, not a consistent badge component. Inconsistent with the rest of the system.

17. **The `PageHeader` in admin pages fires its animation every time you switch pages**, but the animation relies on `SplitType` which does not always cleanly revert. On rapid navigation this creates character artifacts in the title.

18. **No `aria-label` on icon-only buttons.** The "deactivate" shield button has a `title` prop (good), but no `aria-label`. Title is not accessible on keyboard or screen reader in all contexts.

19. **The bento grid is `repeat(4, 1fr)` hard-coded.** On a 1280px screen with a 260px sidebar, each column is about 270px wide — manageable. But on a 1024px screen (a typical exam presentation laptop), the 4-column grid is too tight and the stat values will wrap badly. No `@media` response exists for the bento grid.

20. **The `display-title` class animation on PageHeader does not account for admin page re-renders.** Each navigate fires the SplitType animation from scratch. On slow machines, you'll briefly see unstyled text.

---

## C. Best Redesign Direction

The admin section should feel like a **Mission Control dashboard**, not a settings page. The mental model to target is: Vercel's deployment dashboard + Linear's issue tracker + GitHub's organization admin. Key principles:

1. **Feed over form** — The admin's primary job is to monitor and react. Lead with a live event feed, not static stat cards.
2. **Progressive disclosure** — Surface the most important alerts first, let the admin drill down. Not everything at once.
3. **Destructive actions require ceremonies** — Confirmation dialogs with clear consequence descriptions, not just "Are you sure?".
4. **Trust indicators** — Show audit trail. "Role changed by admin@editease.com 2h ago."
5. **Status-first design** — Every user and job should communicate its state at a glance without reading.

---

## D. Detailed Section-by-Section Improvements

### D1. Admin Overview (`Dashboard.jsx` → `AdminOverview`)

**Current state:** 6 bento stat cards + 2 charts. Clean surface but shallow.

**Problems:**
- No system health verdict
- `recent_organized_uploads` data discarded
- No refresh
- No alerts for failures
- "Quick Actions" is filler

**Exact changes:**

1. **Add a System Health Banner at the very top** (above the bento grid). Logic:
   - If `tasks_failed > 0` → red banner: "🚨 {N} background tasks failed. [View Jobs →]"
   - If `tasks_running > 0` and `tasks_failed === 0` → blue banner: "⚙ {N} tasks are processing. [Monitor →]"
   - If `pending_review > 10` → amber banner: "⚑ Review queue is building up ({N} clips). [Go to Review →]"
   - If all clear → green banner: "✓ System healthy — all tasks running normally."
   This is the single most impactful addition. One paragraph of code, massive presentation value.

2. **Replace "Quick Actions" bento with a "Recent Activity" feed.** Use the `recent_organized_uploads` array already returned by `/admin/overview`. Render a compact list: `[thumbnail icon] "filename.mp4" organized → Action Scene • by username • 2min ago`. This makes the dashboard feel *alive*.

3. **Add a `<RefreshCw>` icon button to the PageHeader actions** that re-calls `api.get('/admin/overview')` and updates stats. Add a `lastRefreshed` timestamp displayed subtly: "Updated 2m ago".

4. **Make bento stat cards clickable navigation.** The "Total Users" card should link to `/app/admin/users`. "Active Tasks" should link to `/app/admin/jobs`. This transforms passive display into navigation shortcuts.

5. **Responsive bento grid.** Change `repeat(4, 1fr)` to:
   ```css
   grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
   ```
   This adapts to screen sizes without breaking layout.

6. **Add "Uncertain Clips" as its own bento card** (currently it's a sub-note under Pending Review). Uncertain clips are a distinct admin concern — they represent AI model failure. Give them their own red accent card.

---

### D2. User Management (`UserManagement.jsx`)

**Current state:** A paginated table with role select and activate/deactivate toggle. Structurally correct but dangerously missing safety gates.

**Exact changes:**

1. **MUST: Add a ConfirmationModal component** for destructive actions. Minimum props: `title`, `description`, `confirmLabel`, `confirmVariant ('danger' | 'warning')`, `onConfirm`, `onCancel`. Trigger this before `handleRoleChange` and `handleStatusChange`. The description should say something specific:
   > "You are about to promote **ash@editease.com** to **Admin**. They will gain full platform access including user management and job control. This cannot be auto-reversed."

2. **MUST: Add search input.** A single `<input type="search" placeholder="Search by name or email...">` that debounces (300ms) and appends `?search=query` to the API call. The backend already has MongoDB — a simple `$regex` or `$text` search on `username`/`email` is trivial to add.

3. **MUST: Add role and status filter dropdowns** next to the search bar. Filter by `role: ['admin', 'editor', 'reviewer', 'all']` and `status: ['active', 'inactive', 'all']`. These should be in the table toolbar (below PageHeader, above the table).

4. **SHOULD: Add "Last Seen" column.** Requires adding `last_login_at` to the user document on successful auth in `auth.py` (`auth_service.login_user()` should set `last_login_at: datetime.utcnow()`). Display as "3h ago", "Yesterday", "2 weeks ago" using `date-fns` or a simple relative-time formatter.

5. **SHOULD: Add page number indicator.** Change `Prev / Next` to:
   ```
   [← Prev]  Page 2 of 8  [Next →]
   ```

6. **SHOULD: Replace the role `<select>` in the table Actions column with an "Edit" button** that opens a `UserDetailPanel` (a right-side slide-over panel or modal). This is cleaner and allows showing the full user profile, role history, and confirmation dialog in one dedicated space, rather than an inline dropdown that looks unfinished.

7. **SHOULD: Color-code role badges properly:**
   - `admin` → `.badge.info` (blue — already exists)
   - `editor` → `.badge.success` (green — already exists)
   - `reviewer` → `.badge.warning` (amber — already exists)
   Currently only `admin` gets `.badge.info`. Other roles get plain unstyled grey.

8. **SHOULD: Replace the `Status` text display with a `.badge.success`/`.badge.danger` component**, consistent with the rest of the system.

9. **NICE: Add a "Bulk Actions" toolbar** that appears when checkboxes are selected. Actions: "Deactivate Selected", "Export CSV". This is the #1 feature that impresses an examiner as "scale-aware."

10. **NICE: Add an "Audit Log" tab** or link → shows recent admin actions: "Admin promoted ash@editease.com to Admin at 14:32." Requires a backend `audit_log` collection that records writes in `update_user_role` and `update_user_status`.

---

### D3. Job Monitor (`JobMonitor.jsx`)

**Exact changes:**

1. **MUST: Fix the stale closure bug.** Change the interval to use a ref:
   ```js
   const jobsRef = useRef(jobs);
   useEffect(() => { jobsRef.current = jobs; }, [jobs]);
   // Inside interval: if (jobsRef.current.some(...))
   ```
   Or better, always poll on a fixed interval when the page is visible (use `document.visibilityState`).

2. **MUST: Add a "Duration" column.** The backend `task_service.get_paginated_jobs()` should return `started_at` and `completed_at` (or `updated_at`). Compute `duration = completed_at - started_at` in seconds. Display as "4.2s", "1m 23s". This is the most operationally useful single field.

3. **MUST: Add "Copy Task ID" action.** The task ID is shown truncated. Add a copy-to-clipboard `<Copy size={12}>` icon next to it. Clicking copies the full UUID. This is a trivial 5-line addition that immediately signals "this is a real tool."

4. **MUST: Add error expand / modal.** When `j.error_message` exists, show a "View Error" link that opens a modal/expand with the full traceback. Currently it's truncated in the cell with no way to read the full error message.

5. **SHOULD: Add a "Retry" action button for FAILURE jobs.** This requires a new backend endpoint: `POST /admin/jobs/<task_id>/retry` that re-dispatches the Celery task. On the front end, a small "↺ Retry" button in the row's Actions column.

6. **SHOULD: Add a "Cancel" action for PENDING/STARTED jobs.** Requires `celery.control.revoke(task_id, terminate=True)` on the backend. High value for an admin who sees a runaway job.

7. **SHOULD: Add color-coded status pill badges** instead of plain text:
   - `SUCCESS` → `.badge.success`
   - `FAILURE` → `.badge.danger`
   - `PENDING` → `.badge.warning`  
   - `STARTED` → `.badge.info` + animated pulse dot

8. **SHOULD: Show the user who triggered the job.** The `tasks_col` document should include `triggered_by: user_id`. The Job Monitor table should show the triggering user's avatar+name.

9. **NICE: Add a live stats ribbon** at the top of the Job Monitor page:
   `[  Running: 2  |  Succeeded: 47  |  Failed: 1  |  Avg Duration: 8.3s  ]`
   Computed from the current filter results. Gives management-level insight without needing to read rows.

10. **NICE: Add a "Clear Completed" button** that archives/soft-deletes all SUCCESS tasks older than 24h. Keeps the table clean.

---

### D4. Navigation & AppShell

**Exact changes:**

1. **SHOULD: Add a notification dot on the "Job Monitor" nav item** if `tasks_failed > 0`. A small red dot indicator on the nav icon communicates urgency without requiring the admin to visit the page. Requires passing `adminStats` down from a context or polling.

2. **SHOULD: Add "System" section label distinction.** The admin nav group already has a divider and "System" label — good. But the label should also show a subtle badge count: "System  `●2`" (indicating 2 items of interest). 

3. **NICE: Add keyboard shortcut hints.** In the sidebar nav items, add small monospace shortcut hints: `Ctrl+U` for Users, `Ctrl+J` for Jobs. Purely visual hints (non-functional) still signal product maturity and impress presentation reviewers.

---

### D5. Invite Modal

**Exact changes:**

1. **SHOULD: Add role description help text.** Below the role select, show a dynamic description:
   - Editor: "Can upload videos and trigger auto-organization. Cannot manage users or view system jobs."
   - Reviewer: "Can review ambiguous clips in the Review Queue. Read-only access to organized footage."
   - Admin: "Full platform access. Can manage users, monitor jobs, and access system settings."

2. **SHOULD: Prevent sending to already-registered emails.** Before submitting, check `GET /admin/users?email=...` and surface "This email is already registered." This prevents wasted invites.

3. **NICE: Add "Pending Invitations" list** below the user table, showing sent-but-not-accepted invites with a "Revoke" action. Requires a backend `invitations` collection with status tracking.

---

## E. Suggested Layout / Wireframe (Text Representation)

### Admin Overview Page

```
┌──────────────────────────────────────────────────────────────┐
│  SYSTEM HEALTH BANNER (conditional, full width)              │
│  🚨 2 tasks failed — [View Failed Jobs]   [Dismiss]           │
└──────────────────────────────────────────────────────────────┘

┌─ PageHeader ────────────────────────────────────────────────┐
│  Overview                              [↺ Refresh]  Updated 2m ago │
│  System status and real-time activity.                       │
└──────────────────────────────────────────────────────────────┘

┌─ Bento Row 1 (5 cards) ─────────────────────────────────────┐
│ [Clips Extracted ×2] │ [Organized] │ [Pending Review] │ [Failed Tasks] │ [Users] │
└──────────────────────────────────────────────────────────────┘

┌─ Bento Row 2 (2 cards) ─────────────────────────────────────┐
│  Review Pipeline (Pie chart)      │  Classification Breakdown (Bar) │
└──────────────────────────────────────────────────────────────┘

┌─ Recent Activity Feed (full width) ─────────────────────────┐
│  ● action_scene.mp4 organized by ash@  1m ago               │
│  ● interview_002.mp4 organized by john@  3m ago             │
│  ● narration.mp4 organized by mary@   7m ago                │
│  ● task FAILURE: auto_organize on clip.mp4  12m ago  🔴     │
└──────────────────────────────────────────────────────────────┘
```

### User Management Page

```
┌─ PageHeader ───────────────────────────────────────────────┐
│  User Management                   [Invite User]           │
└─────────────────────────────────────────────────────────────┘

┌─ Table Toolbar ─────────────────────────────────────────────┐
│  [🔍 Search users...]  [Role: All ▼]  [Status: All ▼]      │
│                                         Total: 42 members   │
└─────────────────────────────────────────────────────────────┘

┌─ Table ─────────────────────────────────────────────────────┐
│ □ │ User          │ Role     │ Status   │ Last Seen │ Actions│
│───┼───────────────┼──────────┼──────────┼───────────┼────────│
│ □ │ ash@email     │ 🔵Admin  │ ✅Active  │ Just now  │ [Edit] │
│ □ │ john@email    │ 🟢Editor │ ✅Active  │ 3h ago   │ [Edit] │
│ □ │ mary@email    │ 🟡Review │ ⛔Inactive│ 2 weeks  │ [Edit] │
└─────────────────────────────────────────────────────────────┘

┌─ Pagination ────────────────────────────────────────────────┐
│  Showing 15 of 42          [← Prev]  Page 1 of 3  [Next →] │
└─────────────────────────────────────────────────────────────┘
```

### Job Monitor Page

```
┌─ PageHeader ───────────────────────────────────────────────┐
│  Job Monitor                    [Type: All▼][Status: All▼] │
└─────────────────────────────────────────────────────────────┘

┌─ Live Stats Ribbon ─────────────────────────────────────────┐
│  Running: 2  │  Succeeded: 47  │  Failed: 3  │  Avg: 8.3s  │
└─────────────────────────────────────────────────────────────┘

┌─ Table ─────────────────────────────────────────────────────┐
│ Task ID  │ Type      │ Status     │ Triggered by │ Duration │ Actions  │
│──────────┼───────────┼────────────┼──────────────┼──────────┼──────────│
│ a4f1... 📋│ auto_org  │ 🔴FAILURE  │ ash@         │ 12.4s   │ [↺Retry] │
│ b2c9... 📋│ upload    │ 🟢SUCCESS  │ john@        │ 3.1s    │          │
│ e7d3... 📋│ auto_org  │ 🔵STARTED● │ mary@        │ ongoing │ [✕Cancel]│
└─────────────────────────────────────────────────────────────┘
```

---

## F. Features to Add

### Must Have
| Feature | Where | Effort |
|---|---|---|
| Confirmation modal for role/status changes | UserManagement | ~2h |
| User search + filter | UserManagement + admin.py | ~3h |
| System health banner on Overview | Dashboard AdminOverview | ~1h |
| Fix stale closure in JobMonitor polling | JobMonitor | ~30min |
| Error expand modal for failed jobs | JobMonitor | ~1h |
| Full task ID copy-to-clipboard | JobMonitor | ~30min |
| Proper status and role badges | UserManagement + JobMonitor | ~1h |
| Page number in pagination | Both tables | ~30min |

### Should Have
| Feature | Where | Effort |
|---|---|---|
| Recent Activity feed on Overview | Dashboard | ~2h |
| Refresh button on Overview | Dashboard | ~30min |
| Last Seen column | UserManagement + auth.py | ~2h |
| Duration column | JobMonitor + task_service.py | ~1h |
| Retry / Cancel job actions | JobMonitor + admin.py | ~3h |
| Role help text in Invite Modal | InviteModal | ~30min |
| Bento cards as nav links | Dashboard | ~30min |
| Failed job nav badge | AppShell | ~1h |
| Responsive bento grid | Dashboard CSS | ~30min |

### Nice to Have
| Feature | Where | Effort |
|---|---|---|
| Audit log (who did what) | New page + audit_service.py | ~5h |
| Pending invitations list | UserManagement | ~2h |
| Bulk user actions | UserManagement | ~2h |
| Live stats ribbon on Job Monitor | JobMonitor | ~1h |
| Keyboard shortcut hints in nav | AppShell | ~30min |
| "Clear Completed Jobs" | JobMonitor + admin.py | ~1h |
| Export users as CSV | UserManagement | ~2h |

---

## G. UI Polish Ideas

### Immediate visual upgrades (< 1h each):

1. **Status badge color system.** See section D2 item 7. One-line CSS class change per badge type.

2. **Table row hover color.** The current `var(--hover-surface)` is barely perceptible (5% white). Change it to `rgba(88, 166, 255, 0.04)` so the hover accent matches the brand color subtly.

3. **Add `letter-spacing: 0.08em; text-transform: uppercase;` to all `<th>` cells.** This single change makes any table look 10× more professional. Done in the `.data-table th` rule.

4. **Add `border-left: 2px solid var(--danger)` to table rows where `status === 'FAILURE'`** in JobMonitor. The left-border accent on failure rows is a table design pattern used in Sentry, Linear, and Datadog. Immediately scannable.

5. **Use `font-variant-numeric: tabular-nums` on all stat values and table numbers.** This prevents numbers from "jumping" as they change width. Add to `.data-table td`, `.stat-value-anim`.

6. **Add a subtle `background: rgba(218,54,51,0.03)` to entire failure rows** in JobMonitor. The row should be tinted, not just the status cell.

7. **Add transition to table rows:** `transition: background 0.15s`. Smooth hover feels premium.

8. **Shimmer skeleton on stat cards.** Currently `LoadingState` renders a table skeleton. The admin overview should show skeleton bento cards (same shape as the real ones) while data loads. This prevents layout shift and looks polished.

9. **Fix the `display-title` PageHeader jitter.** Wrap the `h1` contents in a `<span style="display:block;">` to prevent the SplitType wrapping from causing inline width jitter across re-renders. Reset the split on every `title` change properly.

10. **Add `tabIndex` to table rows** with role actions, so keyboard users can tab through and activate role changes without a mouse.

---

## H. Technical Implementation Suggestions

### Backend (Flask + MongoDB)

**1. Add `last_login_at` tracking (auth.py)**
```python
# In auth_service.login_user(), after successful auth:
users_col.update_one(
    {'_id': user['_id']},
    {'$set': {'last_login_at': datetime.utcnow()}}
)
```
Return `last_login_at` in `/admin/users` response.

**2. Add search and filter to `/admin/users` (admin.py)**
```python
@admin_bp.get('/users')
@role_required(['admin'])
def get_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    return jsonify(auth_service.get_paginated_users(page, limit, search, role, status))
```
In `auth_service.get_paginated_users()`, build a query dict:
```python
query = {}
if search:
    query['$or'] = [
        {'username': {'$regex': search, '$options': 'i'}},
        {'email': {'$regex': search, '$options': 'i'}}
    ]
if role:
    query['role'] = role
if status == 'active':
    query['is_active'] = True
elif status == 'inactive':
    query['is_active'] = False
```

**3. Add job retry endpoint (admin.py)**
```python
@admin_bp.post('/jobs/<task_id>/retry')
@role_required(['admin'])
def retry_job(task_id):
    from services.task_service import get_job_by_task_id
    job = get_job_by_task_id(task_id)
    if not job or job['status'] != 'FAILURE':
        return jsonify({'error': 'Only failed jobs can be retried'}), 400
    # Re-dispatch based on job type
    from api.celery_worker import auto_organize_task  # adjust import
    new_task = auto_organize_task.delay(job['input_path'], job.get('user_id'))
    return jsonify({'new_task_id': new_task.id})
```

**4. Add job cancel endpoint (admin.py)**
```python
@admin_bp.delete('/jobs/<task_id>')
@role_required(['admin'])
def cancel_job(task_id):
    from api.celery_worker import celery_app
    celery_app.control.revoke(task_id, terminate=True, signal='SIGTERM')
    from services.task_service import tasks_col
    tasks_col.update_one({'task_id': task_id}, {'$set': {'status': 'REVOKED'}})
    return jsonify({'revoked': task_id})
```

**5. Add duration fields to tasks (task_service.py)**
When a task starts (STARTED), record `started_at = datetime.utcnow()`.
When it ends (SUCCESS/FAILURE), record `completed_at = datetime.utcnow()`.
Expose both in `get_paginated_jobs()`. Compute `duration_seconds = (completed_at - started_at).total_seconds()`.

**6. Add basic audit logging**
```python
# services/audit_service.py
from database import get_db
from datetime import datetime

def log_action(actor_id, action, target_id=None, metadata=None):
    get_db()['audit_log'].insert_one({
        'actor_id': actor_id,
        'action': action,           # e.g. 'ROLE_CHANGE', 'USER_DEACTIVATE'
        'target_id': target_id,
        'metadata': metadata or {},
        'created_at': datetime.utcnow()
    })
```
Call `log_action()` in `update_user_role()` and `update_user_status()`.

### Frontend (React)

**1. ConfirmationModal (reusable)**
```jsx
// components/ConfirmationModal.jsx
export function ConfirmationModal({ title, body, confirmLabel = 'Confirm', 
  variant = 'danger', onConfirm, onCancel, loading }) {
  return (
    <div style={{ position:'fixed', inset:0, zIndex:9999, 
      display:'flex', alignItems:'center', justifyContent:'center',
      backgroundColor:'rgba(0,0,0,0.65)', backdropFilter:'blur(4px)' }}>
      <div className="panel" style={{ maxWidth: 440, width: '90%' }}>
        <h3 style={{ marginBottom: 8 }}>{title}</h3>
        <p style={{ marginBottom: 24, color: 'var(--text-secondary)' }}>{body}</p>
        <div style={{ display:'flex', gap:12, justifyContent:'flex-end' }}>
          <button className="btn" onClick={onCancel} disabled={loading}>Cancel</button>
          <button className={`btn btn-${variant}`} onClick={onConfirm} disabled={loading}>
            {loading ? 'Processing...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
```

**2. useRelativeTime hook (for "Last Seen")**
```js
// hooks/useRelativeTime.js
export function relativeTime(dateStr) {
  if (!dateStr) return 'Never';
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
```

**3. SystemHealthBanner component**
```jsx
function SystemHealthBanner({ stats }) {
  const [dismissed, setDismissed] = useState(false);
  if (dismissed) return null;
  
  let color = 'var(--success)', icon = '✓', message = 'System healthy.', link = null;
  
  if (stats.tasks_failed > 0) {
    color = 'var(--danger)';
    icon = '🚨';
    message = `${stats.tasks_failed} background task${stats.tasks_failed>1?'s':''} failed.`;
    link = { to: '/app/admin/jobs', label: 'View Failed Jobs' };
  } else if (stats.pending_review > 10) {
    color = 'var(--warning)'; icon = '⚑';
    message = `Review queue has ${stats.pending_review} clips waiting.`;
    link = { to: '/app/review', label: 'Go to Review Queue' };
  } else if (stats.tasks_running > 0) {
    color = 'var(--accent)'; icon = '⚙';
    message = `${stats.tasks_running} task${stats.tasks_running>1?'s':''} currently processing.`;
    link = { to: '/app/admin/jobs', label: 'Monitor Jobs' };
  }
  
  return (
    <div style={{ background: `${color}18`, border: `1px solid ${color}44`,
      borderLeft: `4px solid ${color}`, borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-16) var(--space-24)', marginBottom: 'var(--space-24)',
      display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color }}>{icon} {message}</span>
      <div style={{ display:'flex', gap: 12, alignItems:'center' }}>
        {link && <Link to={link.to} className="btn" style={{ fontSize: 13 }}>{link.label}</Link>}
        <button onClick={() => setDismissed(true)} style={{ background:'none',border:'none',
          color:'var(--text-muted)',cursor:'pointer',fontSize:18 }}>×</button>
      </div>
    </div>
  );
}
```

**4. Fix JobMonitor stale closure**
```jsx
// Replace the useEffect interval with:
useEffect(() => {
  fetchJobs();
}, [page, filterType, filterStatus]);

useEffect(() => {
  const interval = setInterval(() => {
    // Always re-fetch; the backend decides what's active
    fetchJobs();
  }, 5000);
  return () => clearInterval(interval);
}, [page, filterType, filterStatus]); // Re-register when filters change
```
No need to check job statuses from stale closure — just always poll when on this page.

---

## I. Priority Roadmap

### Phase 1 — "Presentation Ready" (2-4 hours total)

These changes will transform the visual and safety quality of the admin section before a defense/demo:

| # | Change | File | Time |
|---|---|---|---|
| 1 | System Health Banner component | Dashboard.jsx | 1h |
| 2 | Role/Status badge colors | UserManagement.jsx + index.css | 20min |
| 3 | Confirmation modal for role change + deactivate | UserManagement.jsx + new modal | 1.5h |
| 4 | Page number in pagination (both tables) | UserManagement + JobMonitor | 20min |
| 5 | Table column header uppercase + tracking | index.css | 5min |
| 6 | Fix JobMonitor polling stale closure | JobMonitor.jsx | 20min |
| 7 | Copy task ID button | JobMonitor.jsx | 20min |
| 8 | Failure row tinted background | JobMonitor.jsx (inline style) | 10min |

### Phase 2 — "Production Quality" (1-2 days)

| # | Change | Files | Time |
|---|---|---|---|
| 9 | User search + filter (frontend + backend) | UserManagement + admin.py + auth_service | 3h |
| 10 | Recent Activity feed on Overview | Dashboard.jsx | 1.5h |
| 11 | Refresh button + "Updated X ago" | Dashboard.jsx | 30min |
| 12 | Error expand modal in JobMonitor | JobMonitor.jsx | 1h |
| 13 | `last_login_at` tracking + display | auth.py + auth_service + UserManagement | 2h |
| 14 | Duration column in Job Monitor | task_service.py + admin.py + JobMonitor | 1.5h |
| 15 | Bento cards as navigation links | Dashboard.jsx | 20min |
| 16 | Triggered-by user in Job Monitor | tasks_col + JobMonitor | 1h |
| 17 | Responsive bento grid | Dashboard.jsx + index.css | 30min |

### Phase 3 — "Impressive Demo" (3-5 days)

| # | Change | Files | Time |
|---|---|---|---|
| 18 | Job retry + cancel endpoints | admin.py + JobMonitor | 3h |
| 19 | Audit log service + page | audit_service.py + new AuditLog.jsx | 5h |
| 20 | Pending invitations list | InviteModal + new backend | 2h |
| 21 | Bulk user actions | UserManagement | 2h |
| 22 | Live stats ribbon on Job Monitor | JobMonitor | 1h |
| 23 | Nav badge for failed jobs (context-driven) | AppShell + context | 1.5h |
| 24 | Export users CSV | UserManagement + admin.py | 2h |

---

## Key Phrases to Use in Presentation

When a supervisor asks "Why did you design it this way?" — these answers will land:

- **On the health banner:** "This implements triage-level information architecture. An admin shouldn't have to read the whole dashboard to know if the system needs attention."
- **On the confirmation modal:** "Destructive actions require ceremonies. Promoting a user to admin is irreversible in a collaborative multi-tenant system — the UI enforces that weight."
- **On the activity feed:** "Dashboards should feel alive. Static stats are screenshots; a live feed makes the system feel operational."
- **On role-colored badges:** "Color should carry semantic meaning, not just decoration. The admin can scan the user table without reading each role label."
- **On the retry button:** "Observability without actionability is just stress. An admin who sees a failure needs a path to resolution, not just the information that something broke."
