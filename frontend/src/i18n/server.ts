import { cookies } from "next/headers";
import { createTranslator } from "next-intl";
import { cache } from "react";
import {
  DEFAULT_LOCALE,
  isSupportedLocale,
  LOCALE_COOKIE,
  type Locale,
} from "./config";
import type { MessageNamespace, Messages } from "./types";

const messageLoaders: Record<Locale, () => Promise<Messages>> = {
  en: () =>
    import("@/messages/en.json", { with: { type: "json" } }).then(
      (mod) => mod.default,
    ),
  de: () =>
    import("@/messages/de.json", { with: { type: "json" } }).then(
      (mod) => mod.default,
    ),
};

async function loadMessages(locale: Locale): Promise<Messages> {
  const loader = messageLoaders[locale] ?? messageLoaders[DEFAULT_LOCALE];
  return loader();
}

export const getLocaleMessages = cache(async () => {
  const cookieStore = await cookies();
  const localeCookie = cookieStore.get(LOCALE_COOKIE)?.value;
  const locale = isSupportedLocale(localeCookie)
    ? localeCookie
    : DEFAULT_LOCALE;
  const messages = await loadMessages(locale);
  return { locale, messages };
});

export const getTranslator = cache(async (namespace: MessageNamespace) => {
  const { locale, messages } = await getLocaleMessages();
  return createTranslator({ locale, namespace, messages });
});
