export default function Loading() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        {/* Loading dots */}
        <div className="flex gap-1">
          <span
            className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-pulse"
            style={{ animationDelay: "0ms" }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-pulse"
            style={{ animationDelay: "200ms" }}
          />
          <span
            className="w-1.5 h-1.5 rounded-full bg-primary/60 animate-pulse"
            style={{ animationDelay: "400ms" }}
          />
        </div>
      </div>
    </div>
  );
}
