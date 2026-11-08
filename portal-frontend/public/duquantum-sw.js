self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch (_error) {
    payload = {};
  }

  event.waitUntil(
    self.registration.showNotification(payload.title || "DuQuantum 2026", {
      body: payload.body || "There is a new DuQuantum event update.",
      icon: "/duquantum-2026/icon-192.png",
      badge: "/duquantum-2026/icon-192.png",
      tag: payload.tag || "duquantum-2026-update",
      renotify: false,
      data: {
        url: payload.url || "/events/duquantum-2026",
      },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const destination = new URL(
    event.notification.data?.url || "/events/duquantum-2026",
    self.location.origin,
  );
  const safeUrl =
    destination.origin === self.location.origin
      ? destination.href
      : `${self.location.origin}/events/duquantum-2026`;

  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then((windows) => {
        const existing = windows.find(
          (client) => new URL(client.url).origin === self.location.origin,
        );
        if (existing) {
          return existing.navigate(safeUrl).then(() => existing.focus());
        }
        return self.clients.openWindow(safeUrl);
      }),
  );
});
