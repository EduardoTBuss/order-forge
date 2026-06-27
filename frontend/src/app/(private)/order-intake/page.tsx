import { requireSession } from "@/auth/session";
import OrderIntakeClient from "@/components/order-intake/OrderIntakeClient";

export default async function OrderIntakePage() {
	await requireSession();
	return <OrderIntakeClient />;
}
