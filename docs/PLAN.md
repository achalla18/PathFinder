# PathFinder — plan for Maryland's 6th district (MD-6)

## Product (refocused 2026-10-15)

PathFinder is a **city accessibility app**. The owner's direction (2026-10-15):

- **For both, routes first.** It leads with step-free route planning for people with
  mobility disabilities: wheelchair, walker, cane and stroller users. The same
  evidence-graded data feeds a **city barrier map** for the cities and for advocates. The map
  shows recorded barriers (raised curbs, missing ramps, steep grades, steps, streets with no
  sidewalk) and, just as visibly, the places nobody has recorded.
- **Crossings fold into accessibility.** A crossing is judged as an accessibility question:
  curb ramps at both ends, signal control, crossing distance, and accessible signals once
  data exists. After-dark lighting and the crime layer are removed from the product.
- **Three dimensions** make up the priority mix: crossings & curbs, slope, sidewalk
  (`routing/cost.py`, penalty version v5). **Mobility profiles**
  (`routing/profiles.py`) set the starting requirements and mix, and an explicit choice
  always overrides them.
- **A new go/no-go bar** applies to the accessibility product, fixed before any
  accessibility source is loaded (`docs/PROGRESS.md`, Decisions log). Phase B's result
  against the old bar stays recorded.

Everything below Phase B was written for the walking navigator. Phase C, D and E are
reordered for accessibility. The DC methods still carry over.

## Context

DistrictDirect (repo `C:\dev\DistrictDirect`) is a working, evidence-graded walking navigator for DC. The goal is to find out, cheaply and honestly, whether it can deliver the same value in MD-6, and then to port it there without breaking DC.

The earlier write-up got some things wrong, and online research (2026-10-15) changed the picture. This plan is built on what was actually checked: REST endpoints queried, record counts taken, dates read.

Guiding rule, unchanged: **accuracy over coverage**. A region ships only where evidence is good enough that most decisive places aren't "unknown".

---

## Data

### What the research changed

Each item is verified unless marked otherwise.

| Topic | Earlier assumption | What's true now |
|---|---|---|
| District lines | Unclear | The 2022 map stands. A November 2026 ballot amendment could allow a redraw, but not before **2028**. Rockville is in MD-8; MD-6 ends just south of Gaithersburg. Official boundary: iMAP `Boundaries/MD_ElectionBoundaries/FeatureServer/0` or TIGER `tl_2024_24_cd119.zip`. |
| Lanes and speed (the biggest gap) | "Not found" | **FHWA HPMS 2024 for Maryland** (`geo.dot.gov/.../HPMS_FULL_MD_2024/FeatureServer/0`) gives through_lanes on 93% of Montgomery segments, but speed on only 20%. **MDOT SHA statewide Bicycle LTS** gives speed, lanes and AADT on every segment; 73% of its speeds are *derived*, so they come in as "inferred". Montgomery Planning's LTS layer and the City of Frederick's Roads layer have posted speed limits. |
| Traffic volume (AADT) | 2019 only | MDOT SHA hosted AADT layer covers **2015–2024** plus a current-year column (edited 2026-08). |
| Montgomery sidewalks | 2015 survey | Montgomery Planning `Sidewalks___Driveways/FeatureServer/3` has polygons **captured in 2023**, with a capture-year code. It's the drop-in for DC's 2021 planimetrics. Gaithersburg has its own `Sidewalks_Public` layer (edited 2026-05). |
| Frederick ADA data | Frederick County Sidewalks service | That service is **dead**. Its replacement, `DPW/Walkability`, has only 35 ramps. The real prize is **City of Frederick `Sidewalks/FeatureServer`**: **6,366 ramps surveyed Mar–Jun 2025** (slope, landing, tactile pad), a sidewalk condition index, and a Roads layer with SPEEDLIMIT. There is no open license, so we need written permission. |
| State-road accessibility | Not known | **MDOT SHA `Sidewalk_Public` MapServer**: crossings (markings, ped-signal type, accessible-signal attributes), curb cuts (slope, warning surface), sidewalks (width, slopes). Covers state roads in all five counties. |
| Streetlights | County layer only, missing PEPCO lights | Use three layers together: the county layer (38.5k lights, no Pepco), **Gaithersburg StreetLights** (4,695, including Pepco) and **SHA Highway Lighting** (39k). Absence still counts as evidence only inside Gaithersburg city limits plus state roads. |
| Crashes | MSP 2018 statewide | The statewide open crash data is now **login-only**. dataMontgomery `n7fk-dce5` is public domain, updated weekly, runs 2015–2026, and includes state roads. Its wording changed in 2024 (the ACRS 2.0 form) and needs normalising. Frederick has no public crash points; ask the county. |
| Crime | Precision unknown | dataMontgomery `icn6-v9z3` locates each report to its **100-block**. That is compatible with our block-level method. Nothing is public outside Montgomery. |
| Elevation | One statewide layer | Per-county iMAP lidar ImageServers. Montgomery: 2020 survey in **EPSG:2893, US feet** (must be converted). Frederick: 2012 (vintage unclear). Allegany: 2021. The existing `fetch_image_service` works with them. |
| Project Sidewalk | Unconfirmed | **No Maryland deployment.** |
| OSM sidewalks | Unknown | Live Overpass counts: Gaithersburg box has 2,546 sidewalk ways and 1,502 crossings (good). Germantown has 802 (thin). A 2026 CDC study found Maryland OSM sidewalks thinner in low-density and minority tracts, the same equity issue as Wards 7 and 8. |
| Competitors | — | Google's step-free walking routes are opaque, with no curb or slope detail. AccessMap/OpenSidewalks has Montgomery data only. **Nothing evidence-graded covers Frederick or the western counties.** |

**Pilot choice, from the above:** **Gaithersburg** (Olde Towne, Kentlands, Rio/Crown) and **downtown City of Frederick**. They have the best data in the district and different layouts (suburban arterial vs historic grid). Germantown comes later because its OSM is thin. Hagerstown, Cumberland and Frostburg only after data partnerships, since they publish almost nothing.

---

## Phase A: Make the region a setting — done 2026-10-15

Done in DistrictDirect's code before the fork, checked there (the DC graph rebuilt identical
apart from two renames; 200 tests passed), then moved into PathFinder as a separate app with
DC removed. The steps below are kept as the record of what the region layer covers.

Today there's no region concept and no config file. About 84 DC references sit in about 11 files. Refactor first, prove DC is unaffected, and only then add Maryland.

1. **`src/districtdirect/config.py`**: add `DD_REGION` (default `dc`). Data and reports go under `DATA_DIR/<region>/` and `reports/<region>/`.
   - Keep the DC paths working through a migration shim or a one-time move. Don't touch the ~0.5 GB-free machine's existing DC data without a check.
2. **New `src/districtdirect/regions/`** package with `base.py`, a frozen `Region` dataclass. Fields:
   - id, name, boundary source id, buffer_m, OSM source id, bbox (derived from the boundary)
   - analysis CRS (EPSG:26985 for every MD region)
   - time zone, map centre
   - reporting-district source and field (DC: wards; MD: census tracts or town)
   - street-name style (quadrant or plain)
   - transit-notice provider (wmata or none)
   - **field adapters**: per-source rename maps into one canonical schema
   - **inventory-coverage polygons** per attribute family (see Phase C)

   Then `regions/dc.py`, holding today's constants moved out of `sources.py`. `SOURCES` becomes `region.sources`.
3. **Rename `outside_dc` → `outside_region` and `dc_inventory_covered` → `inventory_covered`.** This touches:
   - `graph/build.py:438-472`
   - `graph/enrich.py:591-616, 718-758`
   - `routing/cost.py`
   - `analysis/coverage.py:131-151`
   - `tests/conftest.py:48`
   - `tests/test_data_invariants.py`
4. **Make optional sources optional in `graph/enrich.py:797-831`.** Each enrich step checks whether its source exists for the region. If it doesn't, the attribute stays `init_unknown()` (`evidence.py:65`); it is never defaulted to a favourable value. This is rule 1.
5. **Surface-gap bridging** (`graph/build.py:239-273, 466-470`): run it only when the region provides a planimetric surface layer, using an adapter onto the "Sidewalk / Crosswalk / Stairs" classes. Montgomery Planning's FEATURE_CODE 1206/1208 maps to this. Otherwise do the 3 m pass only and report near-misses.
6. **Small DC-specific items:**
   - `routing/guidance.py:43-74, 191`: quadrant optional, style comes from the region.
   - `routing/service.py:41-47, 259`: build the crime caveat text from region metadata.
   - `fetch.py:162, 260-272`: bbox from the region, WMATA gated by region.
   - `graph/elevation.py:60, 90-94`: elevation-model date and nodata handling become per-source config.
   - `basemap.py`: tile extract bbox from the region.
   - `analysis/coverage.py:89-128, 173, 224`: wards become the generic reporting district.
   - `analysis/crux.py:39, 228`: per-region trip-sample path. Add an exit when a distance band can't be filled, because small towns may never reach 1.5–2.5 km pairs.
   - `web/`: add a `GET /api/region` endpoint in `api.py` (map centre, name, source labels), used by `MapView.tsx:45` and `Conditions.tsx:9-14`.
7. **Golden check:** before the refactor, snapshot DC `edges.parquet` hashes, `coverage.json`, crux results and a fixed set of 20 `dd route` outputs. After it, `dd build-graph && dd enrich && dd coverage` for DC must match exactly, apart from the renamed columns. All 181 tests must still pass.

## Phase B: OSM-only pilot (go/no-go, about a day) — done 2026-10-15

Both pilots missed criterion 1 (sidewalk-level share: Gaithersburg 41.8%, Frederick 36.4%)
and passed the other two. The bar stands as written. The accessibility product has its own
bar (Product, above).

1. **`regions/gaithersburg.py` and `regions/frederick.py`:**
   - Boundary: Gaithersburg city limits (from the city portal) and a downtown Frederick polygon (city limits clipped to the downtown core, or a buffer around the Golden Mile and downtown; decide on a first look).
   - Sources: only `osm_md` and the boundary.
2. **OSM extract without running out of memory:** fetch Geofabrik `maryland-latest.osm.pbf` once. Clip it with `osmium extract -b <bbox>` (streaming, low RAM), or with a pyosmium bbox filter if osmium-tool isn't installed. Keep only the clip. Add a new source kind `pbf_clip` in `fetch.py`.
3. Run `DD_REGION=gaithersburg dd extract-osm && dd build-graph && dd enrich && dd coverage`, then the same for frederick.
4. **Go/no-go bar.** Record it in `docs/PROGRESS.md` before running, so it isn't moved afterwards:
   - share of walking length on real sidewalks of at least 50% (DC is 67.6%)
   - share of crossings with a known control type of at least 60% from OSM alone
   - a main connected component holding at least 90% of the length

   If a town misses the bar, record why and move to the next candidate. Don't lower the bar.

## Phase C: Register Maryland sources, accessibility first (each one inspected before trusted)

Order is what unblocks a step-free route, then the barrier map. Today no step-free route
exists in either pilot at "recorded or likely" (2026-10-15), because curb ends are
unrecorded almost everywhere and the router does not treat an unrecorded curb as passable.
Every source is sampled against aerial imagery (MD iMAP six-inch 2023–25) before a region
names it, as was done in DC.

| # | Need | Source | Status it earns | Where absence counts |
|---|---|---|---|---|
| ✓ | Sidewalk existence | Montgomery Planning planimetrics (code 1206 only); City of Frederick Sidewalks 2025 (photo-dated) | verified | Nowhere yet: no stairs class, so "both sides" only |
| ✓ | Elevation / slope | iMAP `{Montgomery,Frederick}/MD_*_dem_m/ImageServer`, exported for each town's box on the 1 m analysis grid | verified (3-line agreement rule, unchanged) | n/a. Done 2026-10-16 |
| ✓ (Frederick) | Curb ramps | City of Frederick ramps (6,366, 2025); MDOT SHA curb cuts (state roads) still to do | verified, dated per ramp; the city's verdict as graded `ramp_check_a/b` | not used for absence. Done for Frederick 2026-10-16 |
| 2 | Gaithersburg curb ramps | none open: ask the City of Gaithersburg or Montgomery County DOT. Montgomery DOT's public "ADA Curb Ramp Requests" layer holds residents' requests, not an inventory | verified | n/a |
| 3 | State-road curb cuts, crossings and accessible signals | **Not open (checked 2026-10-16).** The public `Sidewalk_Public` service has 8 curb cuts statewide (Charles County) and no crossings in either town; SHA's ADA inventory ("Handicap Ramps", "Pedestrian Signals", `ADA_Maryland_SHA` on the internal `shagbegis1`; `OHD_ADA` needs a token) is internal. Ask MDOT SHA's Office of Highway Development | verified | state roads only |
| ✓ (Frederick) | Sidewalk condition and width | City of Frederick Sidewalks: the survey's own condition index (SCI, 0–100) and recorded width, matched to the sidewalk an edge walks on | verified on sidewalk-level edges; inferred (worse side) on streets with a sidewalk on record | n/a. Done 2026-10-16 |
| ✓ (Gaithersburg) | Signal locations | Montgomery `Traffic_Signals_Bill_1123` (locations only: its LPI and no-turn-on-red fields are empty and it has no APS field; data last edited 2023-11-09) | inferred `signal` at implicit junctions; never makes a mapped crossing a signal | Nowhere: it misses real signals (5+ of 84 OSM signal intersections). Done 2026-10-16 |
| ✓ (Frederick) | Signal locations | Frederick County `DPW/Traffic_Signals` (mostly city signals; no edit date: used only where OSM confirms, dated by the OSM extract) | inferred `signal` at implicit junctions | Nowhere: 45 of OSM's 116 signal intersections missing. Done 2026-10-16 |
| 5 | Signals with pedestrian features (APS, LPI) | none open in either town. Frederick County's Cartegraph `DPW/Signals` lists 43 pedestrian buttons in the Frederick box, county-maintained, 1 marked audible: too few to use. Ask MCDOT and the City of Frederick | verified | where shown complete |
| 6 | Lanes, speed, AADT (crossing difficulty) | MDOT SHA statewide Bicycle LTS + SHA AADT 2024 + HPMS 2024 lanes | verified when not `*_DERIVED`, otherwise inferred | n/a |

Dropped with the refocus: streetlights, pedestrian crashes, the High Injury Network,
reported crime.

Also needed:
- **Retire for MD:** WMATA elevators (except a notice when a Gaithersburg trip ends at Shady Grove), Project Sidewalk, the Secret Service redaction layer (`usss_redaction`).
- **Licensing:** dataMontgomery is public domain. City of Frederick, Montgomery Planning, Gaithersburg and the MDOT proxy URLs have **no stated license**. Use them internally for the pilot only. Get written permission before anyone outside sees results.
- The MDOT SHA ADA proxy (`utility.arcgis.com/...PedestrianFacilities...`) can change without notice. Cache the fetched copy with its checksum and don't build against the live URL.

## Phase D: Re-run the experiments per region

For each pilot region, with a fixed seed and the per-region trip sample:
1. `dd crux --resample` (distance bands may shrink to 400–800 m and 800–1500 m), then `dd crux-report`. Does "routes differ in one to three places" hold? DC was 93.7%.
2. Share of trips where an alternative is worth showing (DC 80.5%), and the step-free feasibility rate in verified-only and allow-likely modes (DC 31.5% / 65.3%).
3. Coverage and barriers by census tract (`pf coverage`, `pf barriers`: 2020 tracts are
   registered for both pilots), to measure the equity gap the CDC study predicts.
4. The accessibility bar (Product, above; numbers in `docs/PROGRESS.md`).

Write the numbers into `reports/<region>/` and `docs/PROGRESS.md`. Every claim comes from generated output only.

**Decision gate:** expand to Germantown or the western counties only if both pilots clear the accessibility bar *and* at least 60% of trips have an alternative worth showing.

## Phase E: Partners and data access (alongside B–D, no code)

Ranked for the accessibility app (programs, not personal contacts):
1. **The Freedom Center (Frederick's centre for independent living).**
   - Recruit 5–10 testers who use wheelchairs, walkers, canes or strollers for the first
     outdoor walks.
   - Revise the profile numbers with them.
   - These would also be the first walks anywhere, DC included.
2. **City of Frederick: the owner of the 2025 ramp survey and its ADA work** (the Vision
   Zero coordinator and the Active Mobility Advisory Committee).
   - Ask for data-use permission.
   - The barrier map is a direct use for their survey.
3. **Frederick County Planning / Transportation Engineering.**
   - $1.05M SS4A demonstration grant with municipal technical-assistance funds.
   - Ask for the full Cartegraph ramp export (2,677 ramps).
4. **City of Gaithersburg.**
   - First SS4A action plan ($360K, FY24), working through Montgomery County Vision Zero.
   - Ask about its sidewalk and ramp records.
5. **Hagerstown / Hagerstown–Eastern Panhandle MPO** (May 2025 action plan) and **Garrett County "Pathways to Safety"**. Their data has to come through a partnership before those towns can be considered.

Prepare a one-page private brief with the DC results and the pilot coverage numbers before any outreach. Rule 6 still applies: nothing becomes public until you decide.

## Risks and mitigations

- **No step-free route until curbs are recorded:** the router rightly refuses unrecorded curbs at "recorded or likely". Curb ramps (Phase C #2) are the critical path; until then the app offers the smallest compromise ("accept places with no evidence") and says so.
- **A profile is a judgment, not a measurement:** its numbers are starting points until testers revise them; an explicit choice always overrides it.
- **Thin suburban OSM** (Germantown): use the 2023 Montgomery planimetrics to infer sidewalk edges, labelled "inferred". Don't treat the town as covered until it is.
- **Unlicensed municipal data:** pilot-internal only until permission. Keep a `license_status` field in provenance, and refuse to serve a source whose license status is "unknown" when running hosted.
- **Speeds that are 73% derived:** they arrive as inferred and are priced as such. They never count as verified.
- **Memory:** clip the PBF per town and run one region at a time. Every step can be restarted, as in DC.
- **Boundary change in 2028:** regions are per-town, not per-district, so a redraw changes nothing in the code.
- **Breaking DC:** golden check (Phase A.7), plus DC as the default region in the test suite.

## Verification

- `python -m pytest -q` passes, with new tests for:
  - the region config loader
  - field adapters, against a 5-row synthetic fixture per source
  - "missing source → attribute unknown"
  - "absence outside the coverage polygon → not verified"
- DC golden check is byte-identical (Phase A.7).
- For each MD region: `dd coverage` report produced, a hand-check of 10 decisive places against aerial imagery and Street View, and 5 explained trips (`dd route`) read end to end for wrong claims, such as calling a Pepco-lit block "unlit" or quoting a derived speed as verified.
- `dd serve` with `DD_REGION=gaithersburg`: the map centres correctly, place search returns Gaithersburg places, source labels say Maryland.
- Every change gets a `docs/PROGRESS.md` entry with numbers from generated reports.

## Critical files

`src/districtdirect/config.py`, `sources.py`, `fetch.py`, `osm.py`, `places.py`, `graph/build.py`, `graph/enrich.py`, `graph/elevation.py`, `routing/guidance.py`, `routing/service.py`, `analysis/coverage.py`, `analysis/crux.py`, `api.py`, `web/src/MapView.tsx`, `web/src/Conditions.tsx`, tests (`conftest.py`, `test_data_invariants.py`, `test_guidance.py`), plus the new `src/districtdirect/regions/`.


## Appendix: endpoints (verified 2026-10-15)

| Need | Endpoint |
|---|---|
| District boundary | `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_ElectionBoundaries/FeatureServer/0`; TIGER `https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_24_cd119.zip` |
| City limits | `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_PoliticalBoundaries/FeatureServer/5` (`MUN_NAME`) |
| OSM | `https://download.geofabrik.de/north-america/us/maryland-latest.osm.pbf` |
| Lanes / speed / AADT (statewide LTS) | `https://services.arcgis.com/njFNhDsUCentVYJW/arcgis/rest/services/Maryland_Bicycle_Level_of_Traffic_Stress_(LTS)_view/FeatureServer/0` |
| AADT 2015–2024 | `https://services.arcgis.com/njFNhDsUCentVYJW/ArcGIS/rest/services/MDOT_SHA_Annual_Average_Daily_Traffic/FeatureServer/1` |
| HPMS 2024 | `https://geo.dot.gov/server/rest/services/Hosted/HPMS_FULL_MD_2024/FeatureServer/0` |
| SHA crossings (state roads) | `https://services.arcgis.com/njFNhDsUCentVYJW/ArcGIS/rest/services/MDOT_SHA_Bicycle_Pedestrian_Crossings_External/FeatureServer/0` |
| SHA sidewalks, curb cuts, crossings | `https://gisportalapps.sha.maryland.gov/arcgis/rest/services/OMOC/Sidewalk_Public_Maryland_MDOTSHA/MapServer` |
| SHA highway lighting | `MDOT_SHA_Highway_Lighting_(View)` layer 1 (same ArcGIS org) |
| Montgomery sidewalks (2023) | `https://montgomeryplans.org/server/rest/services/Overlays/Sidewalks___Driveways/FeatureServer/3` |
| Montgomery signals | `https://services.arcgis.com/hdlG36cOubTzNDBb/ArcGIS/rest/services/Traffic_Signals_Bill_1123/FeatureServer/0` |
| Montgomery streetlights (no Pepco) | `https://gis4.montgomerycountymd.gov/arcgis/rest/services/DOT/streetlights/FeatureServer/0` |
| Montgomery High Injury Network | `https://services.arcgis.com/hdlG36cOubTzNDBb/ArcGIS/rest/services/High_Injury_Network/FeatureServer/0` |
| Montgomery non-motorist crashes | `https://data.montgomerycountymd.gov/resource/n7fk-dce5.json` |
| Montgomery crime (100-block) | `https://data.montgomerycountymd.gov/resource/icn6-v9z3.json` |
| Gaithersburg sidewalks / lights | `https://maps.gaithersburgmd.gov/arcgis/rest/services/layers/` (`Sidewalks_Public`, `StreetLights`) |
| City of Frederick ramps, sidewalks, roads | `https://spires.cityoffrederick.com/ArcGIS/rest/services/Sidewalks/FeatureServer` |
| City of Frederick lights | `https://spires.cityoffrederick.com/ArcGIS/rest/services/Electrical/MapServer/0` |
| Frederick County walkability, signals, lighting | `https://fcgis.frederickcountymd.gov/server_pub/rest/services/DPW/` (`Walkability`, `Traffic_Signals`, `Street_Lighting`, `Transportation`) |
| Elevation (per county) | `https://mdgeodata.md.gov/lidar/rest/services/{County}/MD_{county}_dem_m/ImageServer` |
| Washington County hub | `https://gisoffice-washcomd.opendata.arcgis.com/` |
| Garrett County | `https://gis.garrettcounty.org/server/rest/services` |
