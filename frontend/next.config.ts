import type { NextConfig } from "next";
import nextIntlPlugin from "next-intl/plugin";

import "./src/env"; // Validate environment variables at build time

const withNextIntl = nextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // Azure App Service
  output: "standalone",
  poweredByHeader: false, // Disable x-powered-by header for security
  compress: false, // Compression is handled by Azure
  // Dev utils
  skipTrailingSlashRedirect: true,
  devIndicators: { position: "bottom-right" },
  // Dependencies
  transpilePackages: ["@t3-oss/env-nextjs", "@t3-oss/env-core"],
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "@base-ui/react",
      "date-fns",
      "framer-motion",
      "cmdk",
    ],
  },
};

export default withNextIntl(nextConfig);
