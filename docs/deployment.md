# Production Deployment Architecture

## Services

- `frontend`: Next.js application served by Node in standalone mode.
- `backend`: Django REST Framework application served by Gunicorn.
- `postgres`: PostgreSQL with PostGIS, `pg_trgm`, and `citext`.
- `nginx`: HTTPS reverse proxy, static/media serving, security headers.

## Deployment Workflow

1. Build frontend and backend images in CI.
2. Run frontend lint, typecheck, and build.
3. Run backend tests and migration checks.
4. Push tagged images to a private registry.
5. Deploy to staging with production-like environment variables.
6. Run smoke tests against staging.
7. Promote the same image tags to production.
8. Run database migrations once during release.
9. Verify health checks and logs.

## Production Environment Strategy

Use separate environments:

- local
- staging
- production

Each environment must have its own:

- database
- secrets
- Google Maps API keys
- allowed hosts
- CORS origins
- JWT signing keys

Do not reuse production secrets in staging or local development.

## Secret Handling

Production secrets should be injected by the deployment platform or secret manager.

Required secrets:

- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `JWT_SIGNING_KEY`
- `GOOGLE_MAPS_API_KEY`
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`

Never commit real `.env` files. Commit only `.env.example`.

## HTTPS

Nginx terminates HTTPS and forwards traffic to internal containers.

Use:

- TLS 1.2+
- HSTS
- HTTP-to-HTTPS redirect
- secure cookies
- strict allowed hosts
- strict CORS origins

For managed platforms, HTTPS may be terminated by the load balancer instead of Nginx.

## Logging

Log to stdout/stderr from containers.

Recommended fields:

- timestamp
- service
- level
- request id
- path
- status code
- latency
- user id when authenticated
- remote IP or trusted forwarded IP

Avoid logging:

- passwords
- JWTs
- refresh tokens
- precise public user coordinates
- full request bodies for auth endpoints

## Monitoring

Track:

- container health
- CPU and memory
- database connections
- PostgreSQL disk usage
- API latency
- 4xx and 5xx rates
- login failures
- nearest mosque query latency
- Google Maps quota usage

Recommended tools:

- Sentry for application errors
- Prometheus/Grafana or managed metrics
- uptime checks for frontend and API health endpoints
- PostgreSQL monitoring from the hosting provider

## Backup Strategy

PostgreSQL:

- daily full backups
- point-in-time recovery if managed Postgres supports it
- encrypted backup storage
- retention policy: 7 daily, 4 weekly, 6 monthly
- quarterly restore drills

Media/images:

- prefer object storage in production
- enable versioning where possible
- back up metadata in PostgreSQL

Before destructive migrations:

- take a manual database snapshot
- verify rollback plan

## Scaling Strategy

Phase 1:

- one frontend container
- one backend container
- one PostgreSQL instance
- Nginx reverse proxy

Phase 2:

- multiple backend replicas behind Nginx/load balancer
- managed PostgreSQL
- Redis for cache and rate limiting
- object storage for images

Phase 3:

- read replica for public discovery reads
- CDN for static assets and images
- background worker containers for imports/geocoding
- autoscaling based on CPU/latency

## Production Security Checklist

- `DJANGO_DEBUG=false`
- HTTPS enabled
- secure refresh cookies
- strict CORS and CSRF origins
- restricted Google Maps API keys
- non-root containers
- database not publicly exposed
- regular dependency updates
- rate limiting on auth and public discovery APIs
- backups tested
- logs reviewed for sensitive data leakage
