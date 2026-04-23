# SENTINEL Dashboard (web)

Next.js 15 moderator dashboard. Consumes the Dashboard BFF at `services/dashboard_bff/` (default `http://127.0.0.1:8009`).

## Requirements

- Node.js >= 20
- npm >= 10
- A running BFF

## Run

```bash
cd dashboard/web
cp .env.example .env.local
npm install
npm run dev   # http://localhost:3000
```

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | dev server on :3000 |
| `npm run build` | production build |
| `npm run start` | serve built app |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` strict |
| `npm run test` | vitest single-run |
See the [root README](../../README.md) for platform context.
