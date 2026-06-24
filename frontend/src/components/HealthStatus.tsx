"use client";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { backend } from "@/lib/backend";
import type { ServerHealthOutput } from "@/lib/backend/generated";

type HealthResponse = {
  ok: boolean;
  status?: number;
  data?: ServerHealthOutput;
  error?: string;
};

export default function HealthStatus({ backendUrl }: { backendUrl: string }) {
  const [loading, setLoading] = useState(true);
  const [resp, setResp] = useState<HealthResponse | null>(null);
  const t = useTranslations("healthStatus");

  useEffect(() => {
    let mounted = true;
    async function run() {
      setLoading(true);
      try {
        const { data } = await backend.info.healthCheck({
          throwOnError: true,
        });
        if (mounted) setResp({ ok: true, status: 200, data });
      } catch (e) {
        if (mounted) {
          setResp({
            ok: false,
            error: e instanceof Error ? e.message : "fetch_failed",
          });
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    run();
    const t = setInterval(run, 15000);
    return () => {
      mounted = false;
      clearInterval(t);
    };
  }, []);

  const isLive = resp?.ok === true;

  return (
    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
      <div className="text-xs sm:text-sm text-muted-foreground">
        {t.rich("connected", {
          url: (chunks) => (
            <code className="font-mono text-foreground bg-muted/50 px-1.5 py-0.5 rounded text-xs">
              {chunks}
            </code>
          ),
          address: backendUrl,
        })}
      </div>
      {loading ? (
        <div className="flex items-center gap-1.5 text-xs sm:text-sm text-muted-foreground">
          <span className="inline-block h-2 w-2 rounded-full bg-muted-foreground/40 anim-pulse" />
          {t("checking")}
        </div>
      ) : isLive ? (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-green-500/15 px-2.5 py-1 text-xs font-medium text-green-600 dark:text-green-400 transition-colors duration-200">
          <span className="status-dot status-dot-success" />
          {t("live")}
        </span>
      ) : (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-medium text-red-600 dark:text-red-400 transition-colors duration-200">
          <span className="status-dot status-dot-error" />
          {t("down")}
        </span>
      )}
    </div>
  );
}
