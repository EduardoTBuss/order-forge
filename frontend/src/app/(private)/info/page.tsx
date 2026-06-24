import { BookOpen } from "lucide-react";
import { UI } from "@/components/ui";
import { getTranslator } from "@/i18n/server";

interface ModuleInfo {
  code: string;
  description: string;
}

const MODULES: ModuleInfo[] = [
  {
    code: "postgresql",
    description: "CRUD operations for relational data.",
  },
  {
    code: "cosmosdb",
    description: "Document storage with auto-create collections.",
  },
  {
    code: "blob-storage",
    description: "File upload and download with SAS tokens.",
  },
  {
    code: "info",
    description: "Health checks and service metadata.",
  },
];

export default async function InfoPage() {
  const commonT = await getTranslator("common");
  const appName = `${commonT("projectName")} - ${commonT("clientName")}`;

  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-balance flex items-center gap-3">
          <div className="size-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0">
            <BookOpen className="size-5 text-primary" />
          </div>
          <span>{appName}</span>
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl">
          This workshop starter ships with a running backend and a minimal
          frontend shell. The features are yours to build.
        </p>
      </div>

      <UI.Card className="animate-fade-in-up">
        <UI.CardHeader>
          <UI.CardTitle className="text-lg">Available backend modules</UI.CardTitle>
          <UI.CardDescription>
            These API modules are ready to call through the generated SDK.
          </UI.CardDescription>
        </UI.CardHeader>
        <UI.CardContent>
          <ul className="space-y-3 text-sm">
            {MODULES.map((mod) => (
              <li key={mod.code} className="flex gap-2">
                <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono shrink-0">
                  {mod.code}
                </code>
                <span className="text-muted-foreground">{mod.description}</span>
              </li>
            ))}
          </ul>
        </UI.CardContent>
      </UI.Card>
    </div>
  );
}
