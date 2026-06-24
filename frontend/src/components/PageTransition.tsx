"use client";
import { usePathname } from "next/navigation";
import { useEffect, useLayoutEffect, useRef } from "react";

const TRANSITION_DURATION = 350;

export default function PageTransition() {
  const pathname = usePathname();
  const prevPathRef = useRef<string | null>(pathname);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useLayoutEffect(() => {
    const root = document.getElementById("page-transition-root");
    if (!root) return;
    root.classList.add("page-enter");
    requestAnimationFrame(() => {
      root.classList.add("page-enter-active");
    });
    timerRef.current = setTimeout(() => {
      root.classList.remove("page-enter", "page-enter-active");
    }, TRANSITION_DURATION);
  }, []);

  useEffect(() => {
    if (prevPathRef.current === null) return;
    const root = document.getElementById("page-transition-root");
    if (!root) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    root.classList.remove("page-enter", "page-enter-active");
    root.classList.add("page-enter");
    requestAnimationFrame(() => {
      root.classList.add("page-enter-active");
    });
    timerRef.current = setTimeout(() => {
      root.classList.remove("page-enter", "page-enter-active");
    }, TRANSITION_DURATION);
    prevPathRef.current = pathname;
  }, [pathname]);

  return null;
}
