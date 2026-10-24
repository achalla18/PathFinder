# Data, attribution, and limitations

## Region choices

| Region ID | Intended use | Evidence available |
| --- | --- | --- |
| `gaithersburg_public` | Sharing and demonstrations | OSM and retained public sources, including terrain; excludes municipal inventories marked internal |
| `frederick_public` | Sharing and demonstrations | OSM, terrain, and the team's field-check source; excludes the city's internal inventories and the post-ADA parcel inference role |
| `dc` | Comparison and demonstrations | OSM, DC inventories, terrain, and registered crowdsourced evidence |
| `gaithersburg` | Internal research | Adds restricted municipal sources |
| `frederick` | Internal research | Adds restricted city inventories and research roles |

“Public” is the project's region designation: `regions.public()` excludes sources whose license metadata says “Internal use only,” and drops the parcel inference role. It is not a blanket license for every retained source. Some MD iMAP services have no explicit license recorded; review the service terms before redistributing data. `pf sources` lists the selected region's registry; the definitive URLs, dates, limitations, and license notes live in `src/pathfinder/regions/`.

## Attribution

- **OpenStreetMap contributors:** OSM data, distributed under ODbL 1.0; extracts provided by Geofabrik. Preserve attribution and review share-alike obligations for derived databases.
- **Open Data DC:** the registered DC inventories are identified as CC BY 4.0 in the source registry.
- **Maryland iMAP and county terrain providers:** boundaries and terrain; consult each source entry for provider, vintage, and terms.
- **U.S. Census Bureau:** public-domain census tract boundaries used for reporting.
- **Project Sidewalk:** crowdsourced observations in the DC region; consult its registered source terms.
- **PathFinder field checks:** the team's own observations in `field/`, with per-visit evidence dates.

Map tiles, fonts, software dependencies, imagery, and research tools have separate terms. Source-code availability does not transfer rights to them. No general open-source license has been assigned to PathFinder's own code.

## What is excluded from the handoff archive

Git export rules omit the internal `reports/frederick/` and `reports/gaithersburg/` outputs, along with working plans, progress logs, internal briefs, field-mapping worklists, and agent instructions. They remain in repository history for research continuity. Public-region and DC reports remain in the archive as dated snapshots; rebuilding with current sources may produce different results.

The repository itself and its history still contain internal research material. Archive filtering does not make the full repository suitable for unrestricted publication.

## Interpreting results

Terrain models describe bare-earth elevation, not the exact surface under a wheel. Inventories can be incomplete or old; OSM coverage varies. Survey absence counts only where completeness and coverage justify it. A mobility profile expresses starting assumptions, not an individual assessment.

The prototype has not completed the planned outdoor user-validation program. Experimental Tile2Net sidewalk outputs failed their evaluation threshold and are not used for routing. Internal-pilot metrics must not be presented as public-region performance.
