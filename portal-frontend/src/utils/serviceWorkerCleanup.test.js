import { retireEventServiceWorkers } from "./serviceWorkerCleanup";

afterEach(() => {
  delete navigator.serviceWorker;
});

test("retires only the old same-origin event worker", async () => {
  const retired = {
    active: { scriptURL: `${window.location.origin}/duquantum-sw.js` },
    unregister: jest.fn().mockResolvedValue(true),
  };
  const unrelated = {
    active: { scriptURL: `${window.location.origin}/other-worker.js` },
    unregister: jest.fn(),
  };
  const installing = {
    installing: { scriptURL: `${window.location.origin}/duquantum-sw.js` },
    unregister: jest.fn().mockResolvedValue(true),
  };
  Object.defineProperty(navigator, "serviceWorker", {
    configurable: true,
    value: { getRegistrations: jest.fn().mockResolvedValue([retired, unrelated, installing]) },
  });
  await retireEventServiceWorkers();
  expect(retired.unregister).toHaveBeenCalledTimes(1);
  expect(installing.unregister).toHaveBeenCalledTimes(1);
  expect(unrelated.unregister).not.toHaveBeenCalled();
});

test("a restricted browser does not prevent the portal from loading", async () => {
  Object.defineProperty(navigator, "serviceWorker", {
    configurable: true,
    value: { getRegistrations: jest.fn().mockRejectedValue(new Error("Restricted")) },
  });
  await expect(retireEventServiceWorkers()).resolves.toBeUndefined();
});

test("supports browsers without service workers", async () => {
  await expect(retireEventServiceWorkers()).resolves.toBeUndefined();
});
