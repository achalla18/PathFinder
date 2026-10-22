import type { Claim, Condition } from "./types";
import { t } from "./i18n";

// Every statement shown to a user carries its status, source and date (product rule 4).

const SOURCES: Record<string, string> = {
  osm_dc: "OpenStreetMap",
  montgomery_sidewalks: "Montgomery Planning sidewalk survey",
  frederick_sidewalks: "City of Frederick sidewalk survey",
  frederick_ramps: "City of Frederick ramp survey",

  sidewalks_2021: "DC planimetric survey",
  sidewalk_ramps_2010: "DC ramp survey",
  project_sidewalk_dc: "Project Sidewalk",
  traffic_signals: "DDOT signal inventory",
  dtm_2024: "DC LiDAR terrain",
  roadway_block: "DDOT roadway inventory",
};

export const RAMP_CHECK: Record<string, string> = {
  passed: "ramp passed the city's check",
  fails: "ramp fails the city's check (too steep, no landing or damaged)",
  no_tactile_pad: "ramp has no working tactile warning pad",
};

export const CONTROL: Record<string, string> = {
  signal: "signalized",
  marked_uncontrolled: "painted, no signal",
  unmarked: "unmarked, no signal",
};

export const KERB: Record<string, string> = {
  lowered: "lowered curb",
  flush: "flush curb",
  ramp_present: "curb ramp",
  raised: "raised curb",
  no_ramp: "no curb ramp",
  no_curb: "no curb to mount",
  ramp_likely: "ramps recorded at the corners",
  no_ramp_reported: "a missing ramp is reported here",
  unknown: "curb not recorded",
};

/** A street as the roadway inventory names it ("MINNESOTA AVE NE"), in ordinary case with the quadrant kept. */
export const streetName = (s: string) =>
  s.toLowerCase().replace(/(^|[\s-])([a-z])/g, (_, gap: string, c: string) => gap + c.toUpperCase()).replace(/\b(Nw|Ne|Sw|Se)$/, (q) => q.toUpperCase());

function backing(c: Partial<Claim>): string {
  if (!c.status || c.status === "unknown") return "no record";
  // a claim merged from two halves of a crossing may name several sources, ", "-separated
  const label = (s: string) => SOURCES[s] ?? (s.startsWith("osm_") ? "OpenStreetMap" : s.startsWith("derived") ? "estimated" : s);
  const src = c.source ? [...new Set(c.source.split(", ").map(label))].join(" and ") : "";
  const year = c.as_of ? ` ${String(c.as_of).slice(0, 4)}` : "";
  return `${c.status === "inferred" ? "likely" : "recorded"}${src ? ` · ${src}` : ""}${year}`;
}

export function Fact({ text, claim }: { text: string; claim: Partial<Claim> }) {
  return (
    <li className={`fact ${claim.status ?? "unknown"}`}>
      <span>{text}</span>
      <small>{backing(claim)}</small>
    </li>
  );
}

export function kerbs(c: { curb_ramps?: Claim[] | Claim }): Claim[] {
  if (!c.curb_ramps) return [];
  return Array.isArray(c.curb_ramps) ? c.curb_ramps : [c.curb_ramps];
}

export function Conditions({ items }: { items: Condition[] }) {
  if (items.length === 0) return <p className="muted">{t("Nothing notable is recorded on this stretch.")}</p>;
  return (
    <ul className="facts">
      {items.map((c, i) => {
        const key = `${c.type}-${i}`;
        if (c.type === "crossing" || c.type === "unmapped_crossing") {
          const control = c.control?.value ? (CONTROL[String(c.control.value)] ?? String(c.control.value)) : "control not recorded";
          const name = c.type === "crossing" ? `Crossing${c.street ? ` of ${streetName(c.street)}` : ""}` : "Street crossing that is not mapped";
          return (
            <li key={key} className="group">
              <strong>{name}</strong>
              <ul>
                <Fact text={control} claim={c.control ?? { status: "unknown" }} />
                {kerbs(c).map((k, j) => (
                  <Fact key={j} text={k.value ? (KERB[String(k.value)] ?? String(k.value)) : "curb not recorded"} claim={k} />
                ))}
                {(c.ramp_checks ?? []).filter((k) => k.status !== "unknown" && k.value).map((k, j) => (
                  <Fact key={`check-${j}`} text={RAMP_CHECK[String(k.value)] ?? String(k.value)} claim={k} />
                ))}
              </ul>
            </li>
          );
        }
        const m = c.length_m != null ? `${Math.round(c.length_m)} m` : "";
        const text: Record<string, string> = {
          steps: `Steps (${m})`,
          steepest_sustained_grade_pct: `Steepest sustained slope ${c.value}%`,
          slope_unknown: `Slope not measured for ${m}`,
          no_sidewalk: `No sidewalk for ${m}`,
          sidewalk_one_side_recorded: `Sidewalk recorded on one side for ${m}; the other side is not recorded`,
          lowest_sidewalk_condition: `Lowest sidewalk condition on record: ${Math.round(Number(c.value))} of 100 (the survey's index, higher is better)`,
          narrowest_sidewalk_width_m: `Narrowest sidewalk on record: ${c.value} m`,
          inferred_link: `${c.count} short link${c.count === 1 ? "" : "s"} assumed walkable (gap in the map)`,
        };
        return <Fact key={key} text={text[c.type] ?? c.type} claim={c} />;
      })}
    </ul>
  );
}
