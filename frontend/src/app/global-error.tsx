"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";
import "./globals.css";
import { isDevelopment } from "@/env";

/**
 * Global error boundary for root layout failures.
 * This is a fallback when the root layout itself fails.
 * Since the layout may be broken, we don't use i18n or complex components.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    if (isDevelopment()) console.error("Global error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="m-0 min-h-screen font-sans antialiased">
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center text-foreground">
          <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-destructive/20">
            <AlertTriangle
              className="h-8 w-8 text-destructive"
              aria-hidden="true"
            />
          </div>
          <h1 className="mb-2 text-2xl font-semibold">Something went wrong</h1>
          <p className="mb-6 max-w-sm text-muted-foreground">
            A critical error occurred. Please try refreshing the page.
          </p>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={reset}
              className="cursor-pointer rounded-md border-0 bg-primary px-4 py-2 font-medium text-primary-foreground transition-opacity hover:opacity-90"
            >
              Try again
            </button>
            <Link
              href="/"
              className="inline-flex items-center justify-center rounded-md border border-border bg-transparent px-4 py-2 font-medium text-foreground no-underline transition-colors hover:bg-muted/50"
            >
              Go to homepage
            </Link>
          </div>
          {error.digest && (
            <p className="mt-4 text-xs text-muted-foreground">
              Error ID: {error.digest}
            </p>
          )}
        </div>
      </body>
    </html>
  );
}
