# Demo walkthrough

## One-region review

Complete the [local setup](../README.md#run-locally) first, using `gaithersburg_public`, `frederick_public`, or `dc`. Build the web app and start `pf serve`.

1. Open http://127.0.0.1:8000 and choose a mobility profile.
2. Select an offered example trip, or search for an origin and destination inside the region.
3. Review the route and its sourced conditions. Notice which conditions are recorded, inferred, or unknown.
4. Adjust the crossings/curbs, slope, and sidewalk priorities in the triangle. Compare alternatives when the app finds meaningful differences.
5. Change a hard requirement or the certainty setting. If no route qualifies, explain the missing evidence or requirement rather than claiming the destination is unreachable in reality.
6. Open the barrier map to inspect recorded obstacles and unrecorded places.

Public Maryland regions have less curb and sidewalk evidence than the internal research pilots. A missing route at a strict evidence setting is an expected result, not proof that no physical route exists.

## Three-place landing page

Prepare the graph for **each** of `dc`, `gaithersburg_public`, and `frederick_public` by changing `PF_REGION` in `.env` and running the five preparation commands in the README. Build the web app once, stop any process already using port 8000, then run:

```bash
pf demo
```

The local landing page runs on port 8000, with DC, Gaithersburg, and Frederick on ports 8001–8003. It starts the servers and warms example trips; it does not download or build missing graphs. Ctrl-C stops the group. Use `pf demo --no-browser` to skip opening a browser automatically.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Root page is missing | Build `web/dist/` with `npm ci` and `npm run build`, then restart `pf serve` |
| Planning or search fails on missing files | Complete the data pipeline for the same region and data directory used by the server |
| The wrong town opens | Check shell overrides of `PF_REGION`; restart after changing `.env` |
| The map backdrop fails | Check internet access and retry the map; the app shell cache does not include map coverage |
| Demo startup fails | Check all three prepared graphs, ports 8000–8003, and any `PF_APP_PASSWORD` setting |
| Strict settings find no qualifying route | Inspect the evidence gaps; relax certainty only as an explicit user choice |

A health response at `/api/health` confirms that the server responds, not that its graph has finished loading or that routing works.
