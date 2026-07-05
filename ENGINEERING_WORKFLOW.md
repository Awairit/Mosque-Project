# MCPHire Engineering Workflow v1.2 (Adapted for Mosque Platform)

This document establishes the optimized engineering workflow for Mosque Finder. It prioritizes implementation quality, safety, and velocity while eliminating unnecessary markdown documentation for routine tasks.

---

## 1. Documentation Policy

### Rule 1 — Documentation is NOT the Default Output
Do NOT automatically generate markdown documents (`implementation_plan.md`, `execution_summary.md`, `task.md`, `walkthrough.md`) for routine tasks such as visual refactoring, bug fixes, or minor layout enhancements. Instead, present investigations, plans, and summaries directly in the chat conversation.

### Rule 2 — Documentation is Created ONLY When Necessary
Generate or modify markdown documentation *only* when the task introduces changes to:
1. **Architecture**: New subsystems, architectural redesigns, new models, or ADRs.
2. **Database**: Schema modifications, database migrations, indexing adjustments, or normalization.
3. **Security**: Authentication, authorization, encryption, rate limiting, or privacy policies.
4. **Deployment**: Docker config, CI/CD, hosting, monitoring, or rollback strategies.
5. **Public API**: API contract modifications, endpoint changes, or SDK integrations.
6. **Explicit Requests**: Only when the user explicitly requests a report/document.

---

## 2. Standard Task Lifecycle (No Markdown Documents)

For all routine engineering work:

### Phase 1 — Requirement & Scope Analysis (Chat)
Categorize the task and define boundaries directly in chat:
* **Task Classification & Estimation**: Category (UI/UX, Backend, Bug Fix, etc.), Risk Level (Low/Med/High), Complexity, and Production Impact.
* **Scope Control**: Define:
  * **IN SCOPE**: The exact features/fixes to be changed.
  * **OUT OF SCOPE**: Unrelated modifications that must remain untouched.

### Phase 2 — Investigation & RCA (Chat)
Inspect the codebase and present evidence:
* Locate the affected files, symbols, component hierarchies, and CSS layout classes.
* For bug fixes, identify the exact root cause and document why previous attempts failed.

### Phase 3 — Architecture & Safety Review (Chat)
Review design impact and confirm safety:
* **Architecture Preservation Check**: Does this task require:
  * New Component? (YES / NO)
  * New API? (YES / NO)
  * New Model? (YES / NO)
  * New Migration? (YES / NO)
  * New Package? (YES / NO)
  * New Environment Variable? (YES / NO)
  * *Provide technical justification for any "YES".*
* **Production Safety Checklist**: Confirm:
  * No deployment configuration changes, Render/Vercel/Neon overrides, env variable updates, migrations, or downtime.
  * Rollback path is available.

### Phase 4 — WAIT FOR APPROVAL (Stop Condition)
* **STOP**. Do not modify any code. Present the analysis in chat and wait for the user's explicit authorization to proceed.

### Phase 5 — Implementation & Validation
* Implement *only* the approved scope. No opportunistic refactoring or styling changes.
* Run validation checks:
  * `npm run typecheck`
  * `npm run build`
  * `python manage.py test`
  * Verify layouts manually on Desktop, Tablet, and Mobile.

### Phase 6 — Review & Git Staging (Chat)
Present the results directly in chat using this structure:
* **Files Modified**: Exactly which files changed.
* **Changes Made**: Concrete code or configuration changes.
* **Build/Test Results**: Status of quality gate commands.
* **Regression Check**: Confirmation that existing features remain stable.
* **Git Preparation**: Suggested branch, commit message, and rollback commands.

---

## 3. Definition of Done (DoD)
A task is **NOT** complete unless all of the following are true:
* [ ] Requirement fully satisfied.
* [ ] Scope strictly respected (no unrelated files modified).
* [ ] Build (`npm run build`) and typecheck (`npm run typecheck`) succeed.
* [ ] Tests (`python manage.py test`) pass.
* [ ] Responsive views verified on Desktop, Tablet, and Mobile.
* [ ] Console is clean (no layout warnings or hydration errors).
* [ ] No regressions introduced.
* [ ] Git branch/commit and rollback instructions prepared.
* [ ] Production-safe and ready for automated deployment.
