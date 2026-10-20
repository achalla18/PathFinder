"""Extract pedestrian-relevant ways and nodes from the OSM PBF.

Output (INTERIM_DIR):
- ``osm_ways.parquet``  — every way with a ``highway`` tag: node refs, geometry, key tags.
- ``osm_nodes.parquet`` — tagged nodes relevant to walking (kerbs, crossings, signals,
  elevators, subway entrances, street lamps, POIs with opening hours).

Nothing is classified or filtered here beyond "has a highway tag"; walkability rules live in
``graph.build`` so they are testable and documented in one place.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd
import osmium
import pandas as pd
from shapely.geometry import LineString, Point

from .config import INTERIM_DIR, WGS84, ensure_dirs
from .fetch import raw_path
from .sources import REGION

log = logging.getLogger(__name__)

WAY_KEYS = (
    "highway", "footway", "sidewalk", "sidewalk:both", "sidewalk:left", "sidewalk:right",
    "crossing", "crossing:markings", "crossing:signals", "crossing:island", "crossing_ref",
    "surface", "smoothness", "width", "incline", "lit", "foot", "access", "service", "area",
    "bridge", "tunnel", "layer", "level", "indoor", "name", "lanes", "maxspeed", "wheelchair",
    "tactile_paving", "ramp", "ramp:wheelchair", "conveying", "handrail", "step_count",
    "oneway", "junction", "covered",
)
NODE_KEYS = (
    "highway", "kerb", "barrier", "crossing", "crossing:markings", "crossing:signals",
    "tactile_paving", "railway", "entrance", "wheelchair", "opening_hours", "amenity", "shop",
    "name", "button_operated", "traffic_signals:sound", "traffic_signals:vibration",
    "crossing:island", "level",
)


def _relevant_node(tags) -> bool:
    hw = tags.get("highway")
    return (
        "kerb" in tags
        or tags.get("barrier") == "kerb"
        or hw in ("crossing", "traffic_signals", "elevator", "street_lamp", "stop", "give_way")
        or "crossing" in tags
        or tags.get("railway") == "subway_entrance"
        or ("opening_hours" in tags and ("amenity" in tags or "shop" in tags))
    )


BARRIER_KEYS = ("railway", "waterway", "tunnel", "bridge", "layer", "cutting", "embankment")


class _Handler(osmium.SimpleHandler):
    def __init__(self) -> None:
        super().__init__()
        self.ways: list[dict] = []
        self.nodes: list[dict] = []
        # Linear features pedestrians cannot cross at grade: used to detect grade
        # separation (and to mask DTM samples where a walkway passes over/under them).
        self.barriers: list[dict] = []

    def node(self, n) -> None:
        if not n.tags or not _relevant_node(n.tags):
            return
        rec = {"osm_node_id": n.id, "lon": n.location.lon, "lat": n.location.lat}
        for k in NODE_KEYS:
            rec[k] = n.tags.get(k)
        self.nodes.append(rec)

    def way(self, w) -> None:
        if "highway" not in w.tags:
            if w.tags.get("railway") in ("rail", "subway", "light_rail", "tram", "narrow_gauge") or \
                    w.tags.get("waterway") in ("river", "stream", "canal", "drain", "ditch"):
                coords = [(nd.location.lon, nd.location.lat) for nd in w.nodes if nd.location.valid()]
                if len(coords) >= 2:
                    rec = {"osm_way_id": w.id, "coords": coords}
                    for k in BARRIER_KEYS:
                        rec[k] = w.tags.get(k)
                    self.barriers.append(rec)
            return
        refs, coords = [], []
        for nd in w.nodes:
            if not nd.location.valid():
                return  # incomplete way at extract boundary; skip rather than guess
            refs.append(nd.ref)
            coords.append((nd.location.lon, nd.location.lat))
        if len(refs) < 2:
            return
        rec = {"osm_way_id": w.id, "node_refs": refs, "coords": coords}
        for k in WAY_KEYS:
            rec[k] = w.tags.get(k)
        rec["all_tags"] = json.dumps({t.k: t.v for t in w.tags}, sort_keys=True)
        self.ways.append(rec)


def extract(pbf: Path | None = None) -> tuple[Path, Path]:
    ensure_dirs()
    pbf = pbf or raw_path(REGION.osm)
    h = _Handler()
    h.apply_file(str(pbf), locations=True)
    log.info("OSM: %d highway ways, %d relevant nodes", len(h.ways), len(h.nodes))

    ways = pd.DataFrame(h.ways)
    geoms = [LineString(c) for c in ways.pop("coords")]
    ways_gdf = gpd.GeoDataFrame(ways, geometry=geoms, crs=WGS84)
    ways_out = INTERIM_DIR / "osm_ways.parquet"
    ways_gdf.to_parquet(ways_out)

    nodes = pd.DataFrame(h.nodes)
    nodes_gdf = gpd.GeoDataFrame(
        nodes, geometry=[Point(xy) for xy in zip(nodes.lon, nodes.lat)], crs=WGS84
    )
    nodes_out = INTERIM_DIR / "osm_nodes.parquet"
    nodes_gdf.to_parquet(nodes_out)

    bars = pd.DataFrame(h.barriers)
    bars_gdf = gpd.GeoDataFrame(bars, geometry=[LineString(c) for c in bars.pop("coords")], crs=WGS84)
    bars_gdf.to_parquet(INTERIM_DIR / "osm_barriers.parquet")
    log.info("OSM: %d railway/waterway ways", len(bars_gdf))
    return ways_out, nodes_out
