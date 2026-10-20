# AGENTS.md — PathFinder

Shared guide for AI coding agents (Codex reads this file; Claude Code imports it from
`CLAUDE.md`). Keep it accurate: if you change a convention, command, or invariant, update
this file in the same change.

## What this project is

PathFinder is an evidence-graded **city accessibility app** for **Maryland's 6th
congressional district** (MD-6): Gaithersburg, Germantown, Frederick, Hagerstown, Cumberland,
Frostburg and the towns between. It has two faces fed by one graph:

- **Routes first:** step-free route planning for people with mobility disabilities, chosen
  through a **mobility profile** (manual wheelchair, power wheelchair or scooter, walker or
  cane, stroller, custom). It shows **where** routes differ (Crux Map), **what is known vs.
  unknown** about each place (evidence grading), and **how far priorities must move** before
  another route wins (Tradeoff Triangle).
- **The city barrier map:** recorded barriers (raised curbs, missing ramps, steep grades,
  steps, streets with no sidewalk) and the places nobody has recorded, for cities and
  advocates.

Three user-controlled dimensions: **crossings & curbs, slope, sidewalk**. Refocused on
2026-10-15 from a general walking navigator: after-dark lighting and the crime layer were
removed.

PathFinder began on 2026-10-15 as a copy of DistrictDirect (the owner's DC navigator,
`C:\dev\DistrictDirect`), with a region layer added so the pipeline runs per Maryland town.
It is a **separate app**: own repo, package (`pathfinder`), command (`pf`), venv, data folder
and env vars (`PF_*`). Never edit DistrictDirect for PathFinder work. DistrictDirect's plan
and progress log are kept for reference in `docs/reference/`; the rules and methods there
were checked on DC and carry over, the DC numbers do not.

Plan: `docs/PLAN.md` — read it before making product or modeling decisions. Current phase:
**C — Maryland sources, accessibility first** (elevation, then curb ramps), each inspected on
imagery before a region names it. The accessibility product has its own go/no-go bar, fixed
before any accessibility source was loaded (`docs/PROGRESS.md`, Decisions log).

## Non-negotiable product rules

1. **Missing data is never favorable.** A null attribute is `unknown`, and unknown is
   penalized in costs and fails requirements unless the user's certainty setting accepts it.
   Never default a missing curb ramp, slope, light, or signal to the "good" value.
2. **Requirements are never traded off.** Step-free / max-slope are hard edge filters
   (`routing/cost.py: feasible_mask`), not weights.
3. **A profile is a starting point, never a verdict.** It sets requirements and a priority
   mix (`routing/profiles.py`); an explicit choice by the user always overrides it, and its
   numbers are product judgments to be revised with disabled testers.
4. **Never describe a route or place as *accessible*, *ADA-compliant* or *safe*.** Say what
   is recorded. Every claim shown to users carries its source and date.
5. **Inferred is not verified.** Model/heuristic outputs use status `inferred` and never
   satisfy "verified only".
6. **Deployment stays private** unless the owner explicitly authorizes public access. No
   accounts, payments, or social features unless the plan calls for them.
7. **Unlicensed data stays internal.** A source with no stated open license (City of
   Frederick, Montgomery Planning, Gaithersburg, MDOT proxy services) may be used to build and
   test, but nothing built on it is shown to anyone outside until written permission exists.
   Such sources say "Internal use only" in their license line; the barrier report and map
   name them and are marked internal while any is in use.

## Repository layout

```
docs/PLAN.md                 the MD-6 plan (phases A–E, data sources, partners, risks)
docs/PROGRESS.md             running record: timeline, decisions, metrics, open issues
docs/reference/              DistrictDirect's plan and log (DC; methods and their history)
src/pathfinder/
  config.py                  paths (data lives OUTSIDE the repo), CRS constants, PF_REGION
  regions/                   one module per region: its sources, which source plays each role
                             (signals, planimetrics, roadway, ...), where its inventories cover
                             (maryland.py: Gaithersburg and Frederick pilots; planimetrics are
                             Montgomery's and the City of Frederick's sidewalk surveys)
  sources.py                 the current region's registry of external datasets
  fetch.py                   downloads + provenance manifest (sha256, counts, fetch time);
                             pbf_clip cuts a town out of the statewide OSM extract
  osm.py                     OSM PBF -> interim parquet (ways, tagged nodes, rail/water barriers,
                             areas closed to the public)
  evidence.py                value/status/source/as_of grading helpers + invariants
  graph/classify.py          walkability rules (pure functions over OSM tags)
  graph/build.py             topology: classify, separate-sidewalk detection, split,
                             stub pruning, gap bridging, region scope clip, closed areas
                             removed, components
  graph/roles.py             reads the region's source for each role in canonical columns;
                             a missing role is an empty frame, so its attributes stay unknown;
                             without a roadway inventory the streets come from OSM
  graph/enrich.py            evidence-graded attributes (crossings, kerbs, sidewalks, slope, ...)
  graph/elevation.py         sustained slope from a 1 m bare-earth DTM (10 m fitted windows on
                             three parallel lines); none registered for MD yet
  routing/cost.py            requirements + "felt minutes" penalty tables (PENALTIES); the
                             three dimensions cross (crossings & curbs) / slope / sidewalk
  routing/profiles.py        mobility profiles: starting requirements and mix, overridable
  routing/router.py          ellipse-pruned route sets over the preference simplex
  routing/divergence.py      divergence sections between routes (Crux Map core)
  routing/explain.py         worth-showing rule, crux, "what would it take", minimal relaxation
  routing/guidance.py        the steps of a route for on-screen guidance (turns, crossings, stairs)
  routing/service.py         TripPlanner: snap, plan, explain -> JSON with sourced conditions
  places.py                  local place and address search built from the OSM extract
  analysis/coverage.py       coverage report -> reports/<region>/phase0/
  analysis/crux.py           crux-hypothesis experiment -> reports/<region>/phase0/
  analysis/barriers.py       city barrier map: recorded barriers and unrecorded places, by
                             census tract -> reports/<region>/barriers/ and /api/barriers
  analysis/walks.py          reads walk recordings; suggests off-route and alert distances
  basemap.py                 the backdrop map served locally (when a region has tiles)
  wmata.py                   live Metro elevator outages (off until a region registers WMATA)
  api.py                     FastAPI app: /api/plan (optional `profile`), /api/barriers,
                             /api/search, /api/feedback, /api/region (with the profiles),
                             /tiles and /fonts, password gate, serves web/dist
  cli.py                     `pf` command
field/<region>.csv           the team's field checks of blocking curbs (field/README.md); the only
                             data kept in the repo, read as source <region>_field_checks
tools/field_checks/          make_sheet.py: the field sheet from the blocked-trip worklist
web/                         phone web app (React + TypeScript + MapLibre GL, built with Vite)
tests/                       unit tests (synthetic) + data invariants (marked `data`)
reports/<region>/            generated, committed, human-readable outputs (do not hand-edit)
```

## Environment and commands

- Repo: `C:\dev\PathFinder`, moved out of OneDrive (`Desktop\CongoApp`) on 2026-10-19 so sync
  cannot touch git internals. Large data still never goes here. Venv: `C:\Users\arjun\.venvs\pathfinder`
  (it has no pip of its own). Install:
  `py -m pip --python C:/Users/arjun/.venvs/pathfinder/Scripts/python.exe install -e ".[dev]"`.
- Data directory: `PF_DATA_DIR`, default `~/.pathfinder/data`. Each region has
  `<data>/regions/<id>/` (raw, interim, graph, analysis); the statewide Geofabrik extract
  that every town is cut from lives once in `<data>/shared/`.
- Region: `PF_REGION` (default `gaithersburg`; also `frederick`). Every `pf` command works on
  the current region (`pf sources` prints which); reports go to `reports/<region>/`. Run one
  region at a time: memory on this machine is tight (often ~0.5 GB free).
- Pipeline (each step is idempotent; `fetch` skips existing artifacts unless `--force`):

  ```
  pf fetch                 # the region's sources; the OSM clip streams the statewide extract
  pf extract-osm           # also builds the place-search index (interim/places.parquet)
  pf build-graph
  pf enrich                # writes graph/edges.parquet
  pf coverage              # reports/<region>/phase0/coverage.md + maps, and the accessibility bar
  pf barriers              # reports/<region>/barriers/barriers.md, by census tract, + map
  pf crux --per-bin 334    # reports/<region>/phase0/crux.md (Frederick's fixed sample: --per-bin 100)
  python tools/blocked_trips/blocked_trips.py   # after crux: what blocks wheelchair trips,
                                                # reports/<region>/blocked/ (internal)
  python tools/field_checks/make_sheet.py --update   # new worklist places onto field/<region>.csv
  pf route 39.1434,-77.2014 39.1210,-77.2370 --profile manual_wheelchair   # one explained trip, JSON
  pf serve                 # API on 127.0.0.1:8000, plus the built web app if web/dist exists
  ```
  A change to `build.py` needs `pf build-graph` onward; a change to `enrich.py`,
  `elevation.py` or the cost model needs `pf enrich` onward and `pf crux --fresh`.
- Web app: `cd web && npm install`, then `npm run dev` (page on :5173, proxies /api to
  `pf serve`) or `npm run build` (output in `web/dist`, served by `pf serve`); `node_modules`
  is git-ignored. Tabs: What matters (profile, triangle, requirements), Routes,
  Barriers (the city map for the current view). The dark theme follows the phone's setting. `pf serve`
  refuses any non-local host unless `PF_APP_PASSWORD` is set. The map opens at the region's
  centre (`/api/health`). MapLibre 6 needs its worker bundled (`MapView.tsx`).
- Web app on phones (2026-10-19), what keeps it fast:
  - **Startup:** the map's code is fetched and started only after the first paint
    (`useAfterFirstPaint`). Starting it first held the whole page blank. Do not add a preload for
    it: measured on slow 4G, it took bandwidth from the page and made everything later.
  - **Map:** two map workers at most, and pixel ratio capped at 2.
  - **Redraws:** `MapView` redraws each part only when its own data changes; never redraw
    everything on each render.
  - **Saved settings:** writes are gathered every half second.
- What the user sees on a phone:
  - **Sheet:** the panel drags between three heights by its handle (grip and tabs).
  - **Locate:** a locate button floats above the panel. While walking the map follows the user
    until they move it themselves (watched on pointer events), and the button then reads
    "Re-center".
  - **Map failure:** a map that fails to load leaves a retry, never a blank page.
  - **Offline:** there is an offline notice.
- **Home screen and caching:** `web/public/` holds the manifest, icons and `sw.js`. The service
  worker keeps only the app itself, plus `/api/region` and `/api/health`, and never trips,
  searches, barriers or positions. It registers only over HTTPS or on this machine. `api.py`
  serves the page, `sw.js` and the manifest `no-cache` so phones pick up a new build.
- **Touch targets:** 44 px at least.
- Basemap: no Maryland tiles are registered yet, so the page uses OpenStreetMap's public
  raster tiles (light development use only).
- Tests: `python -m pytest -q` (data-invariant tests skip if the graph is not built; run
  them after any pipeline change, with `PF_REGION` set to the region you built).

## Conventions

- **CRS:** compute in `EPSG:26985` (NAD83 / Maryland, meters); store/exchange `EPSG:4326`.
  Maryland's county LiDAR services differ (Montgomery: EPSG:2893, US feet); always
  transform, never assume.
- **New data source:** add it to its region in `regions/` (URL, license, limitations,
  verified date) and fetch it through `fetch.py` so it lands in the manifest. Never hard-code
  URLs elsewhere. A source that plays a role (signals, ramps, ...) needs an adapter in
  `graph/roles.ADAPTERS` into the role's canonical columns, and its records are inspected
  against imagery (about 30 features) before the region names it in `roles`.
- **New region:** a `Region` in `regions/` with its OSM clip, boundary, buffer, map centre
  and bbox. Fill `roles` and `coverage` only with inspected sources; until then the pipeline
  runs on OSM alone and everything else stays unknown.
- **New graded attribute:** use `evidence.init_unknown` / `fill_where_better`, apply sources
  in priority order, add it to `enrich.GRADED_ATTRS`, and cover it in the coverage report.
- **Inferred connectors** (gap-bridging links the pipeline invents) are never `verified`
  step-free; one that touches a planimetric stairs polygon is not step-free at all.
- **Near is not connected.** Gaps up to 3 m between walkways are bridged as mapping slips;
  gaps up to 15 m only where a planimetric survey shows sidewalk surface all the way and the
  line crosses no road, rail, water or stairs (`build.surface_gap_test`). Without a survey
  only the 3 m pass runs. Every other near-miss is counted in the coverage report.
- **Sidewalks from a survey.** Outside inventory coverage a survey can say "both" or
  `at_least_one_side` (one side found within `enrich.ONE_SIDE_MAX_OFFSET_M`, the other not
  known), never `one_side` or `none`; `enrich.SIDEWALK_PRESENT` lists the values that mean a
  sidewalk is there. Estimated sidewalk lines (`graph/survey_sidewalks.parquet`, written by
  `pf enrich`) are a map layer only: the router keeps walking the street centerline, because
  a line beside the street would have to bend back to every junction and its connections
  would be invented. The sidewalk is the survey's; where the line is drawn is `inferred`.
- **Absence is evidence only inside inventory coverage.** "No stairs / no sidewalk / no
  signal on record" counts only where `covered_<family>` holds (families: planimetric,
  signals; each region states "boundary", "everywhere" or none). A region with no inventory
  confirms nothing by absence. Check an inventory's completeness before naming it.
- **Implicit crossings.** On street-centerline edges, passing a junction crosses a street
  with no crossing edge. `xing_u` / `xing_v` flag those ends; cost and requirements treat
  each as half a crossing with inferred evidence at best. A known curb there carries its
  source and date (`xing_<end>_kerb_source` / `_as_of`): the ramp records counted, dated by the
  oldest one, or OSM where the walker is in the roadway.
- **A favorable value needs positive evidence.** A crossing is a `signal` only when OSM says
  so; a nearby inventory signal alone never makes it one, and contradictory tags take the less
  favorable reading.
- **Parameters** (radii, thresholds, penalties) are named module constants with a comment
  explaining the choice. Many were calibrated on DC; say so when a Maryland result depends
  on one. Penalty changes bump `PENALTY_VERSION`.
- **Verify against real data.** After pipeline changes, inspect distributions and a few
  concrete examples (coordinates) before trusting results.
- Match the existing style: type hints, docstrings that explain *why*, no silent fallbacks.
- Privacy: drop contributor identifiers from crowdsourced data on ingest. The server stores
  nothing about plan or search requests. Tester feedback holds only the answers, the comment
  and the day. A walk recording stays in the walker's browser until they save it.

## Data facts worth knowing

- OSM: Geofabrik's Maryland extract (~216 MB) is cut per town by `fetch.clip_pbf`, keeping
  every way with a node in the box complete. Its Last-Modified date is every clip's `as_of`.
  The only relations kept are `landuse=military` areas (`fetch.CLIP_RELATION_TAGS`).
- **Closed areas are not walkable.** Fort Detrick, a closed Army post inside Frederick, is mapped
  only as a relation, and its streets carry `access=yes`. Until 2026-10-19 its 60 km of streets
  and paths were routed and sampled as public. `pf extract-osm` writes `osm_restricted_areas.parquet`
  (`osm.RESTRICTED_AREA_TAGS`), and `build.clip_restricted` cuts every edge at the boundary and
  keeps only its parts outside (a gate road stops at the fence). The cut ends are never bridged,
  no connector may enter, and a trip end inside an area is told so (`TripPlanner.closed_area_at`).
  `test_no_walkway_enters_an_area_closed_to_the_public` checks the built graph.
- OSM `crossing=marked` says a crossing is painted, not whether it is signalized; signals
  are in `crossing=traffic_signals`, `crossing:signals`, and the same tags on the node.
- Without a roadway inventory, lanes and speed come from OSM `lanes` / `maxspeed` tags
  (`roles.osm_streets`), graded as OSM evidence; a bare `maxspeed` number is km/h by OSM
  convention.
- Montgomery Planning sidewalks: only code 1206 is a street sidewalk; 1208 holds private and
  building walks and is walkable surface only. Captures are dated by year (mostly 2014/2017
  around Gaithersburg). No stairs or crosswalk class, so nothing is read from absence. Survey
  presence is never graded on service roads or alleys (`enrich.NO_PLANIMETRIC_PRESENCE_KINDS`).
- City of Frederick sidewalks: lines with no date of their own; each is dated by its first
  survey photo (`arcgis_first_date` source `frederick_sidewalk_photos`, Mar-May 2025) and
  never-photographed segments are dropped. Width 0 means not recorded. `SCI` is the city's
  own condition index (0-100, higher is better; no published category cutoffs), carried as
  graded `sidewalk_condition`; exactly 85.999 is a fill value on 1,208 segments and is not a
  score (`roles.FREDERICK_SCI_FILL`). Recorded width is `sidewalk_width_m`. Not complete:
  it holds 88.9% of OSM's public-street sidewalk length (bar 95%, 2026-10-16) and misses
  newer developments and some public streets, so its silence is never "no sidewalk".
- Montgomery signals (`montgomery_signals`, Gaithersburg's `signals` role): locations only,
  dated by the layer's last data edit (2023-11-09, `Source.as_of`). LPI / no-turn-on-red are
  empty and there is no APS field, so `signal_*` stay unknown; an empty inventory field is
  never read as "no". Signal coverage stays None: it misses real signals.
- Frederick County signals (`frederick_county_signals`, Frederick's `signals` role): mostly
  the City of Frederick's own signals, few state-road ones; no edit date, so a record counts
  only where an OSM signal node lies within `roles.SIGNAL_OSM_CONFIRM_M` and is dated by the
  OSM extract (`Source.as_of = AS_OF_OSM`). Coverage None.
- A junction that is not a street intersection (a driveway meeting a street) takes an
  inventory signal only within `enrich.DRIVEWAY_SIGNAL_RADIUS_M` (15 m); street intersections
  keep 30 m. At 30 m, parking-lot entrances down the street were wrongly signalized.
- MDOT SHA's ADA inventory (curb cuts, pedestrian signals) is not public: the open
  `Sidewalk_Public` service has no crossings or curb cuts in either pilot (2026-10-16).
- Divided roads: probes toward a parallel one-way twin stop halfway (`enrich.divided_road_reach`).
- ArcGIS sources with editor fields list them in `Source.drop_fields`; they are never stored.
- Elevation: each pilot's `dtm` is the county's MD iMAP `MD_<county>_dem_m` service (metres)
  exported for the town's box on the 1 m EPSG:26985 grid (`fetch.fetch_image_service` with a
  `bbox`); the services fill outside their county with exactly 0, read as no data. Montgomery
  flown late 2020 to early 2021 (dated "2020"); Frederick is USGS MD Western 2021 (flown
  2021-12-14 to 21). The terrain predates newer subdivisions.
- City of Frederick curb ramps (`frederick_ramps`, the `ramps` role): "No ramp" records are
  surveyed corners without one (`no_ramp`); the verdict `ADA_Description` becomes
  `ramp_check_a/b` (passed / fails / no_tactile_pad). A failing ramp stays usable for routing
  (`PENALTIES["crossing"]["ramp_fails"]`) and is listed on the barrier map. Gaithersburg has
  no ramp inventory yet, so step-free routes there cannot be confirmed.
- **Field checks** (`<region>_field_checks`, the `field_checks` role; Frederick from 2026-10-20):
  the team's own visits, filled in `field/<region>.csv` and read by `pf fetch` (kind `local_csv`,
  read again whenever the sheet's checksum changes). A corner answer is `verified`, dated by the
  visit, and wins over every other source within `enrich.FIELD_CHECK_RADIUS_M` (3 m: the sheet's
  coordinates are the graph's own); a junction answer replaces the ramp count and stays
  `inferred`. A typo or an undated answer is an error (`roles.field_checks`). Not under rule 7.
  The sheet is never rewritten by code: answered rows are evidence.
- Census tracts (2020, TIGERweb, public domain) are each pilot's `report_districts`, keyed by
  `GEOID`: coverage and barriers break down by tract.
- Imagery for inspection: MD iMAP `SixInch/SixInchImagery2023_2024_2025` (export in
  EPSG:26985); the combined `SixInchImagery` service often returns blank tiles.
- The data sources researched for Maryland (endpoints, vintages, gaps) are in
  `docs/PLAN.md` § Data. Statewide open crash data is login-only since 2026; Montgomery
  County's crash and crime feeds are public domain.

## Progress log

`docs/PROGRESS.md` is the project's running record. In the same change as any meaningful
work, add a dated Timeline entry, update Current status / Key metrics, Decisions log, Open
issues and Next steps. Numbers only from generated reports; never delete history.

## Git

- Its own repository (not DistrictDirect's). Commit only when asked; no remote yet.
- Don't commit data, venvs, or secrets (`.env`).
