import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function base64FromFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () =>
      resolve((reader.result as string).split(",")[1] ?? "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function formatErrorMessage(error: unknown, fallback: string): string {
  if (!error) return fallback;
  if (typeof error === "string") return error;
  if (error instanceof Error) return error.message || fallback;
  const detail = (error as { detail?: Array<{ msg?: string }> }).detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : null))
      .filter(Boolean);
    if (messages.length > 0) return messages.join(". ");
  }
  return fallback;
}

export class HttpError extends Error {
  public readonly url: string;
  public readonly status: number;
  public readonly statusText: string;
  public readonly body: unknown;
  public readonly detail: string | null;
  public readonly request: Request;

  constructor(response: Response, request: Request, parsedBody?: unknown) {
    // Extract error detail from parsed body if available
    const detail = HttpError.extractDetail(parsedBody);
    const message = detail
      ? `${response.status}: ${detail}`
      : `${response.status} ${response.statusText}`;

    super(message);

    this.name = "ApiError";
    this.url = response.url;
    this.status = response.status;
    this.statusText = response.statusText;
    this.body = parsedBody;
    this.detail = detail;
    this.request = request;
  }

  private static extractDetail(body: unknown): string | null {
    if (!body) return null;
    if (typeof body === "string") return body;
    if (typeof body === "object" && body !== null) {
      // Handle FastAPI error format: { detail: string }
      if ("detail" in body) {
        const detail = (body as { detail: unknown }).detail;
        if (typeof detail === "string") return detail;
        if (typeof detail === "object") return JSON.stringify(detail);
      }
      // Handle other common formats: { message: string }, { error: string }
      if (
        "message" in body &&
        typeof (body as { message: unknown }).message === "string"
      ) {
        return (body as { message: string }).message;
      }
      if (
        "error" in body &&
        typeof (body as { error: unknown }).error === "string"
      ) {
        return (body as { error: string }).error;
      }
    }
    return null;
  }
}
