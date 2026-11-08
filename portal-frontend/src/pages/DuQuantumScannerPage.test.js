import React from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import "@testing-library/jest-dom";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import jsQR from "jsqr";
import DuQuantumScannerPage from "./DuQuantumScannerPage";

const mockToken = jest.fn().mockResolvedValue("staff-token");
jest.mock("axios", () => ({
  __esModule: true,
  default: { get: jest.fn(), post: jest.fn() },
}));
jest.mock("jsqr", () => ({ __esModule: true, default: jest.fn() }));
jest.mock("@auth0/auth0-react", () => ({
  useAuth0: () => ({ getAccessTokenSilently: mockToken }),
}));

let nextFrame;
let getUserMedia;
let stop;
beforeEach(() => {
  jest.clearAllMocks();
  mockToken.mockResolvedValue("staff-token");
  stop = jest.fn();
  getUserMedia = jest.fn().mockResolvedValue({ getTracks: () => [{ stop }] });
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia },
  });
  window.requestAnimationFrame = jest.fn((callback) => {
    nextFrame = callback;
    return 1;
  });
  window.cancelAnimationFrame = jest.fn();
  jest.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue();
  Object.defineProperty(HTMLMediaElement.prototype, "readyState", {
    configurable: true,
    get: () => 4,
  });
  Object.defineProperty(HTMLVideoElement.prototype, "videoWidth", {
    configurable: true,
    get: () => 640,
  });
  Object.defineProperty(HTMLVideoElement.prototype, "videoHeight", {
    configurable: true,
    get: () => 480,
  });
  jest.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({
    drawImage: jest.fn(),
    getImageData: () => ({
      data: new Uint8ClampedArray(4),
      width: 1,
      height: 1,
    }),
  });
  axios.get.mockResolvedValue({ data: { check_ins: [], total: 0 } });
  axios.post.mockResolvedValue({
    data: { id: "checkin", first_name: "Test", last_name: "Attendee" },
  });
  jsQR.mockReturnValue({ data: "evt_scanner_test_pass" });
});
afterEach(() => jest.restoreAllMocks());

async function openCamera() {
  const view = render(
    <MemoryRouter>
      <DuQuantumScannerPage />
    </MemoryRouter>,
  );
  await waitFor(() => expect(axios.get).toHaveBeenCalled());
  fireEvent.click(screen.getByRole("button", { name: "Open camera" }));
  await screen.findByRole("button", { name: "Close camera" });
  return view;
}

test("decodes camera frames, uses the current checkpoint, and suppresses a held QR", async () => {
  const view = await openCamera();
  expect(getUserMedia).toHaveBeenCalledWith(
    expect.objectContaining({
      audio: false,
      video: expect.objectContaining({ facingMode: { ideal: "environment" } }),
    }),
  );
  fireEvent.change(screen.getByRole("combobox"), {
    target: { value: "saturday_lunch" },
  });
  await act(async () => {
    nextFrame();
  });
  expect(axios.post).toHaveBeenCalledWith(
    expect.stringContaining("/events/duquantum-2026/check-ins"),
    { pass_id: "evt_scanner_test_pass", checkpoint: "saturday_lunch" },
    { headers: { Authorization: "Bearer staff-token" } },
  );
  expect(
    await screen.findByText("Test Attendee checked in for Saturday lunch."),
  ).toBeInTheDocument();
  await act(async () => {
    nextFrame();
  });
  expect(axios.post).toHaveBeenCalledTimes(1);
  jsQR.mockReturnValue(null);
  await act(async () => {
    nextFrame();
  });
  jsQR.mockReturnValue({ data: "evt_second_attendee_pass" });
  await act(async () => {
    nextFrame();
  });
  expect(axios.post).toHaveBeenCalledTimes(2);
  view.unmount();
  expect(stop).toHaveBeenCalledTimes(1);
  expect(window.cancelAnimationFrame).toHaveBeenCalled();
});

test("manual pass fallback prevents simultaneous duplicate submissions", async () => {
  let finish;
  axios.post.mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  render(
    <MemoryRouter>
      <DuQuantumScannerPage />
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText("Manual pass ID"), {
    target: { value: "evt_manual_test_pass" },
  });
  const form = screen.getByLabelText("Manual pass ID").closest("form");
  fireEvent.submit(form);
  fireEvent.submit(form);
  await waitFor(() => expect(axios.post).toHaveBeenCalledTimes(1));
  await act(async () => {
    finish({ data: { first_name: "Manual", last_name: "Attendee" } });
  });
  expect(
    await screen.findByText("Manual Attendee checked in for Arrival."),
  ).toBeInTheDocument();
});

test("permission denial explains recovery and keeps the manual fallback available", async () => {
  getUserMedia.mockRejectedValue(
    Object.assign(new Error("Denied"), { name: "NotAllowedError" }),
  );
  render(
    <MemoryRouter>
      <DuQuantumScannerPage />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Open camera" }));
  expect(
    await screen.findByText(/Camera permission was denied/),
  ).toBeInTheDocument();
  expect(screen.getByLabelText("Manual pass ID")).toBeEnabled();
  expect(screen.getByRole("button", { name: "Open camera" })).toBeEnabled();
});

test("a playback failure releases the camera stream", async () => {
  HTMLMediaElement.prototype.play.mockRejectedValue(
    new Error("Playback failed"),
  );
  render(
    <MemoryRouter>
      <DuQuantumScannerPage />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Open camera" }));
  expect(
    await screen.findByText(/Camera unavailable: Playback failed/),
  ).toBeInTheDocument();
  expect(stop).toHaveBeenCalledTimes(1);
});

test("a camera stream obtained after leaving the page is immediately stopped", async () => {
  let finish;
  getUserMedia.mockImplementation(
    () =>
      new Promise((resolve) => {
        finish = resolve;
      }),
  );
  const view = render(
    <MemoryRouter>
      <DuQuantumScannerPage />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Open camera" }));
  await waitFor(() => expect(getUserMedia).toHaveBeenCalledTimes(1));
  view.unmount();
  await act(async () => {
    finish({ getTracks: () => [{ stop }] });
  });
  expect(stop).toHaveBeenCalledTimes(1);
});

test("duplicate check-ins display the server message and refresh the log", async () => {
  axios.post.mockRejectedValue({
    response: {
      status: 409,
      data: {
        detail: { message: "Attendee already checked in at this checkpoint" },
      },
    },
  });
  render(
    <MemoryRouter>
      <DuQuantumScannerPage />
    </MemoryRouter>,
  );
  await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1));
  fireEvent.change(screen.getByLabelText("Manual pass ID"), {
    target: { value: "evt_duplicate_test_pass" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Check in" }));
  expect(
    await screen.findByText("Attendee already checked in at this checkpoint"),
  ).toBeInTheDocument();
  await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(2));
});
