# MosqueCom V2 — Engineering Governance, Constitution & Controlled Loop

> **AUTHORITATIVE WORKSPACE GOVERNANCE CONTRACT** — Mandatory Engineering Laws, Agent Guardrails, Controlled Engineering Loop, and Validation Gates for MosqueCom V2 Development.

---

## 1. Product Engineering Objective

MosqueCom v2 is a focused, high-utility platform designed specifically to:
- Help worshippers discover mosques and access accurate prayer timetables.
- Help tourists and travelers find nearby mosques in unfamiliar locations.
- Provide reliable mosque information, operating schedules, and facilities.
- Allow Mosque Administrators to maintain their assigned mosque's details, schedules, events, and janazah notices.
- Allow City Administrators to publish city-wide announcements, events, and prayer timetables.
- Notify users when relevant mosque or city information changes.
- Remain lightweight, fast, reliable, secure, and intuitive across desktop and mobile devices.

### Primary Engineering Target:
$$\text{FAST} \quad \vert \quad \text{LIGHTWEIGHT} \quad \vert \quad \text{RELIABLE} \quad \vert \quad \text{SECURE AGAINST REALISTIC THREATS} \quad \vert \quad \text{MAINTAINABLE} \quad \vert \quad \text{SIMPLE WHERE POSSIBLE}$$

> **Core Principle**: Do NOT introduce unnecessary architectural complexity, microservices, complex caching layers, or speculative frameworks. Use the simplest architecture that correctly satisfies actual product requirements.

---

## 2. Engineering Constitution (17 Invariant Laws)

These 17 laws are architectural invariants that MUST be strictly enforced across all code modifications.

### LAW 1 — ONE PERSON = ONE ACCOUNT
A person must have exactly one canonical `User` identity (one mobile number username, one credential set). A user may simultaneously possess a `CityAdmin` role, a `MosqueAdmin` role, or both, but role assignment must NEVER create duplicate `User` records for the same individual. All identity operations (registration, OTP, login, password changes, account recovery, phone updates, role promotion/assignment) must preserve this single-identity invariant.

### LAW 2 — ROLE ≠ CONTENT SCOPE
A person's role must never automatically dictate content scope. Content scope is determined strictly by the administrative CONTEXT in which content is created:
- City Admin Context $\to$ City-Scoped Content (`city = City`, `mosque = None`).
- Mosque Admin / My Mosque Context $\to$ Mosque-Scoped Content (`city = Mosque.city_relation`, `mosque = Mosque`).
A dual-role user (City Admin + Mosque Admin) creating content in Mosque Admin context creates Mosque-scoped content, NOT City content. Backend permissions and ViewSet querysets must unconditionally enforce this isolation.

### LAW 3 — ONE ACTIVE CITY ADMIN PER CITY
Each registered city may have at most ONE active `CityAdmin` profile. This rule must be enforced at the database layer (via partial unique constraints) and within atomic transaction blocks to prevent multi-threaded assignment race conditions.

### LAW 4 — ONE PERSON = AT MOST ONE MOSQUE ADMINISTRATION
A user may administer at most ONE mosque as a `MosqueAdmin`. Role assignment logic must not silently assign multiple mosques to a single administrator unless the system architecture is explicitly updated.

### LAW 5 — DATABASE IS AUTHORITATIVE
Frontend state is NEVER authoritative for security, authentication, authorization, content scope, role profile resolution, approval status, or identity. All security-critical validations, scope filters, and permissions must be enforced server-side by Django / DRF.

### LAW 6 — NO SILENT ARCHITECTURE CHANGES
Agents must not silently alter core identity, authorization, content-scope, database relationships, API contracts, or deployment models. If a fix requires architectural changes: STOP $\to$ Report current rule, limitation, proposed change, and consequences $\to$ Wait for explicit user authorization.

### LAW 7 — NO UNRELATED SCOPE EXPANSION
Agents must work ONLY on the currently authorized sprint/finding. If an unrelated bug is discovered during investigation, record it as `DISCOVERED — NOT AUTHORIZED` in `BUG_REGISTRY.md` and continue the authorized task unless the issue directly blocks execution or creates an immediate security hazard.

### LAW 8 — NO "WORKS ON MY MACHINE" ACCEPTANCE
A feature or bug fix is NOT complete merely because code was edited or manual UI testing succeeded. Every change requires concrete empirical evidence: targeted unit/integration tests, full backend test execution, TypeScript compilation (`npx tsc --noEmit`), production build validation (`npm run build`), and security/concurrency verification.

### LAW 9 — NEVER FIX A TEST BY WEAKENING THE TEST
Never delete a failing test, weaken assertions, bypass validation, or alter expected test outputs simply to achieve green test runs. When a test fails, investigate and fix the root cause in the underlying production/application code.

### LAW 10 — CONCURRENCY IS PART OF CORRECTNESS
Whenever multiple users, administrators, browser sessions, or API requests can interact with the same database record or state transition, proper concurrency controls (`transaction.atomic()`, `select_for_update()`, unique database constraints, optimistic versioning) MUST be implemented. Sequential execution must never be assumed.

### LAW 11 — EXTERNAL I/O MUST BE DELIBERATE
Database model operations (`save()`, signals) must NEVER perform synchronous external network calls (HTTP requests, SMS, WhatsApp, email, external geocoding APIs). External network dispatches must be explicit, failure-aware, and decoupled from core database persistence. Hardcoded production/test recipient phone numbers or credentials are strictly forbidden.

### LAW 12 — SECURITY MUST BE PROPORTIONAL BUT REAL
Security protections must be strong, practical, and framework-native. At minimum, code must prevent authentication bypass, authorization bypass / IDOR, SQL injection, XSS, CSRF, SSRF, privilege escalation, brute-force attacks, OTP abuse, mass assignment, and race-condition state corruption.

### LAW 13 — PERFORMANCE IS A FIRST-CLASS REQUIREMENT
The application must maintain fast user-perceived performance:
- **Frontend**: Zero unnecessary re-renders, component code-splitting for heavy modals/tabs, bundle size optimization, request deduplication/caching, and elimination of `useEffect` waterfalls.
- **Backend & DB**: Elimination of N+1 query loops, single-pass SQL aggregations, `select_related`/`prefetch_related` optimization, database indexing, bounded pagination, and removal of synchronous network I/O.

### LAW 14 — DSA MUST HAVE PRACTICAL VALUE
Data structures and algorithmic reasoning must deliver tangible performance benefits. Replace full-table $O(N)$ or $O(N \log N)$ in-memory scans with database-level spatial indexing, bounding-box pre-filtering, and Top-$k$ slicing ($O(\log N + k \log k)$ where $k \ll N$).

### LAW 15 — STATE MACHINES MUST BE EXPLICIT
All workflow transitions (`MosqueRegistrationRequest`, `AccountRecoveryRequest`, `JanazahNotice`, `MosqueAnnouncement`) must enforce explicit, validated state machines with row locking:
$$\text{PENDING} \longrightarrow \text{APPROVED} \quad \vert \quad \text{PENDING} \longrightarrow \text{REJECTED} \quad \vert \quad \text{REJECTED} \longrightarrow \text{REOPENED} \longrightarrow \text{PENDING}$$
Arbitrary or illegal state skips must return HTTP 409 Conflict or HTTP 400 Bad Request.

### LAW 16 — DOCUMENTATION MUST REFLECT REALITY
All file creations, modifications, deletions, database migrations, API contract changes, and test results MUST be documented immediately upon sprint completion in `AUDIT_FINDINGS_INDEX.md`, `BUG_REGISTRY.md`, and `V2_ARCHITECTURE_DECISIONS.md`.

### LAW 17 — ALWAYS READ CURRENT FILE STATE
Before modifying any file, the agent MUST inspect the authoritative, current disk version of that file using viewing tools. Never rely on conversation history, stale summaries, or previous tool outputs.

### LAW 18 — EXPLICIT TERMINAL STATE & TASK MODE DISTINCTION

Every engineering run MUST end in exactly one explicit terminal state (`VERIFIED`, `FAILED`, `BLOCKED`, or `WAITING_FOR_USER`). The execution model depends strictly on the task mode:

#### MODE A: AUDIT / INVESTIGATION TASK
If the user prompt explicitly requests investigation, auditing, bug finding, analysis, or specifies "do not modify production code":
- The agent operates in **Audit-Only Mode**.
- The agent performs static/dynamic inspection, traces root causes, and documents evidence.
- The agent terminates upon producing the audit report with zero production code changes.

#### MODE B: IMPLEMENTATION / REMEDIATION TASK
If the user prompt authorizes fixing, implementing, refactoring, optimizing, hardening, or executing a sprint/finding:
- Investigation is **NOT completion**.
- Intermediate statuses ("Investigated", "Found root cause", "Created plan", "Edited documentation", "One test passed", "Background work running") are **NOT terminal states**.
- The agent MUST autonomously continue through the entire 15-step Controlled Engineering Loop without pausing to ask permission between stages.
- `WAITING_FOR_USER` is strictly forbidden as a substitute for "I finished investigation". It is permitted ONLY for genuine product/design decisions, missing credentials, ambiguous specs, or dangerous out-of-scope actions.

#### Stop Conditions Rules:
The agent MAY stop only when one of these terminal states is genuinely true:
- **`VERIFIED`**: Objective implemented, acceptance criteria satisfied, targeted tests pass, full regression suite passes, typecheck/build passes, documentation updated.
- **`FAILED`**: Authorized objective cannot safely be completed; complete root cause and diagnostic evidence documented.
- **`BLOCKED`**: Unresolved external blocker (credentials, environment, permissions) prevents continuation.
- **`WAITING_FOR_USER`**: Genuine user design decision or explicit authorization required.

#### Scope Control & Unrelated Findings:
Loop Engineering does NOT authorize unrelated fixes. If another bug is discovered during execution:
- Record it as `DISCOVERED — NOT AUTHORIZED` in `BUG_REGISTRY.md` with finding ID, severity, evidence, and affected files.
- Do NOT silently fix it unless it is directly required for correctness/security of the authorized task.
- Continue the current authorized objective toward completion.

#### Background Work Transparency Standard:
When starting background tasks (async test runs, builds, timers):
- Log `BACKGROUND WORK STARTED` (Task name, purpose, expected result).
- Wait for actual completion and inspect the actual output/logs.
- Log `BACKGROUND WORK COMPLETED` (Status & result).
- Never declare a task `VERIFIED` while background tasks remain pending, running, or failed.

#### Anti-Infinite-Loop Guardrail:
A failed test or build failure should trigger diagnosis and correction. Never modify code blindly or make speculative edits. If the same failure persists after 2 corrective attempts:
- Stop that corrective attempt.
- Report `FAILED` or `BLOCKED` with diagnostic evidence.
- Do NOT weaken tests, delete failing assertions, or pretend the task is `VERIFIED`.

---

## 3. Agent Guardrails

### Permitted Actions:
- Inspecting repository files, architecture specs, audit logs, and test suites.
- Creating targeted regression and integration tests.
- Modifying authorized code files within the currently approved sprint scope.
- Creating schema migrations when required by authorized findings.
- Running test suites, typecheckers, linters, and build commands.
- Updating project documentation artifacts.

### Prohibited Actions:
- Stopping prematurely after investigation/plan stages when an implementation task is authorized.
- Asking for user confirmation between standard engineering stages during an authorized task.
- Redesigning system architecture without explicit authorization.
- Fixing unauthorized or out-of-sprint bugs.
- Introducing unnecessary external libraries, frameworks, or microservices.
- Deleting or weakening failing unit tests.
- Suppressing exceptions, swallowing errors, or returning fallback dummy data to mask bugs.
- Claiming a task is completed without empirical test verification evidence.
- Overwriting historical audit records or falsifying verification statuses.

---

## 4. Controlled Engineering Loop (15 Steps for Implementation Tasks)

```text
STEP 1: READ CURRENT STATE  ──► Inspect authoritative disk files, V2_ARCHITECTURE_DECISIONS.md & BUG_REGISTRY.md
         │
STEP 2: UNDERSTAND CURRENT CODE ➔ Verify current implementation & active behavior
         │
STEP 3: INVESTIGATE & ROOT CAUSE ➔ Trace complete request-to-database flow & identify failure point
         │
STEP 4: MINIMAL SAFE DESIGN  ──► Design smallest correct fix adhering to 18 Laws & framework defaults
         │
STEP 5: IMPLEMENTATION  ─────► Modify only required target files
         │
STEP 6: TARGETED TESTING ────► Write/run targeted unit, integration, edge-case & concurrency tests
         │
STEP 7: DIAGNOSE & FIX FAILURES ➔ Diagnose and correct any failures caused by implementation
         │
STEP 8: RE-RUN TARGETED TESTS ─► Re-run targeted tests until clean pass is verified
         │
STEP 9: SECURITY & INTEGRITY ──► Verify 7-role authorization, IDOR protection & input validation
         │
STEP 10: PERFORMANCE CHECK ───► Measure query counts, execution latencies & Big-O algorithmic scaling
         │
STEP 11: REGRESSION SUITE ────► Run full backend test suite (python manage.py test) & verify 0 regressions
         │
STEP 12: TYPECHECK & BUILD ────► Run npx tsc --noEmit and npm run build
         │
STEP 13: UPDATE DOCUMENTATION ─► Update BUG_REGISTRY.md, AUDIT_FINDINGS_INDEX.md & V2_ARCHITECTURE_DECISIONS.md
         │
STEP 14: RE-READ & VERIFY STATE ➔ Re-read changed files on disk & verify against final acceptance criteria
         │
STEP 15: TERMINAL REPORT  ────► Output standardized Engineering Task Terminal Report & conclude run
```

---

## 5. Finding Lifecycle & Evidence Gate

A finding cannot transition directly from `OPEN` to `VERIFIED`. It must strictly progress through all 5 lifecycle stages:

$$\text{OPEN} \xrightarrow{\text{Inspection}} \text{INVESTIGATING} \xrightarrow{\text{Code Edit}} \text{IMPLEMENTED} \xrightarrow{\text{Targeted Tests}} \text{TESTED} \xrightarrow{\text{Suite + Build Gate}} \text{VERIFIED}$$

---

## 6. Standardized Terminal Evidence Gate Report Structure

Every engineering task execution MUST conclude with the following standardized terminal report:

```text
------------------------------------------------------------
ENGINEERING TASK TERMINAL REPORT
------------------------------------------------------------
STATUS: VERIFIED / FAILED / BLOCKED / WAITING_FOR_USER
AUTHORIZED OBJECTIVE: ...

ROOT CAUSE: ...

FILES READ: ...
FILES CREATED: ...
FILES MODIFIED: ...
FILES DELETED: ...

DATABASE / MIGRATIONS: ...
API CONTRACT CHANGES: ...
IMPLEMENTATION DETAILS: ...

TARGETED TESTS: ...
REGRESSION TESTS: ...
TYPECHECK: ...
BUILD: ...

SECURITY CHECK: ...
PERFORMANCE / COMPLEXITY CHECK: ...
BACKGROUND TASKS: ...

UNRELATED FINDINGS: ...
REMAINING ISSUES WITHIN SCOPE: ...

FINAL ACCEPTANCE CRITERIA: PASS / FAIL
NEXT ACTION: ...
------------------------------------------------------------
```

