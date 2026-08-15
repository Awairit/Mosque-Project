# Project Context

This summary was created from the Django backend repository while excluding `venv/`, `.env`, `**/__pycache__/`, `.idea/`, `media/`, and `tmp_imports/`. No source code was modified.

## Project Purpose and Major Apps

The project is a Django 5 + Django REST Framework backend for a mosque discovery, mosque administration, prayer timing, city timetable, community content, and platform administration system. The public side exposes active mosques, city prayer timings, mosque availability, announcements, events, janazah notices, and analytics tracking. The admin side supports mosque registration approval, temporary credentials, city admin management, mosque lifecycle controls, timetable imports, and account recovery.

Major apps:

- `apps.common`: shared timestamp model, phone normalization, Haversine distance utility, OTP provider abstraction, notification/email services, Cloudinary storage wrapper, and placeholder shared modules.
- `apps.accounts`: `MosqueAdmin`, `CityAdmin`, OTP/email verification records, password audit logs, identity audit logs, login, password change, forgot password, city admin profile/mobile change, and account recovery APIs.
- `apps.locations`: city registry, baseline city prayer timings, daily imported city timetables, calendar import logs, public city/timing APIs, admin CSV import flow, and timetable parsing service.
- `apps.mosques`: mosque registration requests, approved mosques, operating schedules, photos, announcements, events, community schedules, notification jobs, public mosque discovery/detail APIs, dashboard APIs, city admin content APIs, coordinate parsing, availability engine, and approval service.
- `apps.prayers`: mosque-level jamaat timings, Maghrib city-offset/manual resolution, dashboard timing APIs, and timing serializers.
- `apps.platform_admin`: super admin auth, registration review/approval/rejection, city/city-admin management, mosque lifecycle controls, timetable import preview/import, account recovery review, and mosque approval audit logs.
- `apps.community_services`: janazah notices, privacy-aware public/dashboard APIs, validation, optimistic locking, and auto-archive command.
- `apps.analytics`: privacy-conscious anonymous visitor/session tracking plus super admin and city admin analytics summaries.
- `apps.events`, `apps.operations`, `apps.moderation`: installed modular apps, but currently mostly placeholder models/views/services/selectors/serializers/permissions with empty URL patterns.

Evidence: `README.md`, `config/settings/base.py`, `config/api/v1/urls.py`, `apps/*/models.py`, `apps/*/views.py`, `apps/*/services.py`.

## Settings, Dependencies, API Routing, Authentication, and Permissions

Settings:

- Base settings live in `config/settings/base.py`. They configure environment loading via `django-environ`, SQLite fallback via `DATABASE_URL`, installed local apps, CORS/CSRF lists, DRF auth/throttling, OTP provider settings, and Cloudinary values.
- Local settings in `config/settings/local.py` enable `DEBUG`, local hosts, and localhost frontend CORS/CSRF origins.
- Production settings in `config/settings/production.py` require `DJANGO_SECRET_KEY`, reject localhost allowed hosts, add WhiteNoise, use `apps.common.storage.SafeCloudinaryStorage`, and enable SSL/HSTS/security headers.
- Dependencies are split into `requirements/base.txt`, `requirements/local.txt`, and `requirements/production.txt`; notable packages are Django, DRF, django-cors-headers, django-environ, psycopg, Pillow, openpyxl, xlrd, Twilio, Cloudinary, gunicorn, and WhiteNoise.

Routing:

- Root routes are in `config/urls.py`: `/admin/` and `/api/`.
- API version routing is in `config/api/urls.py`: `/api/v1/`.
- `config/api/v1/urls.py` is the main API hub. It defines health, auth, dashboard, registration OTP, city-admin, public announcements/events routes, includes each app URL module, and registers dashboard/community/city-admin viewsets with a DRF `DefaultRouter`.
- App URL modules include public mosque routes in `apps/mosques/urls.py`, public city routes in `apps/locations/urls.py`, platform admin routes in `apps/platform_admin/urls.py`, analytics routes in `apps/analytics/urls.py`, janazah routes in `apps/community_services/urls.py`, and empty route modules for accounts/prayers/events/operations/moderation.

Authentication and permissions:

- DRF default auth is token + session auth in `config/settings/base.py`.
- DRF default permission is `AllowAny` in `config/settings/base.py`; endpoint classes are expected to lock themselves down.
- Public endpoints explicitly use `AllowAny` in `apps/mosques/views.py`, `apps/locations/views.py`, `apps/accounts/views.py`, `apps/platform_admin/views.py`, `apps/community_services/views.py`, and `apps/analytics/views.py`.
- Role permissions are in `apps/accounts/permissions.py`: `IsMosqueAdmin`, `IsMosqueAdminOfObject`, `IsCityAdmin`, and `IsCityAdminOfObject`.
- Super admin permission is `IsSuperUser` in `apps/platform_admin/permissions.py`.

## Database Models and Relationships

Core shared model:

- `apps.common.models.TimeStampedModel` adds `created_at` and `updated_at` and is abstract.

Accounts:

- `apps.accounts.models.MosqueAdmin` has a one-to-one `User`, foreign key `Mosque`, unique mobile number, active flag, temporary password fields, password lifecycle timestamps, and index on `(mobile_number, is_active)`.
- `apps.accounts.models.CityAdmin` has a one-to-one `User`, foreign key `City`, unique mobile number, active flag, temporary password fields, lifecycle timestamps, and a conditional unique constraint for one active city admin per city.
- `apps.accounts.models.OTPVerification` stores mobile, hashed OTP, purpose, expiry, verification timestamp, attempts, max attempts, and active flag.
- `apps.accounts.models.EmailVerification` stores email verification tokens.
- `apps.accounts.models.PasswordAuditLog` records temporary password generation/change/reset against a user.
- `apps.accounts.models.IdentityAuditLog` records OTP, email, login, registration, recovery, city admin, and mosque lifecycle audit events.
- `apps.accounts.models.AccountRecoveryRequest` links optional mosque, applicant/contact data, target user, reviewer/reopen metadata, and status.

Locations:

- `apps.locations.models.City` stores unique city name, coordinates, timezone, timetable policy, acknowledged timetable year, and Maghrib offset/auto settings.
- `apps.locations.models.CityPrayerTiming` stores baseline or date-specific city prayer times with FK to `City`.
- `apps.locations.models.CityDailyPrayerTiming` stores imported daily city calendar times with unique `(city, date)`.
- `apps.locations.models.CityCalendarImportLog` audits city timetable imports.

Mosques and content:

- `apps.mosques.models.Mosque` stores approved mosque profile, city string plus FK `city_relation`, coordinates, facilities, status, type, image, and Google Maps URL.
- `apps.mosques.models.MosqueRegistrationRequest` stores public registration submissions, verified mobile/WhatsApp metadata, city string plus FK, coordinates, super admin verification notes, approval/rejection metadata, and status.
- `apps.mosques.models.MosqueOperatingSchedule` is one-to-one with `Mosque` and supports `24_HOURS`, `SALAH_BASED`, and `GENERAL` schedules.
- `apps.prayers.models.PrayerTiming` is one-to-one with `Mosque` and stores jamaat timings, `effective_from`, Maghrib mode, Maghrib delay, and updater.
- `apps.mosques.models.MosquePhoto`, `MosqueAnnouncement`, `MosqueEvent`, and `CommunitySchedule` attach gallery/community content to a mosque or city depending on the model.
- `apps.mosques.models.NotificationJob` records pending/sent/failed notification jobs.
- `apps.community_services.models.JanazahNotice` links to a mosque, creator/updater users, deceased/salah/burial/contact info, status timestamps, and validation.

Admin and analytics:

- `apps.platform_admin.models.MosqueApprovalLog` records approve/reject actions for registration requests and links optional mosque plus super admin user.
- `apps.analytics.models.AnonymousVisitor` stores a UUID visitor with visit counts and no PII.
- `apps.analytics.models.VisitEvent` links visitor, optional city, optional mosque, path, event type, and timestamp.

Placeholder model files:

- `apps.events/models.py`, `apps.operations/models.py`, and `apps.moderation/models.py` currently declare that models will be added later.

## Mosque Registration -> OTP -> Approval -> Mosque/MosqueAdmin Creation Flow

1. Public requester calls registration OTP request at `/api/v1/mosque-registration/otp/request/`, implemented by `apps.mosques.views.RegistrationOTPRequestAPIView`.
2. The view normalizes the mobile via `apps.common.utils.strings.normalize_phone_number`, rejects numbers already linked to an active mosque admin user, and calls `apps.common.services.otp.OTPService.generate_and_send_otp` with purpose `registration`.
3. `OTPService` delegates to `apps.common.services.otp_providers.get_otp_provider`. Development mode stores a hashed OTP in `apps.accounts.models.OTPVerification`; Twilio mode calls Twilio Verify. OTP events are audited in `apps.accounts.models.IdentityAuditLog`.
4. Public requester verifies OTP at `/api/v1/mosque-registration/otp/verify/`, implemented by `apps.mosques.views.RegistrationOTPVerifyAPIView`.
5. On success, the verify view returns a signed `verification_token` using `TimestampSigner`.
6. Public requester submits registration at `/api/v1/mosque-registration/`, implemented by `apps.mosques.views.MosqueRegistrationRequestCreateAPIView`.
7. The create view validates that the signed token is no older than 30 minutes, normalizes and compares the submitted mobile, validates with `apps.mosques.serializers.MosqueRegistrationRequestSerializer`, saves the request with WhatsApp/mobile verified flags and `status="pending"`, then writes `REGISTRATION_SUBMITTED` to `IdentityAuditLog`.
8. The serializer synchronizes `google_maps_link` and `google_maps_url`, parses coordinates via `apps.mosques.services.extract_coordinates_from_url`, rejects duplicate pending request for the same mosque/mobile, and requires a registered `apps.locations.models.City`.
9. Super admin reviews routes in `apps.platform_admin.urls.py`, especially request list/detail, mark-under-verification, verification-notes, approve, and reject.
10. Approval is handled by `apps.platform_admin.views.SuperAdminRegistrationRequestApproveAPIView`, which row-locks the registration request with `select_for_update`, checks allowed statuses, checks user/email conflicts, and calls `apps.mosques.services.approve_mosque_registration_request`.
11. `approve_mosque_registration_request` runs in a DB transaction, row-locks the request again, normalizes username variants, generates a secure temporary password if needed, creates or reuses a Django `User`, extracts coordinates, creates or reuses a matching `Mosque`, creates or reuses `MosqueAdmin`, sets `must_change_password=True` and a 7-day temp password expiry when a password was generated, writes `PasswordAuditLog`, marks request approved, writes `MosqueApprovalLog`, writes `IdentityAuditLog`, and returns the temp password to the super admin response.
12. Rejection is handled by `apps.platform_admin.views.SuperAdminRegistrationRequestRejectAPIView`, which row-locks, requires a reason, sets rejected metadata, writes `MosqueApprovalLog`, and writes `REGISTRATION_REJECTED`.

Evidence: `config/api/v1/urls.py`, `apps/mosques/views.py`, `apps/mosques/serializers.py`, `apps/mosques/services.py`, `apps/platform_admin/views.py`, `apps/platform_admin/urls.py`, `apps/accounts/models.py`, `apps/common/services/otp.py`, `apps/common/services/otp_providers.py`.

## Temporary Password -> First Login -> Password Change Flow

Temporary password generation:

- Mosque admin temporary passwords are generated during registration approval in `apps.mosques.services.approve_mosque_registration_request`.
- Mosque admin password reset is exposed at `apps.platform_admin.views.SuperAdminResetMosqueAdminPasswordAPIView`.
- City admin temporary passwords are generated in `apps.platform_admin.views.SuperAdminCityAdminListCreateAPIView`.
- City admin password reset is handled by `apps.platform_admin.views.SuperAdminCityAdminResetPasswordAPIView`.
- Both role profiles carry `must_change_password`, `temporary_password_expires_at`, `password_changed_at`, and `last_password_reset_at` in `apps.accounts.models`.

Login:

- `apps.accounts.views.LoginAPIView` accepts mobile/password, normalizes mobile, supports super admin login by username/email, finds a user/profile through username or role profile mobile number, rejects inactive profile/user/mosque, checks temp password expiry, gets or creates DRF token, records `FIRST_LOGIN` when `must_change_password` is true, and returns role information plus `must_change_password`.
- Dual-role users can receive both `city_admin` and `mosque_admin` roles in the login response.

Password change:

- General authenticated password change is handled by `apps.accounts.views.ChangePasswordAPIView`. It checks current password and minimum length, sets the Django user password, clears `must_change_password` and `temporary_password_expires_at` across both attached MosqueAdmin and CityAdmin profiles, records `PasswordAuditLog`, and writes `PASSWORD_CHANGED`.
- City admin-specific password change is handled by `apps.accounts.views.CityAdminChangePasswordAPIView`; it checks current password, confirmation, minimum length, updates password, clears city admin password flags, deletes old tokens, creates a fresh token, and returns it.
- Forgot-password flow is handled by `ForgotPasswordRequestAPIView`, `ForgotPasswordVerifyAPIView`, and `ForgotPasswordResetAPIView` in `apps.accounts.views`. It sends OTP, verifies OTP, issues a 15-minute signed reset token containing mobile and password-state timestamp, enforces single-use by comparing current state, updates password, clears flags, deletes tokens, and audits `PASSWORD_RESET`.

Evidence: `apps/accounts/models.py`, `apps/accounts/views.py`, `apps/platform_admin/views.py`, `apps/mosques/services.py`.

## Location/Coordinates -> Nearest Mosque -> Haversine Distance/Order Flow

Coordinate extraction:

- `apps.mosques.services.extract_coordinates_from_url` parses raw `lat,lon` strings and Google Maps URL patterns statically without network calls. It first validates allowed Google Maps domains and blocks direct/private/internal IP targets via `is_allowed_google_maps_url`.
- `apps.mosques.models.Mosque.save` extracts coordinates when a Google Maps URL is newly supplied or changed and coordinates are missing or stale.
- `apps.mosques.models.MosqueRegistrationRequest.save` extracts coordinates from `google_maps_url` or `google_maps_link` when coordinates are missing.
- `apps.mosques.serializers.MosqueRegistrationRequestSerializer` also extracts coordinates during validation.
- `apps.mosques.management.commands.backfill_mosque_coordinates` backfills missing coordinates for existing mosques with map URLs.

Nearest mosque discovery:

- Public mosque list is implemented by `apps.mosques.views.MosqueListAPIView`.
- It starts from `get_optimized_mosque_queryset`, which filters active mosques and select/prefetches schedule, prayer timing, city relation, today city timings, and optionally details.
- It supports city name, city ID, bounding box, facility filters, `jumuah_available`, `lat`, `lon`, and `open_now`.
- With user `lat`/`lon` and no bounding box, it prefilters to a 100 km lat/lon bounding box, falls back to all mosques if fewer than 5 candidates, computes exact distance with `apps.common.utils.geo.calculate_haversine`, sorts nearest-first, and returns the top 5 unless `in_bbox` is present.
- `open_now=true` uses `apps.mosques.services.MosqueAvailabilityEngine` to filter candidates by current availability before limiting.
- Serializers expose `distance` through `apps.mosques.serializers.MosqueListSerializer.get_distance`, reusing `distance_val` when already computed.

City nearest resolution:

- `apps.locations.views.CityPrayerTimingAPIView` can resolve the nearest city from `lat`/`lon` by calculating Haversine distance to every city, falling back to manual city ID/name or first city alphabetically.

Evidence: `apps/common/utils/geo.py`, `apps/mosques/services.py`, `apps/mosques/models.py`, `apps/mosques/serializers.py`, `apps/mosques/views.py`, `apps/locations/views.py`, `apps/mosques/management/commands/backfill_mosque_coordinates.py`.

## Prayer Timings and Mosque Availability Engine

Prayer timing model and dashboard:

- `apps.prayers.models.PrayerTiming` stores mosque jamaat times and Maghrib mode/delay.
- `apps.prayers.views.DashboardPrayerTimingAPIView` creates default timings for a mosque admin on first GET, returns resolved Maghrib time for the mosque city timezone, and updates timings on PUT. If `maghrib_time` is updated without mode, it forces manual mode.
- `apps.prayers.serializers.PrayerTimingSerializer` validates timing fields and Maghrib delay range.

Maghrib resolution:

- `apps.prayers.services.PrayerTimingService.resolve_timing` returns a `ResolvedPrayerTiming` dataclass.
- Manual mode uses stored `PrayerTiming.maghrib_time`.
- City-offset mode checks mosque city settings. If enabled, it resolves city `CityDailyPrayerTiming` for the requested date, then adds mosque-specific `maghrib_delay_minutes` if not default, otherwise city `maghrib_congregation_offset`.
- It caches resolved data on the timing instance by date and state key.

Availability engine:

- `apps.mosques.services.MosqueAvailabilityEngine` resolves timezone from `City.timezone`, defaulting to `Asia/Kolkata`.
- It handles no schedule as `Schedule Not Verified`, `24_HOURS` as open all day, `GENERAL` open/close windows including overnight windows, and `SALAH_BASED` per-prayer open/close windows including overnight windows.
- It labels `Open 24 Hours`, `Open Now`, `Closing Soon`, `Closed`, or `Schedule Not Verified`, calculates `opens_at`/`closes_at`, and determines next prayer from resolved jamaat timing with rollover to tomorrow's Fajr.
- `apps.mosques.models.MosqueOperatingSchedule.get_current_status` contains a separate, older availability helper that overlaps with the engine.

City timing API and imports:

- `apps.locations.views.CityPrayerTimingAPIView` prioritizes `CityDailyPrayerTiming` for today's city-local date, then maps today to the latest imported prior-year calendar if necessary, then falls back to `CityPrayerTiming` date-specific or baseline rows.
- `apps.locations.services.parse_and_validate_calendar_csv` validates CSV date/time order for admin import.
- `apps.platform_admin.services.TimetableParser` parses CSV/XLS/XLSX with flexible headers, date formats, Excel serials, leap-year behavior, city warnings, and time normalization.
- `apps.platform_admin.views.SuperAdminCityTimetableAPIView` previews/imports city timetables, detects duplicates, supports replace/merge import modes, bulk creates/updates `CityDailyPrayerTiming`, and writes `CityCalendarImportLog`.

Evidence: `apps/prayers/models.py`, `apps/prayers/services.py`, `apps/prayers/views.py`, `apps/prayers/serializers.py`, `apps/mosques/services.py`, `apps/mosques/models.py`, `apps/locations/views.py`, `apps/locations/services.py`, `apps/platform_admin/services.py`, `apps/platform_admin/views.py`.

## Services, Utilities, Management Commands, and Tests

Services and utilities:

- OTP: `apps/common/services/otp.py`, `apps/common/services/otp_providers.py`.
- Notifications: `apps/common/services/notification.py`.
- Email verification: `apps/common/services/email.py`.
- Geolocation: `apps/common/utils/geo.py`.
- Phone normalization: `apps/common/utils/strings.py`.
- Coordinate parsing, availability, and approval: `apps/mosques/services.py`.
- Prayer timing resolution: `apps/prayers/services.py`.
- Location CSV parsing: `apps/locations/services.py`.
- Platform timetable parsing: `apps/platform_admin/services.py`.
- Cloudinary storage guard: `apps/common/storage.py`.

Management commands:

- `apps/mosques/management/commands/backfill_mosque_coordinates.py`: idempotently fills missing mosque coordinates from Google Maps URLs.
- `apps/community_services/management/commands/archive_janazahs.py`: archives published/completed janazah notices after burial/salah age thresholds in mosque timezone.
- `apps/platform_admin/management/commands/bootstrap_superuser.py`: creates an initial superuser from environment variables if none exists.

Tests:

- Account tests cover auth, account recovery, security hardening, and multi-role behavior under `apps/accounts/tests/`.
- Common tests cover phone normalization and OTP providers/API flow under `apps/common/tests/`.
- Location tests cover city APIs and calendar import under `apps/locations/tests/`.
- Mosque tests cover availability/discovery, city admin flows, attribution, city events lifecycle, community hub, schedules, content isolation, coordinate integrity, facilities, nearest discovery, location parsing, map filters, OTP registration, profile/schedule, sprint race/IDOR regressions, and V2 features under `apps/mosques/tests/`.
- Prayer tests cover timing APIs, resolver modes, Maghrib delay range, and authoritative city validation under `apps/prayers/tests/`.
- Platform admin tests cover auth, request approvals/rejections, city admins, and timetables under `apps/platform_admin/tests/`.
- Community services tests cover janazah validation, privacy, locking, isolation, public filtering, timezone behavior, archiving, and profile integration under `apps/community_services/tests/`.
- Analytics tests cover tracking and analytics views under `apps/analytics/tests/`.

Evidence: `apps/*/tests/*.py`, `apps/*/management/commands/*.py`.

## Current Known Bugs or Risky Areas

High severity:

- `apps/platform_admin/views.py` likely has a broken local import in `SuperAdminResetMosqueAdminPasswordAPIView`: it imports `MosqueRegistrationRequest` from `apps.platform_admin.models`, but that model lives in `apps.mosques.models`. This endpoint should raise an `ImportError` when called.
- `apps/common/services/email.py` calls `notification_service.send_email(to=email, subject=subject, body=body)`, but `NotificationService.send_email` expects `recipient`, not `to`. Email verification sending should raise `TypeError` and return failure unless this code path is currently unused.
- Password validation in `apps/accounts/views.py` mainly checks length >= 8 for change/reset flows instead of using Django's configured `AUTH_PASSWORD_VALIDATORS` from `config/settings/base.py`.

Medium severity:

- DRF global default permission is `AllowAny` in `config/settings/base.py`. Many endpoints do set explicit permissions, but any new endpoint without `permission_classes` will default public.
- `apps/platform_admin/views.py` contains duplicated imports, direct `print`, `traceback.print_exc`, and a commented debug block around timetable parsing. This can leak internals and makes production error handling inconsistent.
- `apps/platform_admin/views.py` dashboard stats uses `timetable_imports_count = 14` as a mock value instead of real `CityCalendarImportLog` data.
- `apps.accounts.views.LoginAPIView` logs `FIRST_LOGIN` every time a user with `must_change_password=True` logs in, not strictly only the first login.
- `apps.mosques.services.approve_mosque_registration_request` returns temporary passwords in API responses. That is operationally intentional here, but sensitive and should be paired with strict HTTPS, audit, and display-once behavior.
- The approval flow checks user conflicts by username variants in the service, but the view-level duplicate check uses only exact `username=request_obj.mobile_number` before service execution.

Low severity:

- `apps.mosques.models.MosqueOperatingSchedule.get_current_status` overlaps with `apps.mosques.services.MosqueAvailabilityEngine`, increasing the risk of future behavior drift.
- `apps.common.services.otp.py` says views should not import `otp_providers` directly, but several views import `OTPErrorCode` from `apps.common.services.otp_providers`.
- `apps.mosques.services.py` imports `urllib.request` but coordinate extraction is documented and tested as zero-network; the import appears unused and confusing.
- `apps.locations.admin.CityAdmin.import_calendar_view` writes temporary uploads into an app-local `tmp_imports` path. This repository summary intentionally did not inspect `tmp_imports/`; runtime cleanup and permissions should be reviewed before production use.

Evidence: `apps/platform_admin/views.py`, `apps/common/services/email.py`, `apps/accounts/views.py`, `config/settings/base.py`, `apps/mosques/services.py`, `apps/mosques/models.py`, `apps/locations/admin.py`, `apps/common/services/otp.py`.

## Duplicate, Dead, or Unclear Code Observations Only

These are observations only; nothing has been removed.

- Placeholder modules exist across `apps.events`, `apps.operations`, `apps.moderation`, and shared app files such as `apps/common/validators.py`, `apps/common/responses.py`, `apps/common/pagination.py`, `apps/prayers/imports.py`, `apps/*/selectors.py`, and several `permissions.py` files.
- `apps.accounts.services.py` is a placeholder even though significant account workflow logic lives in `apps/accounts/views.py`.
- `apps.platform_admin.services.py` starts with a placeholder docstring but contains the substantial `TimetableParser`.
- `apps.mosques.services.py` has duplicated `import re` and an unused `urllib.request` import.
- `apps.platform_admin.views.py` duplicates imports such as `Response` and mixes API logic, timetable import logic, city admin creation/reset, mosque lifecycle, and account recovery in one very large file.
- `apps.mosques.models.MosqueRegistrationRequest` has both `google_maps_link` and `google_maps_url`; serializers synchronize them for compatibility, but dual fields create maintenance overhead.
- `apps.mosques.models.Mosque` and `MosqueRegistrationRequest` both store city as a string and as `city_relation`; save methods dual-write them for compatibility.
- `apps.locations.services.parse_and_validate_calendar_csv`, `apps.locations.admin.CityAdmin.import_calendar_view`, and `apps.platform_admin.services.TimetableParser` overlap in timetable parsing/import responsibilities.
- `apps.common.services.email.EmailVerificationService` appears not wired into API routes found in this scan.
- `apps.analytics`, `apps.community_services`, and mosque community content are functional, while `apps.events` remains placeholder despite event functionality living in `apps.mosques.models.MosqueEvent`.

Evidence: `apps/accounts/services.py`, `apps/platform_admin/services.py`, `apps/platform_admin/views.py`, `apps/mosques/models.py`, `apps/mosques/serializers.py`, `apps/locations/services.py`, `apps/locations/admin.py`, `apps/events/*`, `apps/operations/*`, `apps/moderation/*`.

## Exact Recommended Changes, Prioritized by Severity

P0 - likely broken runtime behavior:

1. Fix the `SuperAdminResetMosqueAdminPasswordAPIView` import to use `apps.mosques.models.MosqueRegistrationRequest`, then add/confirm a test for `/api/v1/platform/requests/<id>/reset-password/`.
2. Fix `EmailVerificationService.generate_and_send_link` to call `notification_service.send_email(recipient=email, subject=subject, body=body)` or update `NotificationService` to accept `to`, then add a test if email verification is intended to ship.
3. Replace manual password length checks in account reset/change endpoints with Django `validate_password`, while preserving existing API error shapes.

P1 - security and correctness hardening:

4. Change DRF default permission from `AllowAny` to `IsAuthenticated` in `config/settings/base.py`, then explicitly mark public endpoints `AllowAny`. If this is too disruptive, add a test or lint rule requiring `permission_classes` on every API view.
5. Remove direct `print`/`traceback.print_exc` production debug behavior from `apps/platform_admin/views.py` and return sanitized parser errors consistently.
6. Replace mock `timetable_imports_count = 14` with a real `CityCalendarImportLog` count.
7. Make first-login audit idempotent, for example by logging once per user/profile or renaming the audit event to temporary-password-login.
8. Ensure temporary passwords are display-once and never logged; consider expiring or rotating generated credentials after the response is delivered.

P2 - maintainability:

9. Move account workflow logic from large view methods into `apps/accounts/services.py`.
10. Split `apps/platform_admin/views.py` into focused modules for auth, registration requests, cities/timetables, city admins, mosques, and account recovery.
11. Consolidate availability logic around `MosqueAvailabilityEngine` and reduce or delegate `MosqueOperatingSchedule.get_current_status`.
12. Decide whether `google_maps_link` or `google_maps_url` is canonical, keep backward-compatible serializer aliases, and plan a migration only after client compatibility is known.
13. Decide whether `city` string or `city_relation` is canonical; prefer `city_relation` while keeping a read-only denormalized city string only if needed.
14. Consolidate timetable parsing/import paths so admin UI and platform API use the same service.

P3 - cleanup and clarity:

15. Remove or implement placeholder modules in `events`, `operations`, and `moderation` when product scope is clear.
16. Remove unused imports and duplicate imports in `apps/mosques/services.py` and `apps/platform_admin/views.py`.
17. Update `README.md` to reflect the current implemented apps and flows; it still describes many app services/selectors/serializers/views as future placeholders.
18. Add route/API documentation for the OTP registration, temporary password, nearest mosque, availability, timetable import, and janazah flows.

