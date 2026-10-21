# Mapping sidewalks in OpenStreetMap

Frederick's sidewalk evidence (accessibility criterion 3) is short of its bar because many
streets have nothing that records whether they have a sidewalk. Tagging those streets in
OpenStreetMap closes the gap, and unlike the city's survey, what goes into OSM is open: it can
be shown to testers and the public.

The worklist says where to look: `reports/<region>/sidewalk_mapping/README.md` (areas, largest
first) and `worklist.csv` (every street, with an edit link and a photo link). Regenerate it with
`python tools/sidewalk_mapping/make_worklist.py`. The worklist itself is internal (it depends on
the city's survey); the tags you add are not.

## Before the first edit (owner)

- Each mapper uses their own OSM account. Never share a login.
- A team mapping campaign falls under the OSM Foundation's Organised Editing Guidelines:
  describe it on an OSM wiki page (who, what, which area, the hashtag) before starting.
- Pick a changeset hashtag for the campaign and use it on every edit.

## What you may map from

- **What you see on site.** Changeset `source=survey`.
- **Street-level photos on Mapillary** (the `photos` link on each row). Its licence allows
  mapping into OSM. `source=Mapillary`.
- **Aerial imagery layers offered inside the iD editor.** `source=` the layer's name.

Never map from:
- **The City of Frederick's sidewalk layer or survey.** It is internal only and not licensed for
  OSM.
- **Google Maps or Street View.** Their terms forbid it.
- **This project's maps or reports.**

## What to tag

Open the `edit` link and select the street (the whole OSM way). Add one tag:

| What you see | Tag |
|---|---|
| A sidewalk on both sides | `sidewalk=both` |
| A sidewalk on one side only | `sidewalk=left` or `sidewalk=right` (left and right follow the way's direction, shown by its arrows in iD) |
| No sidewalk on either side | `sidewalk=no` |

- Tag only what holds **along the whole way**. If the sidewalk starts or stops partway, split the
  way at that point and tag each part, or leave the way for someone who can see it.
- A sidewalk under construction, or lots with silt fence and no sidewalk yet: tag what is
  walkable today (`no` on that side). Never tag one that is not built.
- If you cannot tell, skip it. An untagged street is unknown; a wrong tag is worse.
- "No" counts as evidence too. A street with no sidewalk, recorded, is useful to a wheelchair
  user planning a trip.
- Leave sidewalks already drawn as their own lines alone. Tagging the street is enough.

## Getting the edits into PathFinder

Geofabrik rebuilds its Maryland extract daily, so edits arrive the day after they are made:

```
pf fetch --force osm_frederick      # takes the newer extract (only if the server has one)
pf extract-osm
pf build-graph
pf enrich
pf coverage                         # criterion 3 is in reports/frederick/phase0/coverage.md
pf barriers
pf crux --fresh --per-bin 100
python tools/sidewalk_mapping/make_worklist.py   # what is left
```

OSM tags are `verified` evidence, dated by the extract. Where OSM and the city's survey disagree,
OSM's reading is used, because it is applied first.
