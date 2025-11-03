import { LocationState } from "../src/state";

jest.mock("../src/api", () => ({
  fetchPartLocations: jest.fn(async () => [
    { order_code: "A", location_code: "R1", device_id: null, updated_at: "" },
  ]),
}));

jest.mock("../src/socket", () => ({
  ScanSocket: jest.fn().mockImplementation(() => ({
    connect: jest.fn((handler) => {
      handler({ order_code: "B", location_code: "R2" });
    }),
    disconnect: jest.fn(),
  })),
}));

it("updates state on socket event", async () => {
  const state = new LocationState("http://localhost:8501", { baseUrl: "http://localhost:8501" });
  await state.initialize();
  const locations = state.getLocations();
  expect(locations.find((item) => item.order_code === "B")).toBeDefined();
});
