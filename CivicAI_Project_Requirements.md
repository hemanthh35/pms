# CivicAI --- Smart Civic Complaint Management System

## Complete Product Requirements & Technical Specification

**Version:** 1.0\
**Project Type:** AI-powered Civic Complaint Management Platform\
**Primary Goal:** Allow citizens to report civic problems using images
and live location, automatically analyze the issue with AI, and provide
officers with a clean map-based dashboard to manage, assign, resolve,
and verify complaints.

------------------------------------------------------------------------

# 1. Product Vision

CivicAI is a mobile-first civic issue reporting and management platform.

A citizen should be able to:

1.  Open the application.
2.  Select **Citizen**.
3.  Capture/upload an image of a civic problem.
4.  Automatically fetch their current location.
5.  Let AI identify and describe the issue.
6.  Review the generated complaint.
7.  Submit it.
8.  Track the complaint from submission to resolution.

An officer should be able to:

1.  Select **Officer** and authenticate.
2.  Open a map showing nearby complaints.
3.  Filter complaints by status, severity, category, ward, and distance.
4.  Open a complaint marker.
5.  View the image, AI analysis, location, citizen description, and
    history.
6.  Accept/assign the complaint.
7.  Update progress.
8.  Upload resolution proof.
9.  Mark the complaint as resolved.
10. Allow the citizen to verify the resolution.

An admin should be able to manage users, officers, departments,
complaints, categories, SLAs, analytics, and system configuration.

------------------------------------------------------------------------

# 2. Technology Stack

## Frontend

-   React.js
-   JavaScript
-   React Router
-   React-Leaflet
-   Leaflet
-   OpenStreetMap
-   Axios
-   CSS / Tailwind CSS
-   Lucide React icons

## Backend

-   Python
-   FastAPI
-   REST API
-   Pydantic
-   SQLAlchemy

## Database

-   PostgreSQL
-   PostGIS
-   Docker
-   Alembic migrations

## Maps

-   OpenStreetMap
-   Leaflet
-   React-Leaflet
-   Browser Geolocation API
-   Reverse geocoding service

## AI

AI should be implemented behind a clean service interface so the
model/provider can be changed later.

Potential responsibilities:

-   Image issue classification
-   Issue description generation
-   Severity prediction
-   Department prediction
-   Confidence score
-   Duplicate/similar complaint detection
-   Resolution-image verification

------------------------------------------------------------------------

# 3. Important Architecture Decision

Do NOT use Flask and FastAPI together for the main API.

Use:

``` text
React.js
    |
    | REST / JSON
    v
FastAPI
    |
    +---- SQLAlchemy ---- PostgreSQL/PostGIS
    |
    +---- AI Service
    |
    +---- Map/Geolocation Services
```

FastAPI is the REST API backend.

Flask is not required unless a separate ML microservice is intentionally
introduced later.

------------------------------------------------------------------------

# 4. User Roles

## 4.1 Citizen

Can:

-   Register/login
-   Submit complaints
-   Capture/upload images
-   Allow location access
-   Edit AI-generated complaint details
-   Track complaints
-   View complaint history
-   Receive status updates
-   View officer information where appropriate
-   Verify resolution
-   Reopen an incorrectly resolved complaint
-   Rate the resolution/service

## 4.2 Officer

Can:

-   Login
-   View assigned complaints
-   View complaints on a map
-   Filter complaints
-   View complaint details
-   Accept/assign complaints
-   Update complaint status
-   Add internal/public comments
-   Upload before/after images
-   Submit resolution
-   View route/location
-   Escalate complaints

Officers must only access complaints they are authorized to manage based
on department, ward, region, or assignment.

## 4.3 Admin

Can:

-   Manage citizens
-   Manage officers
-   Manage departments
-   Manage wards/areas
-   Manage complaint categories
-   View all complaints
-   Assign/reassign complaints
-   Configure SLA rules
-   View analytics
-   View audit logs
-   Manage system settings

------------------------------------------------------------------------

# 5. Complaint Lifecycle

The complaint status system should be explicit.

``` text
SUBMITTED
    |
    v
AI_ANALYZED
    |
    v
PENDING_REVIEW
    |
    v
ASSIGNED
    |
    v
ACKNOWLEDGED
    |
    v
IN_PROGRESS
    |
    v
RESOLUTION_SUBMITTED
    |
    v
AWAITING_CITIZEN_VERIFICATION
    |
    +---- Citizen confirms ----> RESOLVED
    |
    +---- Citizen rejects -----> REOPENED
```

Additional states:

-   REJECTED
-   DUPLICATE
-   ESCALATED
-   CANCELLED

Every status change must be recorded in a complaint history table.

------------------------------------------------------------------------

# 6. Citizen Mobile UI

The citizen experience must be **mobile-first**.

Do not design a desktop website and simply shrink it.

The primary interaction should feel like a modern mobile application.

## 6.1 Bottom Navigation

Use a clean bottom navigation bar:

``` text
┌─────────────────────────────┐
│                             │
│         App Content         │
│                             │
├─────────────────────────────┤
│  Home   Report   Map  Track  │
│   🏠      ＋      🗺️    📋   │
└─────────────────────────────┘
```

Recommended tabs:

-   Home
-   Report
-   Map
-   My Complaints
-   Profile

Keep the navigation simple.

Maximum 5 primary navigation items.

------------------------------------------------------------------------

# 7. Citizen Home Screen

The home screen should contain:

### Header

``` text
Good morning 👋
How can we improve your area?
```

### Primary CTA

Large button/card:

``` text
+ Report an Issue
```

### Current Location

``` text
📍 Current Location
Hyderabad, Telangana
```

### Active Complaints

Show cards such as:

``` text
Pothole
High Priority
In Progress

Complaint #CMP-1024
Updated 15 min ago
```

### Quick Statistics

``` text
3 Active
8 Resolved
11 Total
```

Keep the dashboard visually clean with generous spacing.

------------------------------------------------------------------------

# 8. Citizen Complaint Creation Flow

## Step 1 --- Capture Image

Primary interface:

``` text
┌─────────────────────────┐
│                         │
│                         │
│       CAMERA AREA       │
│                         │
│                         │
│           ◉             │
│                         │
│  Upload from Gallery    │
└─────────────────────────┘
```

Allow:

-   Camera
-   Gallery upload
-   Retake
-   Remove image

## Step 2 --- Location

Request location permission.

Show:

``` text
📍 Location detected

17.3850, 78.4867

Hyderabad, Telangana
```

Allow the citizen to adjust the location on the map if GPS is
inaccurate.

## Step 3 --- AI Analysis

Show an analysis state:

``` text
Analyzing image...

✓ Detecting issue
✓ Estimating severity
✓ Identifying department
```

## Step 4 --- AI Result

Example:

``` text
Detected Issue
Pothole

Category
Road Damage

Severity
High

Confidence
94%

Recommended Department
Roads & Infrastructure
```

The user must be able to edit incorrect AI results.

## Step 5 --- Complaint Review

Display:

-   Image
-   Category
-   Issue
-   Description
-   Severity
-   Location
-   Department

CTA:

**Submit Complaint**

------------------------------------------------------------------------

# 9. AI Analysis Requirements

AI response should follow a structured format.

Example:

``` json
{
  "issue": "Pothole",
  "category": "Road Damage",
  "description": "Large pothole affecting the left side of the road.",
  "severity": "HIGH",
  "confidence": 0.94,
  "department": "ROADS"
}
```

Never trust AI blindly.

The citizen/officer should be able to correct AI-generated information.

AI should also return uncertainty when confidence is low.

Example:

``` text
Confidence: 51%

Please verify the detected issue.
```

------------------------------------------------------------------------

# 10. Complaint Categories

Initial categories:

-   Road Damage
-   Pothole
-   Garbage
-   Illegal Dumping
-   Water Leakage
-   Drainage
-   Streetlight
-   Traffic Signal
-   Broken Footpath
-   Fallen Tree
-   Waterlogging
-   Public Infrastructure Damage
-   Open Manhole
-   Other

Categories should be database-driven rather than hardcoded in the
frontend.

------------------------------------------------------------------------

# 11. Severity System

Use:

### CRITICAL

Immediate public safety risk.

Examples:

-   Exposed electrical wires
-   Major road obstruction
-   Open dangerous manhole
-   Major water pipeline failure

### HIGH

Significant problem requiring fast response.

Examples:

-   Large pothole
-   Broken traffic signal
-   Severe garbage accumulation

### MEDIUM

Normal operational issue.

Examples:

-   Broken streetlight
-   Minor road damage

### LOW

Non-urgent issue.

Examples:

-   Cosmetic infrastructure problems

Severity can be AI-generated but must be editable.

------------------------------------------------------------------------

# 12. GPS & Location

Use browser/device geolocation.

Store:

-   Latitude
-   Longitude
-   Accuracy
-   Address
-   City
-   Area
-   Ward
-   Pincode

Example:

``` text
latitude: 17.385044
longitude: 78.486671
accuracy: 8.2m
```

Do not store exact location unless location permission is granted.

The user must understand that location is being used for complaint
routing.

------------------------------------------------------------------------

# 13. Map System

Use:

-   OpenStreetMap
-   Leaflet
-   React-Leaflet

The map should support:

-   Current user location
-   Complaint markers
-   Marker clustering
-   Complaint detail popups
-   Map movement
-   Zoom
-   Location search
-   Heatmap
-   Status-based filtering
-   Category-based filtering

------------------------------------------------------------------------

# 14. Officer Map Dashboard

The officer experience should be **map-first**.

Desktop/tablet layout:

``` text
┌─────────────────────────────────────────────────┐
│ CivicAI       Search       Notifications   👤   │
├──────────────┬──────────────────────────────────┤
│ Filters      │                                  │
│              │                                  │
│ 🔴 Critical  │              MAP                 │
│ 🟠 High      │                                  │
│ 🟡 Medium    │       🔴       🟡                │
│ 🟢 Low       │                                  │
│              │             🔴                   │
│ Status       │                    🟢            │
│ Category     │                                  │
│ Department   │                                  │
├──────────────┴──────────────────────────────────┤
│ Selected complaint / bottom detail panel        │
└─────────────────────────────────────────────────┘
```

On mobile/tablet, use a bottom sheet for complaint details.

------------------------------------------------------------------------

# 15. Officer Dashboard

Top-level cards:

``` text
Total
24

Pending
8

In Progress
10

Critical
3

Overdue
2
```

Then:

-   Complaint map
-   Nearby complaints
-   Assigned complaints
-   Overdue complaints
-   Recent activity

------------------------------------------------------------------------

# 16. Complaint Marker Design

Marker appearance should communicate priority/status.

Example conceptual system:

``` text
🔴 Critical
🟠 High
🟡 Medium
🟢 Low
```

Marker click opens:

``` text
Pothole
High Priority

📍 1.2 km away

Status: Assigned

[View Complaint]
```

Avoid excessive visual clutter.

Use clustering when many complaints exist.

------------------------------------------------------------------------

# 17. Complaint Detail Screen

Display:

### Header

``` text
Complaint #CMP-1024
High Priority
```

### Image

Large image card.

### AI Analysis

``` text
Pothole
Road Damage
Confidence: 94%
```

### Location

Interactive map preview.

### Description

Citizen description + AI description.

### Timeline

``` text
8:32 PM  Complaint submitted
8:34 PM  AI analysis completed
8:40 PM  Officer assigned
9:10 PM  Officer acknowledged
```

### Actions

Officer:

-   Accept
-   Start Work
-   Add Comment
-   Upload Proof
-   Resolve
-   Escalate

------------------------------------------------------------------------

# 18. Officer Assignment

Complaints can be:

-   Automatically assigned
-   Manually assigned
-   Reassigned by admin

Automatic assignment can consider:

``` text
Department
+
Ward
+
Distance
+
Officer workload
+
Availability
```

Example:

``` text
Complaint
    |
    v
Determine department
    |
    v
Determine ward
    |
    v
Find eligible officers
    |
    v
Rank by distance + workload
    |
    v
Assign
```

------------------------------------------------------------------------

# 19. Duplicate Complaint Detection

This is an important intelligent feature.

When a complaint is submitted:

``` text
New Complaint
      |
      v
Search nearby complaints
      |
      +---- Similar issue?
      |
     YES
      |
      v
Possible duplicate
```

Example:

``` text
Possible Duplicate

A pothole complaint was submitted
42 meters from this location 25 minutes ago.

[View Existing Complaint]
[Submit Anyway]
```

If confirmed duplicate, multiple citizen reports can be linked to the
same underlying issue.

------------------------------------------------------------------------

# 20. Resolution Workflow

Officer uploads:

### Before

Original complaint image.

### After

Resolution image.

Then:

``` text
Resolution submitted
        |
        v
AI verification
        |
        v
Citizen verification
```

Citizen receives:

``` text
Your complaint was marked as resolved.

Is the issue fixed?

[Yes, it's fixed]
[No, reopen complaint]
```

------------------------------------------------------------------------

# 21. SLA & Escalation

Every category can have an SLA.

Example:

``` text
Critical → 4 hours
High     → 12 hours
Medium   → 24 hours
Low      → 72 hours
```

If the complaint exceeds SLA:

``` text
Complaint overdue
      |
      v
Officer notified
      |
      v
Supervisor notified
      |
      v
Escalated
```

The exact SLA values should be configurable by admin.

------------------------------------------------------------------------

# 22. Notifications

Notification events:

-   Complaint submitted
-   AI analysis completed
-   Complaint assigned
-   Officer acknowledged
-   Work started
-   Complaint escalated
-   Resolution submitted
-   Complaint resolved
-   Complaint reopened

Build notifications as an extensible backend service.

------------------------------------------------------------------------

# 23. Citizen Complaint Tracking

The citizen should see a visual timeline:

``` text
✓ Submitted
   |
✓ AI analyzed
   |
✓ Officer assigned
   |
● In progress
   |
○ Resolution
   |
○ Verified
```

This should be mobile-friendly.

------------------------------------------------------------------------

# 24. Admin Dashboard

Admin dashboard should include:

``` text
Total Complaints
Resolved
Pending
Overdue
Critical
Average Resolution Time
```

Charts:

-   Complaints by category
-   Complaints by department
-   Complaints by ward
-   Daily complaint volume
-   Resolution time
-   Status distribution

------------------------------------------------------------------------

# 25. Complaint Heatmap

Use geographic aggregation to identify hotspots.

Example insights:

``` text
Top Complaint Areas

1. Ward 12 — 182 complaints
2. Ward 08 — 141 complaints
3. Ward 17 — 119 complaints
```

The map should visually show complaint density.

------------------------------------------------------------------------

# 26. Search & Filtering

Officer/Admin should be able to search by:

-   Complaint ID
-   Category
-   Location
-   Citizen
-   Officer
-   Department

Filters:

-   Status
-   Severity
-   Category
-   Department
-   Ward
-   Date range
-   Assigned/unassigned
-   Overdue

------------------------------------------------------------------------

# 27. Database Design

## users

``` text
id
name
email
phone
password_hash
role
is_active
created_at
updated_at
```

## complaints

``` text
id
complaint_number
citizen_id
category_id
title
description
ai_description
severity
priority
status
latitude
longitude
location_accuracy
address
city
area
ward_id
department_id
assigned_officer_id
created_at
updated_at
resolved_at
```

## ai_analysis

``` text
id
complaint_id
issue
category
description
severity
confidence
department
model_name
created_at
```

## complaint_history

``` text
id
complaint_id
actor_id
old_status
new_status
comment
created_at
```

## departments

``` text
id
name
description
is_active
```

## officers

``` text
id
user_id
department_id
ward_id
employee_code
availability_status
created_at
```

## categories

``` text
id
name
description
default_sla_hours
is_active
```

## resolution_proofs

``` text
id
complaint_id
officer_id
image_url
description
ai_verification_score
created_at
```

## notifications

``` text
id
user_id
complaint_id
title
message
type
is_read
created_at
```

## duplicate_links

``` text
id
complaint_id
matched_complaint_id
similarity_score
distance_meters
created_at
```

------------------------------------------------------------------------

# 28. API Structure

Base:

``` text
/api/v1
```

## Authentication

``` text
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
```

## Complaints

``` text
POST   /complaints
GET    /complaints
GET    /complaints/{id}
PATCH  /complaints/{id}
DELETE /complaints/{id}
```

## AI

``` text
POST /ai/analyze-image
POST /ai/check-duplicate
POST /ai/verify-resolution
```

## Officer

``` text
GET   /officer/complaints
GET   /officer/complaints/nearby
POST  /officer/complaints/{id}/accept
POST  /officer/complaints/{id}/start
POST  /officer/complaints/{id}/resolve
POST  /officer/complaints/{id}/escalate
POST  /officer/complaints/{id}/proof
```

## Admin

``` text
GET   /admin/dashboard
GET   /admin/complaints
GET   /admin/officers
POST  /admin/officers
PATCH /admin/officers/{id}
GET   /admin/analytics
GET   /admin/audit-logs
```

------------------------------------------------------------------------

# 29. Frontend Route Structure

``` text
/
├── /login
├── /register
│
├── /citizen
│   ├── /home
│   ├── /report
│   ├── /complaints
│   ├── /complaints/:id
│   ├── /map
│   └── /profile
│
├── /officer
│   ├── /dashboard
│   ├── /map
│   ├── /complaints
│   ├── /complaints/:id
│   └── /profile
│
└── /admin
    ├── /dashboard
    ├── /complaints
    ├── /officers
    ├── /departments
    ├── /categories
    ├── /analytics
    └── /settings
```

------------------------------------------------------------------------

# 30. UI/UX Design System

The application should feel:

-   Clean
-   Modern
-   Mobile-first
-   Professional
-   Fast
-   Simple
-   Trustworthy

Avoid:

-   Excessive gradients
-   Huge text
-   Excessive cards
-   Crowded dashboards
-   Too many colors
-   Unnecessary animations
-   Desktop-only layouts

## Typography

Use a modern sans-serif font such as Poppins or Inter.

## Icons

Use Lucide React.

## Cards

Use:

-   12--20px border radius
-   Subtle borders
-   Minimal shadows
-   Clear hierarchy

## Buttons

Primary actions should be obvious.

Examples:

``` text
+ Report Issue
Submit Complaint
Accept Complaint
Start Work
Upload Resolution
```

------------------------------------------------------------------------

# 31. Mobile Design Rules

Design for approximately:

``` text
360px
390px
412px
```

minimum widths.

The UI must not require horizontal scrolling.

Touch targets should be large enough for mobile use.

Bottom navigation should remain easy to reach.

Maps should use full available screen space.

Complaint details on mobile should use bottom sheets or stacked
sections.

------------------------------------------------------------------------

# 32. Responsive Desktop Design

On desktop:

``` text
Sidebar
+
Main Content
+
Map / Detail Panel
```

On mobile:

``` text
Top Header
+
Content
+
Bottom Navigation
```

Do not simply display the desktop sidebar on mobile.

------------------------------------------------------------------------

# 33. Security Requirements

Implement:

-   JWT authentication
-   Password hashing
-   Role-based authorization
-   Input validation
-   File upload validation
-   File size limits
-   MIME type validation
-   SQL injection protection through SQLAlchemy
-   CORS configuration
-   Rate limiting where appropriate
-   Audit logs

Citizens must not be able to access another citizen's private complaint
information unless explicitly allowed.

------------------------------------------------------------------------

# 34. Image Upload Requirements

Validate:

-   JPEG
-   PNG
-   WebP

Reject:

-   Executable files
-   Unsupported MIME types
-   Extremely large files

Generate unique file names.

Do not use user-provided file names directly for storage.

------------------------------------------------------------------------

# 35. Docker Setup

Recommended services:

``` text
docker-compose

services:
  postgres:
    PostgreSQL + PostGIS

  backend:
    FastAPI

  frontend:
    React
```

For local development:

``` text
React
localhost:5173

FastAPI
localhost:8000

PostgreSQL
localhost:5432
```

FastAPI documentation:

``` text
/docs
```

------------------------------------------------------------------------

# 36. Backend Project Structure

``` text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── complaints.py
│   │       ├── officer.py
│   │       ├── admin.py
│   │       └── ai.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── location_service.py
│   │   ├── complaint_service.py
│   │   ├── notification_service.py
│   │   └── assignment_service.py
│   │
│   ├── repositories/
│   ├── core/
│   └── utils/
│
├── alembic/
├── tests/
├── Dockerfile
└── requirements.txt
```

------------------------------------------------------------------------

# 37. Frontend Project Structure

``` text
frontend/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   ├── map/
│   │   ├── complaints/
│   │   └── dashboard/
│   │
│   ├── pages/
│   │   ├── auth/
│   │   ├── citizen/
│   │   ├── officer/
│   │   └── admin/
│   │
│   ├── layouts/
│   ├── hooks/
│   ├── services/
│   ├── api/
│   ├── context/
│   ├── utils/
│   ├── routes/
│   └── App.jsx
│
└── package.json
```

------------------------------------------------------------------------

# 38. Error States

Every important action needs proper states.

Examples:

### Location denied

``` text
We couldn't access your location.

Please enable location access or select
your location manually on the map.
```

### AI failure

``` text
We couldn't analyze this image.

You can manually select the issue category.
```

### Network failure

``` text
Something went wrong.

Please try again.
```

### Empty complaints

``` text
No complaints found.
```

Never leave the user with a blank screen.

------------------------------------------------------------------------

# 39. Loading States

Use skeletons/spinners for:

-   Dashboard
-   Complaint list
-   Map data
-   AI analysis
-   Image upload
-   Complaint submission
-   Resolution upload

For AI processing, show meaningful progress rather than a generic
spinner.

------------------------------------------------------------------------

# 40. Accessibility

Support:

-   Keyboard navigation
-   Visible focus states
-   Good contrast
-   Accessible labels
-   Screen-reader-friendly buttons
-   Clear error messages
-   Avoid color-only status indicators

Example:

Do not rely only on:

``` text
🔴
```

Also display:

``` text
Critical
```

------------------------------------------------------------------------

# 41. Audit Logging

Important actions should be logged:

``` text
Login
Complaint created
Complaint assigned
Complaint reassigned
Status changed
Comment added
Resolution uploaded
Complaint reopened
Admin changes
```

Audit records should contain:

``` text
actor
action
entity
entity_id
timestamp
metadata
```

------------------------------------------------------------------------

# 42. Analytics

Admin analytics should calculate:

-   Total complaints
-   New complaints
-   Resolved complaints
-   Average resolution time
-   SLA compliance
-   Complaints by category
-   Complaints by department
-   Complaints by ward
-   Critical complaints
-   Reopened complaints
-   Duplicate complaints
-   Officer workload

------------------------------------------------------------------------

# 43. Performance Requirements

The frontend should:

-   Lazy-load large pages
-   Optimize images
-   Avoid loading all complaints at once
-   Use pagination
-   Use map clustering
-   Debounce map/search requests

Backend should:

-   Use database indexes
-   Paginate complaint lists
-   Index geographic fields
-   Avoid N+1 queries
-   Use asynchronous endpoints where appropriate

------------------------------------------------------------------------

# 44. PostgreSQL/PostGIS Indexing

Important indexes:

``` text
complaints.status
complaints.category_id
complaints.department_id
complaints.assigned_officer_id
complaints.created_at
complaints.severity
geographic location
```

Use PostGIS geographic indexes for nearby-complaint queries.

------------------------------------------------------------------------

# 45. MVP Scope

The first working version should contain:

### Citizen

-   Login/register
-   Home
-   Report issue
-   Image upload
-   GPS location
-   AI issue analysis
-   Complaint submission
-   Complaint tracking

### Officer

-   Login
-   Dashboard
-   Interactive map
-   Complaint list
-   Complaint details
-   Assignment
-   Status updates
-   Resolution upload

### Admin

-   Dashboard
-   Complaint management
-   Officer management
-   Basic analytics

### Infrastructure

-   FastAPI
-   React
-   PostgreSQL/PostGIS
-   SQLAlchemy
-   Docker
-   OpenStreetMap
-   Leaflet

------------------------------------------------------------------------

# 46. Phase 2 Features

After MVP:

-   Duplicate detection
-   AI severity prediction
-   AI resolution verification
-   Heatmaps
-   SLA automation
-   Escalation
-   Notifications
-   Citizen verification
-   Officer workload optimization
-   Advanced analytics

------------------------------------------------------------------------

# 47. Phase 3 / Advanced Features

Potential future features:

-   Predictive complaint hotspots
-   Automatic department routing
-   Computer vision models trained on local civic issues
-   Voice-based complaint submission
-   Multilingual interface
-   WhatsApp/SMS integration
-   Offline complaint capture
-   Route optimization for officers
-   Government ward boundary integration
-   Public transparency dashboard

------------------------------------------------------------------------

# 48. Important Product Principle

The system should NOT become a complicated enterprise dashboard.

The primary flows must remain extremely simple.

Citizen:

``` text
Open
 ↓
Report
 ↓
Photo
 ↓
Location
 ↓
AI
 ↓
Submit
```

Officer:

``` text
Open
 ↓
Map
 ↓
Select issue
 ↓
Work
 ↓
Resolve
```

Admin:

``` text
Open
 ↓
Monitor
 ↓
Analyze
 ↓
Manage
```

------------------------------------------------------------------------

# 49. Definition of Done

The project is considered MVP-complete when:

-   [ ] Citizen can register/login.
-   [ ] Officer can login.
-   [ ] Role-based routing works.
-   [ ] Citizen can capture/upload an image.
-   [ ] Location can be retrieved.
-   [ ] Complaint can be created.
-   [ ] AI analysis returns structured data.
-   [ ] Citizen can edit AI results.
-   [ ] Complaint is stored in PostgreSQL.
-   [ ] Complaint appears on Leaflet map.
-   [ ] Officer can view nearby complaints.
-   [ ] Officer can open complaint details.
-   [ ] Officer can accept/assign complaint.
-   [ ] Officer can change status.
-   [ ] Officer can upload resolution proof.
-   [ ] Citizen can see complaint timeline.
-   [ ] Citizen can confirm/reject resolution.
-   [ ] Admin can view dashboard.
-   [ ] Role-based authorization is enforced.
-   [ ] Database runs through Docker.
-   [ ] API documentation is available through FastAPI.
-   [ ] Mobile UI works at 360px width.
-   [ ] Desktop UI is responsive.
-   [ ] Loading/error/empty states exist.
-   [ ] Audit history is recorded.

------------------------------------------------------------------------

# 50. Final UX Goal

The finished application should feel like a real production civic
platform, not a college CRUD application.

The visual hierarchy should prioritize:

``` text
                    CITIZEN
                       |
                 📸 Report Issue
                       |
                 📍 Location
                       |
                    🤖 AI
                       |
                 📋 Complaint
                       |
        ┌──────────────┴──────────────┐
        |                             |
     Officer                         Admin
        |                             |
      🗺️ Map                       📊 Analytics
        |                             |
      🔧 Work                      ⚙️ Manage
        |                             |
      📸 Proof                         |
        |                             |
      ✅ Resolve <─────────────────────┘
```

The most important differentiators are:

1.  **AI-powered issue detection**
2.  **Automatic live location**
3.  **Map-first officer workflow**
4.  **Automatic department/ward routing**
5.  **Duplicate complaint detection**
6.  **SLA and escalation**
7.  **Before/after resolution proof**
8.  **Citizen verification**
9.  **Complaint heatmaps**
10. **Clean mobile-first UX**

The application should remain fast, minimal, accessible, and easy to
understand even when the underlying system is complex.
