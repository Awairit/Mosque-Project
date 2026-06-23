# Technical Debt Register

This register details known technical debt in the platform, categorized by severity, to guide maintenance cycles and technical resource allocation.

---

## 1. High Severity Technical Debt

### A. Non-Relational `Mosque.city` CharField Mapping
* **Description**: `Mosque.city` is defined as a plain `CharField` rather than a `ForeignKey` to the `City` model.
* **Risk**: High risk of data inconsistency. A simple spelling mistake (e.g. "Pune" vs "pune ") on the mosque will fail to resolve the timezone from the `City` model, falling back to a default timezone and breaking the availability calculations.
* **Impact**: Blocks database-level joins, cascade deletes, and referential integrity constraints. It necessitates custom in-memory caching to bypass N+1 queries.
* **Recommended Timing**: Phase 7 (Foundation Refactor).
* **Recommended Solution**: Transition `Mosque.city` to a `ForeignKey` to `City`. Write a custom migration mapping string values to corresponding `City` records (creating missing ones where appropriate).

### B. Lack of Phone Number Verification / OTP Auth
* **Description**: Admin accounts log in and reset credentials using standard passwords without verification of the mobile number.
* **Risk**: High risk of account takeover, registration request spoofing, and credential stuffing.
* **Impact**: Critical security vulnerability for administration portals.
* **Recommended Timing**: Immediately following Phase 7.
* **Recommended Solution**: Implement an OTP validation workflow. Integrate with SMS service gateways to verify registration requests and require 2FA on administrative logins.

---

## 2. Resolved Technical Debt

### A. Centralized Logging & Error Tracking
* **Description**: The system previously relied purely on Django defaults and stdout/console print statements.
* **Resolution**: Successfully designed and documented central logging integration. Added Sentry configuration blocks and error monitoring pipelines routing critical trace alerts directly to sysadmin endpoints. Completed during the Phase 8B.3 Launch Hardening sprint.

---

## 3. Remaining Medium Severity Technical Debt

### A. Storage Backend Verification
* **Description**: Local media uploads are used, and tests verify image uploads via in-memory mock files. Integration tests for cloud storage providers (like S3 or GCS) are missing.
* **Risk**: Live cloud storage upload configurations could fail in production due to permission mismatches, naming rules, or library inconsistencies.
* **Impact**: Deployment blocking.
* **Recommended Timing**: Prior to staging deployment.
* **Recommended Solution**: Write integration tests using local mock endpoints (e.g. LocalStack) to verify media signing and upload pathways.

---

## 3. Low Severity Technical Debt

### A. Synchronous Maps Link Redirect Resolution
* **Description**: The coordinate resolver parses Google Maps links synchronously inside the main request-response cycle on registration approval.
* **Risk**: Network timeouts during link redirects can hang the admin save thread for up to 5 seconds.
* **Impact**: Minor admin interface latency during approval saves.
* **Recommended Timing**: Post-launch.
* **Recommended Solution**: Defer the link resolution task to an asynchronous queue (e.g. Celery or django-q), updating coordinate fields in the background.
