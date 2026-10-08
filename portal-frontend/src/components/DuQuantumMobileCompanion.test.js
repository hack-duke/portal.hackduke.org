import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import axios from "axios";
import DuQuantumMobileCompanion from "./DuQuantumMobileCompanion";

jest.mock("axios", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

describe("DuQuantumMobileCompanion", () => {
  const subscription = {
    toJSON: () => ({
      endpoint: "https://push.example.test/device",
      keys: { p256dh: "public-device-key", auth: "auth-secret" },
    }),
    unsubscribe: jest.fn(),
  };
  const pushManager = {
    getSubscription: jest.fn(),
    subscribe: jest.fn(),
  };
  const serviceWorkerRegistration = {
    pushManager,
    showNotification: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(window, "isSecureContext", {
      configurable: true,
      value: true,
    });
    Object.defineProperty(window, "PushManager", {
      configurable: true,
      value: function PushManager() {},
    });
    Object.defineProperty(window, "Notification", {
      configurable: true,
      value: {
        permission: "default",
        requestPermission: jest.fn().mockResolvedValue("granted"),
      },
    });
    Object.defineProperty(navigator, "serviceWorker", {
      configurable: true,
      value: { ready: Promise.resolve(serviceWorkerRegistration) },
    });
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: jest.fn().mockReturnValue({ matches: false }),
    });
    pushManager.getSubscription.mockResolvedValue(null);
    pushManager.subscribe.mockResolvedValue(subscription);
    axios.get.mockResolvedValue({
      data: {
        enabled: true,
        subscribed: false,
        public_key: "AQIDBA",
        schedule_count: 14,
      },
    });
    axios.post.mockResolvedValue({ data: { subscribed: true } });
  });

  test("enables authenticated web push after the attendee opts in", async () => {
    const getAccessTokenSilently = jest.fn().mockResolvedValue("access-token");
    render(
      <DuQuantumMobileCompanion
        getAccessTokenSilently={getAccessTokenSilently}
      />,
    );

    const button = await screen.findByRole("button", {
      name: "Enable event alerts",
    });
    await waitFor(() => expect(button).toBeEnabled());
    fireEvent.click(button);

    await waitFor(() => expect(axios.post).toHaveBeenCalledTimes(1));
    expect(pushManager.subscribe).toHaveBeenCalledWith({
      userVisibleOnly: true,
      applicationServerKey: expect.any(Uint8Array),
    });
    expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining(
        "/events/duquantum-2026/notifications/subscriptions",
      ),
      subscription.toJSON(),
      { headers: { Authorization: "Bearer access-token" } },
    );
    expect(serviceWorkerRegistration.showNotification).toHaveBeenCalledWith(
      "DuQuantum alerts are ready",
      expect.objectContaining({ tag: "duquantum-2026-alerts-ready" }),
    );
    expect(
      await screen.findByText(
        "14 schedule alerts are enabled for this device.",
      ),
    ).toBeInTheDocument();
  });
});
