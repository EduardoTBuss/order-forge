"use client";

import { AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect } from "react";
import { Button } from "@/components/ui";
import { isDevelopment } from "@/env";

export default function AppError({
  error: appError,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useTranslations("errors.generic");

  useEffect(() => {
    // Log error to console in development
    if (isDevelopment()) console.error("App error:", appError);
  }, [appError]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
        <AlertTriangle className="h-8 w-8 text-red-600 dark:text-red-400" />
      </div>
      <h1 className="mb-2 text-2xl font-semibold">{t("title")}</h1>
      <p className="mb-6 max-w-md text-muted-foreground">{t("description")}</p>
      <div className="flex items-center gap-3">
        <Button onClick={reset} variant="default">
          {t("retry")}
        </Button>
        <Link href="/">
          <Button variant="outline">{t("goHome")}</Button>
        </Link>
      </div>
      {appError.digest && (
        <p className="mt-4 text-xs text-muted-foreground">
          Error ID: {appError.digest}
        </p>
      )}
    </div>
  );
}
