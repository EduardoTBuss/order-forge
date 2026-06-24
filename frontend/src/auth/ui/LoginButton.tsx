"use client";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

type LoginButtonProps = {
  children?: React.ReactNode;
};

export default function LoginButton({ children }: LoginButtonProps) {
  const t = useTranslations("auth.loginButton");

  // Dev stub: no popup / identity provider. Just hit the login route, which
  // sets the session cookie and redirects back here.
  function handleLogin() {
    const next = encodeURIComponent(
      `${window.location.pathname}${window.location.search}${window.location.hash}`,
    );
    window.location.assign(`/api/auth/login?next=${next}`);
  }

  return (
    <Button
      onClick={handleLogin}
      size="lg"
      className="text-lg font-semibold px-8"
    >
      {children ?? t("default")}
    </Button>
  );
}
