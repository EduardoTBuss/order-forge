/**
 * App Identity - Single Source of Truth for Frontend
 *
 * This file contains non-internationalized app identity values.
 * Keep in sync with:
 * - docs/project.md (authoritative source)
 * - backend/src/settings.py
 * - frontend/src/messages/*.json (i18n values)
 *
 * The project name is internationalized in messages/*.json.
 * This file contains the English defaults for contexts where i18n is not available.
 */

// Client name - constant across all languages
export const CLIENT_NAME = "Workshop";

// App slug - used for cache names, storage keys, and technical identifiers
export const APP_SLUG = "invoice-intake-workshop";

// Default values for contexts where i18n is not available (PWA manifest, service worker)
export const DEFAULT_PROJECT_NAME = "Invoice Intake";
export const DEFAULT_DISPLAY_NAME = `${DEFAULT_PROJECT_NAME} - ${CLIENT_NAME}`;
export const DEFAULT_DESCRIPTION =
  "Workshop starter for building an invoice intake app with FastAPI + Next.js.";
