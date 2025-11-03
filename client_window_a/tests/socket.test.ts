import { ScanSocket } from "../src";

const events: Record<string, any> = {};
const mockOn = jest.fn((event: string, handler: any) => {
  events[event] = handler;
});
const mockDisconnect = jest.fn();

jest.mock("socket.io-client", () => ({
  io: jest.fn(() => ({
    on: mockOn,
    disconnect: mockDisconnect,
  })),
}));

describe("ScanSocket", () => {
  it("should register handler on connect", () => {
    const socket = new ScanSocket({ baseUrl: "http://localhost:8501" });
    const handler = jest.fn();
    socket.connect(handler);

    expect(events["scan.ingested"]).toBe(handler);
  });
});
