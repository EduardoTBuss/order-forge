"use client";

interface CardSkeletonProps {
  /** Show header section */
  hasHeader?: boolean;
  /** Number of content lines to show */
  lines?: number;
  /** Custom className for the container */
  className?: string;
}

export function CardSkeleton({
  hasHeader = true,
  lines = 3,
  className = "",
}: CardSkeletonProps) {
  return (
    // biome-ignore lint/a11y/useSemanticElements: role="status" is appropriate for loading indicators
    <div
      className={[
        "animate-pulse rounded-xl border border-border bg-card p-6",
        className,
      ].join(" ")}
      role="status"
      aria-label="Loading content"
    >
      {hasHeader && (
        <div className="mb-4 space-y-2">
          <div className="h-5 w-1/3 rounded bg-muted" />
          <div className="h-3 w-2/3 rounded bg-muted/60" />
        </div>
      )}
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div // biome-ignore lint/suspicious/noArrayIndexKey: Static skeleton placeholders
            key={i}
            className="h-4 rounded bg-muted"
            style={{ width: `${100 - i * 15}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export default CardSkeleton;
