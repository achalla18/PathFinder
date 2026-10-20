# PathFinder — Progress Log

A running record of what has been built, what we learned, and the decisions we made — so we
can see how the project grows. **Keep it current:** every meaningful change (new feature,
experiment result, major fix, product decision) gets an entry in the same change that makes
it. See "How to update" at the bottom.

- Plan and rationale: [`PLAN.md`](PLAN.md)
- Generated evidence: [`../reports/`](../reports/)

---

## Current status

| | |
|---|---|
| **Phase** | 1 — Citywide MVP: **started** (2026-10-05). Phase 0 complete after a full audit |
| **Next** | Phase 1 — guidance tried on a real phone outdoors, which needs hosting (see "Next steps") |
| **Branch** | `feature/initial-platform`, merged to `master` 2026-10-13 |
| **Repo** | github.com/achalla18/PathFinder (private) |
| **Tests** | 181 passing (incl. invariants on the real citywide graph) |

### Key metrics over time

Add a column each time a metric changes, so growth is visible at a glance.

| Metric | 2026-10-04 (Phase 0) | 2026-10-04 (after verification fixes) | 2026-10-05 (Phase 0 audit, penalties v2) | 2026-10-05 (gaps bridged; trips resampled) | 2026-10-13 (elevator rooms out; same trips) |
|---|---|---|---|---|---|
| Verified data sources ingested | 23 | 23 | 23 | 23 | 23 |
| Walkable edges / nodes (all of DC) | 141,929 / 108,610 | 141,929 / 108,610 | 141,929 / 108,610 | 142,532 / 108,713 | 142,526 / 108,707 |
| Share of walkable length in main connected network | 96.5% | 96.5% | 96.5% | 96.5% | 96.5% |
| Sidewalk-level (vs. street-centerline) share of length | 67.6% | 67.6% | 67.6% | 67.6% | 67.6% |
| Crossings with known control type | 100% (17,674) | 100% (17,674) | 94.7% verified + 5.2% inferred | 94.7% verified + 5.2% inferred | 94.7% verified + 5.2% inferred |
| Crossings with curb evidence at both ends | 90.4% | 90.4% | 90.4% | 90.4% | 90.4% |
| Walkable length with measured slope | 96% verified + 3% inferred | 96% verified + 3% inferred | 82% verified + 17% inferred (new metric) | 82% verified + 17% inferred | 82% verified + 17% inferred |
| Walkable length with known streetlight density | 91% | 91% | 91% | 91% | 91% |
| Crux hypothesis (≤3 divergence sections when route changes) | 93.4% | 93.4% | 93.5% | 93.7% | 93.7% |
| Step-free trips with a feasible route (allow likely / verified only) | 60.3% / 47.7% | 60.2% / 47.7% | 67.8% / 35.7% | 65.3% / 31.5% | 65.3% / 31.5% |
| Routing latency p50 / p95 | 0.25 s / 1.1 s | 0.13 s / 0.8 s (same routing code) | 0.28 s / 1.3 s | 0.12 s / 0.7 s | 0.15 s / 0.46 s |
| Recommendation worth showing (≥30 felt s better than fastest), % of trips | — | — | 80.0% | 80.5% | 80.5% |
| Implicit (unmapped) crossing edge ends priced | 0 | 0 | 7,927 | 7,927 | 7,927 |
| Inferred connectors (≤3 m slips / wider gaps on mapped sidewalk surface) | 571 / 0 | 571 / 0 | 571 / 0 | 571 / 500 | 571 / 500 |

---

## Timeline

### 2026-10-04 — Project setup

- Installed the OpenAI Codex CLI (0.160.0) and Claude Code's Codex plugin so both agents can
  work on the project.
- Found that git was tracking the whole home folder (`C:/Users/arjun`); created a separate
  repository for PathFinder instead (home-folder repo left untouched).
- Initial commit (`c3797fe`): `.gitignore`, placeholder README.
- Created the private GitHub repo `achalla18/PathFinder` and pushed `master` and
  `feature/initial-platform`.

### 2026-10-04 — Product planning

- Researched DC data availability and existing products (Google Maps wheelchair routing,
  AccessMap/OpenSidewalks, Project Sidewalk, academic safe-path routing, SketchFactor).
- Developed five concepts (Crux Map, detour budget, confidence-aware navigation, Metro
  last-mile, Tradeoff Triangle) and recommended a combination: **Crux Map + Tradeoff Triangle,
  evidence-graded, with hard requirements**.
- Owner decisions: build a **real, usable product** with income potential, **citywide**, no
  time limit; defer to the plan on the security dimension.
- Wrote [`PLAN.md`](PLAN.md): thesis, differentiation, B2B business model, cost model,
  geospatial design, ML roles, architecture, roadmap, evaluation, verified data table.

### 2026-10-04 — Phase 0: data pipeline (`8c6abde`)

- **Source registry + fetcher** with a provenance manifest (URL, record count, SHA-256,
  fetch time) for 23 sources: OSM, DDOT roadway blocks, traffic signals, streetlights,
  planimetric sidewalks/curbs/ramps, pedestrian crashes, MPD crime (2019–2026, opt-in layer
  only), High Injury Network, Project Sidewalk, 2024 1 m LiDAR terrain (120 tiles).
- Verified every endpoint live; discovered DDOT signal data includes leading pedestrian
  intervals, HAWK beacons and accessible pedestrian signals; roadway blocks include lanes,
  widths, speed limits and traffic volumes.

### 2026-10-04 — Phase 0: citywide pedestrian graph (`8c6abde`)

- Sidewalk-level graph from OSM (DC has ~2,370 km of separately mapped sidewalks and ~17.7k
  crossings), with street centerlines as a clearly flagged fallback.
- Geometric detection of separately mapped sidewalks for untagged streets.
- **Fixes found by inspecting real output:**
  - Removing roads with separate sidewalks left ~9,700 dead-end stubs → pruned.
  - Sidewalks ending 1–3 m short of each other → 571 disclosed `inferred_connector` edges
    (never silent).
  - Network extended into Maryland/Virginia → clipped to DC + 200 m at edge level.

### 2026-10-04 — Phase 0: evidence-graded attributes (`8c6abde`)

- Every attribute stores value, status (`verified` / `inferred` / `unknown`), source and
  date. Missing data is never treated as favorable.
- Crossing control, signal features, crossed-road lanes/width/speed/volume, curb ramps at
  both crossing ends, step-free, slope, surface, streetlight density, crash context.
- **Fixes found by inspecting real output:**
  - LiDAR server fills areas outside DC with exactly 0 m → treated as no-data.
  - Smoothing padded profiles with zeros → impossible >100% grades → replaced with a robust
    median filter (regression test added).
  - Sidewalks over highway cuts, rail lines and creeks measured the ground below → masked
    at grade-separation points (450 edges).
  - Kerbs were looked up at the middle of the street for split crossings → now evaluated at
    each physical crossing's two curb ends.
  - Bridges had no slope → inferred end-to-end grade.
  - 436 stairs missing from OSM found via DC planimetric data.

### 2026-10-04 — Phase 0: routing core (`8c6abde`)

- Requirements (step-free, max slope, certainty level) as hard filters.
- Versioned "felt minutes" penalty tables for crossing safety, accessibility, after-dark
  comfort.
- Exact ellipse pruning (proved and tested against full-graph shortest paths), route sets
  across 66 preference mixes, detour budget via Lagrangian relaxation, divergence sections.

### 2026-10-04 — Phase 0: coverage report (`8c6abde`)

- [`reports/phase0/coverage.md`](../reports/phase0/coverage.md) with maps.
- **Finding — equity gap:** Wards 7 and 8 are only 47–52% sidewalk-level mapped vs. 68–83%
  elsewhere, and Ward 8 has the lowest curb-evidence coverage.
- **Finding — data age:** 65% of curb evidence comes from Project Sidewalk imagery from
  before 2018.

### 2026-10-04 — Phase 0: crux experiment (`30c91c6`, `6e3f059`)

- 1,002 citywide trips × 6 profiles: [`reports/phase0/crux.md`](../reports/phase0/crux.md).
- Two runs were stopped by Claude Code's low-memory guard (the machine had ~0.4 GB free).
  Made the experiment lean (~40 MB per worker) and resumable (per-trip checkpoints);
  completed on resume.
- **Results:**
  - Crux hypothesis **supported**: 93.4% of changed routes differ in ≤3 places (98.6% /
    96.1% / 86.4% by distance band); stable at night and with doubled penalties.
  - Recommended route differs from fastest in 92% of trips, but 43% of those changes save
    <30 s of extra walking → need a "worth showing" threshold.
  - Step-free routes feasible for only 60% of trips; ~82% of failures are caused by the slope
    limit. The 6 m steepest-stretch metric flags 17.3% of sidewalk length as >8.33% vs. 2.4%
    by average grade → metric is too noise-sensitive.
  - Network circuity median 1.25; 40 trips >2× straight-line (possible missing links).

### 2026-10-04 — Progress log and repo relocation

- Created this progress log and added a rule to `AGENTS.md` that every agent keeps it
  current.
- Diagnosed low memory (~0.5 GB free of 15.7 GB): Chrome (~6.4 GB), OneDrive (~1.4 GB,
  partly from syncing this repo), startup apps.
- Moved the repository out of OneDrive to `C:\dev\PathFinder` to stop OneDrive syncing
  git internals and to free memory; reinstalled the package from the new path.

### 2026-10-04 — Phase 0 verification and fixes (`efcd31f`)

- Audited Phase 0 end to end: all 23 manifest entries match their files (SHA-256 and record
  counts), graph integrity and evidence invariants hold, and every figure in the crux report
  reproduces from the raw results. Ran a Codex adversarial review of the branch.
- **Fix — inferred connectors were graded verified step-free.** 404 of the 571 gap-bridging
  connectors carried `step_free = verified`, and connectors were never checked against
  planimetric stairs. Connectors are now always `inferred`; the 38 that touch a stairs
  polygon are marked not step-free. Regression test and a real-graph invariant added.
- **Fix — crux resume could accept partial results.** A trip counted as done once any one of
  its six profile rows existed. Resume now requires every profile, drops truncated lines and
  partial trips (logged) and recomputes them, and writes each trip in one piece. The
  committed run was complete, so its numbers were not affected.
- **Fix — coverage report omitted 5 of 20 graded attributes** (`signal_hawk`,
  `signal_all_ped_phase`, `lit_tag`, `street_lanes`, `grade_avg_pct`); a test now keeps the
  report in step with `GRADED_ATTRS`.
- Re-ran `pf enrich`, `pf coverage` and `pf crux --fresh` (same seed, same 1,002 trips):
  [`coverage.md`](../reports/phase0/coverage.md), [`crux.md`](../reports/phase0/crux.md).
  - Crux hypothesis unchanged at 93.4%.
  - Step-free feasibility: allow likely 60.3% → 60.2%, verified only unchanged at 47.7%,
    allow unknown 69.1% → 69.0%.
  - Unmapped-stairs flag 436 → 474 (now includes the 38 connectors).
  - Latency p50 / p95 0.25 / 1.1 s → 0.13 / 0.8 s with no routing-code change — most likely because
    the earlier run was on a memory-starved machine; treat latency as hardware-dependent.
- `PLAN.md` status line updated to Phase 0 complete.
- **Why verified-only feasibility did not move** (ad-hoc counterfactual, not a generated
  report: the same 1,002 trips routed under the old and new connector grading). 323
  connectors were usable under verified-only before and none are now, but only 5 of the 478
  feasible trips had a fastest route through one; all 478 stay feasible and 4 get slower (at
  most 53 s). For all 524 infeasible trips the origin and destination are in different pieces
  of the verified-only network under either grading. That network is fragmented into about
  3,350 pieces (largest ~46,600 of 108,610 nodes): 21.5% of walkable length fails the slope
  test, 10.2% is not verified step-free, and 16.6% of crossing edges fail on kerbs.

### 2026-10-05 — Phase 0 audit: every module re-read against the plan and the real data (`efcd31f`)

Owner request: make sure nothing in Phase 0 is left unfixed before Phase 1. Each finding was
confirmed on the real graph before and after the fix. Reports regenerated:
[`coverage.md`](../reports/phase0/coverage.md), [`crux.md`](../reports/phase0/crux.md).

- **Slope metric replaced** (was open issue 1). Repeatability test on 6,000 sidewalks: with the
  old metric (6 m end-difference) the 8.33% verdict flipped for 16% of edges when the mapped
  line was shifted 1 m to each side. New metric: least-squares slope over 10 m windows on 1 m
  samples, read on three parallel lines; the value is their median and it is `verified` only
  when they agree within 3 points (verdict flips 3% among those). Result:
  82.2% of length verified, 17.2% inferred, 0.6% unknown;
  15,009 edges graded "not repeatable".
- **Short edges measured along the network.** A third of pedestrian edges are under 6 m and
  were measured along a straight line projected past their ends; profiles now continue along
  the edges that continue them.
- **DTM discontinuities.** 145 edges whose profile has a wall-like step (≥3 m within 2 m, e.g. a
  sidewalk on an untagged deck over a sunken road) have grade `unknown` instead of readings
  up to 226%.
- **Implicit crossings** (rule 1 violation). Walking a street centerline through a junction
  crossed a street at no cost and with no curb requirement, so the least-mapped wards looked
  best. 7,927 edge ends are now priced as half a crossing each and held to the curb-ramp
  requirement with inferred evidence at best. Penalty tables bumped to **v2**.
- **Evidence beyond the District line** (rule 1 violation). 814 on-street edges in the
  Maryland/Virginia buffer were verified step-free, and many verified unlit, from DC
  inventories that do not cover them. Absence now counts only inside `dc_inventory_covered`.
- **Crossing control** (was open issue: 1,550 conflicts). `crossing:signals` and the tags on
  the crossing node were ignored, and `crossing=marked` was read as "unsignalized". Now:
  163 crossings with contradictory tags take the less favorable reading (inferred);
  761 painted crossings near a DDOT signal with no signal tag are inferred, not verified;
  657 are explicitly unsignalized in OSM (slip lanes, mid-block) and stay verified.
- **Smaller fixes.** `wheelchair=no/yes` and bad `smoothness` tags are used; connectors carry
  `outside_dc`; `evidence.validate` rejects unknowns with values and graded rows without a
  source; an inferred kerb no longer passes "verified only"; the router refuses a graph that
  lacks columns the cost model needs; coverage report gains an attribute × ward table.
- **Plan corrected, not code:** the USSS redaction areas remove only non-ground LiDAR
  returns. The bare-earth DTM there has the same 1 m texture as its surroundings, so slope is
  kept (the plan said "unknown").
- **Crux experiment re-run** (same 1,002 trips, penalties v2): crux hypothesis
  93.5% (was 93.4%); recommended differs from fastest in 91.0% of trips;
  step-free feasible 67.8% / 35.7% / 73.2% (likely / verified only / unknown ok; was
  60.3% / 47.7% / 69.1%). The run was stopped twice by the low-memory guard and resumed from
  its checkpoint.
- **High-circuity trips** (fastest route > 2× straight line; 40 trips): for 33 the straight line crosses a river or stream, a railway or a limited-access road (a real barrier); 7 are unexplained and remain candidates for missing links (see Open issues).

### 2026-10-05 — Phase 1 started: explanation engine and trip planner (`efcd31f`)

- `routing/explain.py`: **worth-showing rule** (a recommendation under 30 felt seconds better
  than the fastest is not offered as a separate choice — 80.0% of everyday trips clear it,
  87.9% of changed routes; crux hypothesis among those: 92.6%), **crux**
  (the section with the largest net advantage), **"what would it take"** (nearest priorities
  where another route wins) and **minimal relaxation** (smallest single compromise and where
  it applies).
- `routing/service.py` + `pf route`: plans one trip from coordinates and returns JSON in
  which every condition has a status, source and date. Tried on the real graph.

### 2026-10-05 — Gaps and missing links (`8d9f8e5`)

- **The 7 unexplained detours are not missing links.** For each, the two points of the route
  that are closest in space while far apart along it are 120–530 m apart: large barriers
  (parks, cemeteries, campuses), not mapping gaps.
- **Real gaps found instead:** 2,869 pedestrian dead ends stop 3–15 m short of another
  walkway on the same layer. Checked what lies in each gap against the planimetric survey,
  road centerlines, railways and waterways.
- **Bridged on evidence:** 500 dead ends where the straight line across the gap lies ≥ 90% on
  planimetric sidewalk surface (crosswalk paint counts when the dead end is a crossing that
  stops short) and crosses no road, rail, water or stairs polygon. Each is a disclosed
  `inferred_connector` (never verified step-free). Components 757 → 749; dead-end nodes
  10,636 → 10,127.
- **Left alone and reported:** 2,365 dead ends within 15 m of another walkway with no
  evidence of a connection, now a line in the coverage report.
- **Crux experiment re-run** on the new graph: crux hypothesis 93.7%, step-free feasible
  65.3% / 31.5% (likely / verified only), circuity p95 1.784 with 29 trips above 2.
  **Caveat:** the graph changed, so `--fresh` drew a different set of 1,002 trips; these
  figures are not comparable trip-for-trip with the previous column.
- **Measured effect of the bridged gaps** (ad-hoc counterfactual, not a generated report: the
  same 1,002 trips, fastest route with and without the 500 connectors): small. 6 everyday
  trips get faster (median 61 s, at most 87 s), 3 step-free trips (at most 27 s), and no trip
  changes between feasible and infeasible under any certainty setting. The gaps were real
  but mostly at the ends of side paths, not on through routes.

### 2026-10-05 — Codex review of the branch: three findings fixed (`8a358a7`)

- **Trip endpoints snapped to nodes only.** 634 edges (290 km) are longer than 300 m, so a
  point in the middle of one was refused as "not near the network", and the walk to the node
  was left out of every trip. The planner now places a point anywhere along the nearest
  walkway and counts the partial edges at both ends in time, length, felt minutes and
  geometry. With requirements set, it uses the nearest walkway that meets them and says
  when a nearer one was passed over.
- **Sidewalk absence outside inventory coverage.** 1,904 centerline edges (mostly alleys and
  service roads) were graded verified "no sidewalk" from missing planimetric polygons while
  off-street. Absence now counts only inside `dc_inventory_covered`; verified sidewalk
  presence on centerlines is 78.5% of length (was 89.1%). Graph rebuilt, coverage report
  regenerated.
- **"What would it take" used the wrong baseline.** It compared against the optimizer's
  choice even when that was not worth showing, so it could point at the route already on
  screen. Both sides now go through the same shown-route rule.
- **Crux experiment re-run on the same 1,002 trips:** every routing figure is identical to
  the previous run (crux hypothesis 93.7%, step-free 65.3% / 31.5%); only latency differs,
  and that run was memory-starved (stopped once by the low-memory guard and resumed).

### 2026-10-05 — Phase 1: API and first version of the phone web page (`283cb02`)

- **Owner decision:** live location and on-screen guidance along the chosen route move from
  Phase 4 into Phase 1 (`PLAN.md` §8 updated). Spoken turn-by-turn stays in Phase 4.
- **API** (`api.py`, `pf serve`): `POST /api/plan` wraps the trip planner; input validated;
  HTTP Basic password gate via `PF_APP_PASSWORD`; the server refuses to listen on a non-local
  address without a password; nothing about a request is stored.
- **Planner additions:** evidence held in memory instead of re-read per request; every route
  that would be shown somewhere on the priorities triangle is returned as an option with its
  comparison to the fastest route, plus the triangle itself (66 grid points → option);
  each differing place carries a map location and both sides' geometry.
- **Web page** (`web/`, React + TypeScript + MapLibre GL 6): map with a bottom sheet on
  phones; start from the browser's location or a tapped point; requirements, priorities and
  budget controls; route choices as cards; numbered pins where the chosen route leaves the
  fastest, each opening a card with the recorded conditions on both sides, with status,
  source and year; a no-route screen showing the smallest compromise.
- **Checked in a browser on the real graph:** a 3.4 km trip returned 8 options in about 1 s;
  routes, pins and decision cards rendered. Basemap is OpenStreetMap's raster tiles for
  development only.
- **Not built yet:** following the user along the route, decision-point alerts, re-planning
  when off route, the triangle as a control, address search, hosting.

### 2026-10-05 — Phase 1: place search, opt-in reported crime, route following (`283cb02`)

- **Owner decision — reported crime becomes an opt-in priority** (rule 3 reworded in
  `AGENTS.md` and `PLAN.md` §1; it was "descriptive layer only"). Off by default and outside
  the three-way mix (`Preferences.crime_weight`); penalty tables **v3**, default routes
  identical to v2.
  - Data: 11,290 MPD reports of robbery, assault with a dangerous weapon, homicide and sex
    abuse, 2023–2025. Per edge: reports within 100 m, per hectare per year; unknown beyond
    the District line (98.1% of length known). 35% of length has no such report nearby.
  - Penalty rises with the rate and is capped at the citywide 95th percentile (1.25 per
    hectare per year). Shown to the user only when opted in, always with the caveat that it
    describes blocks and reports, not spots and risk.
  - Tried on the real graph: one downtown trip with the weight at 2 took a route 0.9 min
    longer and cut the reported-crime felt minutes from 4.5 to 1.9.
- **Place search** (`places.py`, `GET /api/search`): a local index of 149,469 named places and
  addresses built from the OSM extract by `pf extract-osm`, so what people type never goes
  to a third-party geocoder. Street abbreviations are understood; about 50 ms per search.
- **Web page:** search boxes for start and destination (tap-on-map still works), the crime
  slider with its caveat, and a walking mode: the part of the route behind the user fades,
  the part ahead is highlighted, the next place where the routes differ is called out, and
  the trip is re-planned after two position fixes more than 40 m off the route. `?demo` in the
  address simulates a walk for trying it at a desk.
- **Checked in a browser on the real graph:** search suggestions, a Dupont Circle → Union
  Station plan, and the simulated walk. Not exercised in the browser: the crime slider
  (checked through `pf route` instead), a real phone, real GPS, and re-planning.
- **Codex review of this round, four findings fixed:** a route request still in flight when
  the inputs change is now cancelled and its answer discarded (it could have shown a route
  computed without a requirement just switched on); short trips on one walkway or through one
  node now return a route option, so the page shows them; the place index merged every
  same-named place into one (11 Safeways were 1) and now merges only entries within 75 m;
  arrival needs the user to be within 30 m of the route's end, not just projected onto its
  last metres. The page was rebuilt but not re-checked in a browser after these fixes.

### 2026-10-05 — Reported crime made more representative (`4b3c810`)

After a review of the research (ambient population, crime harm indices, hot-spot dynamics,
shrinkage, network methods), the first three of five recommendations were implemented. The
opt-in design is unchanged; penalty tables **v4**; default routes are unaffected.

- **Own block, not a circle.** Each MPD report is assigned to the DDOT roadway block it sits
  on (99.7% lie exactly on one; reports at intersections are shared among the blocks meeting
  there). Edges take the rate of the block they run along: 67.9% of length verified, 24.9%
  inferred (alleys and paths within 100 m behind a block), 7.2% unknown (was 1.9% under the
  100 m circle, which reached across parks and parallel streets).
- **Harm weighting.** Homicide 15, sex abuse 5, assault with a dangerous weapon 4, robbery 1
  (ratios from the Cambridge Crime Harm Index; the mapping of MPD categories is a judgment);
  robberies with a gun x2, with a knife x1.5.
- **Recency weighting, five years.** 2021–2025 (19,231 reports) with a two-year half-life.
- **Shrinkage.** Block rates are pulled toward the city mean by how little evidence they
  have. 56% of blocks have no report; they get a small non-zero rate, not zero.
- **Day and night.** Separate rates by the local hour each report began (night 18:00–06:00;
  62.5% of reports), selected by the after-dark switch. Contrary to an earlier note,
  `START_DATE` is present on every report.
- **Tried on three real trips** (ad-hoc): with the weight at 2 the route changed in all three
  by day and after dark; after dark the reported-crime felt minutes were higher and the
  saving larger (e.g. Dupont Circle to Union Station: 8.0 on the fastest route, 6.9 on the
  chosen one, for 2.9 extra minutes). Effects are modest because shrinkage flattens rates.
- **Not done:** a foot-traffic denominator (needs a new data source and an owner decision)
  and validation against held-out 2026 reports.

### 2026-10-05 — Web page redesigned around the Tradeoff Triangle (`4b3c810`)

- **Priorities are set by dragging one point in a triangle** (crossings, surface and slope,
  after dark) instead of three sliders. Once routes are planned, the triangle is coloured by
  which route wins at every mix, so dragging the point switches route at once and shows how
  far the next change of answer is. Keyboard arrows work too.
- **One colour per route**, shared by its line on the map, its card and its territory in the
  triangle; the fastest route is always the neutral grey. Colours stay with a route when the
  numbers are refreshed.
- **Route cards** show minutes large and a bar of walking time plus felt minutes by
  dimension, so the trade is visible without reading.
- **Requirements are chips, evidence a segmented control, reported crime an opt-in switch**;
  "after dark" dims the map and turns the whole interface dark.
- Layout: a search card on top, a two-tab panel ("What matters" / "Routes") that is a
  bottom sheet on phones, and a full-width action button that takes the chosen route's
  colour. Decision points replace "places"; walking mode has a progress bar.
- **Checked in a desktop browser on the real graph:** search, 30 route options for Dupont
  Circle to Union Station, the coloured triangle, and a drag that moved the selection to the
  winner at the new mix. A bug found this way was fixed: a drag could end before the page
  had re-rendered, so the refresh went out with the previous priorities.
- Not checked: a phone-sized screen, the night theme, and the walking screen after the
  redesign.

### 2026-10-05 — Faster and more practical (`e611dd1`)

Measured first: about 85% of a plan request went to describing the places where routes
differ (pandas work repeated for every option), and a 3.8 km trip sent 1.8 MB of JSON.

- **Plan requests 3-8x faster.** Evidence for all options is read once as plain rows, and
  each distinct place is described once and shared between the options that pass it.
  Dupont Circle to Union Station (31 options): 3.3 s to about 0.8 s through the server;
  Columbia Heights to Howard: 2.8 s to 0.34 s; a 0.9 km trip: 0.6 s to 0.1 s. Route search is
  now the largest part.
- **Answers compressed** (gzip): 1.8 MB to 106 kB on the wire for the longest of those.
  Built assets are cached for good (their names carry a content hash).
- **The network and place index load when the server starts**, not on the first request.
- **Moving the point in the triangle no longer asks the server anything**: the felt minutes
  for any mix are computed in the page from the per-dimension minutes already sent.
- **Routes are planned automatically** when both ends are set and again when a requirement
  changes; there is no button to press first.
- **Practical touches:** settings and the last five places are remembered on the device
  (nothing is sent); the trip is kept in the address after "#" so a reload or a shared link
  restores it (that part is never sent to a server); a swap button; arrival times; the
  screen is kept awake while walking where the browser allows.
- Checked through the server and in a browser: the timings above, compression and caching
  headers, and a trip restored and planned from a link. Not checked: a phone, the wake
  lock, remembered places, and the swap button.

### 2026-10-06 — Reported-crime measure checked against held-out 2026 reports

Ad-hoc validation, not a generated report. The measure in the graph uses 2021-2025; the
2,144 reports of the same offences from 2026-01-01 to 2026-10-04 were held out. Blocks were
ranked by each measure and scored by how much of 2026 fell on the top of the ranking.

| Measure | 2026 reports on top 10% of street length | top 20% | 2026 harm on top 10% |
|---|---|---|---|
| Old: count within 100 m, 2023-2025 | 42.9% | 63.1% | 41.2% |
| Plain count on the block, 2021-2025 | 55.5% | 72.7% | 59.0% |
| As built: harm, recency, shrinkage | 52.3% | 72.0% | 56.0% |

- **Assigning reports to their own block is what helped**: about 10-15 points more of next
  year's reports on the top tenth of street length than the old circle.
- **Harm and recency weighting did not improve prediction**; they cost about 3 points on the
  top tenth against a plain block count, even when the target is 2026 harm. Shrinkage alone
  changes nothing in the ranking of blocks that have reports. With 2,144 held-out reports
  a difference of 2-3 points is near the edge of what the sample can show.
- The weights are kept for what they represent (severity, currency, not over-reading one
  report), not because they predict better. Simplifying to a plain block count is an open
  decision for the owner.
- Also tried and withdrawn: loading the map library separately cut the first script from
  1.29 MB to 0.25 MB, but the map stayed blank in the two checks made before the browser
  connection was lost, so the change was reverted unverified.

### 2026-10-06 — Routes redrawn on the map (`5651a68`)

Display only (`web/src/MapView.tsx`, `web/src/styles.css`); no routing or data change.

- The chosen route has a white casing, a soft glow in its own colour, a gradient from a
  lighter start to a deeper end, and white chevrons showing direction.
- Other routes are thinner, cased, and keep the colours used on the cards and the triangle.
- An open decision point shows a soft band under both ways through it, with the fastest
  route's side dashed in coral.
- While walking, the part already covered is a dotted grey trail; the part ahead keeps the
  full treatment. Start, destination and the user's position are HTML markers; the user's
  dot pulses.
- Checked in a browser on the real graph (Dupont Circle to Union Station): casing, gradient,
  alternative routes, pins and chevrons draw. The chevrons were then enlarged and spaced
  closer; that last change builds but was not seen in a browser (connection lost). The
  walking view and the night theme were not checked.

### 2026-10-06 — Route search made much faster (`5651a68`)

A long trip took up to 20 s to plan; almost all of it was the route search
(`routing/router.py`), which ran about 460 shortest-path searches over a 69,000-edge area.
Ad-hoc timings on this machine, not a generated report.

- **Tighter search area.** Inside the budget ellipse an edge is kept only if the fastest way
  from the start to it, along it, and on to the destination fits in the time budget. No
  route within the budget is lost; about a third of the edges remain.
- **Fewer searches per priority mix.** When the best route for a mix breaks the budget, the
  smallest time penalty that fits it is found by intersecting the two bracketing routes
  (Handler & Zang) instead of ten rounds of bisection.
- Subgraphs are built with array operations, and weights are passed to igraph without a
  slow per-element conversion.
- **Timing:** a cross-city plan request 20.3 s -> 1.9 s; 24 sample trips (0.3-7 km, day and
  night, some step-free) 148.6 s -> 5.2 s in total for the route search.
- **Results:** on those trips, 1,351 of 1,518 priority mixes get the identical route; the
  other 167 get a route with lower felt cost (median 54 felt seconds less), none higher and
  none over budget. The fastest route is unchanged on all of them. Routes differ because the
  tighter area stops over-budget detours from steering the budget search.
- `reports/phase0/crux.md` was generated with the earlier search and has not been re-run.
- **Later the same day: `pf crux --fresh` re-run** with the new search (same 1,002 trips):
  [`crux.md`](../reports/phase0/crux.md). Feasibility and the crux hypothesis are unchanged
  in every profile (everyday 93.7%, step-free likely 86.7%, verified 91.8%) except
  everyday x2, 92.3% -> 92.1%. Median routes per set rose 9 -> 10 (everyday) and 11 -> 12
  (x2). Latency, everyday: p50 0.283 -> 0.143 s, p95 1.968 -> 0.496 s; worst profile p95
  3.683 -> 0.627 s (`09ecb12`).

### 2026-10-06 — Own map tiles, walk recording, tester feedback (`5651a68`)

Three of the open Phase 1 items, built so that phone testing can start once hosting is chosen.

- **Self-hosted basemap.** `pf fetch basemap_dc basemap_fonts` copies the 745 tiles over DC
  (to zoom 15, 29.9 MB) out of the Protomaps world build by range requests, plus Noto Sans
  label glyphs; both are registered in `sources.py` and land in the manifest. `pf serve`
  serves them (`/tiles`, `/fonts`), and the page draws a vector map from them, light by day
  and dark after dark. No outside tile service is asked when they are present; without them
  the page falls back to OpenStreetMap's raster tiles as before.
- **Walk recording, for tuning guidance.** While walking, an opt-in switch records each
  position fix with its accuracy, distance from the route and distance to the next decision
  point, plus re-plans and arrival. It stays in the browser; "Save recording" writes a JSON
  file the walker passes on themselves. Nothing is uploaded.
- **Tester feedback.** A three-question form (do felt minutes make sense, are decision
  points clear, is it better than a route list) with a comment, offered after a walk and
  from the routes list. `POST /api/feedback` appends the answers and the day to
  `<data>/feedback/feedback.jsonl`; no location, trip or device details.
- Checked in a browser with the simulated walk: vector map with labels, routes over it,
  recording counter, the saved-walk card and the feedback form all appear. Not exercised:
  the download itself, sending the form from the page (the endpoint is covered by a test),
  the dark map, a phone-width screen. 153 tests pass.
- Not done: nothing has been walked outdoors, so the off-route (40 m) and alert (80 m)
  distances are untuned, and there is no script yet that reads a recording.

### 2026-10-06 — Crossing-risk model, first study (`8a3d07f`)

Owner decisions the same day: missing-infrastructure inference is removed from Phase 2, and
the crossing-risk model is started now. Report: [`crossing_risk.md`](../reports/phase2/crossing_risk.md)
(`pf crossing-risk`). Nothing in routing uses it yet.

- **Method.** A safety performance function (Poisson regression of injury crashes on
  design) with empirical-Bayes adjustment toward each place's own history. Fitted on
  2015-2022, scored on 2023-2025.
- **Unit: the site, not the crossing.** 17,674 mapped crossings form 7,493 sites (the
  crossings of one intersection). A quarter of crashes are located at the centre of an
  intersection, so the leg being crossed is not recorded. A first attempt per crossing was
  dropped for that reason: assigning each crash to the nearest leg is arbitrary, and sharing
  it among legs breaks the count model.
- **Result on 2023-2025** (1,425 assigned injury crashes): Poisson deviance 0.832 with one
  rate for every site, 0.714 by High Injury Network membership, 0.615 for the design model,
  **0.536 for design + own history**. Share of later crashes at the top tenth of sites:
  7.2%, 32.2%, 42.1% and **50.4%**; own history alone 47.6%, with no finite deviance because
  25.6% of later crashes happened at sites with no crash in 2015-2022.
- 71.2% of injury crashes lie within 25 m of a mapped crossing; the rest are left out.
- The model forecast 1,642 crashes for 2023-2025 against 1,425 recorded (15% high).
- **Limits.** It predicts reported crashes per site, not risk per person crossing: there is
  no count of people on foot, and mapped places nearby are a crude stand-in. Signalized
  sites show more crashes (x1.37 other things equal), which reflects where signals are put,
  not what they do. Today's design is matched to earlier crashes.
- 162 tests pass (7 new, on synthetic data).

### 2026-10-06 — Live Metro elevator outages, as a notice (`5651a68`)

- **Finding that changed the design.** The plan assumed step-free walking routes depend on
  Metro elevators. The graph has 6 elevator links citywide and none is a Metro elevator:
  two near the White House and one in Georgetown are far from any station entrance, and the
  three at 9th & G St NW are indoor elevator rooms of a building (`indoor=room`, levels
  0-2). Removing broken Metro elevators from routes would change nothing.
- **What was built instead.** When a trip starts or ends within 150 m of a station entrance,
  the plan carries a notice for each elevator WMATA reports out at that station: where in
  the station, expected return, source and the time the list was read. If the list cannot
  be read the notice says the status is unknown. No route changes. The outage list is the
  same request for everyone, at most once a minute; nothing about a trip goes to WMATA.
- Station entrances and names are registered sources (`wmata_entrances`, 275 entrances;
  `wmata_stations`, 102 stations). The key lives in `.env`.
- Checked against the live feed (8 elevators and 23 escalators reported out at the time): a
  trip ending at Benning Road carried its reported outage, a trip ending at Dupont Circle
  carried none, and a trip away from any station carried none. The notice on the page was
  type-checked and built but not looked at in a browser. 154 tests pass.
- Limits: escalators are not reported; a notice cannot say whether the broken elevator is the
  street one or the platform one beyond WMATA's own description.

### 2026-10-13 — Phone layout checked at phone width (`43b18a5`)

- **How it was checked.** The built page in a 390 × 760 frame inside desktop Chrome, on two
  trips (White House to the Capitol, Dupont Circle to the Lincoln Memorial) and the demo
  walk. This tests the layout only: no touch input, no real GPS, no real phone browser.
- **Found and fixed: a trip's ends hidden on a phone.** The map framed a trip assuming the
  search card took 60 px and the panel half the screen; they take 157 px and 56%. On the
  north-south trip the start sat under the search card and the end under the panel. The
  room each takes is now measured when a trip is framed and while walking
  (`MapView.covered`); after the fix the start and end sit 28 px inside the visible map.
- **Fixed from reading the styles, not seen in a browser:** search boxes and the feedback
  box used 15 px type, which makes iPhones zoom the page in on focus; now 16 px. The
  numbered pins (28 px) and the swap button (34 px) keep their size but take taps over
  44 px.
- Nothing overflows sideways at 390 px; both tabs, search suggestions and the walking panel
  fit. The visible map between card and panel is only about 175 px tall on this size.
- `feature/initial-platform` merged into `master` (they were already at the same commit
  before this change).

### 2026-10-13 — Step-by-step guidance while walking (`b76bede`)

- **What was missing.** Walking mode already followed the walker, re-planned when off the
  route and announced decision points, but never said what to do next.
- **What was built.** Every route option now carries its steps in walking order
  (`routing/guidance.py`): a turn where there is a choice of ways (three or more walkways
  meet and the way bends 30° or more, measured 12 m either side), each street crossing with
  its control and curbs as claims with status, source and date, crossings that are not
  mapped (the `xing_u` / `xing_v` ends; two halves that disagree read as unknown), stairs
  and escalators, and stretches with no sidewalk. Each step points at a vertex of the
  route's geometry, so the page works out the distance ahead from the walker's position
  with no further request. The walking panel shows the next step, how far it is, what is
  on record about it, and the step after when it follows within 30 m. Nothing changes any
  route.
- **Finding that shaped it.** Sidewalks carry no street name in the graph (0% of 2,352 km),
  so a turn can rarely say "onto K Street"; only named paths, alleys and streets walked on
  can. Crossings know the street they cross, so guidance reads "Bear left, then cross
  Minnesota". That name comes from the roadway inventory in capitals without "Avenue" or
  the quadrant; the page lower-cases it and adds nothing it does not know.
- **Checked on real trips** (scratch runs, not a generated report): Dupont Circle to the
  Lincoln Memorial, 2.7 km, 35 steps (21 turns, 10 crossings, 2 flights of steps); a
  Deanwood trip, 1.8 km, 24 steps including one unmapped crossing and an escalator. Four
  trips gave 24–41 steps on the recommended route. Steps add about 60% to the compressed
  answer (58 → 93 kB for a 31-option trip) and no measurable planning time.
- **Seen in a browser** in the phone-sized frame with the simulated walk: steps advance,
  "now" at 15 m, crossing evidence shown. Not tried: a real phone, real GPS, and whether
  the turn thresholds read right on the street. 170 tests pass.

### 2026-10-13 — Street names in guidance, a fixed crux sample, and five smaller items (`ab979aa`)

- **Street names.** A sidewalk now takes the name of the DDOT roadway block it runs beside
  (`along_street`: the nearest block within 30 m that runs the same way; 94% of sidewalk
  length has one), and a crossing carries the crossed street's full name with type and
  quadrant instead of the bare name. Guidance now reads "Turn right onto New Hampshire Ave
  NW" and "Cross 20th St NW" (seen in the browser on the Dupont Circle trip). Both names are
  for wording only and enter no cost. The names on the Dupont Circle trip read right; a wider sample was printed but not checked
  against a map.
- **Elevator rooms.** The rule written for the three room outlines at 9th & G St NW applies
  to all six elevator ways in the extract: every one is a closed outline tagged
  `indoor=room`. They are no longer walkable links (142,526 edges, 6 fewer; 743 components,
  6 fewer). The graph now has no elevator links at all.
- **Fixed crux sample.** The 1,002 trips of the 2026-10-06 run were converted from node
  ids to coordinates (`reports/phase0/crux_od_pairs.csv`) before the graph was rebuilt.
  Each run places them on the current network; a trip with an end more than 30 m from it
  is left out and counted. `--fresh` keeps the trips, `--resample` draws new ones.
- **Result of re-running on the rebuilt graph:** all 1,002 trips were found again and every
  figure in the crux summary is identical to the previous run except latency (everyday
  p50 0.15 s, p95 0.46 s). The coverage report changed only by the six edges; the
  crossing-risk report did not change.
- **Pull-down panel.** On a phone the panel has a grip that drops it to its button; the
  trip is framed again in the larger map (start and end about 28 px inside it, measured).
- **Map fetched after the page.** The first script is 83 kB compressed instead of 377 kB;
  the map library (293 kB) follows. This exposed a fault, fixed in the same change: the
  library's stylesheet now arrives after the page's and collapsed the map to no height.
- **Walk recordings.** `pf walks <files>` reads recordings saved from the page and prints
  how far fixes were from the route, how many re-plans each off-route distance would have
  caused, how much notice decision points got, and a suggested off-route and alert
  distance. Tested on made-up recordings only: no real walk exists yet. It cannot tell a
  walker who left the route from a poor fix, and says so.
- 180 tests pass with the graph built. Seen in a browser: the phone-sized frame only.

### 2026-10-14 — One style of street name, and a layout for a phone held sideways (`46a9170`)

- **Street names.** OSM spells names out ("C Street Southeast") and the roadway inventory
  abbreviates them ("C ST SE"), so guidance mixed the two on one trip, and a turn from a
  street onto the sidewalk beside it could name the same street as if it were a new one.
  An OSM name that ends in a street type and quadrant is now written as the inventory
  writes it (`guidance._inventory_style`); one with words after them keeps them ("20th St
  NW Cycletrack"). Trail and park names are unchanged. On the real graph 951 of 1,338 OSM
  names change (64% of named length); 727 of the 938 that become the inventory's exact
  form match a name the inventory gives some sidewalk or crossing, and the rest are minor
  streets no sidewalk is named after.
- **Phone held sideways.** Wider than 760 px it got the desktop layout, whose panel was
  about 186 px tall; narrower it got the portrait layout, which left a strip of map. On a
  short, wide screen the search card and the panel now stack down the left side and scroll
  as one, with the button pinned at the bottom; the map frames the trip to their right
  (measured, as on portrait phones) and frames it again when the phone turns. Seen in
  844 x 390 and 667 x 375 frames in desktop Chrome on a Dupont Circle to NoMa trip: three
  route cards readable, the trip clear of the column. Portrait phone and desktop layouts
  are unchanged (measured). Walking mode sideways was not looked at.
- 181 tests pass with the graph built.

---

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-10-15 | **Maryland pilot go/no-go bar, fixed before the first run** (owner-approved plan): a pilot town is worth more work only if, from OSM alone, (1) at least **50%** of walkable length is sidewalk-level (DC: 67.6%), (2) at least **60%** of mapped crossings have a known control type, and (3) the main connected component holds at least **90%** of walkable length. A town that misses it is recorded with the reason, and the bar is not lowered | Set before any Maryland number exists so the result cannot move it. Below these, most decisive places would be `unknown` and the product would say little |
| 2026-10-15 | The pipeline runs per **region** (`PF_REGION`, default `dc`); DC keeps its paths and outputs. Pilots: **Gaithersburg** and **City of Frederick** (MD-6), from OSM and city limits only | Owner-approved plan of 2026-10-15: best-documented data in MD-6, two different street layouts. Each county or state inventory is added later, one at a time, after inspection |
| 2026-10-15 | Without a stairs, lights or signal inventory, **nothing is confirmed by absence**: a painted crossing with no signal on record is `inferred` unsignalized, not verified; zero lights on record is `unknown` | Rule 1. In DC those absences counted only because DDOT's inventories are comprehensive inside the District line |
| 2026-10-06 | **Missing-infrastructure inference removed from Phase 2**; the crossing-risk model stays and is started first | Owner decision. Unrecorded curb ramps and sidewalks stay `unknown`; step-free coverage is expected to improve through user confirm/correct reports instead |
| 2026-10-06 | Metro elevator outages are a **notice on the trip**, not a routing input | The walking graph has no Metro elevator links, so removing broken ones would change no route |
| 2026-10-04 | "Personal security" becomes **after-dark comfort**; reported crime only as an opt-in descriptive layer | Block-level, report-based data; documented bias; SketchFactor precedent in DC; B2B customers won't adopt neighborhood-avoidance |
| 2026-10-04 | Revenue primarily **B2B** (institution widgets, data/API, conditions reports); core step-free routing always free | Consumer navigation is hard to monetize; accessibility shouldn't be paywalled |
| 2026-10-04 | **Citywide** from Phase 0 | Owner requirement; feasible thanks to ellipse pruning |
| 2026-10-04 | Data and venv live **outside the repo** | GBs of reproducible data must never be committed or cloud-synced (repo was in OneDrive at the time) |
| 2026-10-04 | Repo lives at `C:\dev\PathFinder`, **not in OneDrive** | OneDrive syncing git internals risks corruption and used ~1.4 GB RAM; GitHub is the backup |
| 2026-10-04 | "Verified" includes **confirmed absence** in an inventory comprehensive for that place | Lets on-street step-free be verified via OSM + planimetric stairs; off-street stays inferred |
| 2026-10-04 | Grades > 25% downgraded to **inferred** | Can't distinguish genuinely steep paths from misaligned lines on hillsides |
| 2026-10-04 | `AGENTS.md` is the single agent guide; `CLAUDE.md` imports it | Claude and Codex follow the same rules without drift |
| 2026-10-05 | Sustained grade = 10 m least-squares window; **verified only if three parallel lines agree within 3 points** | A reading that changes when the line moves 1 m is not an observation of the walkway; 10 m is the longest run an ADA ramp may have |
| 2026-10-05 | Street-centerline junctions are **implicit crossings**, priced and held to curb requirements | Otherwise unmapped areas get free, ramp-free crossings (rule 1) |
| 2026-10-05 | A crossing is a signal only on positive OSM evidence; a nearby DDOT signal alone never makes it one | A quarter of painted crossings near signals that have node evidence are not signalized |
| 2026-10-05 | Absence in a DC inventory is evidence only on-street **inside the District line** | The inventories stop at the boundary |
| 2026-10-05 | Slope is kept inside USSS redaction areas | Only non-ground returns are redacted; the DTM is intact there |
| 2026-10-05 | Gaps of 3–15 m are bridged **only on planimetric sidewalk-surface evidence**; other near-misses are counted, not bridged | Near is not connected; a straight line across unknown ground may be a fence, a wall or a road |
| 2026-10-05 | **Live location and on-screen guidance** along the chosen route move from Phase 4 into Phase 1 (owner) | Owner's product direction: a phone website that follows you as you walk and lets you pick among the route choices |
| 2026-10-05 | **Live location and on-screen guidance** along the chosen route move from Phase 4 into Phase 1 (owner) | Owner's product direction: a phone website that follows you as you walk and lets you pick among the route choices |
| 2026-10-05 | The API stores nothing and listens only locally unless a password is set | Deployment stays private (rule 6); location is used for routing only |
| 2026-10-05 | **Reported crime is an opt-in priority**, off by default and outside the three-way mix (owner) | Owner wants crime reports in the decision; opt-in keeps defaults free of the block-level, report-based bias the plan warns about |
| 2026-10-05 | Reported crime is measured **per block, harm- and recency-weighted, shrunk, by day and night** | A raw count in a circle mixed neighbouring streets, treated a homicide like a robbery, let one old report define a quiet block and ignored time of day |
| 2026-10-05 | The priorities control is the **Tradeoff Triangle**, coloured by winning route | It is the product's signature idea (PLAN §2) and makes "what would it take" something you can see and drag |
| 2026-10-05 | Place search runs on a **local OSM index**, not a third-party geocoder | What people type is often their home or destination; nothing leaves our server |
| 2026-10-05 | Alternatives must be ≥ 30 felt seconds better to be shown | Many "different" recommendations were practically equivalent to the fastest route |
| 2026-10-04 | Inferred connectors are never **verified** step-free; any contact with a stairs polygon makes them not step-free | The link itself is a heuristic (rule 5), and a 1–3 m gap sitting on a stairs polygon is most likely the unmapped stairs |

---

## Open issues

Resolved on 2026-10-05 (see Timeline): slope metric noise; worth-showing threshold; the
1,550 signal conflicts; edges with grades above 100%.

- Equity gap in Wards 7 and 8 sidewalk mapping (data, not code): 47–52% sidewalk-level.
- 65% of curb evidence predates 2018.
- Step-free trips are feasible for only 67.8% (allow likely); slope and curb gaps fragment
  the network. Phase 2 inference and field audits are the remedy, not looser rules.
- 17% of length has only an inferred slope; a field sample should check the 3-point
  repeatability tolerance and the 10 m window.
- Sidewalks wholly on untagged decks still read the ground below with no warning sign in
  the profile (only those crossing the deck edge are caught).
- Implicit crossings overstate turns (a corner turn counts as a crossing) and use the widest
  street at the junction.
- Latency in the 2026-10-06 crux run (p50 0.14 s, p95 0.50 s everyday) was measured on a
  memory-starved machine with other work running; treat it as an upper bound.
- The web page has been exercised in a desktop browser only, at desktop width and (2026-10-13)
  in a phone-sized frame. A real phone, touch, real GPS, and re-planning when off route have
  not been tried.
- A phone held sideways has its own layout (2026-10-14), seen only in desktop Chrome and
  not in walking mode; the button text wraps at 667 px. The panel is pulled down by
  tapping its grip, not by dragging it.
- Reported crime still has no measure of how many people are present, so busy blocks read
  as worse than they are per passer-by. Against held-out 2026 reports the harm and recency
  weights did not predict better than a plain block count (see Timeline, 2026-10-06);
  whether to keep them is an owner decision.
- 6% of sidewalk length has no street name. OSM names without a quadrant ("Entry Road")
  are shown as OSM spells them. Turns come one per 130 to 210 m on the trips checked, which may be too many; the
  thresholds are untested on the street.
- Place search only knows what OSM has: an address missing from OSM is not found.
- The basemap is now served locally, to zoom 15 and with Latin label glyphs only; it is a
  dated extract (2026-10-06) and goes stale until fetched again.
- The map library is still 293 kB compressed; it now loads after the page (83 kB) rather
  than before anything shows.
- Felt minutes computed in the page use minutes rounded to 0.1, so they can differ from the
  planner's own total by a few tenths.
- 2,365 pedestrian dead ends lie within 15 m of another walkway with no evidence either way;
  they need field or imagery review, or OSM edits.
- Crux runs before 2026-10-05 used other trips and are not comparable trip-for-trip with
  later ones; from 2026-10-06 on the trips are fixed.
- Latency varies about twofold with free memory on this machine (p50 0.12–0.28 s everyday).
- WMATA elevator data needs a (free) API key from the owner.
- Machine memory is tight; the low-memory guard stopped long runs three times on 2026-10-05.

## Next steps (Phase 2, started early)

1. Decide whether and how the crossing-risk estimate enters the crossing penalty. It is per
   site and reflects foot traffic as well as danger, so using it raw would steer people away
   from busy crossings; that needs the owner's decision before any penalty changes.
2. An exposure measure (people on foot) would turn crashes per site into risk per crossing.

## Next steps (Phase 1)

1. Try guidance on a real phone outdoors (needs hosting); tune the off-route and alert
   distances from that.
2. The Tradeoff Triangle as a control: done 2026-10-05 (see Timeline).
3. Self-hosted basemap: done 2026-10-06. The script that reads walk recordings (`pf walks`):
   done 2026-10-13; it needs real walks to say anything.
4. Hosting for phone testing: HTTPS is required for location. Suggested 2026-10-14:
   Tailscale Serve, which gives `pf serve` an HTTPS address only the owner's own devices
   can open (private, free, nothing public). A public host still needs the owner's
   go-ahead, provider and budget.
5. WMATA elevator outages: done 2026-10-06 as a notice on the trip (see Timeline).
6. Review "Why Not This Route?" (2026) before any explanation claims; user interviews on
   felt minutes.

---

## How to update this log

- Add a dated entry under **Timeline** for each meaningful change, with the commit hash.
- Record results as numbers with links to the generated report, not impressions.
- Record product/technical choices in the **Decisions log** with the reason.
- Update **Current status**, add a new column to **Key metrics over time** when metrics
  change, and keep **Open issues** / **Next steps** accurate (move resolved items into the
  Timeline entry that resolved them).
- Never delete history; correct mistakes with a new dated note.
