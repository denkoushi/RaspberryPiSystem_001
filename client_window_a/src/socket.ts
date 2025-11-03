import { io, Socket } from "socket.io-client";

export interface SocketOptions {
  baseUrl: string;
  namespace?: string;
  eventName?: string;
  token?: string;
}

export type ScanEventHandler = (payload: Record<string, unknown>) => void;

export class ScanSocket {
  private socket: Socket | null = null;
  constructor(private opts: SocketOptions) {}

  connect(handler: ScanEventHandler): void {
    const url = `${this.opts.baseUrl}${this.opts.namespace ?? "/socket.io"}`;
    this.socket = io(url, {
      auth: this.opts.token ? { token: this.opts.token } : undefined,
    });
    const eventName = this.opts.eventName ?? "scan.ingested";
    this.socket.on(eventName, handler);
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }
}
