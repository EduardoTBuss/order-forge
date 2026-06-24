"use client";

import { usePathname, useSearchParams } from "next/navigation";
import type React from "react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { LoadingScreen } from "@/components/LoadingScreen";

interface NavigationLoadingContextType {
  isLoading: boolean;
  startLoading: () => void;
  stopLoading: () => void;
}

const NavigationLoadingContext = createContext<
  NavigationLoadingContextType | undefined
>(undefined);

export function NavigationLoadingProvider({
  children,
}: {
  children: React.ReactNode;
}): React.ReactNode {
  const [isLoading, setIsLoading] = useState(false);
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const previousPathRef = useRef(pathname);
  const previousSearchRef = useRef(searchParams.toString());

  const startLoading = useCallback(() => {
    setIsLoading(true);
  }, []);

  const stopLoading = useCallback(() => {
    setIsLoading(false);
  }, []);

  // Stop loading when navigation completes (pathname or searchParams change)
  useEffect(() => {
    const currentPath = pathname;
    const currentSearch = searchParams.toString();

    // Check if the route actually changed
    if (
      previousPathRef.current !== currentPath ||
      previousSearchRef.current !== currentSearch
    ) {
      // Navigation completed, stop loading after a small delay
      const timeout = setTimeout(() => {
        setIsLoading(false);
      }, 50);

      previousPathRef.current = currentPath;
      previousSearchRef.current = currentSearch;

      return () => clearTimeout(timeout);
    }
  }, [pathname, searchParams]);

  // Intercept link clicks to show loading screen
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest("a");

      if (!link) return;

      // Skip download links
      if (link.hasAttribute("download")) return;

      // Skip if it's an external link
      const href = link.getAttribute("href");
      if (
        !href ||
        href.startsWith("http") ||
        href.startsWith("#") ||
        href.startsWith("mailto:")
      ) {
        return;
      }

      // Skip if modifier keys are pressed (open in new tab, etc.)
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button !== 0) {
        return;
      }

      // Skip if the link has target="_blank"
      if (link.target === "_blank") {
        return;
      }

      // Skip if navigation is to the same page
      const currentPath = window.location.pathname;
      const linkPath = href.split("?")[0].split("#")[0];
      if (
        linkPath === currentPath ||
        (linkPath === "/" && currentPath === "/")
      ) {
        // Check if only hash or search params change
        if (
          !href.includes("?") ||
          window.location.search === href.split("?")[1]
        ) {
          return;
        }
      }

      // Show loading screen
      setIsLoading(true);
    };

    // Add listener to document for all link clicks
    document.addEventListener("click", handleClick);

    return () => {
      document.removeEventListener("click", handleClick);
    };
  }, []);

  return (
    <NavigationLoadingContext.Provider
      value={{ isLoading, startLoading, stopLoading }}
    >
      <LoadingScreen isLoading={isLoading} minimumDisplayTime={1200} />
      {children}
    </NavigationLoadingContext.Provider>
  );
}

export function useNavigationLoading(): NavigationLoadingContextType {
  const context = useContext(NavigationLoadingContext);
  if (context === undefined) {
    throw new Error(
      "useNavigationLoading must be used within a NavigationLoadingProvider",
    );
  }
  return context;
}
