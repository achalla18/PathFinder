# PathFinder

A city accessibility app for **Maryland's 6th congressional district**: Gaithersburg,
Germantown, Frederick, Hagerstown, Cumberland, Frostburg and the towns between.

**For people getting around with a wheelchair, walker, cane or stroller** it plans
step-free routes from a mobility profile. It shows **where** sensible routes differ, usually
one to three decisive places: a missing curb ramp, a steep block, a street with no sidewalk.
It shows **what is known vs. unknown** about each of them, with source and date, and **how
far your priorities would have to move** before a different route wins, across crossings &
curbs, slope and sidewalk. Hard requirements (step-free, maximum slope) are never traded off.

**For cities and advocates** it maps the barriers that are on record, and the places nobody
has recorded, by census tract: the survey worklist.

It never certifies a route or place as accessible. It says what was recorded, by whom and
when.

PathFinder grew out of DistrictDirect, the same idea built and tested for Washington, DC;
it is a separate app with its own data, repo and command.

- Plan: [`docs/PLAN.md`](docs/PLAN.md)
- Progress log: [`docs/PROGRESS.md`](docs/PROGRESS.md)
- Agent/contributor guide: [`AGENTS.md`](AGENTS.md)

## Status

**Phase C — Maryland sources, accessibility first** in the Gaithersburg and City of
Frederick pilots.

- **Loaded:** OpenStreetMap, plus each city's sidewalk survey.
- **Next:** elevation, then curb ramps. Until curbs are recorded, no step-free route can be
  confirmed, and the app says so.
- **How each source is added:** one at a time, after its records are checked against aerial
  imagery.

## Quick start

```bash
python -m uv venv ~/.venvs/pathfinder --python 3.13
python -m uv pip install --python ~/.venvs/pathfinder/Scripts/python.exe -e ".[dev]"

export PF_REGION=gaithersburg    # or frederick; data goes to ~/.pathfinder/data/regions/<region>
pf fetch                         # city limits + an OSM cut of the statewide Maryland extract
pf extract-osm
pf build-graph
pf enrich
pf coverage                      # -> reports/gaithersburg/phase0/coverage.md
pf barriers                      # -> reports/gaithersburg/barriers/barriers.md
pf route 39.1434,-77.2014 39.1210,-77.2370 --profile manual_wheelchair
python -m pytest -q
```

Data © OpenStreetMap contributors (ODbL); boundaries from MD iMAP.
