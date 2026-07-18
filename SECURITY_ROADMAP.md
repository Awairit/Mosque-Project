# MosqueCom Security Roadmap

This roadmap documents findings from the Post-V1.1 Production Audit and categorizes security hardening tasks by release.

---

## ✅ Completed in v1.2

These items have been implemented in the v1.2 Security Hardening Sprint to resolve critical/high/medium production concerns:

1. **Cloud Media Storage:**
   - Replaced ephemeral local filesystem media storage with Cloudinary.
   - Restored persistence of mosque profile pictures, photos, and event banners across container rebuilds/redeploys.
   - Configured fallback to local media directories in development.

2. **Notification Authorization:**
   - Hardened `CityAdminNotificationSendAPIView` and city admin event/announcement managers.
   - Ensured City Admins can only dispatch notifications to recipients or mosques belonging to their assigned city.
   - Banned sending SMS, WhatsApp, and email messages to arbitrary unregistered phone numbers/emails.

3. **One-Time Password Reset Tokens:**
   - Modified `ForgotPasswordResetAPIView` so that the reset token is invalidated immediately upon a successful password change.
   - Prevented reset token reuse within the 15-minute window.
   - Ensured expired tokens fail validation, while failed password change attempts do not invalidate the token.

4. **City Admin Password Recovery:**
   - Fixed forgotten password flow to query both `MosqueAdmin` and `CityAdmin` profile models.
   - Reused core OTP services to prevent logic duplication.

---

## ⏳ Planned for v1.3

These items represent planned future releases for enhanced session controls and token security:

* **Modern Authentication Strategy:** Replace long-lived DRF `TokenAuthentication` with short-lived access tokens and secure HTTPOnly/Secure stateful refresh tokens (e.g. using `dj-rest-auth` or `django-rest-knox`).
* **Token Rotation:** Automatically rotate refresh tokens upon usage.
* **Token Revocation:** Introduce explicit log-out APIs to delete token entries immediately.
* **Session Expiration:** Configure absolute token/session timeouts.

---

## 📋 Future Security Backlog

These items are recorded in the backlog for future maintenance sprints:

* **OWASP Penetration Testing:** Perform regular automated pen-testing against the top 10 vulnerabilities.
* **Automated Security Scanning:** Integrate `bandit` for Django backend security linting and `npm audit` in CI/CD pipeline.
* **Load Testing:** Benchmark the API views with tools like Locust to verify database connection stability.
* **Disaster Recovery Testing:** Mock recovery scenarios for database dropouts, Twilio service failure, and Cloudinary downtime.
* **Monitoring & Alerting:** Integrate Sentry to log errors and alert engineers.
* **Security Headers Review:** Clean up header integrations on deployment ingress proxies (Render/Vercel).
* **CSP Improvements:** Add a strict Content Security Policy to the Next.js frontend to mitigate XSS risks.
* **Advanced Audit Logging:** Track administrative actions using a structured central audit trail model.
* **Rate Limiting Enhancements:** Customize throttling classes to bound requests from specific user segments more strictly.
* **Infrastructure Hardening:** Restrict PostgreSQL database connections strictly to trusted servers.
