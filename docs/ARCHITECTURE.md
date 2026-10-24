# Architecture

PathFinder uses one evidence-graded graph for both route planning and barrier analysis.

## Data pipeline

1. **Configure:** `regions/` defines boundaries, sources, source roles, and inventory coverage. `PF_REGION` selects a region when the process starts.
2. **Fetch:** `fetch.py` downloads inputs and records provenance, including checksums and dates. Maryland's OSM extract is shared and clipped per town.
3. **Extract:** `osm.py` converts pedestrian ways, tagged nodes, and restricted areas into interim tables; `places.py` builds local search.
4. **Build:** `graph/build.py` constructs topology, removes restricted areas, and handles limited mapping gaps.
5. **Enrich:** `graph/roles.py` adapts source schemas; `graph/enrich.py` attaches values with evidence status, source, and date. Terrain processing lives in `graph/elevation.py`.
6. **Analyze:** `analysis/coverage.py` and `analysis/barriers.py` produce reports; `analysis/crux.py` evaluates route differences.

Raw and derived data stay outside the checkout. Reports are written to `reports/<region>/`.

## Routing

`routing/profiles.py` supplies overridable starting settings. `routing/cost.py` applies hard requirements and computes preference costs. `routing/router.py` searches for route alternatives across the preference space. `routing/divergence.py` and `routing/explain.py` identify meaningful differences and explain the choices. `routing/service.py` exposes this as a trip plan; `routing/guidance.py` produces on-screen steps.

An attribute can be verified, inferred, or unknown. Unknown conditions carry a penalty and can fail requirements, depending on the chosen certainty setting. An inferred connector or curb does not satisfy verified-only requirements. The application does not infer favorable conditions from an inventory's silence outside its stated coverage.

## API and interface

`api.py` serves the FastAPI endpoints and the production build in `web/dist/`. The primary endpoints are `/api/region`, `/api/health`, `/api/search`, `/api/plan`, `/api/barriers`, `/api/feedback`, and `/api/report`.

`web/` uses React, TypeScript, Vite, and MapLibre GL. `App.tsx` manages planning and settings; `MapView.tsx` draws map layers; the other components handle search, conditions, guidance, feedback, and the preference triangle. Vite proxies API requests to port 8000 during development.

The map loads after the initial screen. Its worker count and pixel ratio are limited for phones. The service worker caches the app shell and region/health metadata, not trips, searches, barrier requests, or user positions. Offline shell availability does not provide offline routing.

## Research tools

`tools/` contains field-check, mapping, and evaluation utilities. The Tile2Net experiments are separate from production routing. Internal evaluation data and external research dependencies are not bundled with the source handoff.
