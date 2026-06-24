"use client";
import { Moon, Sun } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

type ThemeMode = "light" | "dark";

function getInitialTheme(): ThemeMode {
  if (typeof window === "undefined") return "light";
  const stored = (localStorage.getItem("theme") as ThemeMode | null) || null;
  if (stored === "light" || stored === "dark") return stored;
  // Default to light mode for first-time users
  return "light";
}

type ThemeToggleProps = {
  variant?: "default" | "outlined";
};

export default function ThemeToggle({ variant = "default" }: ThemeToggleProps) {
  const [theme, setTheme] = useState<ThemeMode>(() => getInitialTheme());
  const t = useTranslations("controls.themeToggle");

  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    const next: ThemeMode = theme === "light" ? "dark" : "light";
    setTheme(next);
    const root = document.documentElement;
    // Flag to enable smooth CSS variable transitions
    root.setAttribute("data-theme-switching", "");
    root.setAttribute("data-theme", next);
    window.setTimeout(() => {
      root.removeAttribute("data-theme-switching");
    }, 350);
  }

  const Icon = theme === "dark" ? Sun : Moon;

  const baseClasses =
    "inline-flex h-9 w-9 items-center justify-center rounded-lg border cursor-pointer transition-[background-color,border-color,color,transform] duration-200";
  const variantClasses =
    variant === "outlined"
      ? "border-white/50 bg-transparent text-white hover:bg-white/10"
      : "border-border bg-card text-foreground hover:bg-primary/10 hover:border-primary/30 hover:text-primary active:scale-95";

  return (
    <button
      type="button"
      aria-label={t("ariaLabel")}
      onClick={toggleTheme}
      className={`${baseClasses} ${variantClasses}`}
    >
      <Icon className="h-4 w-4 transition-transform duration-200 hover:rotate-12" />
    </button>
  );
}
