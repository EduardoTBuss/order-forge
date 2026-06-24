"use client";

import { Languages } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import Dropdown from "@/components/Dropdown";
import { availableLocales, useChangeLocale } from "@/i18n/client";

type LanguageSelectorProps = {
  variant?: "default" | "outlined";
};

export default function LanguageSelector({
  variant = "default",
}: LanguageSelectorProps) {
  const locale = useLocale();
  const changeLocale = useChangeLocale();
  const t = useTranslations("controls.languageSelector");

  const triggerClassName =
    variant === "outlined"
      ? "shrink-0 !border-white/50 !bg-transparent !text-white hover:!bg-white/10"
      : "shrink-0";

  return (
    <Dropdown
      trigger={<Languages className="h-4 w-4" aria-hidden />}
      triggerClassName={triggerClassName}
      triggerVariant="icon"
      align="right"
      triggerAriaLabel={t("ariaLabel")}
    >
      {availableLocales.map((code) => {
        const label = t(`locales.${code}`);
        const isActive = code === locale;
        return (
          <button
            key={code}
            type="button"
            onClick={() => changeLocale(code)}
            className={[
              "block w-full rounded-lg px-3 py-2 text-left text-sm transition-colors duration-150",
              isActive
                ? "bg-primary/15 text-primary font-medium"
                : "text-foreground hover:bg-primary/10",
            ].join(" ")}
            aria-pressed={isActive}
          >
            {label}
          </button>
        );
      })}
    </Dropdown>
  );
}
