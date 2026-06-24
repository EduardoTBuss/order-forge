# Frontend Development Skill

**When to use this skill:** Use when writing, reviewing, or refactoring frontend code in the Next.js application. This skill provides detailed reference material for project structure, tooling, API integration, components, state management, CI checks, and the working pipeline. For guardrails and mandatory rules, see `frontend/AGENTS.md`.

---

## 1. Project Overview

- The project is a **Next.js application** that uses the **App Router** located under `src/app`.
- **Reusable UI building blocks** live under `src/components`; pages and feature modules compose these pieces instead of duplicating markup or logic.
- **Shared utilities** such as formatting helpers and custom hooks live under `src/lib`.
- **API-related code** lives under `src/lib/backend` which contains the generated type definitions and SDK exports.
- Refer to the **Project structure** section of `README.md` for the authoritative directory layout before creating files; mirrors there show where new routes, layout shells, and service files belong.
- Whenever you change architecture, tooling, or workflows, update both `README.md` and `AGENTS.md` in the same PR so contributors never have to guess which source is current.

---

## 2. Tooling & Package Management

- The repo is pinned to **`pnpm@11.1.2`** via the `packageManager` field in `package.json`.
- Run `corepack enable pnpm` once and use `pnpm` for every install, script, or dependency change so lockfiles stay deterministic with CI.
- **Do NOT run `npm install`** or add a `package-lock.json`; if one appears, delete it and reinstall with `pnpm install`.
- Common commands (e.g., `pnpm dev`, `pnpm update-api-client`) must remain defined in `package.json` scripts so local dev, CI, and docs stay aligned.
- `pnpm update-api-client` regenerates `src/lib/backend/generated`.

---

## 3. Environment Variables

- Local development is driven by the root `.env` (see `.env.example`). The
  workshop ships a **dev stub login** — there is no identity provider, so no
  auth credentials are needed.
- The only frontend-relevant variables are the backend proxy settings:

| Variable | Purpose |
| -------- | ------- |
| `BACKEND_API_URL` | Backend proxy target (e.g. `http://backend:8000`) |
| `BACKEND_API_KEY` | Backend proxy auth (shared local secret) |

- **Avoid reading secrets client-side**—proxy credentials stay on the server (`/api/[...path]`).
- Document any new env var in both the README and `.env.example` (if introduced).

---

## 4. File Placement Rules

| Artifact | Location |
| -------- | -------- |
| **Pages and route handlers** | `src/app/<route>` using App Router conventions |
| **Reusable React components** | `src/components`; prefer colocating subcomponents within a directory module (e.g., `src/components/Table/*`) |
| **Feature-specific compositions** (page-level orchestration) | Relevant route directory in `src/app`; import lower-level pieces from `src/components` |
| **Utility functions, hooks, constants** (shared) | `src/lib`; keep feature-specific helpers colocated with their feature when not widely shared |
| **Assets** (images, icons, PDFs) | `public` unless dynamically generated |

---

## 5. Component Reuse Expectations

- This project uses **[shadcn/ui](https://ui.shadcn.com/)** for its component library, specifically their **[Base UI](https://base-ui.com/)** variants.
- Components live in `src/components/ui/` where you have full ownership.
- Before introducing a new component, search `src/components/ui/` to verify a suitable shadcn component already exists; extend it via props rather than duplicating markup.
- Use the **`cn()`** utility from `@/lib/utils` to merge Tailwind classes safely when extending components.
- When wiring feature pages, compose existing components from `src/components` and do not define React components inline in `src/app` files unless they are trivial wrappers.
- If a new reusable building block is needed, add it to `src/components` with a clear, documented API so future features can adopt it.

### Install shadcn Components Before Using Them

**You MUST install any shadcn/ui component BEFORE importing it in your code.** If you use a component that doesn't exist in `src/components/ui/`, the build will fail with an import error.

**Installation command:**
```bash
cd frontend
pnpm shadcn add <component-name>
```

**Workflow:**
1. **Check if component exists**: Look in `src/components/ui/` for the component
2. **If missing, install it**: Run the install command above
3. **Then import and use**: Only after installation, import from `@/components/ui/<component>`

**Common components and their install names:**

| Component          | Install Command                                   |
| ------------------ | ------------------------------------------------- |
| Table              | `pnpm shadcn add table`                           |
| Tabs               | `pnpm shadcn add tabs`                            |
| Form               | `pnpm shadcn add form`                            |
| Checkbox           | `pnpm shadcn add checkbox`                        |
| Dropdown Menu      | `pnpm shadcn add dropdown-menu`                   |
| Alert              | `pnpm shadcn add alert`                           |
| Toast              | `pnpm shadcn add toast sonner`                    |
| Tooltip            | `pnpm shadcn add tooltip`                         |
| Avatar             | `pnpm shadcn add avatar`                          |
| Progress           | `pnpm shadcn add progress`                        |
| Skeleton           | `pnpm shadcn add skeleton`                        |
| Separator          | `pnpm shadcn add separator`                       |
| Label              | `pnpm shadcn add label`                           |
| Textarea           | `pnpm shadcn add textarea`                        |
| Calendar           | `pnpm shadcn add calendar`                        |
| Date Picker        | `pnpm shadcn add calendar popover button`         |
| Command (Combobox) | `pnpm shadcn add command`                         |
| Data Table         | `pnpm shadcn add table` + `@tanstack/react-table`  |

**Currently installed components** (check `src/components/ui/`): accordion, badge, button, card, dialog, input, popover, scroll-area, select, sheet, switch

**Example workflow:**
```bash
# Need a table? First check if it exists:
ls src/components/ui/table.tsx  # If "No such file", install it:

# Install the component
pnpm shadcn add table

# Now you can import it
import { Table, TableBody, TableCell, ... } from "@/components/ui/table";
```

**❌ NEVER do this:**
```tsx
// Importing a component that hasn't been installed - THIS WILL FAIL
import { Table } from "@/components/ui/table";  // Error: Module not found
```

**✅ ALWAYS do this:**
```bash
# First install
pnpm shadcn add table
```
```tsx
// Then import
import { Table } from "@/components/ui/table";  // Works!
```

---

## 6. API Integration Rules (Detailed)

### Update the API Client First

Before making ANY frontend changes that involve API calls, regenerate the API client:

```bash
# Ensure backend is running
docker compose up -d --watch backend

# From the devcontainer terminal (not inside a container):
./scripts/update-api-client.sh
```

This is mandatory because:
- The generated SDK provides typed endpoint helpers
- Skipping this step leads to runtime errors from schema mismatches
- The types are the contract between frontend and backend

### Client Components Only - No Server Component API Calls

**The generated SDK MUST only be used in client components.** Never import from `@/lib/backend` in server components.

The SDK uses relative URLs (`/api`) and browser credentials that do not work in React Server Components:
- Relative URLs have no origin to resolve against in Node.js
- Browser cookies aren't forwarded to server-side fetch calls
- The SDK is designed for browser execution only

**✅ CORRECT: Client component with "use client"**

```tsx
// MyFeatureClient.tsx
"use client";
import { backend } from "@/lib/backend";

export function MyFeatureClient() {
  const [data, setData] = useState(null);

  useEffect(() => {
    backend.postgresql.postgresqlGetItems({...})
      .then(setData);
  }, []);

  return <div>{/* render data */}</div>;
}
```

**✅ CORRECT: Server component delegates to client component**

```tsx
// page.tsx (server component - NO SDK imports here)
import { requireSession } from "@/auth/session";
import { MyFeatureClient } from "./MyFeatureClient";

export default async function MyPage() {
  await requireSession(); // Auth check on server
  return <MyFeatureClient />; // Client component handles API calls
}
```

**❌ WRONG: SDK in server component**

```tsx
// page.tsx - THIS WILL FAIL
import { backend } from "@/lib/backend"; // ❌ NO!

export default async function MyPage() {
  // This fails: relative URL, no cookies, wrong environment
  const data = await backend.postgresql.postgresqlGetItems({...});
  return <div>{JSON.stringify(data)}</div>;
}
```

**Responsibilities:**
- **Server components**: Layout, authentication (`requireSession()`), static content, translations
- **Client components**: All API calls via the generated SDK, interactive UI, loading states

### Only Use Generated SDK Functions

**NEVER use `fetch()`, `axios`, or any other HTTP client directly for backend calls.**

```typescript
// ✅ CORRECT: Use generated SDK (nested classes: backend.<module>.<method>)
import { backend } from "@/lib/backend";
const { data } = await backend.postgresql.postgresqlGetItems({...});

// ❌ WRONG: Direct fetch - NEVER DO THIS
const response = await fetch("/core/postgresql/get-items", {...});
```

**Why this is mandatory:**
- Generated functions are fully typed (request and response)
- They automatically use the `/api` proxy
- API key injection is handled automatically
- Schema changes are caught at compile time

### API Call Requirements

**Backend (`BACKEND_API_URL`):**
1. Use ONLY the generated SDK functions from `src/lib/backend`
2. Be made from client components only (files with `"use client"` directive)
3. Reference generated types in `src/lib/backend/generated/` for request/response sync
4. Go through the `/api` proxy—never call `BACKEND_API_URL` directly from browser/server code
5. Keep API-layer logic (query building, mutations) centralized under `src/lib/backend`

**General:**
- Do NOT create hand-written fetch wrappers—the generated SDK covers all endpoints
- Use `./scripts/update-api-client.sh` whenever the backend schema changes
- Never edit generated files by hand—re-run the script instead

---

## 8. State, Data, and Side Effects

- **Fetching** occurs in `src/lib/backend` via SDK calls; client components should depend on typed hooks or helpers rather than calling the API directly.
- **Shared state** hooks or context providers belong under `src/lib` or `src/components` (for UI-specific state) and should be made reusable across pages.

---

## 9. CI Checks

Before pushing any frontend changes, run these checks locally:

```bash
cd frontend
pnpm format      # Biome - code formatting
pnpm lint        # Biome - code quality
pnpm typecheck   # TypeScript - type safety (the primary local check)
```

This starter has no CI; run these yourself before committing. `pnpm build` is
skipped locally — see the upstream Next.js note below.

### Available npm Scripts

| Script      | Command          | Purpose                                  |
| ----------- | ---------------- | ---------------------------------------- |
| `format`    | `pnpm format`    | Run Biome format on all files            |
| `lint`      | `pnpm lint`      | Run Biome lint on all files              |
| `typecheck` | `pnpm typecheck` | Run TypeScript compiler without emitting |
| `build`     | `pnpm build`     | Build Next.js production bundle          |
| `dev`       | `pnpm dev`       | Start development server                 |

---

## 10. Strict Typing

All TypeScript code must use explicit, precise types — parameters, return types, and props.

**Discouraged types:** `any`, `unknown`, `Record<string, unknown>`, and `object` should be avoided. Prefer `interface` or `type` with well-defined fields that reflect the real structure of the data. When dealing with genuinely dynamic data (e.g. third-party error objects, user-controlled JSON, or external API payloads you don't control), narrowed types with runtime guards are acceptable — but `any` as a shortcut for "I didn't bother typing this" is not.

**API types are auto-generated:** the SDK in `src/lib/backend/generated/` provides fully typed request/response types. Always use them — never hand-write API types or cast responses to `any`.

```typescript
// ❌ BAD: Lazy typing — structure is known
function processUser(data: any): any { ... }

// ❌ BAD: Overly generic when shape is known
function processUser(data: Record<string, unknown>) { ... }

// ✅ GOOD: Explicit types
interface User { id: number; name: string }
interface Result { success: boolean; message: string }
function processUser(data: User): Result { ... }

// ✅ GOOD: Narrowing genuinely unknown data
function getErrorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "detail" in error) {
    return (error as { detail: string }).detail;
  }
  return String(error);
}
```

---

## 11. File Size Limits

### Thresholds

| Level | Lines | Action |
|-------|-------|--------|
| **Ideal zone** | 100–300 | Target range for all hand-written `.ts`/`.tsx` files |
| **Soft warning** | 300 | Proactively look for split points when approaching this |
| **Hard limit** | 500 | Pre-commit blocks the commit (unless exempted) |

Counting includes **all lines** (code, blanks, comments) — measured by `wc -l`.

### Why This Matters

- React components above ~300 lines almost always violate Single Responsibility
- AI agents produce better, smaller diffs on focused files (<500 LOC)
- JSX-heavy files inflate line counts quickly — a 500-line component often has only ~350 lines of actual logic, spread thin across markup

### Excluded from Limits

| Category | Pattern | Reason |
|----------|---------|--------|
| Generated SDK | `**/generated/**`, `*.gen.*` | Machine output — not editable |
| Lock files | `*.lock` | Tooling-managed |
| Snapshot tests | `**/__snapshots__/**` | Auto-generated |
| Markdown/docs | `**/*.md` | Documentation and skill files are reference material |

### When and How to Split

**Split when a client component approaches 300 lines.**

Natural split points for React/Next.js files:

```
app/(private)/invoices/
├── page.tsx                  # Server component — auth + layout only
├── InvoicesClient.tsx        # Client component — orchestrates sub-components
├── components/
│   ├── InvoiceTable.tsx      # Table display
│   ├── InvoiceFilters.tsx    # Filter bar / search
│   └── InvoiceDetailDialog.tsx  # Detail modal
├── hooks/
│   └── useInvoices.ts        # Data fetching + state logic
└── types.ts                  # Local type definitions
```

**Common extraction patterns:**

| What to extract | Where to put it | When |
|----------------|----------------|------|
| Data fetching + state | `hooks/useFeatureName.ts` | Any component with >30 lines of state/effect logic |
| Sub-sections of UI | `components/SectionName.tsx` | Distinct visual areas (table, form, dialog, filters) |
| Shared types | `types.ts` next to the component | >5 type/interface definitions in one file |
| Utility functions | `utils.ts` or `lib/` | Pure functions used across components |

**Split files MUST have meaningful names.** `ComponentPart1.tsx` /
`ComponentPart2.tsx` is forbidden — always name by responsibility
(`InvoiceTable.tsx`, `InvoiceFilters.tsx`).

### Exception Mechanism

If a file legitimately needs to exceed 500 lines and no domain-driven split
makes sense, add a comment in the first 5 lines:

```typescript
// file-size-exception: complex form wizard with tightly coupled step transitions
```

This bypasses the pre-commit hard limit. Use sparingly and document the reason.

---

## 12. Working Pipeline

1. **Implement** the required changes first before any verification.
2. **Run CI commands** with safe mock environment variables so they mimic CI without leaking secrets; document whichever placeholders you needed:
   ```bash
   pnpm lint
   pnpm typecheck
   pnpm build
   ```
3. **Fix issues** if any check fails; re-run until all succeed locally.
4. **Propose a commit** subject and body that summarize the change set, and explicitly ask the user to confirm.
5. **After user approval**: stage the touched files (`git add …`) and create the commit with that subject/body.

---

## 13. Breadcrumb Conventions

If you add breadcrumbs, give each segment a human-readable label (capitalized,
with spaces — not camelCase, kebab-case, or snake_case) and never render raw IDs.
For dynamic segments, fetch and display a meaningful name instead of the ID.

---

## 14. Design System

The design tokens live in `globals.css` as CSS variables (`--primary`, fonts,
radii, etc.). To change the look, edit those token values — most of the UI
(buttons, cards, focus rings, gradients) derives from them automatically, so
nothing else needs touching.
