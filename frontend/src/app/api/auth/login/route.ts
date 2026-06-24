import { type NextRequest, type NextResponse } from "next/server";
import { handleLogin } from "@/auth/routes/login";

export const runtime = "nodejs";

export async function GET(request: NextRequest): Promise<NextResponse> {
  return handleLogin(request);
}
