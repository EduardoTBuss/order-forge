"use client";

import { Toast as ToastPrimitive } from "@base-ui/react/toast";
import {
  AlertTriangleIcon,
  CheckCircle2Icon,
  InfoIcon,
  XCircleIcon,
  XIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

type ToastType = "success" | "error" | "warning" | "info";

interface ToastOptions {
  id?: string;
}

export const toastManager = ToastPrimitive.createToastManager();

function addToast(
  type: ToastType,
  title: string,
  description?: string,
  options?: ToastOptions,
): string {
  return toastManager.add({ type, title, description, ...options });
}

export const toast = {
  success: (title: string, description?: string, options?: ToastOptions) =>
    addToast("success", title, description, options),
  error: (title: string, description?: string, options?: ToastOptions) =>
    addToast("error", title, description, options),
  warning: (title: string, description?: string, options?: ToastOptions) =>
    addToast("warning", title, description, options),
  info: (title: string, description?: string, options?: ToastOptions) =>
    addToast("info", title, description, options),
  dismiss: (id?: string) => toastManager.close(id),
};

const TYPE_ICONS: Record<
  ToastType,
  React.ComponentType<{ className?: string }>
> = {
  success: CheckCircle2Icon,
  error: XCircleIcon,
  warning: AlertTriangleIcon,
  info: InfoIcon,
};

function ToastIcon({ type }: { type: string | undefined }) {
  const Icon =
    type && type in TYPE_ICONS ? TYPE_ICONS[type as ToastType] : null;
  if (!Icon) return null;
  const tone =
    type === "success"
      ? "text-emerald-500"
      : type === "error"
        ? "text-red-500"
        : type === "warning"
          ? "text-amber-500"
          : "text-sky-500";
  return <Icon className={cn("size-4 shrink-0 mt-0.5", tone)} />;
}

function ToastList() {
  const { toasts } = ToastPrimitive.useToastManager();
  return toasts.map((t) => (
    <ToastPrimitive.Root
      key={t.id}
      toast={t}
      className={cn(
        "absolute right-0 bottom-0 w-full p-4 pr-10",
        "rounded-xl bg-background text-foreground text-sm ring-2 ring-foreground/10 shadow-lg",
        "transition-[opacity,transform] duration-200",
        "data-starting-style:opacity-0 data-ending-style:opacity-0",
        "data-[type=success]:ring-emerald-500/30 data-[type=success]:bg-emerald-50",
        "data-[type=error]:ring-red-500/30 data-[type=error]:bg-red-50",
        "data-[type=warning]:ring-amber-500/30 data-[type=warning]:bg-amber-50",
        "data-[type=info]:ring-sky-500/30 data-[type=info]:bg-sky-50",
      )}
      style={{
        zIndex: "calc(1000 - var(--toast-index))",
        transform:
          "translateX(var(--toast-swipe-movement-x)) translateY(calc(var(--toast-index) * -20% + var(--toast-swipe-movement-y))) scale(calc(1 - var(--toast-index) * 0.05))",
      }}
    >
      <ToastPrimitive.Content className="flex items-start gap-3">
        <ToastIcon type={t.type} />
        <div className="flex flex-col gap-0.5 min-w-0 flex-1">
          <ToastPrimitive.Title className="font-medium text-foreground empty:hidden" />
          <ToastPrimitive.Description className="text-muted-foreground text-sm leading-snug wrap-break-word empty:hidden" />
        </div>
      </ToastPrimitive.Content>
      <ToastPrimitive.Close
        aria-label="Close"
        className="absolute top-2 right-2 inline-flex size-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
      >
        <XIcon className="size-4" />
      </ToastPrimitive.Close>
    </ToastPrimitive.Root>
  ));
}

export function Toaster({ children }: { children?: React.ReactNode }) {
  return (
    <ToastPrimitive.Provider toastManager={toastManager}>
      {children}
      <ToastPrimitive.Portal>
        <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-100 w-88 max-w-[calc(100vw-2rem)]">
          <ToastList />
        </ToastPrimitive.Viewport>
      </ToastPrimitive.Portal>
    </ToastPrimitive.Provider>
  );
}
