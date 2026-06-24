import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  server: {
    // Backend proxy
    BACKEND_API_URL: z
      .string()
      .url()
      .transform((url) => url.replace(/\/$/, "")),
    BACKEND_API_KEY: z.string().min(1),
    // Workshop dev stub: when "true", a fake local user is signed in.
    // There is no real identity provider in this template.
    IS_DEV_ENVIRONMENT: z.string().optional(),
  },
  client: {},
  // Runtime environment variables
  // Write explicitly because Next.js sometimes doesn't pick up env vars from process.env
  runtimeEnv: {
    BACKEND_API_URL: process.env.BACKEND_API_URL,
    BACKEND_API_KEY: process.env.BACKEND_API_KEY,
    IS_DEV_ENVIRONMENT: process.env.IS_DEV_ENVIRONMENT,
  },
});

/**
 * Helper to check if we're in production.
 */
export function isProduction(): boolean {
  return process.env.NODE_ENV === "production";
}

/**
 * Helper to check if we're in development.
 */
export function isDevelopment(): boolean {
  return process.env.NODE_ENV !== "production";
}

/**
 * Helper to check if we're in a dev environment.
 * Used for auto-granting the dev role and bypassing admin checks.
 * Set IS_DEV_ENVIRONMENT=true in docker-compose for local development.
 */
export function isDevEnvironment(): boolean {
  return process.env.IS_DEV_ENVIRONMENT === "true";
}
