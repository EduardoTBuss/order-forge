"use client";

import { Check, ChevronDown } from "lucide-react";
import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export interface ComboboxOption {
  value: string;
  label: string;
}

interface ComboboxProps {
  options: ComboboxOption[];
  value?: string;
  onChange: (value: string | undefined) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  className?: string;
  disabled?: boolean;
  /** Allow typing a new value not in the list */
  allowCustomValue?: boolean;
}

export function Combobox({
  options,
  value,
  onChange,
  placeholder = "Select an option...",
  searchPlaceholder = "Search...",
  emptyMessage = "No results found.",
  className,
  disabled = false,
  allowCustomValue = false,
}: ComboboxProps) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");
  const inputRef = React.useRef<HTMLInputElement>(null);

  const selectedOption = options.find((option) => option.value === value);

  // Filter options based on search
  const filteredOptions = React.useMemo(() => {
    if (!search) return options;
    const lower = search.toLowerCase();
    return options.filter((option) =>
      option.label.toLowerCase().includes(lower),
    );
  }, [options, search]);

  const handleSelect = React.useCallback(
    (selectedValue: string) => {
      if (selectedValue === value) {
        onChange(undefined);
      } else {
        onChange(selectedValue);
      }
      setOpen(false);
      setSearch("");
    },
    [value, onChange],
  );

  // Handle creating custom value when allowCustomValue is true
  const handleKeyDown = React.useCallback(
    (e: React.KeyboardEvent) => {
      if (
        allowCustomValue &&
        e.key === "Enter" &&
        search &&
        filteredOptions.length === 0
      ) {
        e.preventDefault();
        onChange(search);
        setOpen(false);
        setSearch("");
      }
      // Close on Escape
      if (e.key === "Escape") {
        setOpen(false);
        setSearch("");
      }
    },
    [allowCustomValue, search, filteredOptions.length, onChange],
  );

  // Focus input when popover opens
  React.useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className={cn("h-10 w-full justify-between", className)}
            disabled={disabled}
          />
        }
      >
        <span className="truncate">
          {selectedOption?.label ?? value ?? placeholder}
        </span>
        <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </PopoverTrigger>
      <PopoverContent
        className="p-0"
        style={{ width: "var(--anchor-width)" }}
        align="start"
      >
        <div className="flex flex-col">
          {/* Search input */}
          <div className="flex items-center border-b px-3">
            <input
              ref={inputRef}
              type="text"
              className="flex h-10 w-full bg-transparent py-3 text-sm placeholder:text-muted-foreground"
              style={{
                outline: "none",
                border: "none",
                boxShadow: "none",
              }}
              placeholder={searchPlaceholder}
              aria-label={searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>

          {/* Options list */}
          <div className="max-h-[300px] overflow-y-auto p-1">
            {filteredOptions.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                {allowCustomValue && search
                  ? `Press Enter to use "${search}"`
                  : emptyMessage}
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={cn(
                    "relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none",
                    "hover:bg-accent hover:text-accent-foreground",
                    "focus:bg-accent focus:text-accent-foreground",
                  )}
                  onClick={() => handleSelect(option.value)}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      value === option.value ? "opacity-100" : "opacity-0",
                    )}
                  />
                  {option.label}
                </button>
              ))
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
