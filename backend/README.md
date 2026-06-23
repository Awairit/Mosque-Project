# Mosque Platform Backend

Runnable Django 5 backend foundation for the mosque discovery and prayer intelligence platform.

## Structure

```text
backend/
  manage.py
  config/
    settings/
      base.py
      local.py
      production.py
    api/
      v1/
  apps/
    common/
    accounts/
    locations/
    mosques/
    prayers/
    operations/
    moderation/
    events/
    platform_admin/
```

## Important Files

- `manage.py`: command entrypoint for Django tasks.
- `config/settings/base.py`: shared settings for all environments.
- `config/settings/local.py`: local development settings.
- `config/settings/production.py`: production security settings.
- `config/urls.py`: root project URLs.
- `config/api/v1/urls.py`: versioned API router.
- `apps/*/services.py`: future write/business workflows.
- `apps/*/selectors.py`: future read/query helpers.
- `apps/*/serializers.py`: future DRF serializers.
- `apps/*/views.py`: future DRF views.

## Local Setup

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements/local.txt
```

Run migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Health check:

```text
http://127.0.0.1:8000/api/v1/health/
```

## Database

By default, local development falls back to SQLite so beginners can run the app immediately.

To use PostgreSQL, set `DATABASE_URL`:

```text
DATABASE_URL=postgresql://mosque_app:password@localhost:5432/mosque_platform
```

Production should always use PostgreSQL.
