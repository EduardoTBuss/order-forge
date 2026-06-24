import type { MetadataRoute } from "next";

import {
  DEFAULT_DESCRIPTION,
  DEFAULT_DISPLAY_NAME,
  DEFAULT_PROJECT_NAME,
} from "@/config/app-identity";

const APP_NAME = DEFAULT_DISPLAY_NAME;
const APP_SHORT_NAME = DEFAULT_PROJECT_NAME;
const APP_DESCRIPTION = DEFAULT_DESCRIPTION;

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: APP_NAME,
    short_name: APP_SHORT_NAME,
    description: APP_DESCRIPTION,
    start_url: "/",
    display: "standalone",
    background_color: "#0a0a0a",
    theme_color: "#0031ff",
    icons: [
      {
        src: "/icon_192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon_512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
