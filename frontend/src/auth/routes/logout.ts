import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE, getPostLogoutRedirect } from "../config";

export function handleLogout(request: NextRequest): NextResponse {
  const response = NextResponse.redirect(getPostLogoutRedirect(request));
  response.cookies.set(AUTH_COOKIE, "", {
    httpOnly: true,
    path: "/",
    maxAge: 0,
  });
  return response;
}
