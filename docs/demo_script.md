# Demo video script (Congressional App Challenge, MD-6)

About 3 minutes. Everything shown is built from open data only (rule 7): DC's open data, and the
public builds of Gaithersburg and Frederick.

## Before recording

1. `pf demo` (from `C:\dev\PathFinder`, with the venv's `pf.exe`). Wait for
   "PathFinder demo: http://127.0.0.1:8000". It opens the browser.
2. **Warm up every place once.** The first trip after start-up is slow while each server loads its
   graph (the Zoo trip takes about 12 s the first time).
   - Open each card and click each example once.
   - Then return to the landing page.
3. **Browser window:** 1920×1080 with no other tabs or bookmarks bar showing. Zoom at 100%.
   Extensions with toolbars or pop-ups should be hidden or off. Light theme reads best on video.
4. **Recording:** Windows: Win+Alt+R (Xbox Game Bar), or OBS at 1080p, 30 fps.

## Shots

| # | Time | On screen | Say (suggested) |
|---|---|---|---|
| 1 | 0:00–0:20 | Landing page; the cards rise in and the evidence bars fill | "For people who use a wheelchair, a walker or a stroller, the fastest route often isn't one they can take. PathFinder plans around missing curb ramps, steep hills and streets without sidewalks." |
| 2 | 0:20–0:35 | Point at the three cards and the bars: DC 92% curb evidence, Frederick 17% | "It works anywhere the data exists. Washington publishes its sidewalks and curb ramps; in Maryland's 6th district, most of it has never been recorded." |
| 3 | 0:35–1:05 | Click **Washington, DC**. The map glides in. Click **Gallery Place to Ford's Theatre**. The routes draw in. | "Here's a manual-wheelchair trip downtown. PathFinder finds several routes and recommends the one with the easiest crossings, for the same eight minutes." |
| 4 | 1:05–1:20 | Open **What matters**: the profiles, then drag the point in the triangle | "Everyone's needs differ. Pick how you get around, then drag toward what matters most: crossings, slope or sidewalks." |
| 5 | 1:20–1:45 | Back to **Routes**. Click **Woodley Park Metro to the National Zoo** | "And when no route meets your needs, PathFinder says so. This hill is steeper than an ADA ramp. It shows the smallest compromise, and exactly where, with the source: DC's 2024 LiDAR survey." |
| 6 | 1:45–2:00 | **Barriers** tab; pan the map a little | "Every curb, slope and sidewalk carries its source and date." |
| 7 | 2:00–2:30 | Click **Washington, DC ▾** (Change place), then **Frederick**. Click **City Hall to Nicodemus Athletic Complex** | "Now Frederick, in our district. The recommended route takes a minute longer but avoids the hardest crossings. Because curbs here aren't recorded, it shows what isn't known instead of guessing." |
| 8 | 2:30–2:45 | Click **Start walking** with `?demo` in the address (see below) | "Then step-by-step guidance along the way." |
| 9 | 2:45–3:00 | Back on the landing page; scroll to "The data gap in Maryland's 6th district" | "The gap can be closed. A community mapping campaign in OpenStreetMap can record Frederick's sidewalks street by street, and every tag makes PathFinder better for everyone." |

**Simulated walk (shot 8):** add `?demo` before the `#`, for example
`http://127.0.0.1:8003/?demo#from=…`. The blue dot then moves along the route on its own. Without
`?demo` the app waits for real GPS.

## Facts to keep straight on camera

- **DC evidence:** curb evidence 92%, slope measured 82%, sidewalk evidence 75%. From
  `reports/dc/phase0/coverage.md`.
- **Frederick evidence:** curbs 17%, slope 96%, sidewalks 42%. **Gaithersburg:** curbs 19%,
  slope 89%, sidewalks 47%. From the open-data builds only.
- **Frederick and Gaithersburg examples** use "Anything not ruled out" as the evidence setting.
  With "Recorded or likely" most Maryland trips have no route, because the curbs are unrecorded:
  that is the data gap.
- **Mapping campaign:** say it "can" close the gap; it has not started yet. The forum post is
  pending.
- **Do not show** the internal builds (`frederick`, `gaithersburg` without `_public`); `pf demo`
  never starts them.
