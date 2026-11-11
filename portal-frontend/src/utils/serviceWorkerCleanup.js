// Remove only the retired event worker; unrelated registrations are untouched.
export async function retireEventServiceWorkers() {
  if (!("serviceWorker" in navigator)) return;
  try {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(
      registrations
        .filter((registration) => {
          const worker =
            registration.active || registration.waiting || registration.installing;
          if (!worker) return false;
          const url = new URL(worker.scriptURL, window.location.origin);
          return (
            url.origin === window.location.origin &&
            url.pathname === "/duquantum-sw.js"
          );
        })
        .map((registration) => registration.unregister()),
    );
  } catch (_error) {
    // Restricted browser contexts must not prevent the portal from loading.
  }
}
