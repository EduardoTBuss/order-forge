import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { NextRequest } from "next/server";
import { AUTH_COOKIE, LOGIN_PATH } from "./config";

// ---------------------------------------------------------------------------
// Workshop dev-stub authentication.
//
// This template ships WITHOUT a real identity provider. A "session" is just a
// cookie holding a base64-encoded fake user. The login route sets it, the
// logout route clears it, and the proxy guard (auth/proxy.ts) checks for it.
// The full login -> cookie -> protected-route -> logout flow is preserved so
// the pattern is teachable; only the Azure AD / MSAL backend is gone.
//
// Replace this with a real provider (MSAL, Auth.js, Clerk, ...) when taking
// the app beyond the workshop.
// ---------------------------------------------------------------------------

export type AuthSession = {
  sub: string;
  name?: string;
  email?: string;
};

export const DEV_USER: AuthSession = {
  sub: "dev-user",
  name: "Workshop User",
  email: "dev@example.com",
};

export function encodeSession(session: AuthSession): string {
  return Buffer.from(JSON.stringify(session), "utf-8").toString("base64url");
}

function decodeSession(value: string | undefined): AuthSession | null {
  if (!value) return null;
  try {
    const json = Buffer.from(value, "base64url").toString("utf-8");
    const parsed = JSON.parse(json) as Partial<AuthSession>;
    if (typeof parsed.sub !== "string") return null;
    return {
      sub: parsed.sub,
      name: typeof parsed.name === "string" ? parsed.name : undefined,
      email: typeof parsed.email === "string" ? parsed.email : undefined,
    };
  } catch {
    return null;
  }
}

export async function getSessionOrNull(): Promise<AuthSession | null> {
  const cookieStore = await cookies();
  return decodeSession(cookieStore.get(AUTH_COOKIE)?.value);
}

export async function requireSession(): Promise<AuthSession> {
  const session = await getSessionOrNull();
  if (!session) {
    redirect(LOGIN_PATH);
  }
  return session;
}

export function readSessionFromRequest(
  request: NextRequest,
): AuthSession | null {
  return decodeSession(request.cookies.get(AUTH_COOKIE)?.value);
}
