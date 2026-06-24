import { type NextRequest, type NextResponse } from "next/server";
import { handleLogout } from "@/auth/routes/logout";

export const runtime = "nodejs";

export async function GET(request: NextRequest): Promise<NextResponse> {
  return handleLogout(request);
}
