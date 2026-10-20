# PathFinder — Product & Technical Plan

_Last revised: 2026-10-05. Status: Phase 0 (data foundation) complete; Phase 1 next._

PathFinder is a citywide walking navigator for Washington, DC that shows people
**where** routes differ, **what is known vs. unknown** about each place, and **how far their
priorities would have to move** before a different route wins. It is a usable product with a
business model, not a research demo.

---

## 1. Product thesis

Mainstream walking directions answer "what is shortest?". A walker's real question is
"is there anything on this walk that matters *to me*, and is avoiding it worth the time?".

Working hypothesis (tested in Phase 0, see §8): sensible alternative routes usually differ at
only **one to three decisive places** — a crossing of a wide arterial, a block with no
sidewalk, a missing curb ramp, an unlit cut-through. Decisions hinge on those places, so the
product makes them the unit of comparison instead of collapsing a whole route into one score.

### Three dimensions (user-controlled)

| Dimension | What it means in PathFinder | What it is built from |
|---|---|---|
| **After-dark comfort** | Observable environment after dark | Streetlight density, open businesses (OSM hours), main-street vs. cut-through/alley/park path, Metro-entrance proximity |
| **Crossing safety** | Difficulty/exposure of street crossings and walking beside traffic | Lanes, cross-section width, speed limit, AADT, signal features (LPI, HAWK, all-ped phase), marked crossings; pedestrian crashes used for validation and smoothing |
| **Accessibility** | Physical passability | Curb ramps, sidewalk existence/width, stairs, elevators, slope from LiDAR, surface problems, accessible pedestrian signals |

### Decision: reported crime is opt-in, never a default routing weight

"Personal security" is reframed as **after-dark comfort**. Reported crimes against persons
are an **opt-in priority** (owner decision 2026-10-05, replacing "descriptive layer only"):
off unless the user turns it on, kept outside the three-way priority mix, and always shown
with explicit caveats. Reasons it is not a default:

- MPD crime data is anonymized to the **block** level; `SHIFT` is the shift when the report was
  *taken*; start/end times are of "considerably" varying reliability (MPD metadata).
- Recorded crime measures where offences were reported, not individual risk, and under-represents
  harassment (safe-route-finding literature; CHI '24).
- DC precedent: SketchFactor (2014) was widely criticized for encoding neighborhood demographics.
- Business: likely paying customers (BIDs, universities, hotels, DC agencies) will not adopt a
  product that routes people around their neighborhoods.

The product never describes a route as "safe".

---

## 2. Differentiation (the moat)

1. **Evidence-graded local data.** Every attribute carries `value`, `status`
   (`verified` / `inferred` / `unknown`), `source`, and `as_of` date. Missing data is
   **never** treated as favorable. A maintenance loop (scheduled refresh, user confirmations,
   live WMATA outages, later field audits) compounds over time.
2. **Explanation, not just a line.**
   - **Crux Map** — only the places where alternatives differ are highlighted, each as a
     decision card.
   - **Tradeoff Triangle** — the preference simplex partitioned into regions by which route
     wins; boundaries are tipping points. Crossing a boundary highlights the crux that flipped.
   - **"What would it take?"** — distance to the nearest boundary in plain language.
   - **Minimal relaxation** — when no route satisfies all requirements, show the smallest
     compromise and where it occurs.
3. **Requirements are inviolable.** Step-free / no stairs / max slope are hard constraints,
   never traded against scores. Unverified segments are visible.

Novelty stance: the techniques are established (weight-space decomposition, constrained
shortest paths, uncertainty representation). The distinctive part is the combination and the
interaction design. We do not claim "first".

Closest prior art to track: Google Maps wheelchair-accessible routes (binary, no
uncertainty), AccessMap/OpenSidewalks (UW; accessibility-only, WA cities), Project Sidewalk
(data, DC origin), Galbrun et al. safe paths (bi-criteria, crime-based), "Why Not This Route?"
(counterfactual routing explanations, 2026 — must be reviewed before any explanation claims).

---

## 3. Business model

Consumer navigation is hard to charge for. Primary revenue is B2B; the free consumer app is
the showcase and the data flywheel.

| Stream | Customer | Value |
|---|---|---|
| Embeddable "accessible arrival" widget | Universities, hospitals, hotels, convention center, venues | Explained step-free arrival directions from Metro/parking |
| Pedestrian-conditions data/API | Apps, accessibility services, developers | Verified, dated DC network attributes |
| Conditions reports | BIDs, ANCs, developers, consultants | Gap maps: missing ramps, hard crossings, unlit stretches |
| Premium consumer (later) | Commuters | Saved trips, elevator-outage alerts, offline |

**Rule:** core step-free routing and requirements are always free.
**Gate:** interview 5–10 prospective B2B customers before building any billing.

---

## 4. User controls → routing behavior

1. **Requirements** (toggles): step-free, no stairs, max slope, (later) min sidewalk width.
   Implemented as edge filters before search. Unknown edges pass only per the certainty setting.
2. **Priorities** (Tradeoff Triangle): weights `w = (w_dark, w_cross, w_access)` on the
   2-simplex — the *mix* of what matters.
3. **Budget & certainty**: max extra real minutes; tolerance for unverified data
   (`verified only` / `allow likely` / `show me unknowns`).

**Cost model — "felt minutes".** Each condition converts to time-equivalent penalty seconds:

```
cost(route) = walk_time(route) + Σ_edges Σ_dims  w_d · intensity · penalty_d(edge)
real constraint: walk_time(route) ≤ walk_time(fastest feasible) + budget
```

Penalties are in seconds, so every explanation is in minutes ("avoids two crossings you
weigh at ~3 min, for 2 real extra minutes"). Penalty tables are explicit, versioned config —
not learned black boxes — until Phase 2 models replace specific inputs.

**Certainty as a path resource.** Per-edge pass probability `p_e`; route confidence
`Π p_e` ⇔ `Σ -log p_e`, which is additive and constrainable like length.

---

## 5. Geospatial representation

**Pedestrian graph, sidewalk-level where data allows, with crossings as first-class edges.**

- Edge kinds: `sidewalk`, `footway`, `path`, `pedestrian_street`, `crossing`, `steps`,
  `elevator`, `street_centerline` (fallback where sidewalks are not separately mapped),
  later `metro_entrance` connectors.
- Every edge records its `representation` so the UI and reports never pretend a centerline is
  a verified sidewalk.
- Crossings carry: crossing length (geometry, later curb-to-curb from planimetric curbs),
  crossed-road lanes / width / speed / AADT (DDOT Roadway Block), signal and its features
  (DDOT Traffic Signals), marking, kerb/ramp evidence at both ends.
- **Near ≠ connected**: routing is on the graph; the UI surfaces "closest crossing is 180 m
  away" situations explicitly.
- Elevation: 2024 hydro-enforced DTM (1 m). Bridges/tunnels use endpoint interpolation, not
  ground under the deck. Sustained grade is a least-squares slope over 10 m, read on three
  parallel lines that must agree for the reading to count as verified. (The USSS redaction
  areas remove only non-ground LiDAR returns; the bare-earth DTM is intact there, so slope
  is measured as elsewhere — checked 2026-10-05.)
- Where sidewalks are not mapped separately, walking a street centerline through a junction
  is an **implicit crossing**: it is priced and held to the curb-ramp requirement like a
  mapped crossing, with inferred evidence at best.

**Observation → edge rules**

- Streetlights: lights within a buffer along each edge, normalized per 100 m; only lights not
  flagged inactive. (Presence ≠ working/brightness — stated in UI.)
- Pedestrian crashes: snapped to crossing vs. mid-block using DDOT linear referencing
  (`OFFINTERSECTION`, `NEARESTINTKEY`); used for validation and empirical-Bayes smoothing, not
  routed on raw.
- Crime (opt-in priority only): persons crimes, assigned to block (both sides), smoothed, with
  block-level caveat.
- Project Sidewalk: label clusters snapped to nearest edge/crossing end; imagery date carried
  as `as_of` (DC audit imagery ≈ 2014–2016).
- Accumulation: crossings count once each; length-based conditions accumulate with distance.

**Citywide performance**: a feasible route under a detour budget lies inside the ellipse with
foci at origin and destination and major axis `(1+δ)·d`. Each request searches only that
ellipse (typically thousands of edges), so ~60 weight-grid searches stay interactive without
contraction hierarchies. Rust routing core only if Phase 0/1 benchmarks require it.

---

## 6. Machine learning — purposeful only

| Model | Predicts | Why it matters | Baseline to beat | Evaluation | Phase |
|---|---|---|---|---|---|
| Crossing risk (SPF + empirical Bayes) | Expected pedestrian injury crashes per crossing from design | Raw counts are sparse noise; gives every crossing a value | Raw historical counts; HIN membership | Temporal holdout (train ≤2022, test 2023–25); Poisson deviance; rank metrics | 2 |
| Missing-infrastructure inference | P(curb ramp / sidewalk exists) where unrecorded | Unknowns block step-free routing | Nearest-neighbor / block-majority | Spatial-block CV; calibration curves; field audit sample | removed from Phase 2 (owner decision 2026-10-06); not scheduled |
| Crime prediction | — | Not pursued: low routing value, high harm | — | — | never (by default) |

Predictions are **never** shown as verified; they feed only the "allow likely" setting.
Uncertainty reaches routing via felt-minute ranges and pass probabilities.

---

## 7. Architecture

| Layer | Choice | Why |
|---|---|---|
| Data pipeline | Python, GeoPandas, pyosmium, rasterio; GeoParquet outputs; reproducible CLI | Mature geo stack; files are diffable artifacts |
| Storage (Phase 1+) | PostGIS | User reports, data history, spatial queries |
| Routing | FastAPI + igraph on ellipse-pruned subgraphs | Fast enough citywide; simple; replaceable core |
| Frontend (Phase 1) | React + TypeScript + MapLibre GL + deck.gl, PWA, PMTiles | Mobile-first, installable, static tiles |
| Hosting | Private (password gate, no accounts) until owner authorizes public launch | Owner requirement |

Analysis CRS: **EPSG:26985** (NAD83 / Maryland, meters). Storage/exchange: EPSG:4326.

---

## 8. Roadmap

| Phase | Deliverable | Exit gate |
|---|---|---|
| **0. Data foundation** | Ingest all sources with provenance manifest; citywide pedestrian graph with evidence-graded attributes; per-attribute × per-ward coverage report; crux hypothesis experiment on citywide OD sample; ellipse-routing benchmark | Is data sufficient? Does the crux hypothesis hold? Is routing fast enough? |
| **1. Citywide MVP** | A phone website: requirements, Triangle, Crux Map, uncertainty, route choices with explanations, minimal relaxation, **live location and on-screen guidance along the chosen route** (owner decision 2026-10-05), live WMATA outages; private deploy | Testers understand it and prefer it over a route list |
| **2. Data depth + beta** | Crossing-risk model, confirm/correct reports, 20–50 beta testers, usability study. (Missing-infrastructure inference was removed on 2026-10-06 by owner decision: unrecorded curb ramps and sidewalks stay `unknown`.) | Useful enough to launch |
| **3. Launch + B2B pilots** | Public launch (owner authorization), widget pilot, first data/report customers, legal review | Revenue signal |
| **4. Expansion** | Spoken turn-by-turn, native apps, other cities via OpenSidewalks-compatible schema | — |

Deliberately postponed: crime prediction, social features, accounts, billing (until B2B
validation), spoken turn-by-turn.

---

## 9. Evaluation

- **Requirement compliance**: property tests — zero violations, always.
- **Sensibility**: expert panel review of route pairs (planners, disability advocates).
- **Comprehension**: quizzes on what the Crux Map / Triangle say.
- **Decision quality**: within-subjects study vs. plain route list; match between chosen route
  and the participant's separately elicited pairwise preferences; decision time.
- **Uncertainty calibration**: participants' estimates of P(step-free) vs. truth.
- **Field value**: diary study on recurring trips.

Offline model accuracy is not evidence that walking is safer; we never claim it is.

**User research**: 10–12 critical-incident interviews ("the last time you changed how you
walked somewhere in DC"), go-along walks; recruit commuters, wheelchair/cane/stroller users
(via disability organizations), late-shift workers, recent arrivals.

---

## 10. Verified data sources (2026-10-04)

All DC GIS layers below were queried live (record counts and field lists confirmed).
The machine-readable registry is `src/pathfinder/sources.py`.

| Source | Endpoint (DC GIS REST unless noted) | Records | Key fields / notes |
|---|---|---|---|
| OSM DC extract | Geofabrik `district-of-columbia-latest.osm.pbf` | ~21 MB | Footways, crossings, kerbs, steps, elevators, lit, opening hours. ODbL |
| Roadway Block | `DCGIS_DATA/Transportation_WebMercator/163` | 13,833 | `TOTALTRAVELLANES`, `TOTALCROSSSECTIONWIDTH`, `SPEEDLIMITS_IB/OB`, `AADT`, `SIDEWALK_IB/OB_WIDTH` |
| Roadway Block Intersection | `…/Transportation_WebMercator/160` | 7,879 | Intersection keys for crash linkage |
| DDOT Traffic Signals | `…/Transportation_Signs_Signals_Lights_WebMercator/170` | 1,596 | `LPI`, `ALL_PED_PHASE`, `HAWK`, `APS`, `PED_RECALL_MODE`, `STATUS` |
| Street Lights | `…/Transportation_Signs_Signals_Lights_WebMercator/90` | 77,829 | `ASSETSTATUS`, `INOPERATION`, `LIGHTTYPE`, `POLEHEIGHT` |
| Sidewalks 2021 | `DCGIS_DATA/Planimetrics_2021/11` | 55,644 polygons | Planimetric shape, not condition |
| Curbs 2021 | `DCGIS_DATA/Planimetrics_2021/3` | 90,391 lines | For curb-to-curb crossing length |
| Sidewalk Ramps 2010 | `DCGIS_DATA/Planimetrics_2010/2` | 32,426 points | **2010 — stale**; evidence only with date |
| Crashes (pedestrian) | `DCGIS_DATA/Public_Safety_WebMercator/24` where `TOTAL_PEDESTRIANS>0` | 17,442 | Ped injury by severity, `OFFINTERSECTION`, `NEARESTINTKEY`. Contains invalid dates (min ≈ 1827) — filter |
| Crime Incidents | `FEEDS/MPD/MapServer/{year layer}` | ~24k/yr | Block-anonymized. Opt-in priority only, never a default |
| High Injury Network | `DCGIS_DATA/MoveDC/17` | 77 corridors | 2016–2021 crashes; context only |
| Wards 2022 / DC boundary | `…/Administrative_Other_Boundaries_WebMercator/53`, `/10` | — | Reporting units |
| USSS redaction areas | `…/Administrative_Other_Boundaries_WebMercator/41` | 4 | Non-ground LiDAR returns redacted; bare-earth DTM intact (reference only) |
| DTM 2024 (1 m) | `imagery.dcgis.dc.gov/…/Lidar/Hydro_Enforced_DTM_2024/ImageServer` | raster | exportImage allowed; EPSG:2804 |
| Project Sidewalk DC | `sidewalk-dc.cs.washington.edu/v3/api/labelClusters?bbox=…` | — | CC0. Imagery ≈ 2014–2016. Drop contributor IDs |
| WMATA elevator outages | WMATA API `ElevatorIncidents` | live | **Requires free API key** (Phase 1) |

---

## 11. Major uncertainties

| Uncertainty | How it is resolved |
|---|---|
| Crux hypothesis | Phase 0 experiment: distribution of divergence count across sampled OD pairs |
| OSM separate-sidewalk completeness | Phase 0 coverage report by ward |
| Curb-ramp currency (2010 layer, 2014–16 imagery) | Coverage report flags age; user confirm/correct reports (Phase 2). Inference is not planned (2026-10-06) |
| Felt-minutes comprehensibility | User interviews in Phase 1 |
| B2B willingness to pay | 5–10 customer interviews before billing |
| Liability | Never "safe"; source + date on every claim; legal review pre-launch |
