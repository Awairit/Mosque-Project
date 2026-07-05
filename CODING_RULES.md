# Mosque Platform Development Rules

You are working on an existing production-style project.

CRITICAL RULES:

1. Never overwrite working functionality.
2. Never rewrite existing architecture unless explicitly instructed.
3. Always extend the current implementation incrementally.
4. Preserve all working APIs.
5. Preserve all working frontend pages.
6. Create migrations instead of modifying existing migrations.
7. Follow Django + DRF best practices.
8. Follow Next.js App Router best practices.
9. All new functionality must be fully tested.
10. Explain what files were changed after every implementation.

Development Style:

* Small feature slices.
* One business capability at a time.
* Backward compatible changes.
* Production-grade code only.
* Type-safe frontend code.
* Clean architecture.

Before making major changes:

* Inspect current codebase.
* Reuse existing patterns.
* Avoid duplicate models or APIs.

After every task:

* Run migrations.
* Run backend checks.
* Run frontend build.
* Verify functionality.

Do not implement unrelated features.
Do not refactor working code unless necessary.
