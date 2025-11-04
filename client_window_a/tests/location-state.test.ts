/**
 * LocationState unit tests.
 *
 * REST での初期取得と Socket.IO 経由の更新が正しく反映されるかを検証する。
 */

import { LocationState } from "../src/state";

const connectSpy = jest.fn<void, [(payload: Record<string, unknown>) => void]>();
const disconnectSpy = jest.fn<void, []>();
let capturedHandler: ((payload: Record<string, unknown>) => void) | undefined;

jest.mock("../src/socket", () => {
  return {
    ScanSocket: jest.fn().mockImplementation(() => ({
      connect: (handler: (payload: Record<string, unknown>) => void) => {
        connectSpy(handler);
        capturedHandler = handler;
      },
      disconnect: () => disconnectSpy(),
    })),
  };
});

const SAMPLE_ENTRIES = [
  { order_code: "TEST-001", location_code: "RACK-A1", device_id: "HANDHELD-01", updated_at: "2025-11-04T00:00:00Z" },
  { order_code: "TEST-002", location_code: "RACK-B1", device_id: "HANDHELD-01", updated_at: "2025-11-04T01:00:00Z" },
];

describe("LocationState", () => {
  beforeEach(() => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ entries: SAMPLE_ENTRIES }),
    });
    connectSpy.mockClear();
    disconnectSpy.mockClear();
    capturedHandler = undefined;
  });

  afterEach(() => {
    jest.resetModules();
  });

  it("initializes by fetching REST entries and exposes them", async () => {
    const state = new LocationState("http://localhost:8501", { baseUrl: "http://localhost:8501" });
    const result = await state.initialize();

    expect(global.fetch).toHaveBeenCalledWith("http://localhost:8501/api/v1/part-locations", { headers: undefined });
    expect(connectSpy).toHaveBeenCalledTimes(1);
    expect(result).toEqual(SAMPLE_ENTRIES);
    expect(state.getLocations()).toEqual(SAMPLE_ENTRIES);
  });

  it("updates existing orders when socket payload arrives", async () => {
    const state = new LocationState("http://localhost:8501", { baseUrl: "http://localhost:8501" });
    await state.initialize();
    expect(capturedHandler).toBeDefined();

    capturedHandler?.({ order_code: "TEST-002", location_code: "RACK-B9", device_id: "HANDHELD-99" });
    const updated = state.getLocations().find((entry) => entry.order_code == "TEST-002");

    expect(updated).toBeDefined();
    expect(updated?.location_code).toBe("RACK-B9");
    expect(updated?.device_id).toBe("HANDHELD-99");
  });

  it("appends new orders when socket payload is unknown", async () => {
    const state = new LocationState("http://localhost:8501", { baseUrl: "http://localhost:8501" });
    await state.initialize();

    capturedHandler?.({ order_code: "TEST-900", location_code: "RACK-Z9" });

    const orders = state.getLocations().map((entry) => entry.order_code);
    expect(orders).toContain("TEST-900");
  });

  it("disconnects socket on dispose", async () => {
    const state = new LocationState("http://localhost:8501", { baseUrl: "http://localhost:8501" });
    await state.initialize();
    state.dispose();

    expect(disconnectSpy).toHaveBeenCalledTimes(1);
  });
});
