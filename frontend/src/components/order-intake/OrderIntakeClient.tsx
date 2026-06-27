"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { UI } from "@/components/ui";
import { backend } from "@/lib/backend";
import type {
	CustomerOutput,
	OrderSummaryOutput,
} from "@/lib/backend/generated";
import { HttpError } from "@/lib/utils";

function StatusBadge({ status }: { status: string }) {
	const t = useTranslations("orderIntake");
	const label = t(`status.${status}` as "status.in_review") ?? status;
	const variant =
		status === "edifact_generated"
			? "default"
			: status === "in_review"
				? "secondary"
				: "outline";
	return <UI.Badge variant={variant}>{label}</UI.Badge>;
}

function strategyLabel(
	t: ReturnType<typeof useTranslations>,
	code: string,
): string {
	if (code === "bauprofil_text") return t("strategy.bauprofil_text");
	if (code === "ollama") return t("strategy.ollama");
	if (code === "llm_api") return t("strategy.llm_api");
	return code;
}

function errMsg(e: unknown, fallback: string): string {
	if (e instanceof HttpError) {
		const body = e.body as { detail?: unknown } | undefined;
		if (body && Array.isArray(body.detail)) {
			const msgs = (body.detail as Array<{ msg?: string }>)
				.map((d) => d?.msg)
				.filter((m): m is string => typeof m === "string");
			if (msgs.length) return msgs.join(". ");
		}
		if (e.detail) return e.detail;
	}
	return e instanceof Error ? e.message : fallback;
}

export default function OrderIntakeClient() {
	const t = useTranslations("orderIntake");
	const router = useRouter();
	const fileRef = useRef<HTMLInputElement>(null);

	const [customers, setCustomers] = useState<CustomerOutput[]>([]);
	const [strategies, setStrategies] = useState<string[]>([]);
	const [selectedCustomer, setSelectedCustomer] = useState("");
	const [orders, setOrders] = useState<OrderSummaryOutput[]>([]);
	const [loading, setLoading] = useState(true);
	const [uploading, setUploading] = useState(false);
	const [clearing, setClearing] = useState(false);
	const [notice, setNotice] = useState<string | null>(null);
	const [error, setError] = useState<string | null>(null);

	const [showNew, setShowNew] = useState(false);
	const [creating, setCreating] = useState(false);
	const [newCode, setNewCode] = useState("");
	const [newName, setNewName] = useState("");
	const [newCountry, setNewCountry] = useState("");
	const [newStrategy, setNewStrategy] = useState("bauprofil_text");
	const [newApiKey, setNewApiKey] = useState("");
	const [newApiBaseUrl, setNewApiBaseUrl] = useState("");
	const [newApiModel, setNewApiModel] = useState("");

	async function loadCustomers() {
		const { data } = await backend.orderIntake.orderIntakeListCustomers({
			throwOnError: true,
		});
		setCustomers(data.customers ?? []);
		setStrategies(data.strategies ?? []);
		if (!selectedCustomer && data.customers?.length) {
			setSelectedCustomer(data.customers[0].code);
		}
	}

	async function loadOrders() {
		const { data } = await backend.orderIntake.orderIntakeListOrders({
			throwOnError: true,
		});
		setOrders(data.orders ?? []);
	}

	async function loadAll() {
		setLoading(true);
		try {
			await Promise.all([loadCustomers(), loadOrders()]);
		} catch (e) {
			setError(e instanceof Error ? e.message : "load_failed");
		} finally {
			setLoading(false);
		}
	}

	// biome-ignore lint/correctness/useExhaustiveDependencies: load once on mount
	useEffect(() => {
		loadAll();
	}, []);

	async function handleUpload(event: React.FormEvent) {
		event.preventDefault();
		const file = fileRef.current?.files?.[0];
		if (!file || !selectedCustomer) {
			setError(t("customer.needCustomer"));
			return;
		}
		setUploading(true);
		setError(null);
		try {
			const { data } = await backend.orderIntake.orderIntakeCreateOrder({
				body: { file, customer_code: selectedCustomer },
				throwOnError: true,
			});
			if (fileRef.current) fileRef.current.value = "";
			router.push(`/order-intake/${data.id}`);
		} catch (e) {
			setError(errMsg(e, t("upload.error")));
		} finally {
			setUploading(false);
		}
	}

	async function handleClearAll() {
		if (!window.confirm(t("list.clearConfirm"))) return;
		setClearing(true);
		setError(null);
		setNotice(null);
		try {
			const { data } = await backend.orderIntake.orderIntakeClearOrders({
				throwOnError: true,
			});
			setNotice(
				t("list.cleared", {
					orders: data.deleted_orders,
					files: data.deleted_files,
				}),
			);
			await loadOrders();
		} catch (e) {
			setError(errMsg(e, t("list.clearError")));
		} finally {
			setClearing(false);
		}
	}

	async function handleCreateCustomer(event: React.FormEvent) {
		event.preventDefault();
		if (!/^[a-z0-9][a-z0-9_-]*$/.test(newCode)) {
			setError(t("customer.codeHint"));
			return;
		}
		setCreating(true);
		setError(null);
		try {
			const { data } = await backend.orderIntake.orderIntakeCreateCustomer({
				body: {
					code: newCode,
					display_name: newName,
					country: newCountry || null,
					extraction_strategy: newStrategy,
					api_key: newStrategy === "llm_api" ? newApiKey || null : null,
					api_base_url:
						newStrategy === "llm_api" ? newApiBaseUrl || null : null,
					api_model: newStrategy === "llm_api" ? newApiModel || null : null,
				},
				throwOnError: true,
			});
			await loadCustomers();
			setSelectedCustomer(data.code);
			setShowNew(false);
			setNewCode("");
			setNewName("");
			setNewCountry("");
			setNewStrategy("bauprofil_text");
			setNewApiKey("");
			setNewApiBaseUrl("");
			setNewApiModel("");
		} catch (e) {
			setError(errMsg(e, t("customer.error")));
		} finally {
			setCreating(false);
		}
	}

	async function handleDeleteCustomer(code: string) {
		if (!window.confirm(t("customer.deleteConfirm", { code }))) return;
		setError(null);
		try {
			await backend.orderIntake.orderIntakeDeleteCustomer({
				path: { code },
				throwOnError: true,
			});
			if (selectedCustomer === code) setSelectedCustomer("");
			await loadCustomers();
		} catch (e) {
			setError(errMsg(e, t("customer.error")));
		}
	}

	return (
		<div className="space-y-8">
			<div className="space-y-2">
				<h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
					{t("title")}
				</h1>
				<p className="text-muted-foreground">{t("subtitle")}</p>
			</div>

			<UI.Card>
				<UI.CardHeader>
					<UI.CardTitle className="text-lg">{t("upload.label")}</UI.CardTitle>
					<UI.CardDescription>{t("upload.hint")}</UI.CardDescription>
				</UI.CardHeader>
				<UI.CardContent className="space-y-4">
					<form
						onSubmit={handleUpload}
						className="flex flex-wrap items-end gap-3"
					>
						<div className="flex flex-col gap-1 text-sm">
							<label htmlFor="oi-customer" className="text-muted-foreground">
								{t("customer.label")}
							</label>
							<UI.NativeSelect
								id="oi-customer"
								value={selectedCustomer}
								onChange={(e) => setSelectedCustomer(e.target.value)}
								disabled={uploading}
								className="min-w-[16rem]"
							>
								<option value="" disabled>
									{t("customer.select")}
								</option>
								{customers.map((c) => (
									<option key={c.code} value={c.code}>
										{c.display_name} — {strategyLabel(t, c.extraction_strategy)}
									</option>
								))}
							</UI.NativeSelect>
						</div>
						<div className="flex flex-col gap-1 text-sm">
							<label htmlFor="oi-file" className="text-muted-foreground">
								PDF
							</label>
							<UI.Input
								id="oi-file"
								ref={fileRef}
								type="file"
								accept="application/pdf"
								className="max-w-xs"
								disabled={uploading}
							/>
						</div>
						<UI.Button type="submit" disabled={uploading || !selectedCustomer}>
							{uploading ? t("upload.uploading") : t("upload.button")}
						</UI.Button>
						<UI.Button
							type="button"
							variant="outline"
							onClick={() => setShowNew((v) => !v)}
						>
							{t("customer.new")}
						</UI.Button>
					</form>

					{customers.length > 0 && (
						<div className="flex flex-wrap gap-2">
							{customers.map((c) => (
								<span
									key={c.code}
									className="inline-flex items-center gap-1 rounded-full border bg-background px-2 py-0.5 text-xs"
								>
									{c.display_name}
									<button
										type="button"
										onClick={() => handleDeleteCustomer(c.code)}
										className="text-muted-foreground hover:text-destructive"
										aria-label={t("customer.delete")}
									>
										×
									</button>
								</span>
							))}
						</div>
					)}

					{showNew && (
						<form
							onSubmit={handleCreateCustomer}
							className="grid gap-3 rounded-md border bg-muted/30 p-4 sm:grid-cols-2"
						>
							<div className="flex flex-col gap-1 text-sm">
								<label htmlFor="oi-new-code" className="text-muted-foreground">
									{t("customer.code")}
								</label>
								<UI.Input
									id="oi-new-code"
									value={newCode}
									onChange={(e) => setNewCode(e.target.value)}
									placeholder="acme-fr"
									required
								/>
							</div>
							<div className="flex flex-col gap-1 text-sm">
								<label htmlFor="oi-new-name" className="text-muted-foreground">
									{t("customer.name")}
								</label>
								<UI.Input
									id="oi-new-name"
									value={newName}
									onChange={(e) => setNewName(e.target.value)}
									placeholder="ACME Facades"
									required
								/>
							</div>
							<div className="flex flex-col gap-1 text-sm">
								<label
									htmlFor="oi-new-country"
									className="text-muted-foreground"
								>
									{t("customer.country")}
								</label>
								<UI.Input
									id="oi-new-country"
									value={newCountry}
									onChange={(e) => setNewCountry(e.target.value)}
									placeholder="FR"
									maxLength={2}
								/>
							</div>
							<div className="flex flex-col gap-1 text-sm">
								<label
									htmlFor="oi-new-strategy"
									className="text-muted-foreground"
								>
									{t("customer.strategy")}
								</label>
								<UI.NativeSelect
									id="oi-new-strategy"
									value={newStrategy}
									onChange={(e) => setNewStrategy(e.target.value)}
								>
									{strategies.map((s) => (
										<option key={s} value={s}>
											{strategyLabel(t, s)}
										</option>
									))}
								</UI.NativeSelect>
							</div>
							{newStrategy === "llm_api" && (
								<div className="flex flex-col gap-1 text-sm sm:col-span-2">
									<label
										htmlFor="oi-new-apikey"
										className="text-muted-foreground"
									>
										{t("customer.apiKey")}
									</label>
									<UI.Input
										id="oi-new-apikey"
										type="password"
										value={newApiKey}
										onChange={(e) => setNewApiKey(e.target.value)}
										placeholder="sk-..."
										required
									/>
									<span className="text-[11px] text-muted-foreground">
										{t("customer.apiKeyHint")}
									</span>
								</div>
							)}
							{newStrategy === "llm_api" && (
								<div className="flex flex-col gap-1 text-sm">
									<label
										htmlFor="oi-new-baseurl"
										className="text-muted-foreground"
									>
										{t("customer.apiBaseUrl")}
									</label>
									<UI.Input
										id="oi-new-baseurl"
										value={newApiBaseUrl}
										onChange={(e) => setNewApiBaseUrl(e.target.value)}
										placeholder="https://opencode.ai/zen/v1"
									/>
								</div>
							)}
							{newStrategy === "llm_api" && (
								<div className="flex flex-col gap-1 text-sm">
									<label
										htmlFor="oi-new-model"
										className="text-muted-foreground"
									>
										{t("customer.apiModel")}
									</label>
									<UI.Input
										id="oi-new-model"
										value={newApiModel}
										onChange={(e) => setNewApiModel(e.target.value)}
										placeholder="claude-haiku-4-5"
									/>
								</div>
							)}
							<div className="flex gap-2 sm:col-span-2">
								<UI.Button type="submit" disabled={creating}>
									{creating ? t("customer.creating") : t("customer.create")}
								</UI.Button>
								<UI.Button
									type="button"
									variant="ghost"
									onClick={() => setShowNew(false)}
								>
									{t("customer.cancel")}
								</UI.Button>
							</div>
						</form>
					)}

					{notice && <p className="text-sm text-muted-foreground">{notice}</p>}
					{error && <p className="text-sm text-destructive">{error}</p>}
				</UI.CardContent>
			</UI.Card>

			<UI.Card>
				<UI.CardHeader className="flex flex-row items-center justify-between gap-3">
					<UI.CardTitle className="text-lg">{t("list.heading")}</UI.CardTitle>
					{orders.length > 0 && (
						<UI.Button
							type="button"
							variant="outline"
							className="text-destructive"
							disabled={clearing}
							onClick={handleClearAll}
						>
							{clearing ? t("list.clearing") : t("list.clear")}
						</UI.Button>
					)}
				</UI.CardHeader>
				<UI.CardContent>
					{loading ? (
						<p className="text-sm text-muted-foreground">…</p>
					) : orders.length === 0 ? (
						<p className="text-sm text-muted-foreground">{t("list.empty")}</p>
					) : (
						<div className="overflow-x-auto">
							<table className="w-full text-sm">
								<thead>
									<tr className="border-b text-left text-muted-foreground">
										<th className="py-2 pr-4">{t("list.ref")}</th>
										<th className="py-2 pr-4">{t("list.customer")}</th>
										<th className="py-2 pr-4">{t("list.status")}</th>
										<th className="py-2 pr-4 text-right">{t("list.lines")}</th>
										<th className="py-2 pr-4 text-right">{t("list.flags")}</th>
										<th className="py-2" />
									</tr>
								</thead>
								<tbody>
									{orders.map((o) => (
										<tr key={o.id} className="border-b last:border-0">
											<td className="py-2 pr-4 font-mono text-xs">
												{o.order_ref ?? `#${o.id}`}
											</td>
											<td className="py-2 pr-4 capitalize">{o.customer}</td>
											<td className="py-2 pr-4">
												<StatusBadge status={o.status} />
											</td>
											<td className="py-2 pr-4 text-right">{o.line_count}</td>
											<td className="py-2 pr-4 text-right">
												{o.flagged_count > 0 ? (
													<span className="text-destructive font-medium">
														{o.flagged_count}
													</span>
												) : (
													0
												)}
											</td>
											<td className="py-2 text-right">
												<Link
													href={`/order-intake/${o.id}`}
													className="text-primary hover:underline"
												>
													{t("list.open")}
												</Link>
											</td>
										</tr>
									))}
								</tbody>
							</table>
						</div>
					)}
				</UI.CardContent>
			</UI.Card>
		</div>
	);
}
