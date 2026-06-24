import { type NextRequest, NextResponse } from "next/server";
import { LOCALES } from "@/i18n/config";
import { AUTH_COOKIE, buildLoginRedirect, isPublicPath } from "./config";

function stripLocaleFromPathname(pathname: string): string {
  for (const locale of LOCALES) {
    const prefix = `/${locale}`;
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      const remainder = pathname.slice(prefix.length);
      return remainder
        ? remainder.startsWith("/")
          ? remainder
          : `/${remainder}`
        : "/";
    }
  }
  return pathname;
}

export async function proxy(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;
  const normalizedPath = stripLocaleFromPathname(pathname);

  if (normalizedPath.startsWith("/api")) {
    return NextResponse.next();
  }

  if (isPublicPath(normalizedPath)) {
    return NextResponse.next();
  }

  // Dev stub: presence of the session cookie is enough. There is no token to
  // cryptographically verify — see auth/session.ts.
  const idToken = request.cookies.get(AUTH_COOKIE)?.value;
  if (!idToken) {
    return NextResponse.redirect(buildLoginRedirect(request));
  }

  return NextResponse.next();
}
