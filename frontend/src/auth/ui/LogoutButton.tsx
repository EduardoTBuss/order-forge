"use client";

import type { ReactNode } from "react";

type LogoutButtonProps = {
  children: ReactNode;
  className?: string;
};

export default function LogoutButton({
  children,
  className,
}: LogoutButtonProps) {
  function handleClick() {
    window.location.assign("/api/auth/logout");
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={["block w-full text-left font-normal", className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </button>
  );
}
