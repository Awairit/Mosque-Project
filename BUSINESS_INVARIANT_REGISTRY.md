# Mosque Finder — Business Invariant & Domain Rules Registry

> **STRICT AUDIT-ONLY ARTIFACT** — Extraction of all critical business rules across the system, analyzing whether they are enforced by Database Constraints, Application Logic, or Both, along with Concurrency Safety and Failure Scenarios.

---

## Master Business Invariant Registry

| # | Business Invariant | Where Implemented | Database Enforcement? | Application Enforcement? | Test Exists? | Concurrency-Safe? | Failure Scenario | Audit Status |
|---|---|---|---|---|---|---|---|---|
| **INV-01** | **One Person = One Account** | `apps/accounts/models.py`, `views.py` | **Yes** (`User.username` unique) | **Yes** (Shared user pointer) | Partial | **Yes** (Unique username) | Duplicate User creation raises DB IntegrityError. | **PASS** |
| **INV-02** | **One Active City Admin Per City** | `apps/platform_admin/views.py` | ❌ **NO (Missing Partial Unique Constraint)** | **Yes** (`exists()` check) | ❌ **NO** | ❌ **NO (Race condition BUG-006)** | Concurrent creations create 2 active City Admins for 1 city. | ❌ **FAIL (BUG-006)** |
| **INV-03** | **One Mosque Admin Per Mosque** | `apps/accounts/models.py` | **Yes** (`MosqueAdmin.mosque` FK, `user_id` 1-to-1) | **Yes** | **Yes** | **Yes** | Attempting to link multiple users to 1 MosqueAdmin raises IntegrityError. | **PASS** |
| **INV-04** | **One Mosque Admin Profile Per User** | `apps/accounts/models.py` | **Yes** (`MosqueAdmin.user` OneToOneField) | **Yes** | **Yes** | **Yes** | User cannot possess two MosqueAdmin profiles. | **PASS** |
| **INV-05** | **One City Admin Profile Per User** | `apps/accounts/models.py` | **Yes** (`CityAdmin.user` OneToOneField) | **Yes** | **Yes** | **Yes** | User cannot possess two CityAdmin profiles. | **PASS** |
| **INV-06** | **Only Approved Mosques in Public Discovery**| `apps/mosques/views.py` | ❌ **NO (Query-level)** | **Yes** (`filter(mosque_status='active')`) | **Yes** | **Yes** | Unapproved/archived mosques excluded from search queryset. | **PASS** |
| **INV-07** | **Role ≠ Content Scope Isolation** | `apps/mosques/views.py` | ❌ **NO (Query-level)** | ⚠️ **PARTIAL (List only)**| Partial | **Yes** | City Admin can mutate Mosque Admin announcements (`BUG-003`). | ❌ **FAIL (BUG-003)** |
| **INV-08** | **Registration Approval Creates Single Mosque**| `apps/platform_admin/views.py` | ❌ **NO (Missing lock)**| ⚠️ **PARTIAL (No lock)** | ❌ **NO** | ❌ **NO (Race condition BUG-002)** | Concurrent approvals create 2 duplicate mosques from 1 request. | ❌ **FAIL (BUG-002)** |
| **INV-09** | **Account Recovery Requires Previous Contact** | `apps/accounts/views.py` | ❌ **NO (View-level)** | **Yes** (Server-side normalization) | **Yes** | **Yes** | Mismatched previous contact returns 400 immediately. | **PASS** |
| **INV-10** | **Account Recovery Atomicity & Locking** | `apps/platform_admin/views.py` | **Yes** (`transaction.atomic()`) | **Yes** (`select_for_update()`) | **Yes** | **Yes** | Concurrent approval/reject returns 409 Conflict. | **PASS** |
| **INV-11** | **Unique Timetable per City per Calendar Date**| `apps/locations/models.py` | **Yes** (`unique_together = ('city', 'date')`)| **Yes** | **Yes** | **Yes** | Duplicate daily date insert raises DB IntegrityError. | **PASS** |
| **INV-12** | **Janazah Salah Date After Date of Death** | `apps/community_services/serializers.py`| ❌ **NO (Serializer-level)** | **Yes** (`validate()` hook) | **Yes** | **Yes** | Invalid chronological date raises ValidationError 400. | **PASS** |
| **INV-13** | **Janazah Burial Date After Salah Date** | `apps/community_services/serializers.py`| ❌ **NO (Serializer-level)** | **Yes** (`validate()` hook) | **Yes** | **Yes** | Burial before Salah raises ValidationError 400. | **PASS** |
| **INV-14** | **Janazah Optimistic Version Lock** | `apps/community_services/serializers.py`| ❌ **NO (View/Serializer)** | **Yes** (`version = version + 1`) | **Yes** | **Yes** | Stale client edit returns 409 Conflict. | **PASS** |
| **INV-15** | **Dual-Role Single Credential Synchronization**| `apps/accounts/views.py` | ❌ **NO (App-level)** | ⚠️ **PARTIAL (Buggy loop)**| Partial | **Yes** | Password change updates MosqueAdmin but leaves CityAdmin stale. | ❌ **FAIL (BUG-004)** |
