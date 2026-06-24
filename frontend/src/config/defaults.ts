/**
 * Centralized default values for the application.
 * Import from here instead of hardcoding magic values.
 */

// Re-export app identity values
// Convenience aliases for backward compatibility
export {
  APP_SLUG,
  CLIENT_NAME,
  CLIENT_NAME as APP_SHORT_NAME,
  DEFAULT_DESCRIPTION,
  DEFAULT_DISPLAY_NAME,
  DEFAULT_DISPLAY_NAME as APP_NAME,
  DEFAULT_PROJECT_NAME,
} from "./app-identity";

// OpenAI / Model defaults
export const DEFAULT_MODEL = "gpt-5";
export const DEFAULT_MODELS = ["gpt-5", "gpt-4o-mini"];

// PDF preprocessing defaults
export const DEFAULT_DPI = 300;
export const DEFAULT_CONTRAST = 1;
export const DEFAULT_GRAYSCALE = false;
export const DEFAULT_OCR_ENHANCEMENT = "all" as const;
export const DEFAULT_WINDOW_SIZE = 10;
export const DEFAULT_WINDOW_OVERLAP = 2;

// API timeouts
export const API_TIMEOUT_MS = 30_000; // 30 seconds

// Icon paths
export const DEFAULT_NOTIFICATION_ICON = "/icon_192.png";
export const APP_ICON_192 = "/icon_192.png";
export const APP_ICON_512 = "/icon_512.png";
export const APP_ICON_180 = "/icon_180.png";

// App metadata - imported from app-identity.ts above

// Service worker
export const SERVICE_WORKER_PATH = "/sw.js";
export const SHELL_ASSETS = [
  "/",
  "/manifest.webmanifest",
  APP_ICON_192,
  APP_ICON_512,
  APP_ICON_180,
];

// Session refresh
export const SESSION_REFRESH_BUFFER_MS = 5 * 60 * 1000; // 5 minutes before expiry

// Rate limiting defaults
export const RATE_LIMIT_WINDOW_MS = 60_000; // 1 minute
export const RATE_LIMIT_MAX_REQUESTS = 10;
