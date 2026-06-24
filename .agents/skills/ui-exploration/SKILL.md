# UI Exploration with Playwright

## Overview

Claude Code can browse, interact with, and take screenshots of the running
webapp using Playwright directly. This is the **primary way to verify UI
changes** — navigate pages, click elements, fill forms, and visually inspect
the result via screenshots.

## Prerequisites

1. The docker-compose stack must be running (`./up.sh`) — frontend at `http://localhost:3000`
2. `playwright-core` must be installed globally: `npm install -g playwright-core`
3. System Chromium at `/usr/bin/chromium`

## How to Use

Run Playwright scripts via Node.js with `NODE_PATH=/usr/local/lib/node_modules`:

```bash
NODE_PATH=/usr/local/lib/node_modules node -e "
const { chromium } = require('playwright-core');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

  // Navigate and screenshot
  await page.goto('http://localhost:3000/');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '/tmp/screenshot.png', fullPage: true });

  await browser.close();
})();
"
```

Then use the `Read` tool on `/tmp/screenshot.png` to view the result.

### Common actions

| Action | Playwright code |
|--------|----------------|
| Navigate | `await page.goto('http://localhost:3000/home')` |
| Screenshot | `await page.screenshot({ path: '/tmp/shot.png', fullPage: true })` |
| Click by text | `await page.getByText('Sign in').click()` |
| Click by role | `await page.getByRole('button', { name: 'Submit' }).click()` |
| Type into input | `await page.getByLabel('Email').fill('test@example.com')` |
| Wait for element | `await page.waitForSelector('.loaded')` |
| Get page text | `const text = await page.textContent('body')` |

### Typical workflow

1. Launch browser and navigate to the page
2. Screenshot to see how it looks
3. Interact (click, type) as needed
4. Screenshot again to verify the result
5. **Always close the browser** when done

### Tips

- Chain multiple actions in a single script to avoid repeated browser launches
- Use `page.waitForTimeout(2000)` after navigation to let JS render
- Use `page.waitForSelector()` for more reliable waits on specific elements
- Save screenshots to `/tmp/` with descriptive names
- The frontend proxies API calls, so all backend features work when the stack is up

## Capturing Console Errors and Failed Requests

Playwright can capture browser console output, uncaught exceptions, and failed
network requests. Use this to debug UI issues without opening DevTools manually.

```bash
NODE_PATH=/usr/local/lib/node_modules node -e "
const { chromium } = require('playwright-core');
(async () => {
  const browser = await chromium.launch({
    executablePath: '/usr/bin/chromium',
    args: ['--no-sandbox']
  });
  const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await context.newPage();

  // Console messages (log, warn, error)
  page.on('console', msg => {
    console.log('[' + msg.type().toUpperCase() + '] ' + msg.text());
  });

  // Uncaught exceptions
  page.on('pageerror', err => {
    console.log('[PAGE ERROR] ' + err.message);
  });

  // Failed HTTP requests (4xx, 5xx)
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log('[HTTP ' + response.status() + '] ' + response.url());
    }
  });

  await page.goto('http://localhost:3000/home', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  await browser.close();
})();
"
```

### What gets captured

| Listener | What it catches |
|----------|----------------|
| `page.on('console', ...)` | `console.log`, `console.warn`, `console.error` from the browser |
| `page.on('pageerror', ...)` | Uncaught JS exceptions (including Next.js runtime errors) |
| `page.on('response', ...)` | Failed API calls, 404s, 500s — filter by `response.status() >= 400` |

### Next.js error overlays

When Next.js shows an error overlay in dev mode, it will also fire `console.error`
and/or `pageerror` events. Take a screenshot when these occur to capture the
full error overlay visually.

## Authentication — Accessing Private Pages

Public pages (e.g. `/`) work without login. Private routes require a session
cookie. This template ships a **dev stub login** — there is no identity
provider, so you don't need to harvest a real token: just hit the login route,
which sets the session cookie on the browser context and redirects to `/home`.

```javascript
const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await context.newPage();

// Dev stub login: this route sets the session cookie on the context and
// redirects to /home. No credentials, no identity provider.
await page.goto('http://localhost:3000/api/auth/login', { waitUntil: 'networkidle' });

// The cookie now lives on the context — navigate to any protected page.
await page.goto('http://localhost:3000/home', { waitUntil: 'networkidle' });
```

**Important:** reuse the same `context` (don't create a fresh `browser.newPage()`),
since the session cookie is stored on the context that performed the login.
