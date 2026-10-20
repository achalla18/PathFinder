# PathFinder and the City of Frederick: four requests

*Private draft for the owner to edit and send. Figures as of 2026-10-19; sources in
`docs/PROGRESS.md` and `reports/frederick/`.*

**What PathFinder is.** A private, non-commercial route planner for people who use wheelchairs,
walkers or strollers in Maryland's 6th district. It plans step-free routes from a mobility
profile and shows what is recorded about each crossing, curb and slope, with the source and date
of each record. It never calls a route "accessible". It also produces a barrier map by census
tract, listing recorded barriers and the places nothing has been recorded. Frederick is the pilot
because the city's 2025 sidewalk and curb-ramp surveys are the best pedestrian data in the
district.

**What your surveys already do.** With OpenStreetMap alone, 17% of crossing ends had any curb
evidence. With the city's 6,366 ramp records, 69% do. The barrier map lists the city's ramps that
fail its own check (172), ramps with no working tactile pad (1,047), and sidewalks with a condition
index under 40 (325, 19.4 km). PathFinder also measures slope from the county's 2021 elevation data
on 96% of the walkable network.

**Where it falls short.** PathFinder holds itself to a bar fixed before any of your data was loaded.
Frederick meets three of five criteria and misses two:

- **A manual-wheelchair route exists for 47.5% of a fixed sample of 276 trips; the bar is 50%.**
  That is 7 trips short. Of the 145 trips without a route, 73 are blocked only by corners with no
  record: 252 such corners inside the city line, 171 of them with no ramp record within 50 m.
  They cluster in newer neighborhoods (tracts 7512.01 and 7512.02, around Walter Martz, Yellow
  Springs, Rocky Springs and Banner Hill Roads). Only 27 of the 145 touch a state road.
- **Sidewalk evidence covers 56.8% of walkable length; the bar is 60%.** The sidewalk survey holds
  89% of the sidewalk OpenStreetMap shows on public streets. So where the survey shows nothing, we
  cannot say there is no sidewalk, unless we know which streets it was meant to cover.

**Requests**

1. **Written permission to use the surveys outside the project team.** The sidewalk, photo and
   curb-ramp layers state no license. Until the city agrees in writing, everything built on them
   stays internal. That includes showing routes to disabled testers at The Freedom Center, the next
   step. We will credit the city on every record that comes from its data.
2. **The sidewalk survey's scope.** Which streets was the 2025 survey meant to cover? Inside that
   scope, a street the survey shows without a sidewalk could count as "no sidewalk".
3. **The survey report** (O'Connell & Lawrence), for the condition index's own categories. Today we
   show the number only.
4. **Ramp records for newer neighborhoods.** Are the ramps in recent subdivisions recorded anywhere,
   for example in as-built plans or permit inspections? If not, would the city check a short list of
   corners? The first ones, inside the city line, are below. We have looked at them on aerial imagery: some look like
   recent work with crosswalks, others have no sidewalk on one side. Either answer is useful.

| Corner | Lat, lon | Trips it blocks |
|---|---|---|
| Tuscanny Drive at Chestnut Lane (crossing and junction) | 39.44603, -77.44282 | 8 |
| Old Willowbrook Road junction | 39.47451, -77.41233 | 7 |
| Opossumtown Pike at Fairfield Drive | 39.44516, -77.41138 | 3 |
| Tuscanny Drive crossing, south | 39.44366, -77.44148 | 1 |

**What the city gets back.** A copy of the barrier map and the unrecorded-corner list for every
tract, and a list of the city's own ramps that fail its check, near the trips that use them. They
are shared with the city only, and nothing is published without the city's agreement.

Contact: [owner's name, email]
