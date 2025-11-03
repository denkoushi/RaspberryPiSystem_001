export interface PartLocation {
  order_code: string;
  location_code: string;
  device_id?: string | null;
  updated_at: string;
}

export async function fetchPartLocations(baseUrl: string, token?: string): Promise<PartLocation[]> {
  const res = await fetch(`${baseUrl}/api/v1/part-locations` ?? "", {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch part locations: ${res.status}`);
  }
  const data = await res.json();
  return data.entries ?? [];
}
