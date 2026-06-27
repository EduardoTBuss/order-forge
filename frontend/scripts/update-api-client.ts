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
      // Request-side zod validation is disabled: @hey-api/openapi-ts maps an
      // OpenAPI binary body (`type: string, format: binary`, e.g. a FastAPI
      // `UploadFile`) to `z.string()`, so it rejects a real `File`/`Blob` before
      // the request is sent — which breaks every file upload (the core workshop
      // action). The backend validates all input authoritatively via Pydantic,
      // so the client-side request validator is redundant here.
      validator: false,
    },
  ],
});
