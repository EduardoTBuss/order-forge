import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE, getPublicOrigin } from "../config";
import { DEV_USER, encodeSession } from "../session";

// Dev stub login: immediately "sign in" the fake workshop user by setting the
// session cookie, then redirect back to where the user came from. No identity
// provider, no password — this is intentional for the workshop template.
export function handleLogin(request: NextRequest): NextResponse {
  const returnTo = request.nextUrl.searchParams.get("next") || "/";
  const target = new URL(returnTo, getPublicOrigin(request));

  const response = NextResponse.redirect(target);
  response.cookies.set(AUTH_COOKIE, encodeSession(DEV_USER), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    // 7 days
    maxAge: 60 * 60 * 24 * 7,
  });
  return response;
}
