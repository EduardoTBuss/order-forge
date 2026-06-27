import { notFound } from "next/navigation";
import { requireSession } from "@/auth/session";
import ReconciliationClient from "@/components/order-intake/ReconciliationClient";

export default async function OrderDetailPage({
	params,
}: {
	params: Promise<{ id: string }>;
}) {
	await requireSession();
	const { id } = await params;
	const orderId = Number(id);
	if (!Number.isInteger(orderId) || orderId <= 0) {
		notFound();
	}
	return <ReconciliationClient orderId={orderId} />;
}
