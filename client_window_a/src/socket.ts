import { io, Socket } from "socket.io-client";

type Logger = Pick<typeof console, "log" | "error">;

export interface SocketOptions {
  baseUrl: string;
  namespace?: string;
  path?: string;
  eventName?: string;
  token?: string;
  debug?: boolean;
  logger?: Logger;
}

export type ScanEventHandler = (payload: Record<string, unknown>) => void;

const trimTrailingSlash = (value: string): string =>
  value.endsWith("/") ? value.slice(0, -1) : value;

const normalizeNamespace = (value?: string): string => {
  if (!value || value === "/") {
    return "";
  }
  return value.startsWith("/") ? value : `/${value}`;
};

const normalizePath = (value?: string): string => {
  if (!value) {
    return "/socket.io";
  }
  return value.startsWith("/") ? value : `/${value}`;
};

export class ScanSocket {
  private socket: Socket | null = null;
  constructor(private opts: SocketOptions) {}

  connect(handler: ScanEventHandler): void {
    const base = trimTrailingSlash(this.opts.baseUrl);
    const namespace = normalizeNamespace(this.opts.namespace);
    const path = normalizePath(this.opts.path);
    const url = `${base}${namespace}`;

    this.socket = io(url, {
      auth: this.opts.token ? { token: this.opts.token } : undefined,
      path,
    });
    const eventName = this.opts.eventName ?? "scan.ingested";
    this.socket.on(eventName, handler);

    if (this.opts.debug && this.socket) {
      const logger = this.opts.logger ?? console;
      this.socket.on("connect", () => {
        logger.log?.(
          `[scan-socket] connected (id=${this.socket?.id ?? "unknown"})`,
        );
      });
      this.socket.on("disconnect", (reason) => {
        logger.log?.(`[scan-socket] disconnected: ${reason}`);
      });
      this.socket.on("connect_error", (error) => {
        logger.error?.("[scan-socket] connect_error", error);
      });
      this.socket.io.on("reconnect_attempt", (attempt) => {
        logger.log?.(`[scan-socket] reconnect attempt #${attempt}`);
      });
      this.socket.io.on("reconnect_error", (error) => {
        logger.error?.("[scan-socket] reconnect_error", error);
      });
      this.socket.onAny((event, ...args) => {
        logger.log?.("[scan-socket] event", event, ...args);
      });
    }
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }
}
