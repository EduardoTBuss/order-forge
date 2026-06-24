/**
 * Runs once at Next.js server boot. When HTTPS_PROXY is set, installs an
 * undici ProxyAgent as the global dispatcher so that native fetch — and
 * every library built on it (generated SDKs, jose JWKS fetch, etc.) —
 * routes outbound traffic through the Envoy egress sidecar.
 *
 * Why: Node 20+ uses undici under the hood for global fetch, but it does
 * NOT read HTTP_PROXY / HTTPS_PROXY env vars unless a dispatcher is set
 * explicitly. Without this, fetch calls bypass Envoy and break the egress
 * allowlist.
 */
export async function register(): Promise<void> {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;

  const proxyUrl =
    process.env.HTTPS_PROXY ??
    process.env.https_proxy ??
    process.env.HTTP_PROXY ??
    process.env.http_proxy;
  if (!proxyUrl) return;

  const { ProxyAgent, setGlobalDispatcher } = await import("undici");
  setGlobalDispatcher(new ProxyAgent(proxyUrl));

  console.info("[instrumentation] global undici dispatcher → %s", proxyUrl);
}
