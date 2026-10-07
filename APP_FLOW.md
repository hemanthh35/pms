# CivicConnect — Application Flow

How the app actually works end to end: entry, citizen flow, officer flow, notifications, and the pieces tying it together. This reflects the current build, not the original spec.

---

## 1. Entry point

1. User opens the app at `/`.
2. If **not logged in**, they immediately see a **"Who are you?"** screen (`RolePicker` in [App.jsx](frontend/src/App.jsx)) with two options:
   - **Public** → sends them to `/register`
   - **Officer** → sends them to `/login`
3. If **already logged in**, `/` redirects straight to their dashboard (`/citizen/home`, `/officer/home`, or `/admin/home` based on role).

There is no separate "admin" option on the picker — admin accounts log in through the same `/login` screen as officers; the backend's `role` field on the user decides which dashboard they land on.

---

## 2. Accounts & auth

- Citizens self-register (`POST /auth/register`) with name, email, password. Role is always `citizen` for self-signup.
- Officer and admin accounts are not self-serve — they're seeded by the backend on first run (demo accounts) or created directly in the database. There's no "become an officer" flow in the UI.
- Login (`POST /auth/login`) returns a JWT, stored in `localStorage` (`civicconnect_token`), attached as a Bearer token to every API call via an axios interceptor ([api.js](frontend/src/api.js)).
- `Protected` route wrapper checks `user.role` against the route's required role and redirects if mismatched.

---

## 3. Citizen flow — filing a complaint

Route: `/citizen/report`, a 4-step wizard ([`ReportPage`](frontend/src/App.jsx)):

1. **Photo** — take or upload a photo (JPG/PNG/WebP, max 8MB). Stored as a local preview until submit.
2. **Location** — tap "Use my location":
   - Browser Geolocation API requests GPS coordinates (`enableHighAccuracy: true`).
   - Coordinates are reverse-geocoded through OpenStreetMap's Nominatim API to get a real street address (no API key needed).
   - If permission is denied or GPS fails, a clear error is shown (not a silent fallback) — the user can also tap "Use Hyderabad as location" as an explicit manual override.
3. **Details** — title, category, description, severity (LOW/MEDIUM/HIGH/CRITICAL), entered manually by the citizen (no AI involved).
4. **Review & submit** — final check, then `POST /complaints`.

On submit, the backend:
- Generates a complaint number (`CMP-YYMMDD-XXXX`).
- Auto-assigns a **department** based on category (e.g. "Pothole" → Roads & Infrastructure, "Garbage" → Sanitation) — see `category_departments` map in [v1.py](backend/app/api/v1.py).
- Writes the first `ComplaintHistory` row (`SUBMITTED`).
- Sends the citizen an in-app + push notification: "Complaint submitted."

The citizen can then track it from `/citizen/complaints` (list, filterable by status) or `/citizen/complaints/:id` (full detail with timeline, photo, and location pin on a real map).

---

## 4. Officer flow — handling a complaint

Route: `/officer/home` and `/officer/complaints`.

Officers see complaints that are either unassigned or assigned to them (`GET /officer/complaints`). An officer can:

| Action | Endpoint | What happens |
|---|---|---|
| **Accept** | `POST /officer/complaints/{id}/accept` | Assigns the complaint to themself, status → `ASSIGNED` |
| **Start work** | `POST /officer/complaints/{id}/start` | Status → `IN_PROGRESS` |
| **Submit resolution** | `POST /officer/complaints/{id}/resolve` | Status → `AWAITING_CITIZEN_VERIFICATION`, and the citizen gets a push notification: *"Thanks for reporting ... it's been marked as fixed."* |

Every status change appends a row to `ComplaintHistory`, which is what renders as the timeline on the complaint detail page.

### Citizen verification (closing the loop)
Once an officer resolves a complaint, the citizen sees a "Is the issue fixed?" prompt on the complaint detail page:
- **Yes, it's fixed** → `POST /complaints/{id}/verify?accepted=true` → status → `RESOLVED`, `resolved_at` timestamp set.
- **Reopen issue** → status → `REOPENED`, goes back into the officer's active queue.

---

## 5. Live map

Both citizens and officers can view complaints on a real Leaflet/OpenStreetMap map (`/citizen/map`, `/officer/map`):
- Pins colored by severity (critical = red, high = orange, medium = yellow, low = green).
- Clicking a severity filter (Critical/High/Medium/Low) toggles which pins are shown.
- Search box filters by title or address.
- Clicking a pin opens a popup with the complaint title, status, and a link to the full detail page.

The officer dashboard's "Reports nearby" widget is the same map technology, just smaller and non-interactive (read-only preview).

---

## 6. SLA escalation (the "2-day" rule)

A background job ([scheduler.py](backend/app/scheduler.py)) runs every hour inside the FastAPI process (via APScheduler):

1. Finds complaints still in an open status (`SUBMITTED`, `PENDING_REVIEW`, `ASSIGNED`, `ACKNOWLEDGED`, `IN_PROGRESS`) older than `SLA_HOURS` (default **48 hours**, configurable via `.env`).
2. For each one not already escalated, sends a push + in-app notification:
   - To the **assigned officer**, if there is one.
   - To **all officers and admins**, if nobody's picked it up yet.
3. Marks it `sla_escalated_at` so it's not re-notified every hour.

The admin dashboard's "overdue" count reflects complaints that have been escalated this way.

---

## 7. Push notifications

Real browser push (Web Push API + VAPID keys), not polling:

- A service worker ([`public/sw.js`](frontend/public/sw.js)) listens for `push` events and shows OS-level notifications, even if the tab is closed.
- On login, the frontend asks for notification permission and subscribes (`src/push.js`), sending the subscription to `POST /notifications/subscribe`.
- The backend's `notify_user()` helper ([push.py](backend/app/push.py)) does two things for every notification: writes a row to the `notifications` table (for in-app history) **and** pushes to every device the user has subscribed from.
- Notification triggers currently wired up:
  - Complaint submitted → citizen
  - Complaint resolved → citizen
  - SLA breach (2-day overdue) → officer(s)

---

## 8. Roles summary

| Role | Can do |
|---|---|
| **Citizen** | Register, submit complaints, track their own complaints, verify/reopen resolutions |
| **Officer** | View assigned + unassigned complaints, accept/start/resolve, see the map |
| **Admin** | Everything an officer sees, plus dashboard stats (totals, pending, overdue, resolved), officer list |

---

## 9. What's not built yet

- No per-officer workload balancing — assignment is manual ("Accept" button), not automatic.
- No image-based issue detection — category/severity are entered by the citizen, not inferred.
- Admin "Analytics" page is still static placeholder numbers, not computed from real data.
- No SMS fallback for notifications — push + in-app only.
