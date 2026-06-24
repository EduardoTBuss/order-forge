export const LOCALES = ["en", "de"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";

export const LOCALE_COOKIE = "NEXT_LOCALE";

export const LOCALE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 year

export function isSupportedLocale(
  locale: string | null | undefined,
): locale is Locale {
  return (
    typeof locale === "string" &&
    (LOCALES as readonly string[]).includes(locale)
  );
}
