"use client";

import { useEffect, useRef, useState } from "react";

interface AnimatedBackgroundProps {
  children: React.ReactNode;
  className?: string;
}

interface ImageDimensions {
  width: number;
  height: number;
}

export default function AnimatedBackground({
  children,
  className = "",
}: AnimatedBackgroundProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [imageDimensions, setImageDimensions] =
    useState<ImageDimensions | null>(null);

  // Load image dimensions on mount
  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const bgImageDiv = element.querySelector(
      '[style*="background-image"]',
    ) as HTMLElement;
    if (!bgImageDiv) return;

    // Extract image URL from inline styles
    const bgImageUrl = bgImageDiv.style.backgroundImage.match(
      /url\(['"]?([^'"]+)['"]?\)/,
    )?.[1];
    if (bgImageUrl) {
      const img = new Image();
      img.onload = () => {
        setImageDimensions({
          width: img.naturalWidth,
          height: img.naturalHeight,
        });
      };
      img.src = bgImageUrl;
    }
  }, []);

  // Calculate background size and setup CSS transition animation
  useEffect(() => {
    const element = ref.current;
    if (!element || !imageDimensions) return;

    const bgImageDiv = element.querySelector(
      '[style*="background-image"]',
    ) as HTMLElement;
    if (!bgImageDiv) return;

    const calculateBackgroundSize = (zoomFactor = 1) => {
      const containerHeight = element.offsetHeight;
      if (containerHeight === 0) return null;

      // Calculate scale factor: containerHeight / imageHeight
      const scaleFactor = containerHeight / imageDimensions.height;
      // Calculate scaled width: imageWidth * scaleFactor * zoomFactor
      const scaledWidth = imageDimensions.width * scaleFactor * zoomFactor;

      return `${scaledWidth}px auto`;
    };

    // Set initial background properties
    bgImageDiv.style.backgroundRepeat = "no-repeat";
    bgImageDiv.style.backgroundPosition = "center center";

    // Calculate sizes
    const startSize = calculateBackgroundSize(1); // 100%
    if (!startSize) return;

    const endSize = calculateBackgroundSize(1.05); // 105%
    if (!endSize) return;

    // Set initial size (100%)
    bgImageDiv.style.backgroundSize = startSize;

    // Set CSS transition for smooth animation
    bgImageDiv.style.transition =
      "background-size 12s cubic-bezier(0.4, 0, 0.2, 1)";

    // Trigger animation after 100ms delay
    const animationTimeout = setTimeout(() => {
      bgImageDiv.style.backgroundSize = endSize; // 105%
    }, 100);

    // Handle window resize - recalculate without animation
    const handleResize = () => {
      const newStartSize = calculateBackgroundSize(1);
      const newEndSize = calculateBackgroundSize(1.05);

      if (!newStartSize || !newEndSize) return;

      // Temporarily disable transition
      bgImageDiv.style.transition = "none";

      // Update to current end size (maintain zoom state)
      bgImageDiv.style.backgroundSize = newEndSize;

      // Re-enable transition after a brief moment
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          bgImageDiv.style.transition =
            "background-size 12s cubic-bezier(0.4, 0, 0.2, 1)";
        });
      });
    };

    window.addEventListener("resize", handleResize);

    return () => {
      clearTimeout(animationTimeout);
      window.removeEventListener("resize", handleResize);
    };
  }, [imageDimensions]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}
