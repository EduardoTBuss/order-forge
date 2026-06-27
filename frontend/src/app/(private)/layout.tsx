import Link from "next/link";
import { requireSession } from "@/auth/session";
import { getTranslator } from "@/i18n/server";

// `(private)` reads cookies and verifies the session at request time, so it
// can never be meaningfully prerendered. Forcing dynamic opts the whole
// subtree out of static export, which matches the semantics of an auth-gated
// section and avoids Next 16's `/_global-error` prerender bug.
export const dynamic = "force-dynamic";

export default async function PrivateLayout({
	children,
}: {
	children: React.ReactNode;
}) {
	await requireSession();
	const commonT = await getTranslator("common");
	const appName = `${commonT("projectName")} - ${commonT("clientName")}`;

	return (
		<div className="flex min-h-screen flex-col">
			<header className="border-b bg-background/80 backdrop-blur sticky top-0 z-40">
				<nav className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
					<Link href="/home" className="font-semibold tracking-tight">
						{appName}
					</Link>
					<div className="flex items-center gap-4 text-sm">
						<Link
							href="/home"
							className="text-muted-foreground hover:text-foreground"
						>
							Home
						</Link>
						<Link
							href="/order-intake"
							className="text-muted-foreground hover:text-foreground"
						>
							Order Intake
						</Link>
						<Link
							href="/info"
							className="text-muted-foreground hover:text-foreground"
						>
							Info
						</Link>
						<a
							href="/api/auth/logout"
							className="text-muted-foreground hover:text-foreground"
						>
							Logout
						</a>
					</div>
				</nav>
			</header>
			<main className="mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
				{children}
			</main>
		</div>
	);
}
