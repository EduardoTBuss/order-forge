import { getRequestConfig } from "next-intl/server";
import { DEFAULT_LOCALE, LOCALES } from "./config";

export default getRequestConfig(async ({ locale }) => {
  if (!locale) {
    return {
      locales: [...LOCALES],
      defaultLocale: DEFAULT_LOCALE,
      locale: DEFAULT_LOCALE,
    };
  }

  return {
    locales: [...LOCALES],
    defaultLocale: DEFAULT_LOCALE,
    locale,
  };
});
