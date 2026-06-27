# Frontend Agent Guidelines

Read the root `AGENTS.md` first, then follow these frontend-specific guardrails.

---

## Mandatory Rules

1. **Use `pnpm`** — not npm; repo pinned to `pnpm@11.1.2` via `packageManager`
2. **Install shadcn components before using them** — `pnpm shadcn add <name>`
3. **SDK calls in client components only** — never import `@/lib/backend` in server components
4. **Only use generated SDK functions** — never use `fetch()`, `axios`, or direct HTTP
5. **Run `./scripts/update-api-client.sh`** before any frontend work involving API calls
6. **All user-facing text uses translation keys** — `src/messages/en.json` and `de.json`
7. **No mock data** — initialize all data from real API calls via SDK

---

## API Call Pattern

```typescript
// ✅ CORRECT: Client component with SDK
"use client";
import { backend } from "@/lib/backend";
const { data } = await backend.postgresql.postgresqlGetItems({...});

// ❌ WRONG: Direct fetch or server component SDK usage
const response = await fetch("/api/core/...", {...});
```

Server components handle auth (`requireSession()`) and layout; client components handle all API calls.

The backend SDK (`@/lib/backend`) covers the kept core modules — `postgresql`,
`cosmosdb`, `blob_storage`, and `info`. Build the invoice feature's own endpoints
under `backend/src/app/modules/custom/`, regenerate the SDK, then call them the
same way.

---

## Authentication (dev stub login)

This starter ships a **dev stub login** — there is no cloud identity provider.
`requireSession()` / `getSessionOrNull()` read an httpOnly cookie holding a
hardcoded local user; the `(private)` layout and the `proxy.ts` guard enforce it
the same way a real provider would.

- Keep the auth **shape** (`session.ts`, the `proxy.ts` guard, the `(private)`
  route group). It teaches the protected-route + server-side-API-key pattern.
- The `/api/[...path]` proxy still injects `Authorization: Bearer ${BACKEND_API_KEY}`
  — a local shared secret, not a cloud credential.
- Do **not** reintroduce Azure AD / MSAL / RBAC. If a participant wants real SSO,
  that is their choice to add.

---

## Local Checks (run before committing)

This starter has no CI; run the checks yourself:

```bash
cd frontend
pnpm format         # Biome formatting
pnpm lint           # Biome quality
pnpm typecheck      # TypeScript — primary local verification
# (skip pnpm build locally — see "Local build is currently broken upstream" below)
```

### Why `pnpm build` is skipped locally

Two compounding issues — only the first is solvable in this repo:

1. **Env vars missing on the host.** `frontend/src/env.ts` validates
   `BACKEND_API_URL` and `BACKEND_API_KEY` at module load via
   `@t3-oss/env-nextjs`. Those only live in the compose container.
   Mitigation in this repo: `pnpm build:docker` (in `package.json`) shells
   the build into the running frontend container so the validation passes.

2. **Next 16 `/_global-error` prerender bug — upstream framework issue.**
   `next@16.2.6` build fails with
   `TypeError: Cannot read properties of null (reading 'useContext')`
   during static export of `/_global-error`. Tracked upstream:
   [#84994](https://github.com/vercel/next.js/issues/84994),
   [#85668](https://github.com/vercel/next.js/issues/85668),
   [#86178](https://github.com/vercel/next.js/issues/86178),
   [#87719](https://github.com/vercel/next.js/issues/87719). Reporters
   have tried `force-dynamic`, `output: 'standalone'`,
   `experimental.dynamicIO`, removing hooks, `dynamic({ ssr: false })`,
   and `.next` cache clearing — none work. No maintainer-supplied fix yet.
   The dev server is unaffected — only the static-export step in
   `next build` trips on this. Until upstream ships a fix, `pnpm typecheck`
   plus a dev-server smoke test (browse to changed routes, watch
   `docker logs --tail 40 invoice-workshop-frontend-1` for compile errors) is
   the local verification path. Remove this section once `next` ships a fix and
   `pnpm build:docker` runs clean.

---

## File Placement

- **Pages**: `src/app/(private)/[feature]/page.tsx`
- **Components**: `src/components/` (shared) or colocated in `src/app/`
- **Hooks/utils**: `src/lib/`
- **Assets**: `public/`

