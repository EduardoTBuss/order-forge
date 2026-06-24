## Invoice Intake - Workshop Frontend

This is the frontend for the **Invoice Intake - Workshop** starter: a minimal
Next.js shell that participants extend to build an invoice intake feature. It
ships:

### App Identity

The app identity is configured in `src/config/app-identity.ts`:

```typescript
export const CLIENT_NAME = "Workshop";
export const APP_SLUG = "invoice-intake-workshop";
export const DEFAULT_PROJECT_NAME = "Invoice Intake";
export const DEFAULT_DISPLAY_NAME = "Invoice Intake - Workshop";
```

**Keep in sync with:** `docs/project.md` (authoritative source) and `backend/src/settings.py`

**Usage in components:** Build the display name directly in TSX from `clientName` and `projectName`:

```tsx
const commonT = await getTranslator("common");
<h1>{commonT("projectName")} - {commonT("clientName")}</h1>
```

This ensures changing the app name only requires updating `common.clientName` and `common.projectName`.

### Features

This starter provides:

- A **dev stub login** (cookie-based, hardcoded local user — no cloud identity provider)
- An API proxy to a FastAPI backend using an API key stored on the server
- A generated OpenAPI client (`src/lib/backend/generated/`) covering the kept core
  modules (`postgresql`, `cosmosdb`, `blob_storage`, `info`)
- A near-blank UI shell: a public landing page, a protected layout, a home page,
  and an info page

The invoice intake feature itself is **not** pre-built — that is the workshop exercise.

### How it works

- Auth flow (dev stub):
  - `src/auth/session.ts` exposes `getSessionOrNull` and `requireSession`, backed by
    a hardcoded local user stored in an httpOnly cookie.
  - `src/app/api/auth/login` and `logout` set / clear the session cookie.
  - `src/proxy.ts` re-exports the guard defined in `src/auth/proxy.ts`, protecting
    non-public routes and redirecting to login when needed.

- Backend proxy:
  - `src/app/api/[...path]/route.ts` forwards any `/api/*` request to `BACKEND_API_URL`
    with `Authorization: Bearer ${BACKEND_API_KEY}`.
  - The client never sees the API key; calls use the browser path `/api/*`.

- OpenAPI client:
  - `scripts/update-api-client.ts` pulls `<BACKEND_API_URL>/openapi.json`, rebuilds
    `src/lib/backend/generated`, and regenerates the SDK.
  - `src/lib/backend/index.ts` exports the generated SDK with `baseUrl: "/api"` so each
    helper hits the proxy and inherits the `Authorization` header injection. Do **not**
    call `BACKEND_API_URL` directly from the browser — every request must go through `/api`.

- UI + Pages:
  - `src/components/ui/` contains shadcn/ui components managed via the shadcn CLI.
  - `src/app/(public)/page.tsx` — landing page with login.
  - `src/app/(private)/layout.tsx` — authenticated shell (ensures session + header).
  - `src/app/(private)/home/page.tsx` — home page after login.
  - `src/app/(private)/info/page.tsx` — info page.

### Authentication System (dev stub)

This starter does **not** use a cloud identity provider. The auth layer keeps the
*shape* of a real one so the protected-route and server-side-API-key patterns are
taught, but the session is a hardcoded local user.

- **Key components**
  - `src/auth/session.ts` exposes `getSessionOrNull` (read-only access to the local
    user) and `requireSession` (redirects to login when unauthenticated).
  - `src/app/api/auth/login/route.ts` and `logout/route.ts` set / clear the session
    cookie.
  - `src/auth/proxy.ts` is exported via `src/proxy.ts`; it skips public routes (`/`,
    `/api/auth/*`, static assets) and verifies the session cookie for everything else.
  - `src/app/(private)/layout.tsx` runs on every protected page request and calls
    `requireSession()` before rendering the header and page content.

- **Request flow**
  - Browser requests a protected resource → the proxy checks for a valid session
    cookie → unauthenticated requests are redirected to the login route.
  - Once login sets the cookie, the browser is sent back to the original path.
  - The private layout calls `requireSession()` so protected pages never execute
    without a session.

- **Protected surface area**
  - All app routes except `/` and the auth API endpoints require login because of the
    proxy matcher.
  - Everything under `src/app/(private)/*` goes through the private layout, so the
    redirect happens server-side even if the matcher changes.
  - API proxy routes under `/api/[...path]` also pass through the proxy layer, so
    backend calls inherit the same access control.

- **What a new contributor should know**
  - The only session signal is the httpOnly session cookie; there is no server-side
    session store and no identity provider.
  - To bypass auth locally, temporarily comment out the `redirect` inside
    `requireSession()` or the proxy verification (document the change during debugging).
  - When adding a new public page, either add an exception to `proxy.ts` or place it
    inside `src/app/(public)`.
  - When adding a new protected page, create it under `src/app/(private)` so the layout
    enforces the session before rendering.
  - **Do not reintroduce Azure AD / MSAL / RBAC.** If real SSO is needed, that is the
    participant's choice to add — the starter stays minimal.

### Project structure

```
src/
  auth/
    config.ts              # Shared env helpers and constants (cookie name, redirects)
    proxy.ts               # Auth proxy exported through src/proxy.ts
    session.ts             # Server helpers: getSessionOrNull / requireSession
    routes/
      login.ts             # Set session cookie (dev stub user)
      logout.ts            # Clear session cookie
    ui/
      LoginButton.tsx      # Login trigger
  lib/
    backend/
      index.ts             # Backend SDK exports (baseUrl=/api)
      generated/           # Auto-generated types and SDK
    types.gen.ts           # Generated types from FastAPI OpenAPI
    sdk/                   # Typed endpoint helpers (auto-generated)
  app/
    (public)/
      page.tsx             # Landing page with login prompt
    (private)/
      layout.tsx           # Authenticated shell (ensures session + header)
      home/page.tsx        # Home page (protected)
      info/page.tsx        # Info page (protected)
    api/
      [...path]/route.ts   # API proxy to FastAPI, injects Authorization header
      auth/
        login/route.ts     # Set session cookie
        logout/route.ts    # Clear session cookie
    globals.css            # Tailwind v4 styles
  components/
    ui/                    # shadcn/ui components (Button, Card, Dialog, etc.)
    ...
proxy.ts                   # Re-exported auth proxy matcher
```

### Environment variables

Set these in your `.env` (never commit secrets):

```
BACKEND_API_URL=http://backend:8000
BACKEND_API_KEY=dev-secret
```

The dev stub login needs no identity-provider configuration.

### Develop

> [!IMPORTANT]
> This project is pinned to `pnpm@11.1.2` through the `packageManager` field. Always manage dependencies with `pnpm` to keep lockfiles in sync.

1. Generate the API client from your FastAPI instance:
   ```bash
   # Ensure backend is running first
   docker compose up -d --watch backend

   # Then regenerate the API client (run from devcontainer, not inside Docker)
   ./scripts/update-api-client.sh
   ```
   - This runs `scripts/update-api-client.ts` to download the OpenAPI schema from
     `http://localhost:8000/openapi.json`, regenerate `src/lib/backend/generated`, and
     rebuild the typed SDK using `openapi-typescript-codegen`.
   - Import helpers from `src/lib/backend` to call endpoints without hand-written wrappers.
   - **Always run this before making frontend changes** to ensure types are in sync.
2. Run the local checks before committing:
   ```bash
   pnpm format      # Biome - code formatting
   pnpm lint        # Biome - code quality
   pnpm typecheck   # TypeScript - type safety
   ```
3. Run the app:
   - `pnpm dev` (uses the standard Next.js dev server to avoid Turbopack's current HMR bug after login)
4. Open `http://localhost:3000`.

### Package management

- Run `corepack enable pnpm && pnpm install` the first time you clone the repo (the devcontainer executes this automatically).
- The devcontainer activates pnpm via Corepack, so installs share the identical pnpm toolchain and `pnpm-lock.yaml`.
- We intentionally removed `package-lock.json` — if an `npm install` sneaks in and reintroduces it, delete the file and reinstall with pnpm so the workspace stays consistent.

### Local checks

This starter ships no CI. Before committing, run the checks yourself:

```bash
pnpm format      # Biome - code formatting
pnpm lint        # Biome - code quality
pnpm typecheck   # TypeScript - type safety (the primary local check)
```

`pnpm build` may fail locally due to a known upstream Next.js issue (see
`frontend/AGENTS.md`); `pnpm typecheck` plus a dev-server smoke test is the
practical verification path.

### Generated API SDK

- `src/lib/backend/generated` is auto-generated; never edit it manually. Run
  `./scripts/update-api-client.sh` after backend schema changes.
- Import services from `@/lib/backend` to get one function per endpoint:

  ```ts
  // Backend calls (SDK uses nested classes: backend.<module>.<method>)
  import { backend } from "@/lib/backend";

  const { data } = await backend.postgresql.postgresqlGetItems({
    /* typed args */
  });
  ```

- The `backend` client uses `baseUrl: "/api"` so every request routes through the Next.js
  proxy. The proxy adds `Authorization: Bearer BACKEND_API_KEY`, so the browser never sees
  the credential.
- Prefer these helpers over hand-written wrappers in `src/lib` and **never** bypass the
  proxy with a direct fetch to `BACKEND_API_URL`.

#### ⚠️ Client Components Only

**The generated SDK is designed for client components only.** Always use `"use client"` in files that import from `@/lib/backend`.

The SDK uses relative URLs (`/api`) and browser credentials that don't work in React Server Components (RSC). Server components run in Node.js where:
- Relative URLs have no origin to resolve against
- Browser cookies aren't available for authentication

**Correct pattern:**

```tsx
// page.tsx (server component)
export default async function MyPage() {
  await requireSession(); // Auth check on server
  return <MyClient />;    // Delegate data fetching to client
}

// MyClient.tsx (client component)
"use client";
import { backend } from "@/lib/backend";

export function MyClient() {
  useEffect(() => {
    // SDK uses nested classes: backend.<module>.<method>
    backend.postgresql.postgresqlGetItems({})
      .then(setData);
  }, []);
  // ...
}
```

Server components should handle layout, authentication checks, and static content. Client components handle all API calls.

### Notes

- The API key is only read on the server in the proxy route; do not expose it client-side.
- The component library uses [shadcn/ui](https://ui.shadcn.com/) components; add new components with `pnpm shadcn add <component>`.

### shadcn/ui Components

This project uses [shadcn/ui](https://ui.shadcn.com/) for its component library. Components are not installed as npm packages but are copied into `src/components/ui/` where you have full ownership to customize them.

**Adding new components:**

```bash
# Add a single component
pnpm shadcn add button

# Add multiple components
pnpm shadcn add dialog accordion select

# List all available components
pnpm shadcn add --help
```

**Key files:**
- `components.json` - shadcn configuration (style, paths, etc.)
- `src/lib/utils.ts` - `cn()` helper for merging Tailwind classes
- `src/components/ui/` - All shadcn components live here

**Customization:**
- All components use CSS variables defined in `src/app/globals.css`
- Modify component source files directly for project-specific changes
- The `cn()` utility from `@/lib/utils` merges Tailwind classes safely

## Environment variables

Set these in your shell/hosting environment (the compose stack provides them locally):

Required for the backend proxy and OpenAPI generation:
- `BACKEND_API_URL`: Base URL of the FastAPI backend (e.g. `http://backend:8000`)
- `BACKEND_API_KEY`: Shared secret injected by the proxy and validated by the backend

### Local dev examples
```
BACKEND_API_URL=http://localhost:8000 \
BACKEND_API_KEY=dev-secret \
pnpm dev
```

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
corepack enable pnpm
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.
- [the Next.js GitHub repository](https://github.com/vercel/next.js)
