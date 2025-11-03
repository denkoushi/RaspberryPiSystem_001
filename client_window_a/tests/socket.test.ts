import { ScanSocket } from "../src";

describe("ScanSocket", () => {
  it("should register handler on connect", () => {
    const events: Record<string, any> = {};
    jest.mock("socket.io-client", () => ({
      io: jest.fn(() => ({
        on: (event: string, handler: any) => {
          events[event] = handler;
        },
        disconnect: jest.fn(),
      })),
    }));

    const socket = new ScanSocket({ baseUrl: "http://localhost:8501" });
    const handler = jest.fn();
    socket.connect(handler);

    expect(events["scan.ingested"]).toBe(handler);
  });
});
