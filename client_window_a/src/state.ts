import { ScanSocket, SocketOptions } from "./socket";
import { fetchPartLocations, PartLocation } from "./api";

export class LocationState {
  private socket: ScanSocket | null = null;
  private data: PartLocation[] = [];

  constructor(private apiBase: string, private socketOpts: SocketOptions) {}

  async initialize(token?: string): Promise<PartLocation[]> {
    this.data = await fetchPartLocations(this.apiBase, token);
    this.socket = new ScanSocket(this.socketOpts);
    this.socket.connect((payload) => {
      if (payload.order_code && payload.location_code) {
        this.updateLocation(payload as any);
      }
    });
    return this.data;
  }

  dispose(): void {
    this.socket?.disconnect();
  }

  getLocations(): PartLocation[] {
    return this.data;
  }

  private updateLocation(payload: { order_code: string; location_code: string; device_id?: string | null }) {
    const existing = this.data.find((item) => item.order_code === payload.order_code);
    if (existing) {
      existing.location_code = payload.location_code;
      existing.device_id = payload.device_id ?? existing.device_id;
      existing.updated_at = new Date().toISOString();
    } else {
      this.data.push({
        order_code: payload.order_code,
        location_code: payload.location_code,
        device_id: payload.device_id ?? null,
        updated_at: new Date().toISOString(),
      });
    }
  }
}
