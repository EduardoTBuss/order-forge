"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { UI } from "@/components/ui";
import { backend } from "@/lib/backend";
import type {
	EdifactOutput,
	OrderDetailOutput,
	OrderLineOutput,
} from "@/lib/backend/generated";

const TRUSTED_TIERS = ["exact", "manual", "learned"];

function tierLabel(t: ReturnType<typeof useTranslations>, tier: string | null) {
	if (!tier) return t("tier.none");
	if (tier === "exact") return t("tier.exact");
	if (tier === "dimension") return t("tier.dimension");
	if (tier === "fuzzy") return t("tier.fuzzy");
	if (tier === "manual") return t("tier.manual");
	if (tier === "learned") return t("tier.learned");
	return t("tier.none");
}

function ConfidenceCell({ line }: { line: OrderLineOutput }) {
	const t = useTranslations("orderIntake");
	const flags = line.confidence_flags ?? [];
	if (flags.length === 0) {
		return <UI.Badge variant="default">{t("detail.ok")}</UI.Badge>;
	}
	return (
		<div className="flex flex-wrap gap-1">
			{flags.map((flag) => (
				<UI.Badge key={flag} variant="destructive">
					{t(`flags.${flag}` as "flags.unmatched_code")}
				</UI.Badge>
			))}
		</div>
	);
}

export default function ReconciliationClient({ orderId }: { orderId: number }) {
	const t = useTranslations("orderIntake");
	const [order, setOrder] = useState<OrderDetailOutput | null>(null);
	const [loading, setLoading] = useState(true);
	const [generating, setGenerating] = useState(false);
	const [edifact, setEdifact] = useState<EdifactOutput | null>(null);
	const [error, setError] = useState<string | null>(null);
	const [edits, setEdits] = useState<Record<number, string>>({});
	const [savingLine, setSavingLine] = useState<number | null>(null);

	async function loadOrder() {
		setLoading(true);
		try {
			const { data } = await backend.orderIntake.orderIntakeGetOrder({
				path: { order_id: orderId },
				throwOnError: true,
			});
			setOrder(data);
		} catch (e) {
			setError(e instanceof Error ? e.message : "load_failed");
		} finally {
			setLoading(false);
		}
	}

	// biome-ignore lint/correctness/useExhaustiveDependencies: reload when the order id changes
	useEffect(() => {
		loadOrder();
	}, [orderId]);

	async function handleGenerate() {
		setGenerating(true);
		setError(null);
		try {
			const { data } = await backend.orderIntake.orderIntakeGenerateEdifact({
				path: { order_id: orderId },
				throwOnError: true,
			});
			setEdifact(data);
			await loadOrder();
		} catch (e) {
			setError(e instanceof Error ? e.message : t("edifact.error"));
		} finally {
			setGenerating(false);
		}
	}

	async function saveLineCode(lineId: number, code: string) {
		const trimmed = code.trim();
		if (!trimmed) return;
		setSavingLine(lineId);
		setError(null);
		try {
			const { data } = await backend.orderIntake.orderIntakeUpdateLine({
				path: { order_id: orderId, line_id: lineId },
				body: { resolved_internal_code: trimmed },
				throwOnError: true,
			});
			setOrder(data);
			setEdits((prev) => {
				const next = { ...prev };
				delete next[lineId];
				return next;
			});
		} catch (e) {
			setError(e instanceof Error ? e.message : t("edifact.error"));
		} finally {
			setSavingLine(null);
		}
	}

	function downloadEdi() {
		if (!edifact) return;
		const blob = new Blob([edifact.edi_text], { type: "text/plain" });
		const url = URL.createObjectURL(blob);
		const anchor = document.createElement("a");
		anchor.href = url;
		anchor.download = edifact.filename;
		anchor.click();
		URL.revokeObjectURL(url);
	}

	if (loading) {
		return <p className="text-sm text-muted-foreground">…</p>;
	}
	if (!order) {
		return <p className="text-sm text-destructive">{error ?? "not found"}</p>;
	}

	const matched = (order.line_count ?? 0) - (order.unmatched_count ?? 0);

	return (
		<div className="space-y-6">
			<div className="flex flex-wrap items-center justify-between gap-3">
				<div>
					<Link
						href="/order-intake"
						className="text-sm text-muted-foreground hover:text-foreground"
					>
						← {t("detail.back")}
					</Link>
					<h1 className="text-2xl font-bold tracking-tight">
						{order.order_ref ?? `#${order.id}`}
					</h1>
					<p className="text-sm text-muted-foreground">
						{t("detail.summary", { matched, total: order.line_count })}
					</p>
				</div>
				<UI.Badge
					variant={
						order.status === "edifact_generated" ? "default" : "secondary"
					}
				>
					{t(`status.${order.status}` as "status.in_review")}
				</UI.Badge>
			</div>

			<div className="grid gap-6 lg:grid-cols-2">
				{/* Left: original PDF (served through the authed /api proxy) */}
				<UI.Card>
					<UI.CardHeader>
						<UI.CardTitle className="text-base">
							{t("detail.pdfTitle")}
						</UI.CardTitle>
					</UI.CardHeader>
					<UI.CardContent>
						<iframe
							src={`/api/custom/order-intake/orders/${order.id}/source-pdf`}
							title={t("detail.pdfTitle")}
							className="h-[640px] w-full rounded-md border bg-white"
						/>
					</UI.CardContent>
				</UI.Card>

				{/* Right: extracted + reconciled lines */}
				<UI.Card>
					<UI.CardHeader>
						<UI.CardTitle className="text-base">
							{t("detail.linesTitle")}
						</UI.CardTitle>
					</UI.CardHeader>
					<UI.CardContent>
						<div className="overflow-x-auto">
							<table className="w-full text-sm">
								<thead>
									<tr className="border-b text-left text-muted-foreground">
										<th className="py-2 pr-3">{t("detail.pos")}</th>
										<th className="py-2 pr-3">{t("detail.resolved")}</th>
										<th className="py-2 pr-3 text-right">{t("detail.qty")}</th>
										<th className="py-2 pr-3">{t("detail.unit")}</th>
										<th className="py-2 pr-3">{t("tier.label")}</th>
										<th className="py-2">{t("detail.confidence")}</th>
									</tr>
								</thead>
								<tbody>
									{(order.lines ?? []).map((line) => {
										const flags = line.confidence_flags ?? [];
										const mismatch = flags.includes("code_mismatch");
										const resolved = line.resolved_internal_code;
										const showRead =
											line.extracted_code &&
											line.extracted_code !== resolved;
										const canConfirm =
											!!resolved &&
											!TRUSTED_TIERS.includes(line.match_tier ?? "");
										return (
											<tr
												key={line.id}
												className="border-b last:border-0 align-top"
											>
												<td className="py-2 pr-3 font-mono text-xs">
													{line.line_no}
												</td>
												<td className="py-2 pr-3">
													<div className="font-mono text-xs">
														{resolved ? (
															resolved
														) : (
															<span className="text-destructive">
																{t("detail.unmatched")}
															</span>
														)}
													</div>
													{showRead && (
														<div
															className={`mt-0.5 font-mono text-[10px] ${
																mismatch
																	? "text-destructive font-semibold"
																	: "text-muted-foreground"
															}`}
															title={mismatch ? t("detail.mismatchHint") : undefined}
														>
															{t("detail.readCode")}: {line.extracted_code}
															{mismatch ? " ⚠" : ""}
														</div>
													)}
													{line.description && (
														<div className="mt-0.5 max-w-[16rem] truncate text-[11px] text-muted-foreground">
															{line.description}
														</div>
													)}
													<div className="mt-1 flex flex-wrap items-center gap-1">
														<UI.Input
															value={edits[line.id] ?? ""}
															onChange={(e) =>
																setEdits((prev) => ({
																	...prev,
																	[line.id]: e.target.value,
																}))
															}
															placeholder={t("assign.placeholder")}
															className="h-7 w-28 font-mono text-xs"
														/>
														<UI.Button
															type="button"
															variant="outline"
															className="h-7 px-2 text-xs"
															disabled={savingLine === line.id || !edits[line.id]}
															onClick={() =>
																saveLineCode(line.id, edits[line.id] ?? "")
															}
														>
															{savingLine === line.id
																? t("assign.saving")
																: t("assign.set")}
														</UI.Button>
														{canConfirm && resolved && (
															<UI.Button
																type="button"
																variant="outline"
																className="h-7 px-2 text-xs text-primary"
																title={t("assign.confirmHint")}
																disabled={savingLine === line.id}
																onClick={() => saveLineCode(line.id, resolved)}
															>
																{savingLine === line.id
																	? t("assign.confirming")
																	: t("assign.confirm")}
															</UI.Button>
														)}
													</div>
												</td>
												<td className="py-2 pr-3 text-right">
													{line.quantity ?? "—"}
												</td>
												<td className="py-2 pr-3">{line.unit ?? "—"}</td>
												<td className="py-2 pr-3 text-xs text-muted-foreground">
													{tierLabel(t, line.match_tier ?? null)}
												</td>
												<td className="py-2">
													<ConfidenceCell line={line} />
												</td>
											</tr>
										);
									})}
								</tbody>
							</table>
						</div>

						<div className="mt-5 flex flex-col gap-2 border-t pt-4">
							<UI.Button
								onClick={handleGenerate}
								disabled={!order.can_generate_edifact || generating}
							>
								{generating ? t("edifact.generating") : t("edifact.generate")}
							</UI.Button>
							{!order.can_generate_edifact && (
								<p className="text-xs text-muted-foreground">
									{t("edifact.blockedHint")}
									{order.blocking_lines && order.blocking_lines.length > 0 && (
										<>
											{" "}
											{t("edifact.blocked", {
												lines: order.blocking_lines.join(", "),
											})}
										</>
									)}
								</p>
							)}
							{error && <p className="text-sm text-destructive">{error}</p>}
						</div>
					</UI.CardContent>
				</UI.Card>
			</div>

			{edifact && (
				<UI.Card>
					<UI.CardHeader className="flex flex-row items-center justify-between">
						<UI.CardTitle className="text-base">
							{t("edifact.title")}
						</UI.CardTitle>
						<UI.Button variant="outline" onClick={downloadEdi}>
							{t("edifact.download")}
						</UI.Button>
					</UI.CardHeader>
					<UI.CardContent>
						<pre className="max-h-[420px] overflow-auto rounded-md bg-muted p-4 font-mono text-xs leading-relaxed">
							{edifact.edi_text}
						</pre>
					</UI.CardContent>
				</UI.Card>
			)}
		</div>
	);
}
