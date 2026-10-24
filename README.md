# PathFinder

**Plan a trip around your mobility needs—and see the evidence behind each route.**

PathFinder is a web app for people using wheelchairs, scooters, walkers, canes, or strollers. A missing curb ramp or a steep block can change an entire journey. PathFinder compares routes using **crossings and curbs, slope, and sidewalks**, and explains the places that make the difference.

Built for the Congressional App Challenge (Maryland's 6th district), with pilots in **Gaithersburg and Frederick** and a comparison region in **Washington, DC**. Other towns in the district are planned, not implemented pilots.

## What it does

- **Mobility profiles:** start with a profile, then adjust priorities and requirements.
- **Route comparisons:** the Crux Map highlights where routes diverge; the Tradeoff Triangle shows how changing priorities affects the choice.
- **Evidence you can inspect:** recorded, inferred, and unknown conditions remain distinct, with source and date. Missing data never counts as a favorable condition.
- **Hard requirements:** step-free and maximum-slope requirements filter routes before preferences are compared.
- **Barrier map:** browse recorded barriers and gaps in the available information.
- **Phone interface:** on-screen guidance, English and Spanish text, location controls, and a recoverable map-loading state.

This is a research prototype. It describes recorded conditions; it does not certify a route as accessible, safe, or ADA compliant. Coverage varies by region, and an acceptable route may not exist at the selected evidence level. Terrain and inventory dates may precede recent construction.

## Run locally

You need **Python 3.12+**, **Node.js 22.12+**, npm, an internet connection, and several GB of disk space for downloaded and processed geospatial data. Data preparation can take substantial time; it is separate from installing the app.

### 1. Install

```bash
git clone https://github.com/achalla18/PathFinder.git
cd PathFinder
python -m venv .venv
```

Activate the environment:

| Shell | Command |
| --- | --- |
| macOS / Linux | `source .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |

```bash
python -m pip install -e ".[dev]"
```

Copy `.env.example` to `.env` in the repository root. It selects `gaithersburg_public`, a region that excludes the municipal sources marked internal. Use `frederick_public` for the other Maryland pilot or `dc` for the DC comparison. Environment variables already set in your shell override `.env`.

### 2. Prepare one region

```bash
pf sources
pf fetch
pf extract-osm
pf build-graph
pf enrich
```

Run these in order from the repository root. Maryland downloads share one statewide OpenStreetMap extract; the graph and other artifacts are stored separately for each region under `~/.pathfinder/data/regions/<region>/`. No prepared graph is bundled. `pf fetch` skips existing downloads; use `--force` only when you intend to refresh them.

### 3. Build and open the app

```bash
cd web
npm ci
npm run build
cd ..
pf serve
```

Open **http://127.0.0.1:8000**. For frontend development, run `npm run dev` from `web/` in a second terminal while `pf serve` runs, and open **http://localhost:5173**.

To generate the region's evidence reports:

```bash
pf coverage
pf barriers
```

## Review the project

| Guide | Contents |
| --- | --- |
| [Demo walkthrough](docs/DEMO.md) | A short tour and the optional three-place demo |
| [Architecture](docs/ARCHITECTURE.md) | Data pipeline, routing, API, and interface |
| [Data and attribution](docs/DATA.md) | Public regions, source restrictions, and research limits |
| [Contributing](CONTRIBUTING.md) | Checks and development conventions |

The Tile2Net work in `tools/tile2net_pilot/` is an experimental research track. Its outputs did not meet the evaluation bar and are **not used by the router**.

## Checks

```bash
python -m pytest -q
cd web
npm ci
npm run build
```

Most tests use synthetic networks and need no downloads. Tests marked `data` require a prepared graph and skip when it is absent; passing the synthetic tests does not validate a real region's data. GitHub Actions runs the Python suite and TypeScript/production build checks.

## Sharing

Use GitHub's **Code → Download ZIP** for a source handoff. The archive includes the app, tests, public-region reports, and these guides; `.gitattributes` excludes internal pilot reports and development working notes. A Git clone or access to the repository still includes those materials and their history. Keep repository access private when handing out the archive.

The source code currently has no open-source license; sharing a copy does not grant a general reuse license. External data and dependencies retain their own terms. See [data and attribution](docs/DATA.md).
