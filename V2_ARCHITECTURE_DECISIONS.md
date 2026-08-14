# MosqueCom V2 — Architecture Decisions & Architectural Governance

> **V2 ARCHITECTURAL RECORD** — Authoritative log of architectural decisions, schema migration principles, security patterns, and release completion state.

---

## Key Architecture Decisions (ADRs)

### ADR-001: Autonomous Controlled Engineering Loop
All feature modifications and bug remediations MUST proceed through the 15-Step Controlled Engineering Loop until reaching an explicit terminal state (`VERIFIED`, `FAILED`, `BLOCKED`, or `WAITING_FOR_USER`).

### ADR-002: Dynamic Maghrib Jamaat Delay Calculation (RC-BUG-005)
- **Base**: Dynamic sunset time calculated from `CityDailyPrayerTiming.maghrib_time`.
- **Configuration**: Mosque Admin sets `maghrib_delay_minutes` as an integer between 1 and 30 minutes in `PrayerTiming`.
- **Calculation**: `resolved_maghrib_time = add_minutes_to_time(daily_timing.maghrib_time, maghrib_delay_minutes)`.
- **Scope**: Maghrib ONLY. Universal hardcoded offsets or delay settings for other Salahs are prohibited.

### ADR-003: Authoritative City Selection & Backend Validation (RC-BUG-007)
- **Invariant**: Public mosque registration and admin profile updates CANNOT accept arbitrary un-indexed free-text city strings.
- **Enforcement**: Serializer validation against `locations_city`. Submitted city text or ID MUST resolve to a valid registered `City` instance, setting `city_relation` automatically.

### ADR-004: Centralized API Path Resolution & Auth Interceptors (RC-BUG-001 & RC-BUG-002)
- **Path Resolution**: `apiRequest` in `frontend/lib/api/client.ts` automatically normalizes input paths by stripping any leading `api/v1/` prefix, preventing `/api/v1/api/v1/` duplication.
- **Authentication**: Token storage occurs prior to conditional checks during temporary password login. `/change-password` route is excluded from automatic 401 redirection loops.

### ADR-005: Modular Dashboard Decomposition & Navigation IA (RC-BUG-003 & RC-BUG-004)
- **Tab Sequence**:
  1. Prayer Timings (`timetables`)
  2. Announcements (`announcements`)
  3. Events & Programs (`events`)
  4. Janazah Notices (`janazah`)
  5. Operating Hours (`schedule`)
  6. Photo Gallery (`gallery`)
  7. Mosque Profile (`profile`)
  8. Account Settings (`settings`)
- **Functional Parity**: Dedicated `ScheduleTab.tsx` and `GalleryTab.tsx` components encapsulate operating hours and photo gallery management.

---

## Production Release Verification Matrix

| Area | Status | Evidence |
| :--- | :---: | :--- |
| **Backend Test Suite** | `VERIFIED` | 235 / 235 passed (`python manage.py test`) |
| **Frontend Typecheck** | `VERIFIED` | 0 errors (`npx tsc --noEmit`) |
| **Frontend Production Build** | `VERIFIED` | 29 / 29 Next.js pages compiled (`npm run build`) |
| **Dynamic End-to-End Proofs** | `VERIFIED` | 18 / 18 critical workflows verified (`execute_dynamic_proofs.py`) |
| **Master Bug Registry** | `VERIFIED` | 14 / 14 fixed & documented (`BUG_REGISTRY.md`) |
| **RC Findings Registry** | `VERIFIED` | 8 / 8 fixed & documented (`FINAL_RELEASE_CANDIDATE_FINDINGS.md`) |

---

## System Operational State
MosqueCom V2 is **VERIFIED PRODUCTION READY**.
