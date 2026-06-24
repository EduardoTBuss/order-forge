/* eslinbiome-ignore-all lint/style/noRestrictedGlobals */

const DEFAULT_TITLE = "Invoice Intake - Workshop";
const DEFAULT_BODY = "You have a new notification.";
const DEFAULT_URL = "/";
const DEFAULT_ICON = "/icon_192.png";

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  if (!event.data) {
    event.waitUntil(
      self.registration.showNotification(DEFAULT_TITLE, {
        body: DEFAULT_BODY,
        icon: DEFAULT_ICON,
        badge: DEFAULT_ICON,
        data: { url: DEFAULT_URL },
      }),
    );
    return;
  }

  let payload;
  try {
    payload = event.data.json();
  } catch {
    payload = { title: DEFAULT_TITLE, body: event.data.text() || DEFAULT_BODY };
  }

  const {
    title = DEFAULT_TITLE,
    body = DEFAULT_BODY,
    url = DEFAULT_URL,
    icon = DEFAULT_ICON,
    badge = DEFAULT_ICON,
    tag,
  } = payload ?? {};

  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon,
      badge,
      tag,
      data: { url },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = event.notification?.data?.url || DEFAULT_URL;

  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windowClients) => {
        for (const client of windowClients) {
          if ("navigate" in client) {
            client.navigate(targetUrl);
          }
          if ("focus" in client) {
            return client.focus();
          }
        }
        if (self.clients.openWindow) {
          return self.clients.openWindow(targetUrl);
        }
        return undefined;
      }),
  );
});

self.addEventListener("message", (event) => {
  if (!event.data || typeof event.data !== "object") return;
  if (event.data.type === "preview-notification") {
    const payload = event.data.payload || {};
    event.waitUntil(
      self.registration.showNotification(payload.title || DEFAULT_TITLE, {
        body: payload.body || DEFAULT_BODY,
        icon: payload.icon || DEFAULT_ICON,
        badge: payload.badge || DEFAULT_ICON,
        data: payload.data || { url: DEFAULT_URL },
      })
    );
  }
});
