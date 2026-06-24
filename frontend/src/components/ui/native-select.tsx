"use client";

import { ChevronDown } from "lucide-react";
import * as React from "react";
import { cn } from "@/lib/utils";

export interface NativeSelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  containerClassName?: string;
}

/**
 * A styled native select element with consistent arrow positioning.
 * Use this for simple select dropdowns that don't need complex features.
 * For advanced features, use the Select component from @base-ui.
 */
const NativeSelect = React.forwardRef<HTMLSelectElement, NativeSelectProps>(
  ({ className, containerClassName, children, disabled, ...props }, ref) => {
    return (
      <div className={cn("relative", containerClassName)}>
        <select
          ref={ref}
          disabled={disabled}
          className={cn(
            "h-9 w-full appearance-none rounded-lg border border-border bg-transparent pl-3 pr-10 text-sm outline-none transition-colors",
            "focus-visible:ring-[1.5px] focus-visible:ring-ring/30",
            "disabled:cursor-not-allowed disabled:opacity-50",
            className,
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDown
          className={cn(
            "pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground",
            disabled && "opacity-50",
          )}
        />
      </div>
    );
  },
);
NativeSelect.displayName = "NativeSelect";

export { NativeSelect };
