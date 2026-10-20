# PathFinder — Progress Log

A running record of what has been built, what we learned, and the decisions we made.
**Keep it current:** every meaningful change gets an entry in the same change that makes it.
See "How to update" at the bottom.

- Plan: [`PLAN.md`](PLAN.md)
- Generated evidence: [`../reports/`](../reports/)
- Where this came from: DistrictDirect's plan and log, in [`reference/`](reference/)

---

## Current status

| | |
|---|---|
| **Product** | **City accessibility app** (refocused 2026-10-15): step-free routes from mobility profiles first, plus a city barrier map. Dimensions: crossings & curbs / slope / sidewalk |
| **Phase** | C — Maryland sources, accessibility first: sidewalks, elevation (both towns), curb ramps and sidewalk condition and width (Frederick), signal locations (both towns) and sidewalks from the surveys (both towns) in. Each town passes 3 of 5 accessibility criteria |
| **Next** | Frederick is 7 trips short of criterion 4 and 3.2 points short of criterion 3: a brief to the City of Frederick (data permission, survey scope, a corner check from `reports/frederick/blocked/`). Data requests: SHA's ADA inventory (state-road curb cuts and pedestrian signals, internal only) and a Gaithersburg ramp inventory, neither published; signals with pedestrian features (APS, LPI) are open in neither town. Frederick's sidewalk evidence (56.8%) needs mapping beyond the survey |
| **Repo** | `C:\dev\PathFinder` (moved out of OneDrive 2026-10-19), its own git repository; no remote |
| **Tests** | 213 pass on the Frederick graph (unit and data-invariant; 1 skipped by design) |

### Key metrics over time

| Metric | Gaithersburg (OSM only) | Frederick (OSM only) |
|---|---|---|
| Walkable edges / nodes | 24,422 / 18,450 | 28,684 / 21,697 |
| Sidewalk-level share of walkable length (bar ≥ 50%) | **41.8% — misses** | **36.4% — misses** |
| Crossings with known control type (bar ≥ 60%) | 98.8% (73.0 verified + 25.8 inferred) — passes | 78.2% (63.7 verified + 14.5 inferred) — passes |
| Main component share of length (bar ≥ 90%) | 97.9% — passes | 96.8% — passes |
| *With each town's sidewalk survey (2026-10-15, after the divided-road fix)* | Montgomery Planning | City of Frederick 2025 |
| Sidewalk-level share (criterion 1 as written) | 41.8% — still misses | 36.4% — still misses |
| Centerline length with known sidewalk presence (OSM alone: 7.2% / 3.3%) | 16.4% | 17.6% |
| Walkable length with sidewalk evidence (sidewalk-level + centerlines with known presence; not a bar criterion) | 51.4% | 47.6% |
| Street centerlines (not service/alley) with known sidewalk presence | 34.1% of 270.7 km | 36.0% of 432.2 km |

**Accessibility bar** (fixed 2026-10-15, before any accessibility source; see Decisions log). All
figures inside the city line:

| Criterion | Gaithersburg 2026-10-15 | Gaithersburg 2026-10-16 | Frederick 2026-10-15 | Frederick 2026-10-16 | Frederick 2026-10-19 (Fort Detrick removed) |
|---|---|---|---|---|---|
| 1. Curb evidence at crossing ends, implicit included (≥ 60%) | 18.9% | 18.9% — misses (no ramp inventory) | 17.3% | **67.0%** (6,872 of 10,253) — passes | 69.3% (6,760 of 9,757) — passes |
| 2. Slope verified (≥ 80% of walkable length) | 0% | **89.4%** — passes | 0% | **96.0%** — passes | 95.8% — passes |
| 3. Sidewalk evidence (≥ 60% of walkable length) | 51.4%* | 52.5% — misses; **61.7% — passes** with sidewalks from the survey (see below) | 47.6%* | 50.8% — misses; 54.6% — still misses with sidewalks from the survey | 56.8% — misses |
| 4. Manual-wheelchair route exists, allow likely (≥ 50% of trip sample) | — | **2.7%** of 300 trips — misses (no ramp inventory) | — | **44.0%** of 300 trips — misses | 47.5% of 276 trips — misses (7 short) |
| 5. Main component (≥ 90%) | 97.9% | 97.9% — passes | 96.8% | 96.8% — passes | 96.9% — passes |

\* computed then over the whole graph, buffer included; the 2026-10-16 figures count only the
network inside the city line, as the other criteria do.

**Barrier map** ([Gaithersburg](../reports/gaithersburg/barriers/barriers.md), [Frederick](../reports/frederick/barriers/barriers.md); inside the city line):

| | Gaithersburg | Frederick |
|---|---|---|
| Recorded barriers: raised curb / no ramp; steps; no sidewalk | 0; 88; 64 (5.0 km) | 6; 57; 18 (1.0 km) |
| Unrecorded: crossing-end curbs; junction curbs; street sidewalks | 2,272; 2,996; 2,257 (123.2 km) | 3,479; 5,001; 3,360 (203.1 km) |
| *2026-10-16, with elevation and (Frederick) ramps:* | | |
| Missing ramp or raised curb: crossing ends; junction corners | 0; 0 | 50; 157 |
| Ramps failing the city's check; with no working tactile pad | — | 172; 1,047 |
| Steeper than 8.33% (verified edges) | 1,950 | 1,225 |
| Unrecorded crossing-end and junction curbs | 2,272; 2,996 | 1,142; 2,239 |
| *2026-10-16, with Frederick's sidewalk condition:* sidewalks with a condition index under 40 | — (no survey) | 310 (18.4 km) |
| Sidewalk length with a condition index on record (verified + inferred) | 0% | 63.1% (41.8 + 21.3) |

---

## Timeline

### 2026-10-15 — PathFinder created from DistrictDirect

- **Research** (three parallel passes over the code and the web, endpoints queried directly):
  the findings, sources and partner leads are in `PLAN.md`. Main corrections to the first
  write-up: statewide lanes/speed/AADT exist (MDOT SHA statewide Bicycle LTS, HPMS 2024,
  AADT through 2024); Montgomery's sidewalk survey is from 2023, not 2015; the old Frederick
  County ADA sidewalk service is gone, while the City of Frederick surveyed 6,366 curb ramps
  in 2025; statewide open crash data now needs a login; no Project Sidewalk in Maryland.
- **Region layer.** Everything place-specific moved into `regions/`: sources, boundary,
  buffer, map centre, which source plays each role (`graph/roles.py`) and where an inventory
  covers (`covered_<family>`). A role without a source grades nothing, so its attributes stay
  unknown, and a region without an inventory confirms nothing by absence (a painted crossing
  with no signal on record is `inferred` unsignalized). Without a roadway inventory, streets
  and their `lanes` / `maxspeed` come from OSM. Checked before the fork on DC: the DC graph
  rebuilt identical apart from two renames, and 200 tests passed.
- **OSM per town.** `pf fetch` cuts each town (city limits + ~1 km) out of Geofabrik's
  statewide extract by streaming it (`fetch.clip_pbf`, pyosmium `BackReferenceWriter`), so
  memory stays low; ways touching the box are kept whole.
- **Separate app.** Package `pathfinder`, command `pf`, env vars `PF_REGION`,
  `PF_DATA_DIR`, `PF_APP_PASSWORD`, venv `~/.venvs/pathfinder`, data `~/.pathfinder/data`.
  DC's region, sources, crime reader, crossing-risk study and reports were removed; the DC
  plan and log are kept in `docs/reference/`. The web page opens at the region's centre.
  DistrictDirect itself is unchanged.
- 176 unit tests pass in the new environment (incl. new ones: region config and paths, the
  OSM clip, OSM `maxspeed` parsing, and "no inventory" grading for signals, lights, stairs,
  crashes and crime).

### 2026-10-15 — Gaithersburg, OSM only: misses the bar on sidewalks

From [`reports/gaithersburg/phase0/coverage.md`](../reports/gaithersburg/phase0/coverage.md)
(OSM extract of 2026-10-15; city limits + 200 m):

- 24,422 walkable edges, 18,450 nodes; 972 km walkable, of which **407 km (41.8%) is
  sidewalk-level** and 566 km street centerline. The bar is 50%: **missed**. Crossing
  control is known for 98.8% of 1,358 mapped crossings (73.0% verified from OSM tags,
  25.8% painted with no signal on record, so only inferred: there is no signal inventory);
  the main component holds 97.9% of length. Both pass.
- What else OSM alone gives: crossed lanes on 28% of crossings and speed on 18%; curb
  evidence at 1–1.5% of crossing ends; sidewalk presence along 7% of centerline length;
  `lit` tags on 4.5%. 5,261 implicit-crossing ends at 2,487 junctions, 3,734 with no curb
  evidence. Slope, lights, AADT, crashes and crime: no source, all unknown.
- 1,297 pedestrian dead ends lie within 15 m of another walkway with no evidence of a link
  (no planimetric survey to bridge them).
- A trip from Kentlands to Olde Towne (5.4 km) plans end to end: 19 options; the recommended
  route takes 3.8 real minutes more and avoids about 30 felt minutes of crossings and 23 of
  accessibility, every condition sourced to OSM with its date; curb ramps show as unknown.
- 16 data-invariant tests pass on the Gaithersburg graph (one skipped by design).
- **Reading:** connectivity and crossing tags are good; separately mapped sidewalks cover
  under half the network, so Phase C's sidewalk sources (Montgomery Planning 2023
  planimetrics, Gaithersburg `Sidewalks_Public`) decide whether Gaithersburg is viable. Per
  the decision of 2026-10-15 the bar is not lowered; Gaithersburg goes on only if the
  planimetric survey lifts known sidewalk presence, which will be measured, not assumed.

### 2026-10-15 — City of Frederick, OSM only: also misses the bar on sidewalks

The first attempt was stopped by Claude Code during the OSM clip because the machine was low on
memory (not a pipeline failure); the rerun completed (clip 11.5 min, the rest 2.5 min). From
[`reports/frederick/phase0/coverage.md`](../reports/frederick/phase0/coverage.md) (same OSM
extract; city limits + margin):

- 28,684 walkable edges, 21,697 nodes; 1,399 km walkable, of which 509 km (**36.4%**) is
  sidewalk-level and 890 km street centerline (404 km of it with no sidewalk information;
  425 km of all walkable length is service roads). The bar is 50%: **missed**.
- Crossing control known for **78.2%** of 1,803 crossings (63.7% verified, 14.5% painted
  with no signal on record, inferred) — passes, though 21.7% stay unknown, against 1.2% in
  Gaithersburg. Main component **96.8%** of length (168 components) — passes.
- Thinner than Gaithersburg on every other OSM attribute: crossed lanes 22%, crossed speed
  16%, curb evidence 1.1–1.3% of crossing ends, centerline sidewalk presence 3.3%, `lit`
  0.7%, surface on 17% of pedestrian ways. 7,729 implicit-crossing ends at 3,519 junctions
  (5,667 with no curb evidence); 1,527 dead ends within 15 m of another walkway unbridged.
- A trip from downtown (39.4143,-77.4105) west to 39.4215,-77.4470 (4.1 km) plans end to
  end: 12 options; the recommended route takes 1.9 real minutes more and avoids 12.8 felt
  minutes, differing in 5 places.
- 16 data-invariant tests pass on the Frederick graph (one skipped by design).
- **Reading:** both pilots fail the same criterion and pass the other two. On OSM alone
  neither town is viable; Phase C's sidewalk sources decide it. For Frederick that is the
  City of Frederick Sidewalks service (unlicensed: internal until permission, rule 7), so
  the Vision Zero conversation (Phase E) moves earlier on the critical path.

### 2026-10-15 — Gaithersburg: Montgomery's sidewalk survey added (Phase C, step 4)

- **Sources.** `montgomery_sidewalks` (Montgomery Planning Sidewalks & Driveways, codes
  1206/1208, fetched for the town's box: 58,966 polygons) and `gaithersburg_sidewalks` (the
  city's Public Sidewalks, 5,081 polygons) registered; both unlicensed, internal only (rule 7).
  `arcgis_layer` sources can now be fetched for a box (`Source.bbox`) and drop fields on
  ingest (`Source.drop_fields`): both layers carried editor/staff identifiers, now never stored.
- **Checks before naming it.** (1) Against the city's own layer: 98.5% of the city's
  street-side sidewalk area lies within 1.5 m of a Montgomery polygon; 79 small city polygons
  (2,411 m²) have none within 3 m. Montgomery has more (state roads, private walks), so it
  plays `planimetrics` and the city layer stays a cross-check. (2) 24 sampled polygons drawn on
  MD iMAP six-inch imagery (about half the panels came back blank from the service): of the 18
  visible, 17 are real paved walking surface, 1 uncertain (#18, a 2014 street sidewalk that
  looks to sit on the road edge, 39.14352,-77.23573); 6 of 12 code-1208 samples are private
  front or patio walks.
- **Code 1208 is not a street sidewalk.** Counted as one, it put "both sides" on 20.5 km
  (322 edges) that 1206 alone did not; on imagery 11 of 12 sampled were parking aisles, lot
  roads and alleys, and the city's layer agreed on 5 of 322. Now only 1206 grades sidewalk
  presence; 1208 ("Non-Street Sidewalk") is walkable surface for gap bridging only
  (`roles.MONTGOMERY_CLASSES`, `build.WALKABLE_SURFACE`). Cost: Montgomery coded most
  polygons captured from 2017 on as 1208, so recent street sidewalks stay unknown.
- **Service roads and alleys are not graded from the survey.** With 1206 only, 5 of 6 sampled
  service edges reading "both sides" were wrong (a lot's aisle has building or street
  sidewalks within the 30 m probe reach); streets were right in 5 of 6, the exception a
  divided road whose probe reaches the far carriageway's sidewalk (39.14813,-77.23271).
  `enrich.NO_PLANIMETRIC_PRESENCE_KINDS`.
- **Dated by the polygons found, not the layer's newest capture.** The first run dated every
  result 2023; the polygons are mostly from 2014. Each street now carries the oldest capture
  beside it (median 2017 in the report; 2014 on most edges).
- **Planimetric coverage stays None.** The layer has no stairs or crosswalk class, so neither
  "no stairs on record" nor "no sidewalk here" is read from it: only "both sides" can be
  recorded; one side or none needs OSM.
- **Result** ([`coverage.md`](../reports/gaithersburg/phase0/coverage.md)): centerline sidewalk
  presence known on 22.3% of centerline length (7.2% with OSM alone): 85.3 km "both" from the
  survey. Sidewalk-level share is unchanged at **41.8%** (the survey adds no walkways, so
  criterion 1 as written cannot move). Sidewalk evidence of either kind covers **54.9%** of
  walkable length; street centerlines other than service roads and alleys: 46.5% known.
  Surface-gap bridging now runs: 195 more inferred connectors, unbridged near dead ends
  1,297 → 1,101. Kentlands → Olde Towne: 19 options, recommended +3.8 min, avoids 41.4 felt
  minutes (was about 53: fewer unknown sidewalks on the fast route).
- 179 unit tests and 16 data-invariant tests pass (new: adapter classes and dates, editor
  fields dropped, service roads not graded and per-street dating).

### 2026-10-15 — Criterion 1 stands; divided roads fixed; Frederick's 2025 survey added

- **Criterion 1 stands as written** (owner delegated the call). It counts separately mapped
  walkways; reading it after the fact as "sidewalk evidence of any kind" would move the bar
  once Gaithersburg's number was known, which the bar was fixed in advance to prevent. Both
  pilots stay recorded as missing it. Sidewalk evidence is reported beside the bar (Key
  metrics) as information, not as a criterion. Work continues in Phase C, which this miss does
  not gate; the Phase D decision gate still requires both pilots to clear the bar.
- **Divided roads.** On a one-way carriageway with a parallel one-way twin, the probes toward
  the twin now stop halfway to it (`enrich.divided_road_reach`, `DIVIDED_TWIN_MAX_ANGLE_DEG`
  = 20°; `build.sidewalk_side_coverage` takes a reach per street and side). Before, 36.7 km of
  Gaithersburg's 85.3 km survey "both sides" were divided-road halves that borrowed the far
  carriageway's sidewalk; a road with one sidewalk would have given it to both halves. Now
  51.7 km; a half with a sidewalk only on its outer side stays unknown (one side cannot be
  recorded without coverage). Gaithersburg: centerline presence known 22.3% → **16.4%**,
  sidewalk evidence 54.9% → **51.4%** (supersedes the figures in the entry above).
- **Survey connectors inspected.** 12 of the 195 Gaithersburg connectors bridged across survey
  surface, drawn on imagery: all 12 run on visible paved walk (mostly front or building walks
  joining a sidewalk; one joins two pieces of one sidewalk). Median 5.5 m, longest 14.4 m.
- **Coverage flag.** `crossings_marked_in_osm_without_planimetric_crosswalk` now reads n/a
  when the planimetric source records no crosswalks (`coverage._planimetric_has`).
- **Frederick: City of Frederick Sidewalks** (`frederick_sidewalks`; 4,649 segment lines,
  552 km, all inside city limits, median 5.9 m from a street centerline; condition index, width,
  surface; unlicensed, internal only). The records carry no date, so each is dated by its
  first survey photo: new fetch kind `arcgis_first_date` reads the earliest
  `Date_Time_Operation` per `Segment_ID` from the survey's photo layer (311,547 photos,
  2025-03-25 to 2025-05-23) as `frederick_sidewalk_photos`. 3,834 segments (471 km) were
  photographed; the 815 that were not (82 km, nearly all with no width or surface recorded)
  have no date and are not used. Lines become surface polygons at their recorded width, 4 ft
  where none is recorded (`roles.frederick_planimetrics`). Coverage stays None.
- **Checks.** Segments drawn on imagery: the visible ones lie on real sidewalks, including
  two unphotographed downtown segments (left out anyway: undated). 12 sampled streets graded
  "both sides": 11 correct, 1 shows a sidewalk on one side only (arterial at
  39.40686,-77.38697).
- **Result** ([`coverage.md`](../reports/frederick/phase0/coverage.md)): centerline presence
  known on 17.6% of centerline length (3.3% with OSM alone), 127.2 km "both" from the survey,
  dated 2025; sidewalk-level share unchanged at 36.4%; sidewalk evidence 47.6% of walkable
  length; streets other than service roads and alleys 36.0%. 9 connectors bridged across
  survey surface. Downtown → west trip: 15 options, recommended +1.9 min, avoids 12.9 felt
  minutes.
- **Imagery for inspections:** MD iMAP `SixInch/SixInchImagery2023_2024_2025` returns imagery
  where the combined `SixInchImagery` service returns blank tiles; Esri World Imagery returned
  server errors in EPSG:26985 for Frederick.
- 181 unit tests and 16 data-invariant tests pass on each pilot graph (new: Frederick adapter
  dating and undated segments dropped, divided-road halves).

### 2026-10-15 — Refocused as a city accessibility app

Owner's direction: "more of a city accessibility app". The owner chose both faces, routes
first, and folded crossings into accessibility, removing after-dark and crime.

- **Cost model v5** (`routing/cost.py`):
  - The three dimensions are **crossings & curbs** (control, distance, speed, and the curbs
    moved in from accessibility), **slope**, and **sidewalk**.
  - The sidewalk dimension covers walking in the roadway and missing sidewalk, as one table
    summing the two old ones. It also covers surface, obstacles, and steps when step-free is
    not required.
  - After-dark and reported-crime penalties are gone, and so is `night`.
  - The router, the triangle, "what would it take" and the crux code are unchanged in method.
- **Pipeline:** lighting, crash and crime enrichment were removed, along with the `lights`,
  `crashes` and `high_injury_network` roles and the `lights` coverage family. The coverage
  report's lighting map is replaced by a sidewalk-evidence map.
- **Mobility profiles** (`routing/profiles.py`):
  - The profiles are manual wheelchair (step-free, ≤ 8.33%), power wheelchair or scooter
    (step-free, ≤ 12%), walker or cane (no requirement), stroller (step-free) and custom,
    each with a starting mix.
  - They are available in `pf route --profile`, as `profile` on `/api/plan` (explicit fields
    win), and listed in `/api/region`.
- **City barrier map** (`analysis/barriers.py`):
  - **What it lists:** raised curbs and missing ramps at crossing ends and junctions, grades
    over 8.33%, steps, and streets with no sidewalk. Each unrecorded curb and street sidewalk
    is listed beside them.
  - **Report:** `pf barriers` writes `reports/<region>/barriers/` (summary, census-tract
    table, map), marked internal under rule 7.
  - **API:** `/api/barriers?bbox=` serves the same features with complete per-type counts.
    When capped, it keeps every barrier and spreads the cap over the unknown types.
- **Census tracts:** 2020 tracts (TIGERweb, public domain) are registered as each pilot's
  `report_districts`, so coverage and barriers break down by tract.
- **Web app:**
  - **New controls:** a "How I get around" profile picker, triangle corners Crossings &
    curbs / Slope / Sidewalk, and a Barriers tab. In that tab the trip steps aside and a
    tap shows a barrier's source and date.
  - **Theme:** the night toggle is replaced by a dark theme that follows the phone.
  - **Removed:** the crime opt-in.
  - **Checks:** built and checked at 390 px in headless Edge (no horizontal overflow; routes,
    profiles and the barrier map all render).
  - **Bug found and fixed:** the barrier layers first failed silently because a zoom
    expression was nested inside `match`.
- **Rules:**
  - Rule 3 (crime) became "a profile is a starting point".
  - Rule 4 now forbids *accessible*, *ADA-compliant* and *safe* as claims. The plan's
    disclaimer says PathFinder certifies no route or place as accessible.
- **What it shows today:** no step-free route can be confirmed in either town at "recorded or
  likely". Manual-wheelchair and stroller trips (Kentlands → Olde Towne; downtown Frederick →
  west) both end in "no route meets everything", offering "accept places with no
  evidence". The cause is curb evidence: 32 of 2,308 mapped crossing ends in Gaithersburg
  and 43 of 3,522 in Frederick. This is the router keeping rule 1, not a bug. It puts curb
  ramps and elevation first in Phase C.
- 193 tests pass on each pilot graph: new tests for the dimensions, profiles, the API's
  profile handling, barrier extraction and the barrier API. The crime and lighting tests are
  removed.

### 2026-10-16 — Elevation for both towns, curb ramps for Frederick

- **Elevation.**
  - **Services:** MD iMAP's county `dem_m` services (heights in metres). At Olde Towne the
    metre service read 152.2 m against 499 ft on the `_ft` service.
  - **How it is fetched:** `fetch_image_service` now cuts to a source's `bbox` and asks the
    server to export on the 1 m EPSG:26985 analysis grid. That avoids Montgomery's 1 ft
    EPSG:2893 grid and the whole county. Gaithersburg is 25 tiles (300 MB), Frederick 49
    (475 MB). The terrain sanity range is now Maryland's (−50 to 1,100 m; was DC's −100 to
    500).
  - **Dates:** Montgomery was flown late 2020 to early 2021, dated "2020" (the service gives
    no day). Frederick is USGS MD Western 2021, work unit MD_Western_2, flown 2021-12-14 to
    21 (NOAA InPort 70420), public domain.
  - **Result:** slope is verified on 89.4% of Gaithersburg's network and 96.0% of
    Frederick's. Median verified grade is 3.6% and 2.8%. Steep (over 8.33%) is 1,398 edges
    (80 km) and 938 (75 km) inside the line. Sixteen of them, drawn on the county hillshade,
    lie on visible slopes and embankments.
  - **Open:** 14% and 22% of steep edges are flat on average (under 2%) with one steep 10 m
    window. Some are real short ramps up terraces; some are on ground regraded since the
    flight (a subdivision built after 2021 at 39.46288,-77.45099). They pass the three-line
    rule and stay verified, dated by the flight; this is an open issue.
- **City of Frederick curb ramps** (`frederick_ramps`; 6,366 records, each dated 2025-03-18 to
  2025-06-10; unlicensed, internal):
  - **"No ramp" corners:** "No ramp" (187) is a surveyed corner without a ramp, so `no_ramp`.
  - **The city's verdict:** it becomes graded `ramp_check_a/b`: passed (2,435), fails (Fail on
    a ramp, Combination_No_landing, Damage_Need_Repair: 283), no_tactile_pad (3,457; every
    passing ramp has a pad, so the pad is the defect).
  - **Field not used:** `Landing_Cross_Slope` reads "No" on 847 passing ramps, so its meaning
    is unclear and it is not used.
  - **Failing ramps:** a failing ramp stays usable: it costs `PENALTIES["crossing"]["ramp_fails"]`
    = 40 felt s (penalty v6) and is listed on the barrier map.
  - **Junctions:** at junctions the survey's ramps and missing ramps feed `ramp_likely` and
    `no_ramp_reported`.
  - **Checks:** 2,381 of 3,606 mapped crossing ends have a record within 8 m. Twelve records
    drawn on 2023–25 imagery (4 no ramp, 4 failing, 4 passing) all sit at real curb
    transitions.
  - **Result:** Frederick's crossing-end curbs are known for 67.6% (was 1.3%).
- **First confirmed step-free routes.** In Frederick the manual-wheelchair, power-wheelchair
  and stroller profiles now plan the downtown → west trip (19, 21 and 26 options). Every
  crossing shows its control (OSM 2026), its ramps and the city's verdict (2025), and the
  steepest grade (DTM 2021). Gaithersburg still has none: no ramp inventory.
- **Trip sample** ([`reports/frederick/phase0/crux.md`](../reports/frederick/phase0/crux.md),
  100 trips per distance band, 300 in all, not the default 334 per band, for memory):
  - a manual-wheelchair route (step-free, 8.33%, allow likely) exists for **44.0%**;
  - 75.3% if unknowns are accepted;
  - 0% verified-only, because implicit junction crossings are never verified;
  - when it differs from the fastest, an alternative is worth showing for 74.2%.
  - Of the infeasible trips, 92 need only unknowns accepted (mostly unrecorded curbs), 26
    are blocked by grade, and 50 by no single change.
- **Barrier map** gains ramps that fail the city's check and ramps with no working tactile
  pad (`ramp_fails_check`, `ramp_no_tactile_pad`), with source and date. The web legend and
  the crossing facts show the verdict.
- 196 tests pass on each pilot graph (new: ramp adapter, the failing-ramp cost, the ramp
  barrier types, elevation sources cut and dated).

### 2026-10-16 — State-road data is not public; Frederick sidewalk condition and width in

- **MDOT SHA curb cuts and accessible signals: not available.** The public
  `OMOC/Sidewalk_Public` service has 8 curb cuts in the whole state (all in Charles County)
  and 1,121 crossings, none in either pilot; only its sidewalk lines reach them (450 and 355).
  SHA's ADA inventory ("Handicap Ramps", "Pedestrian Signals") is published only on its
  internal server (`ADA_Maryland_SHA` on `shagbegis1`, as listed in the locked "ADA Compliance
  Viewer"), and `OHD_ADA` needs a token. The SHA bike/ped crossings layer records markings
  only, which OSM already gives. Nothing was loaded; a data request to SHA is the way in.
- **No Gaithersburg ramp inventory either.** None on the city's server or ArcGIS Online;
  Montgomery DOT's "ADA Curb Ramp Requests" are residents' requests, not an inventory.
- **City of Frederick sidewalk condition and width** (from the survey already fetched):
  - **The index:** `SCI` is the city's Sidewalk Condition Index (0–100, higher is better).
    The city has published no category cutoffs. Reporting gives a city average of 78,
    "satisfactory", with 36% "fair, poor or very poor" ([WYPR, 2026-08-27](https://www.wypr.org/wypr-news/2026-08-27/frederick-sidewalk-study-reveals-millions-needed-for-repairs)).
    In the data, 17–24% falls below 70 and 45–51% below 86 (by length or by count), so the
    cutoffs cannot be recovered. Only the number is shown, never a category word.
  - **Fill value:** exactly 85.999 on 1,208 of 4,649 segments, photographed or not, so it is
    not read as a score. Width 0 is not recorded.
  - **Matching:** sidewalk-level edges within 3 m of a surveyed line are graded `verified`.
    At 3 m, 229 of 327 km of OSM sidewalks match, and 10 m adds only 4 km. Streets with a
    sidewalk on record take the worse side's value, `inferred`. Several segments give the
    lowest value; any segment without a value leaves the edge unknown.
  - **Result:** the condition index is on record for 63.1% of sidewalk length (41.8% verified,
    21.3% inferred); width for 56.4%.
  - **Imagery check:** 16 sampled edges, 12 sidewalk-level (4 under 40, 4 from 40 to 70, 4 of
    90 or more) and 4 inferred streets, all sit on or beside their surveyed lines. Imagery
    shows placement, not condition.
  - **Cost (penalty v7):** felt seconds per 100 m by band: 70 or more 0, 55–70 10, 40–55 25,
    under 40 45, unknown 5. These are product judgments.
  - **Barrier map:** gains `sidewalk_poor_condition` (index under 40: 310 edges, 18.4 km) and
    `sidewalk_narrow` (under 1.2 m: none recorded; the survey's narrowest is 4 ft).
  - **Routes and the web app:** each route gives the lowest index and the narrowest width
    along it, with source and date, and the web app's legend and facts show them.
- **Trip sample** (Frederick, 300 trips, v7): manual-wheelchair feasibility is unchanged at
  44.0%, since condition changes costs, not requirements. The route differs from the fastest
  in 83.3% of feasible trips (81.8% under v6), and 74.2% are worth showing.
- 201 tests pass on each pilot graph (new: condition matching, the worse side, no survey
  means unknown, the fill value, the condition cost and barriers).

### 2026-10-16 — Montgomery signal locations for Gaithersburg; first Gaithersburg trip sample

- **Source:** `montgomery_signals`, MCDOT's Bill 11-23 review layer, 936 signals county-wide
  and 160 in the Gaithersburg box (county, SHA and city owned). No license is stated, so it
  is internal use only. Its records carry no dates; it is dated by the layer's last data edit,
  2023-11-09. dataMontgomery and ArcGIS Online hold no other Montgomery signal inventory.
- **No pedestrian features:** `Exist_LPI` and `Exist_NToR` are empty on all 160 and there is
  no APS field, so LPI, APS and HAWK stay unknown (PLAN.md had listed APS for this layer in
  error). This exposed a bug, now fixed: an empty inventory field was read as "no".
- **Checked against OSM and imagery:**
  - 81 of the 84 records inside the line sit within 30 m of an OSM signal node.
  - Of OSM's 84 signalized intersections, 17 have no record. Most are I-270 ramp signals and
    ramp meters, but at least 5 are real intersections with crosswalks (e.g. 39.13494,-77.22975
    and 39.15257,-77.21208).
  - So the inventory is not complete. It counts as positive evidence only, and signal coverage
    stays None: "no signal on record" proves nothing.
- **Use:** never makes a mapped crossing a signal (OSM must say so, as before). At street
  junctions crossed without a crossing edge, a record within 30 m gives an `inferred` signal,
  now sourced and dated in routes (it was labelled `traffic_signals`, a DC id, with no date).
  - 167 junctions get one. All 16 sampled on imagery are inside signalized intersections; the
    8 "service" ones are signalized driveway approaches.
  - Mapped-crossing grades are unchanged (73.0% verified, 25.8% inferred).
- **First Gaithersburg trip sample** ([`reports/gaithersburg/phase0/crux.md`](../reports/gaithersburg/phase0/crux.md),
  300 trips, v7):
  - a manual-wheelchair route (allow likely) exists for **2.7%**, which misses criterion 4;
  - 70.7% if unknowns are accepted;
  - of the infeasible trips, 199 need only unknowns accepted (unrecorded curbs: no ramp
    inventory), 82 have no single fix, and 11 involve grade.
- 204 tests pass on each pilot graph (new: the Montgomery adapter, empty fields stay unknown,
  the region names the inventory but not its absence).

### 2026-10-16 — Frederick County signal locations; driveways no longer borrow a signal

- **Source:** `frederick_county_signals`, Frederick County DPW `Traffic_Signals`, 94 records
  in the Frederick box and 75 inside the line, 71 of them maintained by the city. No license is
  stated, so it is internal use only. The city publishes no signal layer of its own; the
  county's `NonCountyTrafficSignals` service is empty.
- **No pedestrian features:** pedestrian-crossing and signal-head counts are blank on most
  records, and there is no APS or LPI field. The county's Cartegraph `DPW/Signals` lists 43
  pedestrian buttons in the box, county-maintained, 1 marked audible: too few to use.
- **No date:** the layer has no edit date (activation dates 2006–2011 on 4 records). A
  record is used only where an OSM signal node lies within 30 m, and is dated by the OSM extract
  (`AS_OF_OSM`). 88 of the 94 records (full signals only, not school beacons) pass.
- **Checked against OSM:**
  - 73 of the 75 records inside the line sit within 50 m of an OSM signal (median 3 m).
  - 45 of OSM's 116 signalized intersections have no record, mostly state roads. Coverage
    stays None.
- **Driveway fix (both towns):** imagery of 16 Frederick junctions given a signal showed
  parking-lot entrances 25–29 m down the street signalized by the 30 m radius (e.g.
  39.42303,-77.41195). Gaithersburg's sample had not caught it.
  - A junction that is not a street intersection now needs its signal within 15 m
    (`DRIVEWAY_SIGNAL_RADIUS_M`); legs of signalized intersections sat 4–14 m from the record.
  - Signalized junctions: Frederick 58 (75 before the fix), Gaithersburg 159 (167 in the
    entry above).
  - 15 of 15 resampled Frederick junctions sit inside signalized intersections. The City of
    Frederick's Aerial_2025 was used: MD iMAP's six-inch service returned blank tiles.
- **Trip samples** (300 trips each, rerun with the signals):
  - manual-wheelchair feasibility is unchanged (Frederick 44.0%, Gaithersburg 2.7%): signals
    change costs, not requirements;
  - in Frederick an alternative is worth showing in 75.8% of feasible trips (74.2% before).
- 206 tests pass on each pilot graph (new: the Frederick adapter, the driveway rule).

### 2026-10-16 — Sidewalks from the surveys (owner's choice): one-side evidence and estimated lines

- **Owner's decision:** of the two routes to criterion 3 (estimate sidewalks from the surveys,
  or map them with partners), the owner chose the surveys.
- **Design:**
  - **Why not routable lines:** routable sidewalk lines beside each street were considered and
    rejected. Every line would have to bend back to the junction node, giving a false turn at
    each junction; streets made of lines would drop out of the count that prices crossings at
    junctions; and a street with both sides would count twice in every length share.
  - **What the router walks:** the street centerline, as before.
  - **What is recorded:** the survey's evidence goes on the centerline.
  - **What is drawn:** the lines are a map layer.
- **`at_least_one_side`:**
  - **The old rule:** outside inventory coverage a survey could record only "both"; a street
    with a sidewalk found on one side stayed unknown, because `one_side` says the other side
    has none.
  - **The new value** says only what the survey shows: a sidewalk on at least one side, the
    other not known. It is verified, from the survey and its date, and priced as `one_side`
    (penalty v8). Routes say "Sidewalk recorded on one side; the other side is not recorded".
- **15 m limit:**
  - **What imagery showed:** of one-side finds farther than 15 m from the street, 6 of 8
    sampled in Gaithersburg were building-front walks across a parking lot, or the far side of
    a divided road (e.g. Lost Knife Circle, 39.15742,-77.20235). All 8 under 5 m were sidewalks
    at the curb.
  - **The rule:** a one-side find counts only within 15 m (`ONE_SIDE_MAX_OFFSET_M`; about 4% of
    finds lie farther out), and no line is drawn beyond it.
  - **What was left alone:** two-sided finds keep the 30 m reach decided earlier.
- **Estimated sidewalk lines** (`graph/survey_sidewalks.parquet`):
  - **Where:** one per street side where the survey shows a sidewalk and OSM maps none. They are
    drawn at the survey's distance from the street, status `inferred`, with the survey's source
    and date.
  - **How many:** Gaithersburg 1,788 lines (123.0 km); Frederick 2,369 (199.9 km).
  - **Imagery check:** on two-sided streets, 16 of 16 sampled lines lie on the survey's
    sidewalk; some one-side lines sit 2–4 m off.
  - **Where they appear:** dashed green in the web app's Barriers tab, with a fact card; in
    `/api/barriers` as `sidewalks`, beside the barriers, never counted as one; and in the
    coverage report's `map_estimated_sidewalks.png`.
- **The bar in the coverage report:** `pf coverage` now writes criteria 1, 2, 3 and 5 into
  `coverage.md`; until now they were computed by hand. It reproduces the earlier criterion 1
  exactly (1,226 of 6,498 and 6,872 of 10,253 ends).
- **Criterion 3, sidewalk evidence (bar 60%):**

  | Town | Before | Now | Sidewalk-level ways | Streets with presence recorded | of which at least one side only |
  |---|---|---|---|---|---|
  | Gaithersburg | 52.5% | **61.7% — passes** | 42.6% | 19.1% | 9.4% |
  | Frederick | 50.8% | 54.6% — misses | 38.9% | 15.7% | 3.9% |

  - **Frederick's gap:** mostly service roads and parking aisles no survey grades (about 417 km),
    and streets where the city's survey shows no sidewalk on either side (about 135 km), which
    the survey cannot call "none".
- **Trip samples** (300 trips each, v8): manual-wheelchair feasibility is unchanged
  (Gaithersburg 2.7%, Frederick 44.0%), since presence changes costs, not requirements.
- **Checks:** 210 tests pass on each pilot graph. New tests cover at least one side, the 15 m
  limit, lines on the survey side and not where OSM maps one, the price, and the API key.
  - Two older tests encoded "only both outside coverage" and were restated for the new rule.
  - The web app passes at 390 px with no overflow.
- **Memory:** the first run of both towns was stopped by Claude Code for low memory; rerun one
  step at a time.

### 2026-10-16 — The City of Frederick sidewalk survey is not complete: its silence stays unknown

- **The bar**, fixed in the Decisions log before measuring: silence counts as "no sidewalk"
  only if (1) at least 95% of OSM-mapped sidewalk along public streets inside the line lies
  within 5 m of a survey line, and (2) at most 2 of 40 imagery-sampled silent street sides show
  a sidewalk.
- **Test 1 fails:**
  - Of 298.3 km of OSM sidewalk along public streets (midpoint within 20 m of an OSM street)
    inside the line, 265.2 km lies within 5 m of a survey line: **88.9%**. Counting only the
    dated segments (those with a survey photo) gives 77.3%.
  - 654 OSM sidewalk edges (26.9 km) are less than 20% covered.
- **Test 2 not run:** with test 1 failed, the result could not change.
- **What the survey misses** (12 sampled misses on the City of Frederick's Aerial_2025; MD
  iMAP returned blank tiles):
  - **8 are sidewalks along public streets:** Porter Street, South Wisner Street, Himes Avenue,
    a gap on East 4th Street, the New Design Road bridge over US 15, and newer developments
    (Blandwood Road, Pangborn Park Drive, Christophers Crossing).
  - **4 are walks a city survey need not hold:** campus and private-complex walks (Hood College
    on Hodson Drive, Evergreen Avenue, Falcon Lane) and a small plaza on North Market Street.
- **Result:**
  - Planimetric coverage for Frederick stays None. "No sidewalk on record" proves nothing, and
    the 135 km of streets where the survey shows no sidewalk stay unknown.
  - Criterion 3 stays at 54.6%.
- **What would change it:** the city's own list of which streets the 2025 survey covered (the
  O'Connell & Lawrence scope), or a survey update for streets built since. With a stated
  scope, silence could count inside that scope only.

### 2026-10-16 — Aerial-imagery sidewalk pilot prepared (Tile2Net, Frederick); awaiting the Colab run

- **Method and setup:**
  - **Model:** Tile2Net (BSD-3), owner's choice of a free Colab GPU: this laptop has only
    Intel graphics and often under 0.5 GB of memory free.
  - **Notebook:** `tools/tile2net_pilot/frederick_pilot.ipynb` exports MD iMAP six-inch
    imagery per zoom-19 tile in Web Mercator. The service's own cache grid has a
    non-standard origin, so its tiles do not line up with Tile2Net's.
  - **What Colab sees:** only public imagery and the cell bounds.
- **Bar, decision rule and pilot cells:** fixed in the Decisions log before anything was run;
  the bar was amended before any detection existed (see there).
- **Test set** (frozen; three cells, 1 km each):
  - 60 street sides where the city survey and an OSM sidewalk agree there is one.
  - 148 sides where both are silent, hand-labelled on MD iMAP: 65 no sidewalk, 36 sidewalk,
    47 cannot tell (canopy, cul-de-sac centres, construction).
- **Already a finding:** of the silent sides that could be judged, 36 of 101 (36%) do have a
  sidewalk, consistent with the survey's failed completeness check.
- **Scoring:** `tools/tile2net_pilot/score.py`, written and dry-run before any detection. With
  the survey itself as the stand-in "detector" it fails the amended bar ("no sidewalk" answers
  64% correct), as it should.

### 2026-10-17 — Imagery sidewalk pilot run and scored: fails its bar; not used

- **Run on this laptop instead of Colab** (owner's call):
  - Tile2Net 0.5.0, unmodified model and checksum-verified weights, inference on the CPU.
  - The package refuses to run without CUDA; a local patch in the scratch copy (outside the
    repo) turns `.cuda()` into a no-op and loads images without worker processes (Windows
    workers ran out of memory). The steps otherwise follow the notebook.
  - Imagery: 3 × 324 zoom-19 tiles from MD iMAP 2023–25, none missing.
  - About 20 min per cell.
  - Detected: 768 sidewalk, 187 road and 94 crosswalk polygons.
  - Tile2Net 0.5 writes polygons as parquet; they were repacked as GeoPackage for the frozen
    `score.py`, which was not edited (sha256 2198ec16…, test set 9fa22247…, both checked
    before scoring).
- **Result, over every labelled side (amended bar):**

  | Answer | Given | Correct | Bar (≥ 30, ≥ 95%) |
  |---|---|---|---|
  | "sidewalk" | 70 | 60 (85.7%) | misses |
  | "no sidewalk" | 49 | 41 (83.7%) | misses |

  - Abstained on 42 of 161 sides.
  - Wrong answers: 10 of 65 sides with no sidewalk were called "sidewalk"; 6 survey+OSM
    sidewalks and 2 of the 36 sidewalks the survey misses were called "none".
  - On the sidewalks the survey misses, 22 of 36 were found, 12 abstained.
- **Decision:** the bar is not moved. Detections are not used, not even as `inferred`, and the
  20-answer imagery check is not run. Frederick's criterion 3 stays at 54.6%.
- **What it shows:** the model finds most of the sidewalks the survey misses, but about one
  answer in seven is wrong either way, too many to mark a street side for a wheelchair user.
  A model fine-tuned on Maryland imagery, or detections used only as a survey worklist for
  partners (where a wrong answer costs a check, not a route), would be separate decisions.

### 2026-10-17 — Retraining prepared (owner: fine-tune); awaiting the Colab run

- **Protocol:** fixed in the Decisions log before any training data was built.
- **Chips:** 1,081 chips lie inside the two city lines, clear of the test-cell buffer. Of them,
  111 qualify, where OSM and the survey agree:
  - Frederick: 86 (62 train, 24 validation).
  - Gaithersburg: 25 (23 train, 2 validation). Montgomery's 2014/2017 capture agrees with OSM less
    often.
- **Labels:** OSM-only masks, checked on imagery on 3 random chips. Sidewalks are drawn on the
  sidewalks. Paths and crossings are greyed out. A few unmapped sidewalks are labelled "not
  sidewalk", which is noise the protocol accepts.
- **Code** (`tools/tile2net_pilot/retrain_lib.py`):
  - Smoke-tested on the CPU: all 1,903 released tensors load, it trains, validates, resumes, and
    saves in Tile2Net's format.
  - Its forward pass reproduces Tile2Net's own inference on a stitched pilot image (IoU 0.90 with
    the released polygons, both 3.8% sidewalk).
  - Local inference now refuses to run if any weight fails to load. Tile2Net skipped missing weights
    silently.
- **Next:** the owner runs `retrain_colab.ipynb` on a T4 GPU. Then local inference on the three test
  cells and one scoring run.

### 2026-10-19 — Retrained model scored once: fails its bar; imagery sidewalks not used

- **Training, on a Kaggle GPU instead of Colab** (owner's call, so the run could be driven from here):
  - The same `retrain_lib.py` and protocol, in a private Kaggle notebook on one T4.
  - Uploaded as a private Kaggle dataset: the 111 chips' bounds, OSM-only masks and the public MD
    iMAP chip images. The images were fetched on the laptop; no survey data was uploaded.
  - Batch 2 fitted, so the out-of-memory fallback was not used. 15 epochs, about 48 s each.
  - Validation sidewalk F1 (pixels against the OSM masks): released weights 0.542, best epoch 5
    0.745 (precision 0.60, recall 0.97). Epoch 5 was kept, chosen on validation only.
  - `best.pth` sha256 d165142c…, checked after download.
- **Inference:** local, on the CPU, with the same patched Tile2Net as on 2026-10-17. The log confirms
  `best.pth` was loaded, and the loader refuses to run if any weight is missing.
  - Detected: 515 sidewalk, 285 road and 80 crosswalk polygons (the released model: 768 / 187 / 94).
- **Scored once** with the frozen `score.py` (sha256 2198ec16…, test set 9fa22247…, both checked
  first):

  | Answer | Given | Correct | Bar (≥ 30, ≥ 95%) |
  |---|---|---|---|
  | "sidewalk" | 115 | 93 (80.9%) | misses |
  | "no sidewalk" | 26 | 26 (100%) | misses: too few answers |

  - Abstained on 20 of 161 sides.
  - Wrong answers: 22 of the 65 sides with no sidewalk were called "sidewalk".
  - Every survey+OSM sidewalk was found, and 33 of the 36 sidewalks the survey misses.
- **Decision:** per the protocol, the model is not used, the 20-answer imagery check is not run, and
  this test set is spent for imagery models. Frederick's criterion 3 stays at 54.6%.
- **What it shows:** fine-tuning made the model find sidewalks almost everywhere they are, but it
  now also reports them on a third of the street sides that have none. Its "no sidewalk" answers
  were all right, but there were too few of them to pass the bar.

### 2026-10-19 — Repo out of OneDrive; Fort Detrick removed from Frederick; what blocks wheelchair trips

- **Repo:** first commit (`5139ac0`, branch `feature/initial-platform`), then moved from
  `OneDrive\Desktop\CongoApp` to `C:\dev\PathFinder` (git clone; contents checked identical). The
  venv's editable install points at the new path; 210 tests passed there before any change.
- **What blocks the trips:** `tools/blocked_trips/blocked_trips.py` (new) reruns each trip with
  no manual-wheelchair route under looser settings, and lists every place on the cheapest route that
  fails the real requirement (`reports/frederick/blocked/`, internal).
- **Fort Detrick bug, found by that breakdown:**
  - The largest gap, tract 751201 with 240 trip links, was Fort Detrick, a closed Army post inside
    the city. Its streets were routed and sampled as public walkways.
  - On imagery, 6 of 10 sampled worklist corners were behind the base fence (boulder-lined roads,
    pipe racks, guard posts).
  - Cause: OSM maps the base only as a multipolygon relation (5872336, `landuse=military`), and the
    town clip dropped every relation. Its streets carry `access=yes`.
  - Fix: the clip keeps `landuse=military` relations. `pf extract-osm` writes them, and
    `build.drop_restricted` removes every edge at least half inside. Frederick lost 805 edges
    (60.3 km). Tests: 213 pass.
  - Gaithersburg's clip touches no military area, so its network is unchanged.
  - The OSM extract was not re-downloaded: same file, same 2026-10-15 date.
- **Frederick's bar, rebuilt** (`pf build-graph` → `pf crux --fresh`):

  | Criterion | Before | After |
  |---|---|---|
  | 1. Curb evidence | 67.0% (6,872 of 10,253) | **69.3%** (6,760 of 9,757) — passes |
  | 2. Slope verified | 96.0% | 95.8% — passes |
  | 3. Sidewalk evidence | 54.6% | **56.8%** — misses |
  | 4. Manual-wheelchair route | 44.0% of 300 trips | **47.5% of 276** — misses |
  | 5. Main component | 96.8% | 96.9% — passes |

  - 24 of the 300 fixed trips had an end on the base and are left out by the sample's existing rule
    (an end more than 30 m from the network).
  - Barrier map: unrecorded crossing-end curbs 1,142 → 1,122, junction curbs 2,239 → 1,875,
    steep edges 1,225 → 1,199.
- **What blocks the 145 trips still without a route:**
  - 73 trips are blocked only by places with no record: curbs at 380 places, slope unknown at 6.
  - 67 trips also need a measured slope over 8.33%.
  - 5 trips have no step-free route at all.
  - Only 27 trips touch a trunk or primary road (mostly state roads). The missing MDOT SHA inventory
    is not the main blocker.
  - Inside the city line, 251 blocking curbs have no record, and 170 of them have no ramp-inventory
    record within 50 m: the city's survey does not reach them. 74 trips touch places outside the
    line, which the city does not survey.
  - The worklist holds 14 places, 6 inside the line. They would open the 7 trips the bar needs if
    every one had a usable ramp. Imagery of the 9 that loaded: 4 look likely to have ramps (newer
    streets with crosswalks), 4 look unlikely (no sidewalk on one side). A realistic check is a few
    dozen corners, and some of the gap is missing sidewalk, not missing records.
  - Not a bug: 146 unknown crossing ends have a ramp record within 3 m of a crossing node. That
    record is the ramp at the opposite curb; the city recorded one side only.
  - Not changed: some crossing ends are 8–12 m from a city ramp record, beyond the 8 m match radius
    calibrated on DC. Widening it needs an imagery check first.

---

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-10-15 | **Go/no-go bar for an OSM-only pilot, fixed before the first run:** (1) at least **50%** of walkable length is sidewalk-level (DC: 67.6%), (2) at least **60%** of mapped crossings have a known control type, (3) the main connected component holds at least **90%** of walkable length. A town that misses it is recorded with the reason; the bar is not lowered | Set before any Maryland number existed so the result cannot move it. Below these, most decisive places would be `unknown` |
| 2026-10-15 | PathFinder is a **separate app** in CongoApp (owner); DistrictDirect is not edited for it | Owner's direction |
| 2026-10-15 | Pilots: **Gaithersburg** and **City of Frederick**; Germantown later (thin OSM); Hagerstown, Cumberland, Frostburg only through data partnerships | Best-documented data in MD-6 and two different street layouts; the western cities publish almost no pedestrian data |
| 2026-10-15 | Without a stairs, lights or signal inventory, **nothing is confirmed by absence** | Rule 1. DC's absences counted only because DDOT's inventories are comprehensive inside the District line |
| 2026-10-15 | Unlicensed municipal data is **internal only** until written permission | City of Frederick, Montgomery Planning, Gaithersburg and the MDOT proxies state no open license |
| 2026-10-15 | Large data stays outside the repo (`~/.pathfinder/data`) | The repo lives in OneDrive at the owner's choice; GBs must not sync |
| 2026-10-15 | Montgomery code 1208 is never a street sidewalk; survey presence is not graded on service roads or alleys | Imagery: 11 of 12 and 5 of 6 sampled results wrong otherwise. Accuracy over coverage |
| 2026-10-15 | Survey results are dated by the oldest polygon beside the street | A mixed-vintage layer must not lend old polygons its newest year |
| 2026-10-15 | **Criterion 1 stands as written**; sidewalk evidence is reported beside the bar, not as a criterion | Reinterpreting it after Gaithersburg's number was known would move the bar (owner delegated the call) |
| 2026-10-15 | A divided-road carriageway's probes stop halfway to its twin | The far carriageway's sidewalk is not this one's |
| 2026-10-15 | Undated survey records are not used (Frederick: 815 segments never photographed) | Rule 4: every claim carries a date |
| 2026-10-15 | **PathFinder is a city accessibility app**: routes first for people with mobility disabilities, plus a city barrier map; crossings fold into accessibility; after-dark and crime are removed | Owner's direction |
| 2026-10-15 | **Accessibility go/no-go bar, fixed before any accessibility source is loaded:** (1) curb evidence, verified or inferred, at ≥ 60% of crossing ends, implicit ends included; (2) slope verified on ≥ 80% of walkable length; (3) sidewalk evidence on ≥ 60% of walkable length; (4) a manual-wheelchair route exists ("allow likely") for ≥ 50% of the fixed trip sample (DC 65.3%); (5) main component ≥ 90%. The Phase B bar measured a different product; its result stays recorded | Below these the routes a disabled walker needs would rest mostly on unknowns |
| 2026-10-15 | Profiles are starting points with stated reasons, overridable by any explicit choice; numbers to be revised with testers | Product judgments, not measurements |
| 2026-10-15 | The barrier map lists unknowns beside barriers, and the API never drops a barrier when it caps | For a city, the gaps are the survey worklist |
| 2026-10-16 | A ramp that fails its survey stays usable for routing (extra cost, barrier map), never a hard barrier | The verdict does not say which check failed; refusing every failing ramp would block corners a wheelchair user can likely use, and guessing would be worse |
| 2026-10-16 | The survey's condition index is shown as its number, never as a category | The city has published no cutoffs; a category word would be PathFinder's claim, not the survey's |
| 2026-10-16 | On a street centerline the worse side's sidewalk condition stands for both, as inferred | Which side the walker takes is not known; missing data is never favorable |
| 2026-10-16 | An incomplete signal inventory is positive evidence only: it gives an inferred signal where it has one and never proves there is none | Montgomery's layer misses real signals (imagery) |
| 2026-10-16 | An undated inventory record is used only where OSM confirms it, and is dated by the OSM extract | Rule 4: no claim without a date; the county's signal layer gives none |
| 2026-10-16 | Sidewalks from the surveys: `at_least_one_side` on the centerline, and estimated lines as a map layer, not walkways | Routable lines would invent connections at every junction, fake a turn there and count two-sided streets twice; the evidence is the same either way |
| 2026-10-16 | A sidewalk found on one side only counts within 15 m of the street | Imagery: beyond 15 m most finds belonged to a building or the far carriageway |
| 2026-10-16 | **Completeness bar for the City of Frederick sidewalk survey, fixed before measuring.** Its silence counts as "no sidewalk" only if (1) at least 95% of OSM-mapped sidewalk length along public streets inside the line lies within 5 m of a survey line (undated segments included: they still show the survey saw the sidewalk) and (2) in a random imagery sample of 40 street sides where the survey has nothing, at most 2 show a sidewalk. Otherwise silence stays unknown | Rule 1: absence is evidence only where an inventory is shown complete |
| 2026-10-16 | **Bar for sidewalks detected in aerial imagery (Frederick pilot), fixed before any method is chosen or run.** Test set: 60 street sides where the city survey and an OSM sidewalk agree there is one, and 60 sides with no sidewalk, labelled by hand on MD iMAP 2023–25 imagery. The detector may abstain (canopy, shadow), but must give at least 30 answers of each kind; its "sidewalk" answers and its "no sidewalk" answers must each be at least 95% correct. Decision rule, also fixed now: on a street side, detected sidewalk found by the side probes within 15 m covering at least 60% of it is "sidewalk", at most 10% is "no sidewalk", anything between is an abstention. Pilot area: three 1 km cells of Frederick (EPSG:26985 cells 363/196, 366/194, 366/198), chosen for unrecorded streets and OSM sidewalks before any detection. Then a fresh imagery check of 20 answers on unrecorded streets with at most 1 wrong. Frozen before any detection: the labelled test set (60 survey+OSM sidewalks, 65 hand-labelled "none", plus 36 silent sides hand-labelled "sidewalk" reported separately; sha256 9fa22247…) and `tools/tile2net_pilot/score.py`. Pass: results enter as `inferred`, dated by the imagery. Fail: not used | Rule 5 and accuracy over coverage: a model's answer is inferred, and only a tested one is used at all |
| 2026-10-16 | **Imagery bar amended before any detection existed:** "sidewalk" and "no sidewalk" precision are measured over every labelled side (60 survey+OSM sidewalks, 65 hand-labelled none, 36 silent sides hand-labelled sidewalk), not over the first two groups only | A dry run of the scoring with the survey itself as the "detector" passed the original bar while answering "no sidewalk" on all 36 sidewalks the survey misses: the original bar could not catch a detector that misses exactly what is needed |
| 2026-10-16 | DTMs are exported for the town's box on the analysis grid by the server, not downloaded whole | County services are GBs in mixed projections and units |
| 2026-10-17 | **Imagery sidewalks (Tile2Net) are not used:** the pilot failed the fixed bar ("sidewalk" 85.7%, "no sidewalk" 83.7% correct; 95% needed) | Rule 5 and accuracy over coverage; the bar was fixed before any detection and is not moved |
| 2026-10-17 | **Retraining protocol (owner: fine-tune on a Colab T4, labels from OSM on survey-picked chips), fixed before any training data is built.** *Test:* the same bar, decision rule (≥ 60% / ≤ 10% within 15 m), frozen test set and frozen `score.py`, scored **once** on the final model; then the 20-answer imagery check. No threshold or checkpoint is chosen on the test set. *Held out:* any chip within 250 m of a test cell is used for nothing. *Chips:* zoom-17 tiles (1024 px of zoom-19 imagery, MD iMAP 2023–25, fetched as one export per chip: identical to 16 stitched tiles up to resampling, mean 1.5 levels) lying wholly inside the Frederick or Gaithersburg city line (survey: Frederick's lines, Montgomery code 1206 polygons), with ≥ 150 m of OSM sidewalk where OSM and the town's survey agree: ≥ 90% of the survey's sidewalk lies within 5 m of an OSM sidewalk and ≥ 90% of the OSM sidewalk lies within 5 m of the survey. The survey only picks chips and never leaves the laptop. *Labels, from OSM alone:* sidewalk within half the tagged width (default 0.75 m) of an OSM sidewalk; ignored from there to 2.5 m and within 3 m of every other OSM footway, path, cycleway, steps or crossing; everything else is "not sidewalk". *Loss:* class-balanced binary loss on the sidewalk output only. *Split:* zoom-15 blocks, 20% of them validation, chosen by a fixed hash; the epoch is chosen by validation sidewalk F1. *Training:* from the released `satellite_2021` weights, SGD (momentum 0.9, lr 1e-3, poly decay, weight decay 1e-4), mixed precision, at most 15 epochs. *Result:* pass → used as `inferred`, dated by the imagery; fail → not used, and this test set is spent for imagery models | The test set has been used once already; one more look at it, with nothing tuned on it, keeps the measurement honest. OSM labels are open; the survey stays internal (rule 7) |
| 2026-10-19 | **The retrained imagery model is not used:** scored once, it failed the same bar ("sidewalk" 80.9% correct; "no sidewalk" 100% but only 26 answers, 30 needed). The frozen test set is now spent for imagery models; any further imagery model needs a new, independently labelled test set fixed before it is built | The protocol fixed the outcome of a fail before training; a third look at the same test set would let it tune the model |
| 2026-10-19 | **Areas closed to the public (`landuse=military`) are not walkable:** edges at least half inside are removed; trips with an end there leave the sample by its existing rule | A route through a guarded gate is not a route; Fort Detrick's streets were mapped as public (`access=yes`). This corrects the network, not the bar |
| 2026-10-19 | **Imagery sidewalk detection is closed (owner).** No new test set and no further models; effort moves to getting Frederick over the accessibility bar through the city's own data | Two models failed, in opposite ways; at six inches, under canopy and beside driveways, 95% looks out of reach, and a new hand-labelled test set would cost about as much as mapping the streets |

---

## Open issues

- No Maryland basemap tiles, elevation, signals, lights, crashes or crime are registered
  yet: every such attribute is unknown until Phase C.
- Many parameters (radii, penalties, the 30 felt-second worth-showing bar) were calibrated
  on DC and are untested on suburban Maryland streets.
- **Slope on regraded or terraced ground:** 14% (Gaithersburg) and 22% (Frederick) of steep
  edges are flat on average with one steep 10 m window; some sit on ground built since the
  flight. Candidates: newer imagery-dated checks, or field checks with testers.
- `ramp_likely` / `no_ramp_reported` at junctions carry no date; they should take the
  survey dates of the ramps they count.
- Gaithersburg has no published curb-ramp inventory; without one no step-free route can be
  confirmed there.
- The City of Frederick sidewalk survey is not complete (88.9% of OSM's public-street
  sidewalk, bar 95%), so its silence proves nothing; its scope from the city would let silence
  count inside that scope.
- MDOT SHA's ADA inventory (state-road curb cuts, pedestrian signals with APS) is internal;
  state roads in both towns stay without it until SHA shares it.
- Condition bands are product judgments; Frederick's survey report (O'Connell & Lawrence)
  would give the index's own categories. Ask the city for it.
- Neither pilot can clear criterion 1 through surveys: it needs walkways mapped as their own
  ways. Routes to it: mapping sidewalks in OSM (a partner or community mapping effort), or
  deriving sidewalk ways from the surveys as `inferred` geometry (plan, Risks). Either is a
  product decision.
- Sidewalk presence on one side only, or none, cannot come from a survey without stairs and
  completeness coverage; a "sidewalk" coverage family separate from stairs would allow it
  where a survey is shown complete. Not done: completeness has not been checked.
- Survey "both sides" is still read within 30 m on undivided streets (DC's reach): 1 of 12
  sampled Frederick streets and 1 of 6 Gaithersburg streets were wrong at that reach.

## Next steps

1. **City of Frederick first** (owner): a one-page private brief (`docs/briefs/frederick-city.md`)
   asks for (a) written permission to show what is built on the city's surveys outside the team
   (rule 7), (b) the sidewalk survey's scope, which would let its silence count inside it
   (criterion 3, 56.8%), (c) the survey report (condition categories), and (d) a check of the
   blocking corners in `reports/frederick/blocked/worklist.csv` (criterion 4, 7 trips short).
2. Data requests (owner): MDOT SHA's ADA inventory (27 of Frederick's 145 blocked trips touch a
   major road); a Gaithersburg ramp inventory (it would lift criterion 4 most there: 199 of the
   blocked trips wait only on unrecorded curbs); MCDOT signals with APS / LPI.
   No further open signal data in either town.
3. Frederick's sidewalk evidence beyond the survey: service roads, lots, and streets the survey shows
   without a sidewalk; mapping with partners. Imagery detection is closed (2026-10-19).
4. Phase E, The Freedom Center: testers and the profile numbers, once the city's permission
   lets them see what is built on its data.

---

## How to update this log

- Add a dated entry under **Timeline** for each meaningful change, with the commit hash.
- Record results as numbers with links to the generated report, not impressions.
- Record product/technical choices in the **Decisions log** with the reason.
- Update **Current status**, **Key metrics**, **Open issues** and **Next steps**.
- Never delete history; correct mistakes with a new dated note.
