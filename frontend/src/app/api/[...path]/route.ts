import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE } from "@/auth/config";
import { env } from "@/env";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type NodeRequestInit = RequestInit & { duplex?: "half" };
const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);

async function handle(request: NextRequest): Promise<NextResponse> {
  console.info("[API PROXY] incoming", {
    method: request.method,
    path: request.nextUrl.pathname,
    search: request.nextUrl.search,
  });
  // Dev stub: require the session cookie's presence (set by /api/auth/login).
  // No token is cryptographically verified — see auth/session.ts.
  const idToken = request.cookies.get(AUTH_COOKIE)?.value;
  if (!idToken) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  // Remove the /api/ prefix from the path.
  const relativePath = request.nextUrl.pathname.replace(/^\/api\//, "");
  const query = request.nextUrl.search;

  const targetUrl = relativePath
    ? `${env.BACKEND_API_URL}/${relativePath}${query}`
    : `${env.BACKEND_API_URL}${query}`;

  const incomingHeaders = new Headers(request.headers);
  // Remove hop-by-hop and sensitive headers
  [
    "host",
    "connection",
    "content-length",
    "accept-encoding",
    "x-forwarded-for",
    "x-forwarded-host",
    "x-forwarded-proto",
    "cookie",
  ].forEach((h) => void incomingHeaders.delete(h));

  // Match FastAPI HTTPBearer: Authorization: Bearer <token>
  incomingHeaders.set("Authorization", `Bearer ${env.BACKEND_API_KEY}`);

  const isBodyMethod = !["GET", "HEAD"].includes(request.method);
  const body = isBodyMethod
    ? (request.body as ReadableStream | null)
    : undefined;

  const init: NodeRequestInit = {
    method: request.method,
    headers: incomingHeaders,
    body,
    redirect: "manual",
  };
  if (body) {
    init.duplex = "half";
  }

  let proxyResponse: Response;
  try {
    proxyResponse = await fetchUpstream(targetUrl, init);
  } catch (error) {
    // Network/Fetch-level error before reaching FastAPI
    console.error("[API PROXY] Upstream fetch failed", {
      method: request.method,
      url: targetUrl,
      error: error instanceof Error ? error.message : String(error),
    });
    return NextResponse.json(
      { error: "Upstream request failed" },
      { status: 502 },
    );
  }

  if (!proxyResponse.ok) {
    // Safely read a clone of the body for logging without consuming the stream
    let bodyPreview = "";
    try {
      bodyPreview = await proxyResponse.clone().text();
      // Truncate to avoid massive logs
      const MAX_LEN = 4000;
      if (bodyPreview.length > MAX_LEN) {
        bodyPreview = `${bodyPreview.slice(0, MAX_LEN)}…[truncated]`;
      }
    } catch {
      bodyPreview = "<unreadable body>";
    }

    console.error("[API PROXY] Upstream returned error", {
      method: request.method,
      url: targetUrl,
      status: proxyResponse.status,
      body: bodyPreview,
    });
  }

  const responseHeaders = new Headers(proxyResponse.headers);
  // Strip hop-by-hop headers from the response as well
  [
    "transfer-encoding",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "upgrade",
  ].forEach((h) => {
    responseHeaders.delete(h);
  });

  return new NextResponse(proxyResponse.body, {
    status: proxyResponse.status,
    headers: responseHeaders,
  });
}

async function fetchUpstream(
  url: string,
  init: NodeRequestInit,
): Promise<Response> {
  let currentUrl = url;
  const method = (init.method ?? "GET").toUpperCase();
  const canRetry = !init.body && (method === "GET" || method === "HEAD");
  let response = await fetch(currentUrl, init as RequestInit);
  if (!canRetry) {
    return response;
  }

  // Only follow redirects that stay on the backend's own origin. The request
  // carries `Authorization: Bearer ${BACKEND_API_KEY}`, and reusing `init`
  // across an off-origin redirect would leak that backend credential to an
  // arbitrary host (unlike the browser Fetch spec, manual following does not
  // strip Authorization on cross-origin hops). Refuse to follow off-origin.
  const backendOrigin = new URL(env.BACKEND_API_URL).origin;
  let redirects = 0;
  while (REDIRECT_STATUSES.has(response.status) && redirects < 5) {
    const location = response.headers.get("location");
    if (!location) {
      break;
    }
    const nextUrl = new URL(location, currentUrl);
    if (nextUrl.origin !== backendOrigin) {
      console.warn("[API PROXY] Refusing off-origin upstream redirect", {
        status: response.status,
        from: currentUrl,
        to: nextUrl.origin,
      });
      break;
    }
    console.warn("[API PROXY] Upstream redirect", {
      status: response.status,
      from: currentUrl,
      to: location,
      count: redirects + 1,
    });
    currentUrl = nextUrl.toString();
    response = await fetch(currentUrl, init as RequestInit);
    redirects += 1;
  }

  if (REDIRECT_STATUSES.has(response.status)) {
    console.warn("[API PROXY] Upstream redirect limit reached", {
      method: init.method,
      url: currentUrl,
      status: response.status,
      redirects,
    });
  }

  return response;
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  return handle(request);
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  return handle(request);
}

export async function PUT(request: NextRequest): Promise<NextResponse> {
  return handle(request);
}

export async function PATCH(request: NextRequest): Promise<NextResponse> {
  return handle(request);
}

export async function DELETE(request: NextRequest): Promise<NextResponse> {
  return handle(request);
}

export async function OPTIONS(request: NextRequest): Promise<NextResponse> {
  return handle(request);
}
