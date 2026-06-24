import { createClient } from "@hey-api/openapi-ts";
import { z } from "zod";

const urlSchema = z.url().transform((url) => url.toString().replace(/\/$/, ""));

const backendUrl = urlSchema.parse(process.env.BACKEND_API_URL);
await createClient({
  input: `${backendUrl}/openapi.json`,
  output: "src/lib/backend/generated",
  plugins: [
    "@hey-api/client-fetch",
    {
      name: "@hey-api/sdk",
      operations: { strategy: "single" },
      validator: { request: "zod" },
    },
  ],
});
