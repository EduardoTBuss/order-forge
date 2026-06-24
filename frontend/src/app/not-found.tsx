import { FileQuestion } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui";
import { getTranslator } from "@/i18n/server";

export default async function NotFound() {
  const t = await getTranslator("notFound");

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 text-center bg-background">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <FileQuestion className="h-8 w-8 text-muted-foreground" />
      </div>
      <h1 className="mb-2 text-2xl font-semibold text-foreground">
        {t("title")}
      </h1>
      <p className="mb-6 max-w-md text-muted-foreground">{t("description")}</p>
      <Link href="/">
        <Button variant="default">{t("goHome")}</Button>
      </Link>
    </div>
  );
}
