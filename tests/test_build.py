import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, box

from pathfinder.config import ANALYSIS_CRS
from pathfinder.graph.build import (
    INFERRED_CONNECTOR,
    SURFACE_GAP_MAX_M,
    SURFACE_GAP_REASON,
    bridge_gaps,
    drop_restricted,
    near_miss_dead_ends,
    node_table,
    prune_removed_road_stubs,
    sidewalk_side_coverage,
    split_into_edges,
    surface_gap_test,
)


def _ways(recs):
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "coords"} for r in recs])
    return gpd.GeoDataFrame(df, geometry=[LineString(r["coords"]) for r in recs], crs=ANALYSIS_CRS)


def test_split_at_shared_nodes_and_endpoints():
    ways = _ways([
        {"osm_way_id": 1, "kind": "sidewalk", "representation": "pedestrian_way",
         "node_refs": [1, 2, 3], "coords": [(0, 0), (50, 0), (100, 0)]},
        {"osm_way_id": 2, "kind": "crossing", "representation": "pedestrian_way",
         "node_refs": [2, 4], "coords": [(50, 0), (50, 20)]},
    ])
    e = split_into_edges(ways)
    assert sorted(map(tuple, e[["u", "v"]].to_numpy())) == [(1, 2), (2, 3), (2, 4)]
    assert e["length_m"].sum() == pytest.approx(120.0)


def test_interior_non_shared_nodes_do_not_split():
    ways = _ways([{"osm_way_id": 1, "kind": "sidewalk", "representation": "pedestrian_way",
                   "node_refs": [1, 2, 3], "coords": [(0, 0), (50, 1), (100, 0)]}])
    e = split_into_edges(ways)
    assert len(e) == 1 and (e.u.iat[0], e.v.iat[0]) == (1, 3)


def test_sidewalk_side_coverage_detects_both_sides():
    street = gpd.GeoSeries([LineString([(0, 0), (200, 0)])], crs=ANALYSIS_CRS)
    sidewalks = gpd.GeoSeries([LineString([(0, 8), (200, 8)]), LineString([(0, -8), (200, -8)])], crs=ANALYSIS_CRS)
    left, right = sidewalk_side_coverage(street, sidewalks)
    assert left[0] == pytest.approx(1.0) and right[0] == pytest.approx(1.0)
    left, right = sidewalk_side_coverage(street, sidewalks.iloc[:1])
    assert left[0] == pytest.approx(1.0) and right[0] == pytest.approx(0.0)


def test_sidewalk_side_coverage_ignores_far_parallel_features():
    street = gpd.GeoSeries([LineString([(0, 0), (200, 0)])], crs=ANALYSIS_CRS)
    far = gpd.GeoSeries([LineString([(0, 60), (200, 60)])], crs=ANALYSIS_CRS)  # next block over
    left, _ = sidewalk_side_coverage(street, far)
    assert left[0] == 0.0


def test_prune_removed_road_stubs_only_drops_short_centerline_stubs():
    xy = [((0, 0), (20, 0)), ((20, 0), (40, 0)), ((20, 0), (20, 50))]
    e = gpd.GeoDataFrame(
        {"u": [1, 2, 2], "v": [2, 3, 4], "kind": ["street_unknown"] * 3,
         "representation": ["street_centerline"] * 3},
        geometry=[LineString(c) for c in xy], crs=ANALYSIS_CRS)
    e["length_m"] = e.geometry.length
    # node 3 lies on a removed road; node 1 does not
    out, n = prune_removed_road_stubs(e, removed_nodes={3})
    assert n == 1 and set(zip(out.u, out.v)) == {(1, 2), (2, 4)}


def test_bridge_gaps_splits_target_and_discloses_connector():
    e = gpd.GeoDataFrame(
        {"u": [1, 3], "v": [2, 4], "kind": ["sidewalk", "sidewalk"], "representation": ["pedestrian_way"] * 2,
         "osm_way_id": [10, 11], "layer": [None, None]},
        geometry=[LineString([(0, 0), (100, 0)]), LineString([(50, 2), (50, 40)])], crs=ANALYSIS_CRS)
    e["length_m"] = e.geometry.length
    e["edge_id"] = np.arange(len(e))
    nodes = node_table(e)
    out, n = bridge_gaps(e, nodes)
    assert n == 1
    conn = out[out["representation"] == INFERRED_CONNECTOR]
    assert len(conn) == 1 and conn["length_m"].iat[0] == pytest.approx(2.0)
    # target split into two halves that preserve total length and attributes
    halves = out[out["osm_way_id"] == 10]
    assert len(halves) == 2 and halves["length_m"].sum() == pytest.approx(100.0)


def test_bridge_gaps_respects_layers():
    e = gpd.GeoDataFrame(
        {"u": [1, 3], "v": [2, 4], "kind": ["sidewalk", "sidewalk"], "representation": ["pedestrian_way"] * 2,
         "osm_way_id": [10, 11], "layer": ["1", None]},  # a bridge sidewalk above
        geometry=[LineString([(0, 0), (100, 0)]), LineString([(50, 2), (50, 40)])], crs=ANALYSIS_CRS)
    e["length_m"] = e.geometry.length
    e["edge_id"] = np.arange(len(e))
    out, n = bridge_gaps(e, node_table(e))
    assert n == 0


def _gap_fixture(gap_m: float):
    """A sidewalk that stops ``gap_m`` short of another sidewalk running across its end."""
    e = gpd.GeoDataFrame(
        {"u": [1, 3], "v": [2, 4], "kind": ["sidewalk", "sidewalk"], "representation": ["pedestrian_way"] * 2,
         "osm_way_id": [10, 11], "layer": [None, None]},
        geometry=[LineString([(0, 0), (100, 0)]), LineString([(50, gap_m), (50, 60)])], crs=ANALYSIS_CRS)
    e["length_m"] = e.geometry.length
    e["edge_id"] = np.arange(len(e))
    return e


def _evidence(sidewalk=None, road=None, stairs=None):
    polys, desc = [], []
    for g, d in ((sidewalk, "Sidewalk"), (stairs, "Stairs")):
        if g is not None:
            polys.append(g)
            desc.append(d)
    planim = gpd.GeoDataFrame({"DESCRIPTION": pd.Series(desc, dtype="object")}, geometry=polys, crs=ANALYSIS_CRS)
    ways = gpd.GeoDataFrame({"highway": ["residential"] if road is not None else []},
                            geometry=[road] if road is not None else [], crs=ANALYSIS_CRS)
    barriers = gpd.GeoDataFrame(geometry=[], crs=ANALYSIS_CRS)
    return surface_gap_test(planim, ways, barriers)


def test_wide_gap_is_bridged_only_across_mapped_sidewalk_surface():
    e = _gap_fixture(8.0)
    # no evidence: near is not connected
    out, n = bridge_gaps(e, node_table(e), tolerance=SURFACE_GAP_MAX_M, accept=_evidence())
    assert n == 0 and len(out) == 2
    # planimetric sidewalk surface spans the gap
    out, n = bridge_gaps(e, node_table(e), tolerance=SURFACE_GAP_MAX_M,
                         accept=_evidence(sidewalk=box(40, -1, 60, 9)), reason=SURFACE_GAP_REASON)
    conn = out[out["representation"] == INFERRED_CONNECTOR]
    assert n == 1 and conn["length_m"].iat[0] == pytest.approx(8.0)
    assert conn["class_reason"].iat[0] == SURFACE_GAP_REASON


def test_wide_gap_is_not_bridged_across_a_road_or_stairs():
    e = _gap_fixture(8.0)
    surface = box(40, -1, 60, 9)
    road = LineString([(0, 4), (100, 4)])
    assert bridge_gaps(e, node_table(e), tolerance=SURFACE_GAP_MAX_M, accept=_evidence(surface, road=road))[1] == 0
    stairs = box(48, 2, 52, 6)
    assert bridge_gaps(e, node_table(e), tolerance=SURFACE_GAP_MAX_M, accept=_evidence(surface, stairs=stairs))[1] == 0
    # surface under only half the gap is not enough
    assert bridge_gaps(e, node_table(e), tolerance=SURFACE_GAP_MAX_M, accept=_evidence(box(40, -1, 60, 4)))[1] == 0


def test_near_miss_dead_ends_are_counted_not_bridged():
    e = _gap_fixture(8.0)
    assert near_miss_dead_ends(e, node_table(e), SURFACE_GAP_MAX_M) == 1
    assert near_miss_dead_ends(e, node_table(e), 5.0) == 0


def test_restricted_area_removes_edges_mostly_inside_and_keeps_the_fence_street():
    """Fort Detrick: streets behind the gate are mapped like public ones; none may be routed."""
    base = box(0, 0, 100, 100)
    areas = gpd.GeoDataFrame({"name": ["Base"]}, geometry=[base], crs=ANALYSIS_CRS)
    ways = _ways([
        {"osm_way_id": 1, "kind": "street_unknown", "representation": "street_centerline",
         "node_refs": [1, 2], "coords": [(10, 50), (90, 50)]},            # inside the base
        {"osm_way_id": 2, "kind": "street_unknown", "representation": "street_centerline",
         "node_refs": [3, 4], "coords": [(-5, 0), (-5, 100)]},            # public road along the fence
        {"osm_way_id": 3, "kind": "street_unknown", "representation": "street_centerline",
         "node_refs": [5, 6], "coords": [(-40, 50), (20, 50)]},           # gate road: a third inside
    ])
    e = split_into_edges(ways)
    kept, removed = drop_restricted(e, areas)
    assert sorted(kept["osm_way_id"]) == [2, 3]
    assert removed == {"Base": {"edges": 1, "km": 0.1}}


def test_no_restricted_areas_keeps_everything():
    ways = _ways([{"osm_way_id": 1, "kind": "sidewalk", "representation": "pedestrian_way",
                   "node_refs": [1, 2], "coords": [(0, 0), (10, 0)]}])
    e = split_into_edges(ways)
    empty = gpd.GeoDataFrame({"name": []}, geometry=[], crs=ANALYSIS_CRS)
    kept, removed = drop_restricted(e, empty)
    assert len(kept) == 1 and removed == {}
