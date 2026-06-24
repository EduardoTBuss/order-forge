import type { Metadata, Viewport } from "next";
import { Outfit } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Suspense } from "react";
import "./globals.css";
import { NavigationLoadingProvider } from "@/components/NavigationLoadingProvider";
import PageTransition from "@/components/PageTransition";
import { Toaster } from "@/components/ui/toast";
import { getLocaleMessages, getTranslator } from "@/i18n/server";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  display: "swap",
  weight: ["300", "400", "500", "600", "700"],
});

export async function generateMetadata(): Promise<Metadata> {
  const [metadataT, commonT] = await Promise.all([
    getTranslator("metadata"),
    getTranslator("common"),
  ]);
  const appName = `${commonT("projectName")} - ${commonT("clientName")}`;
  return {
    title: appName,
    description: metadataT("description"),
    applicationName: appName,
    manifest: "/manifest.webmanifest",
    icons: {
      icon: [
        { url: "/favicon.ico", type: "image/x-icon" },
        { url: "/icon_192.png", type: "image/png", sizes: "192x192" },
        { url: "/icon_512.png", type: "image/png", sizes: "512x512" },
      ],
      shortcut: "/favicon.ico",
      apple: [
        { url: "/icon_180.png" },
        { url: "/icon_180.png", sizes: "180x180" },
      ],
    },
    appleWebApp: {
      capable: true,
      statusBarStyle: "default",
      title: appName,
    },
  };
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
  ],
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { locale, messages } = await getLocaleMessages();
  setRequestLocale(locale);

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={`${outfit.variable} ${outfit.className} antialiased`}>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <Toaster>
            <Suspense fallback={null}>
              <NavigationLoadingProvider>
                <div
                  id="page-transition-root"
                  className="page-enter min-h-screen"
                >
                  {children}
                </div>
                <PageTransition />
              </NavigationLoadingProvider>
            </Suspense>
          </Toaster>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
