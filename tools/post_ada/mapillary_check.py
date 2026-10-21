"""Street-level photo check of the post-ADA ramp rule (Mapillary), where no survey reaches.

Finds Mapillary photos within PHOTO_RADIUS_M of every place the rule filled (curbs no source
records), taken after the place's oldest nearby building, then takes a random sample (fixed
seed) of the places that have one, and writes a sheet for a person to look at each place's
photos and say what the curbs show.

Photo locations come from Mapillary's coverage tiles: its image search returns nothing for any
box (2026-10-21, even Times Square), while the tiles list every photo. Downloading a photo needs
the graph API, which needs the app's Read permission.

    python tools/post_ada/mapillary_check.py sample     # reports/<region>/post_ada/photo_sample.csv
    python tools/post_ada/mapillary_check.py thumbs     # downloads the photos to look at (scratch)

Needs PF_MAPILLARY_TOKEN in the repo's .env (a client token; read access only). Photo ids and
dates are kept, never the uploader. Internal: it lists places the city survey helped choose.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import math

import geopandas as gpd
import mapbox_vector_tile
import pandas as pd
import requests
from shapely.geometry import Point

from pathfinder.config import GRAPH_DIR, REPORTS_DIR, WGS84
from pathfinder.fetch import raw_path
from pathfinder.graph import post_ada
from pathfinder.graph.enrich import _crossing_outer_ends
from pathfinder.sources import REGION

OUT = REPORTS_DIR / "post_ada"
TILES = "https://tiles.mapillary.com/maps/vtp/mly1_public/2/{z}/{x}/{y}"
GRAPH = "https://graph.mapillary.com"
TILE_ZOOM = 14  # the zoom at which the coverage tiles list single photos ("image" layer)
SEED = 20261021
SAMPLE = 40  # places to look at: enough that one wrong call in twenty shows
PHOTO_RADIUS_M = 20.0  # a curb is readable in a photo taken within about a street's width
PHOTOS_PER_PLACE = 6


def rule_places() -> gpd.GeoDataFrame:
    """Every place the rule filled: junction nodes and crossing ends with the rule as source."""
    e = gpd.read_parquet(GRAPH_DIR / "edges.parquet")
    nodes = gpd.read_parquet(GRAPH_DIR / "nodes.parquet").set_index("node_id")
    ids = set()
    for x in "uv":
        ids |= set(e.loc[e[f"xing_{x}"].fillna(False) & e[f"xing_{x}_kerb_source"].eq(post_ada.SOURCE), x])
    jn = gpd.GeoDataFrame({"place": [f"junction:{i}" for i in sorted(ids)], "kind": "junction"},
                          geometry=nodes.geometry.loc[sorted(ids)].values, crs=e.crs)
    groups, end_a, end_b = _crossing_outer_ends(e)
    cr = e[e["kind"].eq("crossing")]
    rows = []
    for end, pts in (("a", end_a), ("b", end_b)):
        filled = set(groups[cr.index[cr[f"kerb_{end}_source"].eq(post_ada.SOURCE)]])
        for g in sorted(filled):
            rows.append({"place": f"crossing_end:{g}:{end}", "kind": "corner", "geometry": pts.loc[g]})
    ce = gpd.GeoDataFrame(rows, geometry="geometry", crs=e.crs).drop_duplicates("geometry")
    places = pd.concat([jn, ce], ignore_index=True)
    parcels = gpd.read_parquet(raw_path(f"{REGION.id}_parcels")).to_crs(e.crs)
    nb = post_ada.neighbourhood(places.geometry, post_ada.built_parcels(parcels))
    return places.assign(oldest=nb["oldest"].to_numpy())


def _tile(lat: float, lon: float, z: int) -> tuple[int, int]:
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def photos(places_ll: gpd.GeoSeries, token: str) -> gpd.GeoDataFrame:
    """Every Mapillary photo in the coverage tiles over the places: id, year taken, panorama.
    The uploader's id, which the tiles carry, is never kept."""
    z, n = TILE_ZOOM, 2 ** TILE_ZOOM
    rows = []
    for x, y in sorted({_tile(p.y, p.x, z) for p in places_ll}):
        r = requests.get(TILES.format(z=z, x=x, y=y), params={"access_token": token}, timeout=60)
        r.raise_for_status()
        layer = mapbox_vector_tile.decode(r.content).get("image", {})
        ext = layer.get("extent", 4096)
        for f in layer.get("features", []):
            px, py = f["geometry"]["coordinates"]
            lon = (x + px / ext) / n * 360 - 180
            lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1 - py / ext) / n))))
            pr = f["properties"]
            rows.append({"photo_id": str(pr["id"]), "taken": pd.Timestamp(pr["captured_at"], unit="ms").date(),
                         "pano": bool(pr.get("is_pano")), "geometry": Point(lon, lat)})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=WGS84)


def sample(token: str) -> None:
    places = rule_places()
    ph = photos(places.geometry.to_crs(WGS84), token).to_crs(places.crs)
    j = gpd.sjoin(places, ph, predicate="dwithin", distance=PHOTO_RADIUS_M)
    j = j[pd.to_datetime(j["taken"]).dt.year > j["oldest"]]
    checkable = j["place"].unique()
    pick = places[places["place"].isin(checkable)].sample(n=min(SAMPLE, len(checkable)), random_state=SEED)
    ll = pick.geometry.to_crs(WGS84)
    rows = []
    for (_, p), pt in zip(pick.iterrows(), ll):
        mine = j[j["place"].eq(p["place"])].sort_values("taken", ascending=False)
        rows.append({"place": p["place"], "kind": p["kind"], "lat": round(pt.y, 6), "lon": round(pt.x, 6),
                     "oldest_building": int(p["oldest"]), "photos_after_build": len(mine),
                     "photo_ids": " ".join(mine["photo_id"].head(PHOTOS_PER_PLACE)), "newest_photo": str(mine["taken"].iat[0]),
                     "verdict": "", "notes": ""})
    out = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "photo_sample.csv", index=False)
    print(f"{len(places)} places filled by the rule; {len(ph)} photos in their tiles; "
          f"{len(checkable)} places with a photo within {PHOTO_RADIUS_M:.0f} m taken after the oldest building; "
          f"{len(out)} sampled")


def thumbs(token: str, dest: Path) -> None:
    s = pd.read_csv(OUT / "photo_sample.csv", dtype=str, keep_default_na=False)
    dest.mkdir(parents=True, exist_ok=True)
    for _, r in s[s["photo_ids"] != ""].iterrows():
        for pid in r["photo_ids"].split():
            f = dest / f"{r['place'].replace(':', '_')}__{pid}.jpg"
            if f.exists():
                continue
            meta = requests.get(f"{GRAPH}/{pid}", timeout=60, params={"access_token": token, "fields": "thumb_1024_url"}).json()
            if "error" in meta:
                sys.exit(f"Mapillary refused photo {pid}: {meta['error'].get('message')} "
                         "(the app needs Read permission in the Mapillary developer dashboard)")
            f.write_bytes(requests.get(meta["thumb_1024_url"], timeout=60).content)


if __name__ == "__main__":
    tok = os.environ.get("PF_MAPILLARY_TOKEN")
    if not tok:
        sys.exit("PF_MAPILLARY_TOKEN is not set (repo .env)")
    if sys.argv[1:2] == ["sample"]:
        sample(tok)
    elif sys.argv[1:2] == ["thumbs"]:
        thumbs(tok, Path(sys.argv[2]))
    else:
        sys.exit(__doc__)
