import HealthStatus from "@/components/HealthStatus";
import { UI } from "@/components/ui";
import { env } from "@/env";
import { getTranslator } from "@/i18n/server";

export default async function PrivateHome() {
  const commonT = await getTranslator("common");
  const appName = `${commonT("projectName")} - ${commonT("clientName")}`;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-balance">
          {appName}
        </h1>
        <p className="text-muted-foreground text-lg">
          A minimal workshop starter — a running FastAPI + Next.js stack with a
          dev auth shell and one example page. Build the rest yourself.
        </p>
        <HealthStatus backendUrl={env.BACKEND_API_URL} />
      </div>

      <UI.Card className="animate-fade-in-up">
        <UI.CardHeader>
          <UI.CardTitle className="text-lg">Getting started</UI.CardTitle>
          <UI.CardDescription>
            The backend exposes the postgresql, cosmosdb, blob-storage, and info
            modules. Use the generated SDK from client components to call them.
          </UI.CardDescription>
        </UI.CardHeader>
        <UI.CardContent>
          <p className="text-muted-foreground text-sm">
            Add your own pages under{" "}
            <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">
              src/app/(private)
            </code>{" "}
            and wire them to the backend through the SDK in{" "}
            <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono">
              src/lib/backend
            </code>
            .
          </p>
        </UI.CardContent>
      </UI.Card>
    </div>
  );
}
