import type { Barriers, LonLat, Plan, PlaceResult, Profile, Settings } from "./types";

export async function planTrip(origin: LonLat, destination: LonLat, s: Settings, signal?: AbortSignal): Promise<Plan> {
  const res = await fetch("/api/plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify({
      origin: { lon: origin[0], lat: origin[1] },
      destination: { lon: destination[0], lat: destination[1] },
      step_free: s.stepFree,
      max_grade_pct: s.maxGrade,
      certainty: s.certainty,
      budget_min: s.budgetMin,
      priorities: { cross: s.cross, slope: s.slope, sidewalk: s.sidewalk },
    }),
  });
  if (!res.ok) {
    throw new Error(res.status === 422 ? "Those settings are not valid." : `The route service answered ${res.status}.`);
  }
  return res.json();
}

export interface FeedbackAnswers {
  felt_minutes_clear?: "yes" | "partly" | "no";
  places_clear?: "yes" | "partly" | "no";
  better_than_route_list?: "yes" | "partly" | "no";
  walked: boolean;
  comment: string;
}

/** Send a tester's answers. Nothing else goes with them. */
export async function sendFeedback(answers: FeedbackAnswers): Promise<void> {
  const res = await fetch("/api/feedback", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(answers) });
  if (!res.ok) throw new Error(`The service answered ${res.status}.`);
}

/** Whether this server has its own map tiles, how far they zoom, and where its region is. */
export async function basemapInfo(): Promise<{ local: boolean; maxZoom: number; center: LonLat | null }> {
  try {
    const h = await (await fetch("/api/health")).json();
    const center = Array.isArray(h.center) && h.center.length === 2 ? (h.center as LonLat) : null;
    return { local: Boolean(h.basemap), maxZoom: h.basemap_max_zoom ?? 15, center };
  } catch {
    return { local: false, maxZoom: 15, center: null };
  }
}

/** The mobility profiles this server offers. */
export async function profiles(): Promise<Profile[]> {
  try {
    return (await (await fetch("/api/region")).json()).profiles ?? [];
  } catch {
    return [];
  }
}

/** Recorded barriers and unrecorded places in a map view. */
export async function barriersIn(bbox: [number, number, number, number], signal?: AbortSignal): Promise<Barriers> {
  const res = await fetch(`/api/barriers?bbox=${bbox.map((v) => v.toFixed(5)).join(",")}`, { signal });
  if (!res.ok) throw new Error(`The barrier map answered ${res.status}.`);
  return res.json();
}

/** Places and addresses matching what was typed, nearest first when a position is given. */
export async function searchPlaces(q: string, near: LonLat | null, signal?: AbortSignal): Promise<PlaceResult[]> {
  const params = new URLSearchParams({ q: q.trim() });
  if (near) { params.set("lon", String(near[0])); params.set("lat", String(near[1])); }
  const res = await fetch(`/api/search?${params}`, { signal });
  if (!res.ok) return [];
  return (await res.json()).results;
}
