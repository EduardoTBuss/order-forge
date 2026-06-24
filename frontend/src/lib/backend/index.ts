import { HttpError } from "@/lib/utils";
import { createClient } from "./generated/client";
import { Sdk } from "./generated/sdk.gen";

const client = createClient({
  baseUrl: "/api",
});

client.interceptors.response.use(async (res, req) => {
  if (res.status >= 400) {
    // Read the response body to get the error detail before throwing
    let errorBody: unknown;
    try {
      errorBody = await res.clone().json();
    } catch {
      // If body isn't JSON, try text
      try {
        errorBody = await res.clone().text();
      } catch {
        errorBody = null;
      }
    }
    throw new HttpError(res, req, errorBody);
  }
  return res;
});

export const backendClient = client;
export const backend = new Sdk({ client });
