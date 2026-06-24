import type { NextRequest } from "next/server";

// Name of the cookie that marks a signed-in session. In this workshop template
// it holds a base64-encoded fake user (see session.ts), NOT a real JWT — there
// is no identity provider wired up.
export const AUTH_COOKIE = "id_token";
export const LOGIN_PATH = "/api/auth/login";
export const LOGOUT_PATH = "/api/auth/logout";

const PUBLIC_PATHS = new Set<string>(["/", "/api"]);
const PUBLIC_PREFIXES = ["/api/", "/_next", "/favicon.ico"];
const FILE_EXTENSION_REGEX = /\.[^/]+$/;

export function isPublicPath(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  if (PUBLIC_PREFIXES.some((prefix) => pathname.startsWith(prefix)))
    return true;
  return FILE_EXTENSION_REGEX.test(pathname);
}

export function buildReturnTo(request: NextRequest): string {
  const { pathname, search } = request.nextUrl;
  return `${pathname}${search || ""}`;
}

export function getPublicOrigin(request: NextRequest): string {
  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto = request.headers.get("x-forwarded-proto") || "https";
  if (forwardedHost) {
    // Handle multiple hosts in x-forwarded-host if present
    const host = forwardedHost.split(",")[0].trim();
    return `${forwardedProto}://${host}`;
  }
  return request.nextUrl.origin;
}

export function buildLoginRedirect(request: NextRequest): URL {
  const origin = getPublicOrigin(request);
  const loginUrl = new URL(LOGIN_PATH, origin);
  loginUrl.searchParams.set("next", buildReturnTo(request));
  return loginUrl;
}

export function getPostLogoutRedirect(request: NextRequest): string {
  return `${getPublicOrigin(request)}/`;
}
