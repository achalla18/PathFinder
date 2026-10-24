# Contributing to PathFinder

Follow the installation steps in [README.md](README.md), then work on a branch. Start with a public region (`gaithersburg_public`, `frederick_public`, or `dc`) unless you are authorized to use the internal pilot sources.

## Checks before a change

```bash
python -m pytest -q
cd web
npm ci
npm run build
```

After changing graph construction, rebuild from `pf build-graph` onward. After changing enrichment, rebuild from `pf enrich` onward. Cost-model changes also require refreshed routing experiments (`pf crux --fresh`). Run the data-invariant tests with the rebuilt region selected and inspect concrete routes and source distributions. Keep generated reports reproducible; do not hand-edit their values.

## Product and data conventions

- Missing information stays unknown. Inference never becomes verification.
- Requirements filter routes; preferences cannot override them.
- Describe recorded conditions with sources and dates. Do not label routes safe, accessible, or ADA compliant.
- Compute distances in EPSG:26985; exchange coordinates in EPSG:4326.
- Register sources and their terms in `src/pathfinder/regions/`; fetch them through the provenance pipeline.
- Keep raw data, graph artifacts, credentials, and personal identifiers out of Git.
- Preserve the map's deferred startup, scoped redraws, and failure recovery on phones.

Explain the problem, resulting behavior, and checks in a pull request. Record meaningful work in `docs/PROGRESS.md` without removing the research history. The detailed agent guide and research notes remain available in the Git repository, but are excluded from source handoff archives.
