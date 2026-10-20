"""Regions: configuration, data paths, the OSM clip, and the roadway fallback."""

import os
import subprocess
import sys
from dataclasses import replace

import numpy as np
import pytest

from pathfinder.graph.roles import CANONICAL, _mph, empty
from pathfinder.regions import COVERAGE_FAMILIES, REGIONS, ROLES, get


def test_every_region_is_consistent():
    for r in REGIONS.values():
        assert r.osm in r.sources and r.boundary in r.sources
        assert set(r.roles) <= set(ROLES)
        assert set(r.coverage) <= set(COVERAGE_FAMILIES)
        assert r.bbox[0] < r.center[0] < r.bbox[2] and r.bbox[1] < r.center[1] < r.bbox[3]


def test_a_pilot_names_only_inspected_sources_and_confirms_nothing_by_absence():
    fred = get("frederick")
    assert fred.roles == {"planimetrics": "frederick_sidewalks", "report_districts": "frederick_tracts", "dtm": "frederick_dtm",
                          "ramps": "frederick_ramps", "signals": "frederick_county_signals",
                          "field_checks": "frederick_field_checks"}
    # the team's own sheet, kept in the repo; not held back under rule 7
    fc = fred.sources["frederick_field_checks"]
    assert fc.kind == "local_csv" and fc.url == "field/frederick.csv" and "internal use" not in fc.license.lower()
    assert fred.sources["frederick_sidewalk_photos"].kind == "arcgis_first_date"
    gai = get("gaithersburg")
    # Montgomery's sidewalk survey plays planimetrics; the city's own layer is a cross-check only
    assert gai.roles == {"planimetrics": "montgomery_sidewalks", "report_districts": "gaithersburg_tracts", "dtm": "gaithersburg_dtm",
                         "signals": "montgomery_signals"}
    for r in (fred, gai):
        dtm = r.sources[r.role("dtm")]
        assert dtm.bbox and dtm.as_of  # cut to the town, and dated by the flight
    assert "gaithersburg_sidewalks" in gai.sources
    for r in (fred, gai):
        # nothing is confirmed by absence: Montgomery's layer has no stairs class
        assert all(r.covers(f) is None for f in COVERAGE_FAMILIES)


def test_planimetric_sources_drop_editor_identifiers():
    gai = get("gaithersburg")
    assert {"CREATED_USER", "LAST_EDITED_USER"} <= set(gai.sources["montgomery_sidewalks"].drop_fields)
    assert {"UPDATE_STAFF_ID", "created_user", "last_edited_user"} <= set(gai.sources["gaithersburg_sidewalks"].drop_fields)


def test_montgomery_sidewalks_become_dated_sidewalk_polygons():
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import box

    from pathfinder.graph.roles import montgomery_planimetrics

    raw = gpd.GeoDataFrame({"FEATURE_CODE": [1206, 1208, 1205, 1201], "SOURCE_CODE": [5, 8, 6, 6]},
                           geometry=[box(0, 0, 1, 1)] * 4, crs=26985)
    out = montgomery_planimetrics(raw)
    # driveways and roads dropped; a non-street walk is never read as a street sidewalk
    assert list(out["DESCRIPTION"]) == ["Sidewalk", "Non-Street Sidewalk"]
    years = pd.to_datetime(out["CAPTUREYEAR"], unit="ms").dt.year.tolist()
    assert years == [2014, 2023]
    assert set(out.columns) >= set(CANONICAL["planimetrics"])
    assert not out["DESCRIPTION"].isin(["Stairs", "Crosswalk"]).any()


def test_a_region_naming_an_unregistered_source_is_refused():
    with pytest.raises(ValueError, match="not registered"):
        replace(get("gaithersburg"), roles={"signals": "nowhere"})
    with pytest.raises(ValueError, match="coverage"):
        replace(get("gaithersburg"), coverage={"signals": "somewhere"})
    with pytest.raises(KeyError):
        get("atlantis")


def _paths(region: str) -> list[str]:
    code = ("from pathfinder import config as c; from pathfinder.sources import REGION; "
            "print(REGION.id); print(c.DATA_DIR); print(c.REPORTS_DIR)")
    env = {**os.environ, "PF_REGION": region, "PF_DATA_DIR": os.path.join("X:", os.sep, "dd")}
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
    return out.stdout.split("\n")[:3]


def test_each_region_has_its_own_data_and_reports():
    for region in ("gaithersburg", "frederick"):
        rid, data, reports = _paths(region)
        assert rid == region
        assert data.replace("\\", "/").endswith(f"dd/regions/{region}")
        assert reports.replace("\\", "/").endswith(f"reports/{region}")


def test_gaithersburg_is_the_default_region():
    env = {k: v for k, v in os.environ.items() if k != "PF_REGION"}
    out = subprocess.run([sys.executable, "-c", "from pathfinder.sources import REGION; print(REGION.id)"],
                         env=env, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "gaithersburg"


@pytest.mark.parametrize("tag, mph", [("25 mph", 25.0), ("40", 24.9), ("30 mph;35 mph", 30.0), ("signals", np.nan),
                                      (None, np.nan), ("50 km/h", 31.1)])
def test_osm_maxspeed_is_read_as_mph(tag, mph):
    got = _mph(tag)
    assert (np.isnan(got) and np.isnan(mph)) or got == mph


def test_a_missing_role_reads_as_an_empty_frame_with_its_columns():
    for role, cols in CANONICAL.items():
        e = empty(role)
        assert len(e) == 0 and set(cols) <= set(e.columns)


def test_clip_keeps_ways_touching_the_box_complete_and_drops_the_rest(tmp_path):
    import osmium

    from pathfinder.fetch import clip_pbf

    src, out = tmp_path / "all.osm.pbf", tmp_path / "clip.osm.pbf"
    with osmium.SimpleWriter(str(src)) as w:
        # nodes 1-2 inside the box, 3 outside it (on way 10), 4-5 far away (way 11)
        for nid, lon, lat in ((1, 0.5, 0.5), (2, 0.6, 0.5), (3, 2.0, 0.5), (4, 5.0, 5.0), (5, 5.1, 5.0)):
            w.add_node(osmium.osm.mutable.Node(id=nid, location=(lon, lat), tags={"kerb": "lowered"} if nid == 2 else {}))
        w.add_way(osmium.osm.mutable.Way(id=10, nodes=[1, 2, 3], tags={"highway": "footway"}))
        w.add_way(osmium.osm.mutable.Way(id=11, nodes=[4, 5], tags={"highway": "footway"}))
    counts = clip_pbf(src, out, (0.0, 0.0, 1.0, 1.0))
    assert counts == {"ways": 1, "tagged_nodes_inside": 1, "nodes_inside": 2, "area_relations": 0}

    nodes, ways = {}, {}
    for o in osmium.FileProcessor(str(out)):
        if o.is_node():
            nodes[o.id] = (o.location.lon, o.location.lat)
        elif o.is_way():
            ways[o.id] = [n.ref for n in o.nodes]
    assert ways == {10: [1, 2, 3]}
    assert set(nodes) == {1, 2, 3}  # node 3 lies outside the box but its way needs it


def test_clip_keeps_a_military_area_relation_with_all_its_members(tmp_path):
    """Fort Detrick is mapped only as a relation: the clip must keep it, and the member ways
    that lie outside the box, or the area would be lost and its streets routed as public."""
    import osmium

    from pathfinder.fetch import clip_pbf

    src, out = tmp_path / "all.osm.pbf", tmp_path / "clip.osm.pbf"
    with osmium.SimpleWriter(str(src)) as w:
        for nid, lon, lat in ((1, 0.5, 0.5), (2, 0.6, 0.5), (3, 2.0, 2.0), (4, 2.1, 2.0)):
            w.add_node(osmium.osm.mutable.Node(id=nid, location=(lon, lat), tags={}))
        w.add_way(osmium.osm.mutable.Way(id=20, nodes=[1, 2], tags={}))   # member inside the box
        w.add_way(osmium.osm.mutable.Way(id=21, nodes=[3, 4], tags={}))   # member far outside it
        w.add_relation(osmium.osm.mutable.Relation(
            id=5, members=[("w", 20, "outer"), ("w", 21, "outer")],
            tags={"type": "multipolygon", "landuse": "military", "name": "Base"}))
        w.add_relation(osmium.osm.mutable.Relation(
            id=6, members=[("w", 20, "outer")], tags={"type": "multipolygon", "landuse": "forest"}))
    counts = clip_pbf(src, out, (0.0, 0.0, 1.0, 1.0))
    assert counts["area_relations"] == 1
    rels, ways = set(), set()
    for o in osmium.FileProcessor(str(out)):
        if o.is_relation():
            rels.add(o.id)
        elif o.is_way():
            ways.add(o.id)
    assert rels == {5} and ways == {20, 21}


def test_frederick_sidewalks_are_dated_by_their_first_photo_and_undated_ones_dropped(monkeypatch, tmp_path):
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import LineString

    from pathfinder.graph import roles

    photos = tmp_path / "photos.parquet"
    pd.DataFrame({"Segment_ID": [1], "first_ms": [pd.Timestamp("2025-04-01").value // 10**6]}).to_parquet(photos)
    monkeypatch.setattr(roles, "raw_path", lambda sid: photos)
    raw = gpd.GeoDataFrame({"Segment_ID": [1, 2], "Width_ft": [0.0, 5.0], "SCI": [roles.FREDERICK_SCI_FILL, 40.0]},
                           geometry=[LineString([(0, 0), (100, 0)]), LineString([(0, 50), (100, 50)])], crs=26985)
    out = roles.frederick_planimetrics(raw)
    assert len(out) == 1  # segment 2 was never photographed: no date, not used
    assert pd.to_datetime(out["CAPTUREYEAR"], unit="ms").dt.date.astype(str).tolist() == ["2025-04-01"]
    # width 0 means not recorded: drawn at the default width, as a polygon
    assert abs(out.geometry.iloc[0].area - 100 * roles.FREDERICK_DEFAULT_WIDTH_FT * 0.3048) < 1e-6
    # ...but its recorded width stays unknown, and the survey's fill value is not a score
    assert pd.isna(out["WIDTH_M"].iloc[0]) and pd.isna(out["CONDITION"].iloc[0])
    assert out["LINE"].iloc[0].equals(raw.geometry.iloc[0])


def test_frederick_ramps_record_missing_ramps_and_the_city_verdict():
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point

    from pathfinder.graph.roles import frederick_ramps

    raw = gpd.GeoDataFrame({
        "Ramp_Type": ["Perpendicular", "No ramp", "Parallel", "Combination", "Parallel"],
        "ADA_Description": ["Passed", "Fail", "Tactile_Warning_Pad_No", "Combination_No_landing", "Need_Verified"],
        "Data_Date": ["20250403", "20250512", "20250318", " 20250610", ""],
    }, geometry=[Point(i, 0) for i in range(5)], crs=26985)
    out = frederick_ramps(raw)
    assert out["KERB"].tolist() == ["ramp_present", "no_ramp", "ramp_present", "ramp_present", "ramp_present"]
    # no verdict on a ramp that is not there, and none where the survey gives none
    assert [None if pd.isna(v) else v for v in out["CHECK"]] == ["passed", None, "no_tactile_pad", "fails", None]
    days = pd.to_datetime(out["CAPTUREYEAR"], unit="ms").dt.date.astype(str).tolist()
    assert days[:4] == ["2025-04-03", "2025-05-12", "2025-03-18", "2025-06-10"] and pd.isna(out["CAPTUREYEAR"].iat[4])


def test_montgomery_signals_give_locations_only_and_a_proposed_signal_is_not_active():
    import geopandas as gpd
    from shapely.geometry import Point

    from pathfinder.graph import roles

    raw = gpd.GeoDataFrame({"OWNER_DESC": ["County", "SHA - Signal Operations", "Proposed"]},
                           geometry=[Point(0, 0), Point(1, 1), Point(2, 2)], crs=26985)
    out = roles.montgomery_signals(raw)
    assert out["STATUS"].tolist() == ["Active", "Active", "Proposed"]
    assert out[["LPI", "APS", "HAWK", "ALL_PED_PHASE", "PED_RECALL_MODE"]].isna().all().all()


def test_gaithersburg_names_the_signal_inventory_but_not_as_proof_of_absence():
    from pathfinder.regions.maryland import GAITHERSBURG

    assert GAITHERSBURG.role("signals") == "montgomery_signals"
    assert GAITHERSBURG.covers("signals") is None
    assert GAITHERSBURG.sources["montgomery_signals"].as_of == "2023-11-09"


def test_frederick_county_signals_count_only_full_signals_that_osm_confirms(monkeypatch, tmp_path):
    import geopandas as gpd
    import pandas as pd
    from shapely.geometry import Point

    from pathfinder.graph import roles
    from pathfinder.regions.base import AS_OF_OSM
    from pathfinder.regions.maryland import FREDERICK

    nodes = gpd.GeoDataFrame({"highway": ["traffic_signals", "crossing"]}, geometry=[Point(0, 0), Point(500, 0)], crs=26985)
    nodes.to_parquet(tmp_path / "osm_nodes.parquet")
    monkeypatch.setattr(roles, "INTERIM_DIR", tmp_path)
    raw = gpd.GeoDataFrame({"SIGNAL_TYPE": ["FUL_SIG", "SB", "FUL_SIG"]},
                           geometry=[Point(5, 0), Point(3, 0), Point(500, 0)], crs=26985)
    out = roles.frederick_county_signals(raw)
    # a school beacon is not a signal; a record with no OSM signal nearby is not used
    assert len(out) == 1 and out["STATUS"].tolist() == ["Active"] and out["APS"].isna().all()
    assert FREDERICK.sources["frederick_county_signals"].as_of == AS_OF_OSM
    assert FREDERICK.covers("signals") is None
