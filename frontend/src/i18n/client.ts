"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import {
  LOCALE_COOKIE,
  LOCALE_COOKIE_MAX_AGE,
  LOCALES,
  type Locale,
} from "./config";

export const availableLocales: Locale[] = [...LOCALES];

export function useChangeLocale(): (locale: Locale) => void {
  const router = useRouter();

  return useCallback(
    (locale: Locale) => {
      const cookie = [
        `${LOCALE_COOKIE}=${locale}`,
        "path=/",
        `max-age=${LOCALE_COOKIE_MAX_AGE}`,
        "SameSite=Lax",
      ].join("; ");
      document.cookie = cookie;
      router.refresh();
    },
    [router],
  );
}
