# DEVELOPMENT ROADMAP

This document tracks completed development cycles, architectural decisions, and schedules future roadmap phases.

---

## Completed Phases

### Phase 1: Mosque Registration & Verification
* **Objectives**: Implement a secure admin-vetted onboarding pipeline to register new mosques and display verified entries.
* **Features Delivered**:
  * `Mosque` and `MosqueRegistrationRequest` models.
  * Workflow action approvals and coordinate automation in Django Admin.
  * Public mosque listing API (`GET /api/v1/mosques/`).
  * Frontend registration form and listing page components.
* **Lessons Learned**: Admins frequently review requests with incomplete information. Requiring coordinates initially blocks submissions; extracting coordinates from Maps URLs is more user-friendly.
* **Architectural Impact**: Introduced separation between draft requests and approved public mosque entities.
* **Testing Status**: Covered by unit tests for moderation states.
* **Production Readiness Impact**: Basic public schema isolation established.

### Phase 2: Mosque Admin Accounts & Authentication
* **Objectives**: Bind approved mosques to secure admin user profiles with auto-generated credentials.
* **Features Delivered**:
  * `MosqueAdmin` model linking active admin accounts to mosques.
  * Auto-generation of random passwords upon approval.
  * Token-based authentication endpoint (`POST /api/v1/auth/login/`).
  * Frontend admin login interface (`/login`).
* **Lessons Learned**: Hardcoding tokens in memory resets logins on refresh. Storing tokens in `localStorage` resolves session loss, but requires deferring initial checks to avoid SSR mismatches.
* **Architectural Impact**: Shifted user authorization to token headers.
* **Testing Status**: Integration tests for login payloads and token generation.
* **Production Readiness Impact**: Enforces administrative boundary checking.

### Phase 3: Prayer Timings & Operating Schedule Management
* **Objectives**: Enable mosque administrators to manage timings and operating windows.
* **Features Delivered**:
  * `PrayerTiming` model for jamaat configuration.
  * `MosqueOperatingSchedule` model supporting 24h slots or prayer timings windows.
  * Profile settings panel (Facilities, Women Spaces, Parking, Wudu, Wheelchair access).
  * Timings management APIs with cross-mosque isolation.
* **Lessons Learned**: Schedules must handle overlapping overnight timings (e.g. Fajr and Isha slots wrapping midnight).
* **Architectural Impact**: Split timings data from core mosque profiles for modularity.
* **Testing Status**: Validated schedule overlap boundary calculations.
* **Production Readiness Impact**: Dashboard security verified via object permission tests.

### Phase 4: Geo Discovery Engine
* **Objectives**: Search and display the closest active mosques using client-side GPS coordinates.
* **Features Delivered**:
  * Bounding-box coordinate query optimizations and Haversine distance computations.
  * Top 5 nearest approved mosques API with dynamic distances.
  * `City` and default `CityPrayerTiming` templates.
  * Dedicated dynamic detail pages (`/mosque/[id]`).
* **Lessons Learned**: Querying the distance of all database entries lacks scalability. Bounding-box pre-filtering (within a 100km radius) preserves performance.
* **Architectural Impact**: Added locations domain models separate from mosques.
* **Testing Status**: Haversine distance tests validated against actual locations.
* **Production Readiness Impact**: Established scalable proximity lookup structures.

### Phase 5A: Community Hub Foundation
* **Objectives**: Support content additions (photos, announcements, events) per mosque.
* **Features Delivered**:
  * `MosquePhoto` model with display ordering controls.
  * `MosqueAnnouncement` model featuring urgency weights and publication states.
  * `MosqueEvent` model sorted by nearest upcoming date.
  * Multi-tenant validation checks for media uploads.
  * Public community hubs (dynamic gallery, lightbox viewer, notice board feed, events timetable).
* **Lessons Learned**: Image processing must use memory-based stream mocks during tests to avoid generating garbage media files in local disk paths.
* **Architectural Impact**: Introduced media storage and notice board models.
* **Testing Status**: Covered by mock-image and visibility tests.
* **Production Readiness Impact**: Completed standard profile media integration.

### Phase 5B: City Prayer Calendar Import System
* **Objectives**: Enable bulk scheduling imports for citywide timelines while preserving mosque independence.
* **Features Delivered**:
  * `CityDailyPrayerTiming` and `CityCalendarImportLog` models.
  * Django Admin CSV import pipeline and interactive template guide generator.
  * Strict validation checking that prayer times follow standard sequences: `Fajr < Sunrise < Dhuhr < Asr < Maghrib < Isha`.
  * Multi-step transaction safety checks (dry-run previews and rollback commits).
  * Timezone-aware API prioritization (falling back to baseline templates only when daily imports are missing).
* **Lessons Learned**: Parsing times from third-party systems requires support for diverse string formats (e.g., 24h, 12h, seconds, AM/PM indicators).
* **Architectural Impact**: Established transaction-safe bulk importer workflows.
* **Testing Status**: Parsers tested against malformed dates and invalid sequences.
* **Production Readiness Impact**: Enabled administrative bulk updates.

### Phase 6A: Maps & Navigation Experience
* **Objectives**: Establish location-first mosque discovery with maps and one-click navigation links.
* **Features Delivered**:
  * Extended viewport queries (`in_bbox` parameters) and shared filters.
  * Leaflet map component with pulsing user location dots and mosque pins.
  * One-click directions deep-link launcher (launching Google Maps or Apple Maps).
* **Lessons Learned**: Client-side map components cannot initialize during SSR. Deferring Leaflet mounting until client-side load is necessary.
* **Architectural Impact**: Connected frontend search inputs with viewport constraints.
* **Testing Status**: Bounding box queries validated via view tests.
* **Production Readiness Impact**: Enhanced discovery UI flow.

### Phase 6A.1: Production Hardening Sprint
* **Objectives**: Address technical debt, optimize query counts, fix hydration mismatches, and add database indexes.
* **Features Delivered**:
  * Deferred Next.js Next Prayer highlights and localStorage auth reading to client-only mounts.
  * Added `select_related()` and `prefetch_related()` joins on Mosque API listings, dropping query counts from 11+ to 4.
  * Implemented a static timezone cache in the Availability Engine.
  * Created composite coordinates index `(latitude, longitude)` on `Mosque`, plus active filters indexes on announcements and events.
* **Lessons Learned**: Standard ORM joins cannot eliminate city timezone lookups because `Mosque.city` is defined as a text CharField. In-memory dictionary caching resolves this.
* **Architectural Impact**: Stabilized query counts and improved database execution plans.
* **Testing Status**: Fully covered by 54 passing tests.
* **Production Readiness Impact**: Eliminated hydration mismatches and database scaling concerns.

### Phase 6B: Community Services Sprint 1 (Weekly Dars & Friday Khutbah)
* **Objectives**: Implement recurring operations timetables (Weekly Dars and Friday sermon shifts) using the `CommunitySchedule` model framework.
* **Features Delivered**:
  * Additive, non-destructive migration applying `CommunitySchedule` schema.
  * Tenant-isolated `/api/v1/dashboard/schedules/` CRUD endpoints.
  * Dynamic timeline view for Jumuah sermons and weekly lectures on the public profile.
  * Conditional entry forms and list management interfaces on the admin dashboard.
  * Duplicate shift detection validation to prevent scheduling conflicts.
* **Lessons Learned**: Shift configurations require checking JSON schema bounds on the backend to avoid database validation failures.
* **Architectural Impact**: Validated schedule model structure and permissions before introducing enrollment/payment services.
* **Testing Status**: Added 4 new automated tests verifying uniqueness, multi-tenant isolation, and serializations (bringing backend test suite total to 58 tests).
* **Production Readiness Impact**: Expanded community schedule features with high test coverage and zero query count regressions.

### Phase 7: City Relation Normalization
* **Objectives**: Normalize database schemas by establishing a direct foreign key relationship from mosques to cities.
* **Features Delivered**:
  - `city_relation` ForeignKey field on the `Mosque` model referencing `locations.City`.
  - In-memory static lookup cache resolver to speed up city-to-timezone maps without introducing N+1 queries.
* **Lessons Learned**: Transitioning CharFields to relational keys requires maintaining dual fields (`city` and `city_relation`) temporarily to preserve backward compatibility with external scripts.
* **Testing Status**: Validated through location and Availability Engine tests.

### Phase 8B.3: Launch Hardening, Privacy & Security
* **Objectives**: Audit and seal application privacy, rate limit requests, fix container deployments, and implement accessibility/copyright compliance.
* **Features Delivered**:
  - Janazah Notice contact details privacy isolation (enforcing client-side conditional checks).
  - DRF API throttling (10/min sensitive auth endpoints, 100/min public geo-discovery).
  - Next.js Standalone build fix (repaired missing `public` folder Docker crash).
  - Responsive global copyright footer and static info pages (/privacy, /terms, /about, /contact).
  - WCAG 2.2 AA enhancements (visual contrast updates and accessible button carousel focus outlines).
  - OpenStreetMap copyright attribution.
* **Lessons Learned**: Modern container environments crash instantly if build templates depend on folder structures not versioned in git. Ensuring directory stubs like `.gitkeep` are committed is vital.
* **Testing Status**: Verified by 66 passing backend tests, next build validation, and tsc check runs.

---

## Future Roadmap

### Phase 8: Phone Verification & Access Control (Planned)
* **Goal**: Implement OTP verification for admin accounts.
* **Tasks**:
  * Integrate third-party SMS providers.
  * Build verification API endpoints.
  * Force SMS validation on login and recovery attempts.
