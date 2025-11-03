import { LocationState } from "../../state";

export async function bootstrapApp() {
  const baseUrl = process.env.API_BASE ?? "http://localhost:8501";
  const token = process.env.API_TOKEN;

  const state = new LocationState(baseUrl, {
    baseUrl,
    namespace: process.env.SOCKET_NAMESPACE ?? "/socket.io",
    eventName: process.env.SOCKET_EVENT ?? "scan.ingested",
    token,
  });

  await state.initialize(token);
  return state;
}
