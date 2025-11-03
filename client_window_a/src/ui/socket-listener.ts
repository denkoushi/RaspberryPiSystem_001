import { ScanSocket } from "../socket";

type UpdateHandler = (payload: Record<string, unknown>) => void;

type Options = {
  baseUrl: string;
  namespace?: string;
  eventName?: string;
  token?: string;
};

export class SocketListener {
  private socket?: ScanSocket;

  constructor(private opts: Options, private onUpdate: UpdateHandler) {}

  start() {
    this.socket = new ScanSocket(this.opts);
    this.socket.connect(this.onUpdate);
  }

  stop() {
    this.socket?.disconnect();
  }
}
