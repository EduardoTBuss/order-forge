/**
 * Generate service worker with build-time cache versioning.
 * Run this before build to inject a unique cache version.
 *
 * Usage: node scripts/generate-sw.js
 */

import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const SW_TEMPLATE = resolve("public/sw.template.js");
const SW_OUTPUT = resolve("public/sw.js");

// Generate a version hash based on timestamp and random value
function generateVersion() {
  const timestamp = Date.now().toString();
  const random = Math.random().toString(36).substring(2, 8);
  const hash = createHash("md5")
    .update(timestamp + random)
    .digest("hex")
    .substring(0, 8);
  return `v${hash}`;
}

try {
  // Check if template exists, if not use existing sw.js as base
  let template;
  try {
    template = readFileSync(SW_TEMPLATE, "utf8");
  } catch {
    // No template, update existing sw.js
    template = readFileSync(SW_OUTPUT, "utf8");
  }

  const version = generateVersion();

  // Replace the cache version in the template
  // App slug should match src/config/app-identity.ts
  const _appSlug = "invoice-intake-workshop";
  const updated = template.replace(
    /const CACHE_NAME = .*?;/,
    `const CACHE_NAME = \`${appSlug}-shell-${version}\`;`,
  );

  writeFileSync(SW_OUTPUT, updated);
  console.log(`✔ Service worker updated with cache version: ${version}`);
} catch (error) {
  console.error("Failed to generate service worker:", error);
  process.exit(1);
}
