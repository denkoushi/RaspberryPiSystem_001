/**
 * Manual Socket.IO listener for Window A demo.
 *
 * Usage:
 *   npx ts-node scripts/listen_for_scans.ts --api http://localhost:8501
 *
 * Optional flags:
 *   --socket <url>    Override Socket.IO base URL (default: API base)
 *   --namespace <ns>  Override namespace (default: /socket.io)
 *   --event <name>    Override event name (default: scan.ingested)
 *   --token <token>   Bearer token if required
 *
 * The same options can be supplied via environment variables:
 *   API_BASE, SOCKET_BASE, SOCKET_NAMESPACE, SOCKET_EVENT, API_TOKEN
 */

import { ScanSocket, SocketOptions } from "../src/socket";

interface ListenerOptions {
  apiBase: string;
  socketBase: string;
  namespace?: string;
  eventName: string;
  token?: string;
}

function parseArgs(): Partial<ListenerOptions> {
  const args = process.argv.slice(2);
  const parsed: Partial<ListenerOptions> = {};

  for (let idx = 0; idx < args.length; idx += 1) {
    const key = args[idx];
    const value = args[idx + 1];
    if (!key?.startsWith("--")) {
      continue;
    }

    switch (key) {
      case "--api":
        if (value) parsed.apiBase = value;
        idx += 1;
        break;
      case "--socket":
        if (value) parsed.socketBase = value;
        idx += 1;
        break;
      case "--namespace":
        if (value) parsed.namespace = value;
        idx += 1;
        break;
      case "--event":
        if (value) parsed.eventName = value;
        idx += 1;
        break;
      case "--token":
        if (value) parsed.token = value;
        idx += 1;
        break;
      default:
        break;
    }
  }

  return parsed;
}

async function main(): Promise<void> {
  const args = parseArgs();
  const defaultBase = "http://127.0.0.1:8501";
  const options: ListenerOptions = {
    apiBase: args.apiBase ?? process.env.API_BASE ?? defaultBase,
    socketBase:
      args.socketBase ??
      process.env.SOCKET_BASE ??
      args.apiBase ??
      process.env.API_BASE ??
      defaultBase,
    namespace: args.namespace ?? process.env.SOCKET_NAMESPACE ?? "/",
    eventName: args.eventName ?? process.env.SOCKET_EVENT ?? "scan.ingested",
    token: args.token ?? process.env.API_TOKEN,
  };

  const socketOpts: SocketOptions = {
    baseUrl: options.socketBase,
    namespace: options.namespace,
    path: process.env.SOCKET_PATH ?? "/socket.io",
    eventName: options.eventName,
    token: options.token,
    debug: (process.env.SOCKET_DEBUG ?? "1") !== "0",
    logger: console,
  };

  const listener = new ScanSocket(socketOpts);
  listener.connect((payload) => {
    const now = new Date().toISOString();
    console.log(`[${now}] Event received (${options.eventName}):`);
    console.dir(payload, { depth: null });
  });

  console.log("=== Window A Socket Listener ===");
  console.log(`API base        : ${options.apiBase}`);
  console.log(`Socket base     : ${options.socketBase}`);
  console.log(`Namespace       : ${options.namespace}`);
  console.log(`Event name      : ${options.eventName}`);
  if (options.token) {
    console.log("Auth token      : (provided)");
  }
  console.log("Listening for events... Press Ctrl+C to exit.\n");

  process.on("SIGINT", () => {
    console.log("\nStopping listener...");
    listener.disconnect();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error("Listener failed:", error);
  process.exit(1);
});
