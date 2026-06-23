# Mosque Platform Frontend

Runnable Next.js frontend foundation for the mosque discovery and prayer intelligence platform.

## Commands

```bash
npm install
npm run dev
npm run build
npm run lint
```

The local app runs at:

```text
http://localhost:3000
```

The frontend is configured to call the Django API at:

```text
http://127.0.0.1:8000/api/v1
```

Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to override it.
