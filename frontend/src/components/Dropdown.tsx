"use client";
import { useCallback, useEffect, useRef, useState } from "react";

type Align = "left" | "right";

export default function Dropdown({
  trigger,
  triggerClassName,
  align = "left",
  children,
  triggerAriaLabel,
  triggerVariant = "default",
}: {
  trigger: React.ReactNode;
  triggerClassName?: string;
  align?: Align;
  children: React.ReactNode;
  triggerAriaLabel?: string;
  triggerVariant?: "default" | "icon";
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const hoverCloseTimerRef = useRef<number | null>(null);

  const openWithAnimation = useCallback(() => {
    setOpen(true);
    const menu = menuRef.current;
    if (!menu) return;
    try {
      menu.animate(
        [
          { opacity: 0, transform: "translateY(6px) scale(0.96)" },
          { opacity: 1, transform: "translateY(0) scale(1)" },
        ],
        {
          duration: 200,
          easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          fill: "forwards",
        },
      );
    } catch {}
  }, []);

  const closeWithAnimation = useCallback(() => {
    const menu = menuRef.current;
    if (!menu) {
      setOpen(false);
      return;
    }
    let finished = false;
    try {
      const anim = menu.animate(
        [
          { opacity: 1, transform: "translateY(0) scale(1)" },
          { opacity: 0, transform: "translateY(4px) scale(0.97)" },
        ],
        {
          duration: 150,
          easing: "cubic-bezier(0.64, 0, 0.78, 0)",
          fill: "forwards",
        },
      );
      anim.onfinish = () => {
        finished = true;
        setOpen(false);
      };
    } catch {}
    // Fallback in case WAAPI not supported
    window.setTimeout(() => {
      if (!finished) setOpen(false);
    }, 160);
  }, []);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!open) return;
      const root = rootRef.current;
      if (!root) return;
      if (!root.contains(e.target as Node)) {
        closeWithAnimation();
      }
    }
    function onKey(e: KeyboardEvent) {
      if (!open) return;
      if (e.key === "Escape") closeWithAnimation();
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
      if (hoverCloseTimerRef.current) {
        window.clearTimeout(hoverCloseTimerRef.current);
        hoverCloseTimerRef.current = null;
      }
    };
  }, [open, closeWithAnimation]);

  function onTriggerClick() {
    if (open) closeWithAnimation();
    else openWithAnimation();
  }

  const alignClass = align === "right" ? "right-0" : "left-0";

  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: Hover handlers on wrapper provide mouse UX while button inside handles keyboard accessibility
    <div
      ref={rootRef}
      className={["relative", open ? "is-open" : ""].filter(Boolean).join(" ")}
      onMouseEnter={() => {
        if (hoverCloseTimerRef.current) {
          window.clearTimeout(hoverCloseTimerRef.current);
          hoverCloseTimerRef.current = null;
        }
      }}
      onMouseLeave={() => {
        if (!open) return;
        if (hoverCloseTimerRef.current)
          window.clearTimeout(hoverCloseTimerRef.current);
        hoverCloseTimerRef.current = window.setTimeout(() => {
          closeWithAnimation();
          hoverCloseTimerRef.current = null;
        }, 150);
      }}
    >
      <button
        type="button"
        onClick={onTriggerClick}
        className={[
          "transition-colors duration-150 font-normal",
          triggerVariant === "icon"
            ? "inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-foreground hover:bg-primary/10 hover:border-primary/30 cursor-pointer"
            : "px-3 py-2 rounded-lg hover:bg-primary/10 cursor-pointer",
          open && triggerVariant !== "icon" ? "bg-primary/5" : "",
          triggerClassName,
        ]
          .filter(Boolean)
          .join(" ")}
        aria-label={triggerAriaLabel}
        aria-expanded={open}
        aria-haspopup="true"
      >
        {trigger}
      </button>
      <div
        ref={menuRef}
        className={[
          "absolute mt-2 min-w-44 rounded-xl border border-border bg-card p-1.5 shadow-lg anim-menu origin-top z-50 text-[0.9375rem] font-normal",
          alignClass,
        ].join(" ")}
        role="menu"
      >
        {children}
      </div>
    </div>
  );
}
