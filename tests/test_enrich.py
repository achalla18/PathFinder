"""Evidence grading in ``graph.enrich`` on synthetic edges."""

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, box

from pathfinder.analysis.coverage import ATTRS
from pathfinder.config import ANALYSIS_CRS
from pathfinder.graph import enrich
from pathfinder.routing.cost import Requirements, feasible_mask

from .conftest import make_edges, make_nodes

CAPTURE_MS = pd.Timestamp("2021-06-01").value // 10**6
CONN = {"kind": "connector", "representation": "inferred_connector"}


@pytest.fixture(autouse=True)
def _osm_date(monkeypatch):
    monkeypatch.setattr(enrich, "_osm_as_of", lambda: "2026-10-04")


def _points(xy: list[tuple[float, float]], **cols) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(cols, geometry=[Point(p) for p in xy], crs=ANALYSIS_CRS)


def _stairs(*polys) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame({"DESCRIPTION": ["Stairs"] * len(polys), "CAPTUREYEAR": [CAPTURE_MS] * len(polys)},
                            geometry=list(polys), crs=ANALYSIS_CRS)


def _edges(rows, xy) -> gpd.GeoDataFrame:
    """make_edges plus the raw OSM tag columns and coverage flags enrich reads."""
    e = make_edges(rows, xy)
    for col in ("wheelchair", "crossing", "crossing:markings", "crossing:signals", "surface", "smoothness"):
        if col not in e:
            e[col] = None
    # DC's coverage: planimetrics cover on-street edges inside the line, signals everywhere
    for family in ("planimetric",):
        if f"covered_{family}" not in e:
            e[f"covered_{family}"] = ~e["offstreet"] & ~e["outside_region"]
    if "covered_signals" not in e:
        e["covered_signals"] = True
    return e


# ---------------------------------------------------------------- step-free


def test_inferred_connectors_are_never_verified_step_free():
    """Regression: connectors skipped the stairs check and were graded verified step-free."""
    xy = {0: (0, 0), 1: (50, 0), 2: (52, 0), 3: (100, 0), 4: (102, 0), 5: (150, 0)}
    e = _edges([
        {"u": 0, "v": 1},
        {"u": 1, "v": 2, **CONN},  # lies inside a stairs polygon
        {"u": 2, "v": 3},
        {"u": 3, "v": 4, **CONN},  # no stairs evidence
        {"u": 4, "v": 5},
    ], xy)
    enrich.enrich_step_free(e, _stairs(box(49, -1, 53, 1)))

    assert e["step_free_status"].tolist() == ["verified", "inferred", "verified", "inferred", "verified"]
    assert e["step_free"].tolist() == [True, False, True, True, True]
    assert e["planimetric_stairs_overlap"].tolist() == [False, True, False, False, False]

    likely = feasible_mask(e, Requirements(step_free=True, certainty="allow_likely"))
    verified = feasible_mask(e, Requirements(step_free=True, certainty="verified_only"))
    assert likely.tolist() == [True, False, True, True, True]
    assert verified.tolist() == [True, False, True, False, True]


def test_step_free_without_any_stairs_polygons():
    e = _edges([{"u": 0, "v": 1}, {"u": 1, "v": 2, **CONN}], {0: (0, 0), 1: (50, 0), 2: (52, 0)})
    enrich.enrich_step_free(e, _stairs(box(1000, 1000, 1004, 1002)))
    assert e["step_free_status"].tolist() == ["verified", "inferred"]
    assert not np.any(e["planimetric_stairs_overlap"])


def test_absence_of_stairs_is_only_evidence_inside_inventory_coverage():
    """Regression: edges beyond the region's line were verified step-free from DC planimetrics."""
    xy = {0: (0, 0), 1: (50, 0), 2: (100, 0), 3: (150, 0)}
    e = _edges([{"u": 0, "v": 1}, {"u": 1, "v": 2, "outside_region": True}, {"u": 2, "v": 3, "offstreet": True}], xy)
    enrich.enrich_step_free(e, _stairs(box(1000, 1000, 1004, 1002)))
    assert e["step_free_status"].tolist() == ["verified", "inferred", "inferred"]
    assert e["step_free_source"].tolist()[1] == "derived:absent_from_osm_steps_outside_inventory"


def test_wheelchair_tag_is_direct_evidence():
    xy = {0: (0, 0), 1: (50, 0), 2: (100, 0)}
    e = _edges([{"u": 0, "v": 1, "wheelchair": "no"}, {"u": 1, "v": 2, "wheelchair": "yes", "offstreet": True}], xy)
    enrich.enrich_step_free(e, _stairs(box(1000, 1000, 1004, 1002)))
    assert e["step_free"].tolist() == [False, True]
    assert e["step_free_status"].tolist() == ["verified", "verified"]
    assert e["step_free_source"].tolist() == [enrich.OSM, enrich.OSM]


# ---------------------------------------------------------------- lighting and surface


def test_smoothness_can_only_worsen_the_surface_class():
    xy = {0: (0, 0), 1: (50, 0), 2: (100, 0), 3: (150, 0)}
    e = _edges([{"u": 0, "v": 1, "surface": "asphalt"},
                {"u": 1, "v": 2, "surface": "asphalt", "smoothness": "bad"},
                {"u": 2, "v": 3, "surface": "gravel", "smoothness": "excellent"}], xy)
    enrich.enrich_surface(e)
    assert e["surface_class"].tolist() == ["smooth", "rough", "unpaved"]


# ---------------------------------------------------------------- crossing control


def _crossing_control(rows, nodes=None, signal_at=None):
    xy = {i: (i * 100.0, 0.0) for i in range(len(rows) + 1)}
    e = _edges([{"u": i, "v": i + 1, "kind": "crossing", **r} for i, r in enumerate(rows)], xy)
    signals = _points([signal_at or (9e5, 9e5)], STATUS=["Active"], LPI=["Yes"], APS=["No"], HAWK=["No"],
                      ALL_PED_PHASE=["None"], PED_RECALL_MODE=["None"])
    planim = gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"], "CAPTUREYEAR": [CAPTURE_MS]},
                              geometry=[box(9e5, 9e5, 9e5 + 1, 9e5 + 1)], crs=ANALYSIS_CRS)
    nodes = nodes if nodes is not None else _points([(9e5, 0.0)], highway=["crossing"], crossing=[None])
    if "crossing:signals" not in nodes:
        nodes["crossing:signals"] = None
    enrich.enrich_crossing_control(e, signals, planim, nodes)
    return e


def test_signal_tags_are_read_from_way_and_node():
    """Regression: only ``crossing=traffic_signals`` on the way counted as a signal."""
    nodes = _points([(350.0, 0.0)], highway=["crossing"], crossing=["traffic_signals"])
    e = _crossing_control([
        {"crossing": "traffic_signals"},
        {"crossing": "marked", "crossing:signals": "yes"},
        {"crossing": "uncontrolled"},
        {"crossing": "marked"},  # the node on this way says it is signalized
    ], nodes)
    assert e["crossing_control"].tolist() == ["signal", "signal", "marked_uncontrolled", "signal"]
    assert (e["crossing_control_status"] == "verified").all()


def test_contradictory_signal_tags_take_the_less_favorable_reading():
    e = _crossing_control([{"crossing": "traffic_signals", "crossing:signals": "no", "crossing:markings": "zebra"}])
    assert e["crossing_control"].tolist() == ["marked_uncontrolled"]
    assert e["crossing_control_status"].tolist() == ["inferred"]
    assert e["crossing_signal_tags_conflict"].tolist() == [True]


def test_painted_crossing_near_a_ddot_signal_is_not_assumed_signalized():
    e = _crossing_control([{"crossing": "marked"}, {"crossing": "marked"}], signal_at=(50.0, 10.0))
    assert e["crossing_control"].tolist() == ["marked_uncontrolled", "marked_uncontrolled"]
    # the one beside the signal may well be signalized: we do not know, and say so
    assert e["crossing_control_status"].tolist() == ["inferred", "verified"]
    assert e["signal_lpi_status"].tolist() == ["unknown", "unknown"]  # no credit for a signal we do not claim


# ---------------------------------------------------------------- implicit crossings


def test_centerline_junctions_become_implicit_crossings():
    #        4
    #        |
    #  0 --- 1 --- 2 --- 3        street through node 1 (four-way) and node 2 (mid-block)
    #        |
    #        5
    xy = {0: (0, 0), 1: (100, 0), 2: (200, 0), 3: (300, 0), 4: (100, 100), 5: (100, -100), 6: (200, 60)}
    st = {"kind": "street_unknown", "representation": "street_centerline"}
    e = _edges([
        {"u": 0, "v": 1, **st}, {"u": 1, "v": 2, **st}, {"u": 2, "v": 3, **st},
        {"u": 4, "v": 1, **st, "sidewalk_presence": "none"}, {"u": 1, "v": 5, **st},
        {"u": 6, "v": 2, "kind": "alley", "representation": "street_centerline"},
        {"u": 3, "v": 6},  # a sidewalk: never an implicit crossing
    ], xy)
    nodes = make_nodes(xy)
    nodes["on_removed_road"] = nodes["node_id"].eq(3)  # node 3 sits on a sidewalk-mapped avenue
    signals = _points([(110.0, 5.0)], STATUS=["Active"])
    roadway = gpd.GeoDataFrame({"TOTALCROSSSECTIONWIDTH": [60.0]}, geometry=[box(95, -200, 105, 200).boundary], crs=ANALYSIS_CRS)
    ps = _points([(95.0, 5.0), (105.0, -5.0), (295.0, 5.0)], label_type=["CurbRamp", "CurbRamp", "NoCurbRamp"])
    ramps = _points([(9e5, 9e5)])
    enrich.enrich_implicit_crossings(e, nodes, signals, roadway, ps, ramps)

    assert e["xing_u"].tolist() == [False, True, False, False, True, False, False]
    assert e["xing_v"].tolist() == [True, False, True, True, False, True, False]
    # node 1: signalized, 60 ft wide, ramps at the corners
    assert e["xing_v_control"].iat[0] == "signal" and e["xing_v_width_m"].iat[0] == pytest.approx(18.3, abs=0.05)
    assert e["xing_v_kerb"].iat[0] == "ramp_likely"
    assert e["xing_v_kerb"].iat[3] == "no_curb"  # no sidewalk: the walker is in the roadway
    # node 3: no signal, a missing-ramp label
    assert e["xing_v_control"].iat[2] is None and e["xing_v_kerb"].iat[2] == "no_ramp_reported"
    # the alley meets a through street at node 2; the street itself does not cross anything there
    assert e["xing_v_kerb"].iat[5] == "no_curb" and not e["xing_v"].iat[1]
    # nothing is recorded on ends that are not crossings
    assert e.loc[~e["xing_u"], "xing_u_kerb"].isna().all()


def test_coverage_report_covers_every_graded_attribute():
    assert {a for a, _, _ in ATTRS} == set(enrich.GRADED_ATTRS)


# ---------------------------------------------------------------- street names


def test_a_sidewalk_takes_the_name_of_the_street_it_runs_beside():
    #  K ST runs east-west along y = 0; 9TH ST runs north-south along x = 100
    xy = {0: (10, 8), 1: (90, 8), 2: (92, 9), 3: (108, 6), 4: (108, 40), 5: (0, 60), 6: (80, 60), 7: (90, 8.5), 8: (93, 8.5)}
    e = _edges([
        {"u": 0, "v": 1},  # beside K ST
        {"u": 3, "v": 4},  # beside 9TH ST; K ST is within range but runs across it
        {"u": 5, "v": 6},  # parallel to K ST but 60 m away: a path in a park, say
        {"u": 7, "v": 8},  # a 3 m stub at the corner: no direction to trust
        {"u": 1, "v": 2, "kind": "crossing"},  # only sidewalks are named this way
    ], xy)
    roadway = gpd.GeoDataFrame({"ROUTENAME": ["K ST NW", "9TH ST NW"]},
                               geometry=[LineString([(0, 0), (200, 0)]), LineString([(100, -100), (100, 100)])], crs=ANALYSIS_CRS)
    enrich.enrich_along_street(e, roadway)
    assert e["along_street"].tolist() == ["K ST NW", "9TH ST NW", None, None, None]


# ---------------------------------------------------------------- a region without an inventory


def test_painted_crossing_without_a_signal_inventory_is_only_inferred_unsignalized():
    """Rule 1: where no signal inventory covers the place, no signal on record is no evidence."""
    e = _crossing_control([{"crossing": "marked", "covered_signals": False},
                           {"crossing": "uncontrolled", "covered_signals": False},  # OSM itself says no signal
                           {"crossing": "traffic_signals", "covered_signals": False}])
    assert e["crossing_control"].tolist() == ["marked_uncontrolled", "marked_uncontrolled", "signal"]
    assert e["crossing_control_status"].tolist() == ["inferred", "verified", "verified"]
    assert e["crossing_control_source"].iat[0] == "derived:osm_marked_no_signal_inventory"


def test_without_a_stairs_inventory_step_free_is_never_verified_by_absence():
    from pathfinder.graph import roles

    e = _edges([{"u": 0, "v": 1, "covered_planimetric": False}, {"u": 1, "v": 2, "kind": "steps", "covered_planimetric": False}],
               {0: (0, 0), 1: (50, 0), 2: (60, 0)})
    enrich.enrich_step_free(e, roles.empty("planimetrics"), None)
    assert e["step_free_status"].tolist() == ["inferred", "verified"]
    assert e["step_free"].tolist() == [True, False]
    assert e["step_free_source"].iat[0] == "derived:absent_from_osm_steps_outside_inventory"


def test_survey_grades_streets_not_service_roads_and_dates_each_by_its_own_polygons():
    """Sidewalk polygons 5 m either side of a street and of a parking aisle: the street reads
    "both", dated by the oldest polygon beside it; the aisle stays unknown (a lot's aisle has
    building and street sidewalks within reach without having its own)."""
    old, new = pd.Timestamp("2014-01-01").value // 10**6, pd.Timestamp("2023-01-01").value // 10**6
    lines = [LineString([(0, 0), (100, 0)]), LineString([(0, 500), (100, 500)])]
    edges = gpd.GeoDataFrame({
        "representation": ["street_centerline"] * 2, "kind": ["street_unknown", "service"],
        "sidewalk_left": [None] * 2, "sidewalk_right": [None] * 2, "covered_planimetric": [False] * 2,
        "oneway": [None] * 2,
    }, geometry=lines, crs=ANALYSIS_CRS)
    polys = [box(-5, 4, 105, 6), box(-5, -6, 105, -4), box(-5, 504, 105, 506), box(-5, 494, 105, 496)]
    planim = gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"] * 4, "CAPTUREYEAR": [old, new, new, new]},
                              geometry=polys, crs=ANALYSIS_CRS)
    enrich.enrich_centerline_sidewalks(edges, planim, "survey")
    assert edges.loc[0, "sidewalk_presence"] == "both"
    assert edges.loc[0, "sidewalk_presence_as_of"] == "2014-01-01"
    assert edges.loc[1, "sidewalk_presence_status"] == "unknown"


def test_a_divided_road_half_does_not_borrow_the_far_carriageways_sidewalk():
    """Two one-way carriageways 20 m apart, a sidewalk only outside the southern one: the
    northern half finds the sidewalk across the median only if its probe overreaches, so it
    stays unknown; the southern half has a sidewalk on its outer side only: at least one side,
    not "both"."""
    lines = [LineString([(0, 0), (100, 0)]), LineString([(100, 20), (0, 20)])]
    edges = gpd.GeoDataFrame({
        "representation": ["street_centerline"] * 2, "kind": ["street_unknown"] * 2,
        "sidewalk_left": [None] * 2, "sidewalk_right": [None] * 2, "covered_planimetric": [False] * 2,
        "oneway": ["yes", "yes"],
    }, geometry=lines, crs=ANALYSIS_CRS)
    planim = gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"], "CAPTUREYEAR": [CAPTURE_MS]},
                              geometry=[box(-5, -7, 105, -5)], crs=ANALYSIS_CRS)
    enrich.enrich_centerline_sidewalks(edges, planim, "survey")
    assert edges["sidewalk_presence"].tolist() == ["at_least_one_side", None]
    # with a sidewalk outside each carriageway the road still has none on either median side
    planim2 = pd.concat([planim, gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"], "CAPTUREYEAR": [CAPTURE_MS]},
                                                  geometry=[box(-5, 25, 105, 27)], crs=ANALYSIS_CRS)])
    edges2 = edges.drop(columns=[c for c in edges if c.startswith("sidewalk_presence")])
    enrich.enrich_centerline_sidewalks(edges2, planim2, "survey")
    assert edges2["sidewalk_presence"].tolist() == ["at_least_one_side", "at_least_one_side"]


# ---------------------------------------------------------------- sidewalk condition survey


def _survey(lines_values):
    """A condition survey's planimetrics: (line, CONDITION, WIDTH_M, capture date)."""
    lines = [l for l, *_ in lines_values]
    return gpd.GeoDataFrame({
        "DESCRIPTION": "Sidewalk",
        "CAPTUREYEAR": [pd.Timestamp(d).value // 10**6 for *_, d in lines_values],
        "CONDITION": [c for _, c, _, _ in lines_values],
        "WIDTH_M": [w for _, _, w, _ in lines_values],
        "LINE": lines,
    }, geometry=[l.buffer(0.6, cap_style="flat") for l in lines], crs=ANALYSIS_CRS)


def test_a_surveyed_sidewalk_takes_the_lowest_index_and_earliest_date_of_its_segments():
    xy = {0: (0, 0), 1: (100, 0), 2: (0, 50), 3: (100, 50)}
    e = _edges([{"u": 0, "v": 1, "kind": "sidewalk"}, {"u": 2, "v": 3, "kind": "sidewalk"}], xy)
    planim = _survey([(LineString([(0, 1), (60, 1)]), 90.0, 1.5, "2025-04-02"),
                      (LineString([(60, 1), (100, 1)]), 35.0, 1.22, "2025-03-28"),
                      (LineString([(0, 51), (100, 51)]), None, None, "2025-04-02")])  # no score recorded
    enrich.enrich_sidewalk_condition(e, planim, "frederick_sidewalks")
    r = e.iloc[0]
    assert r["sidewalk_condition"] == 35.0 and r["sidewalk_width_m"] == 1.22
    assert r["sidewalk_condition_status"] == "verified" and r["sidewalk_condition_as_of"] == "2025-03-28"
    assert e.iloc[1]["sidewalk_condition_status"] == "unknown"  # a missing score is never filled in
    for a in ("sidewalk_condition", "sidewalk_width_m"):
        enrich.ev.validate(e, a)


def test_a_street_takes_the_worse_side_of_its_surveyed_sidewalks_only_as_inferred():
    xy = {0: (0, 0), 1: (100, 0), 2: (0, 200), 3: (100, 200)}
    e = _edges([{"u": 0, "v": 1, "kind": "street_unknown", "representation": "street_centerline",
                 "sidewalk_presence": "both"},
                {"u": 2, "v": 3, "kind": "street_unknown", "representation": "street_centerline"}], xy)
    planim = _survey([(LineString([(0, 8), (100, 8)]), 80.0, 1.5, "2025-04-02"),
                      (LineString([(0, -8), (100, -8)]), 50.0, 1.5, "2025-04-02"),
                      (LineString([(50, -20), (50, -60)]), 10.0, 1.5, "2025-04-02"),  # a cross street
                      (LineString([(0, 208), (100, 208)]), 70.0, 1.5, "2025-04-02")])
    enrich.enrich_sidewalk_condition(e, planim, "frederick_sidewalks")
    assert e.iloc[0]["sidewalk_condition"] == 50.0 and e.iloc[0]["sidewalk_condition_status"] == "inferred"
    # no sidewalk on record for the second street: the survey is not read for it
    assert e.iloc[1]["sidewalk_condition_status"] == "unknown"


def test_without_a_condition_survey_condition_stays_unknown():
    xy = {0: (0, 0), 1: (100, 0)}
    e = _edges([{"u": 0, "v": 1}], xy)
    planim = gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"], "CAPTUREYEAR": [0]},
                              geometry=[box(0, -1, 100, 1)], crs=ANALYSIS_CRS)
    enrich.enrich_sidewalk_condition(e, planim, "montgomery_sidewalks")
    assert (e["sidewalk_condition_status"] == "unknown").all()


def test_an_inventory_signal_with_empty_pedestrian_fields_leaves_them_unknown():
    xy = {0: (0.0, 0.0), 1: (100.0, 0.0)}
    e = _edges([{"u": 0, "v": 1, "kind": "crossing", "crossing": "traffic_signals"}], xy)
    signals = _points([(50.0, 5.0)], STATUS=["Active"], LPI=[None], APS=[None], HAWK=[None],
                      ALL_PED_PHASE=[None], PED_RECALL_MODE=[None])
    planim = gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"], "CAPTUREYEAR": [CAPTURE_MS]},
                              geometry=[box(9e5, 9e5, 9e5 + 1, 9e5 + 1)], crs=ANALYSIS_CRS)
    nodes = _points([(9e5, 0.0)], highway=["crossing"], crossing=[None])
    nodes["crossing:signals"] = None
    enrich.enrich_crossing_control(e, signals, planim, nodes, "montgomery_signals")
    assert e["crossing_control"].tolist() == ["signal"]
    for a in ("signal_lpi", "signal_aps", "signal_hawk", "signal_all_ped_phase"):
        assert e[f"{a}_status"].tolist() == ["unknown"], a  # an empty field is not a "no"


def test_a_driveway_down_the_street_from_a_signal_does_not_borrow_it():
    #  0 --- 1 --- 2 --- 3     a street; a service road meets it at node 2, 25 m from the signal
    #        |     |
    #        4     5
    xy = {0: (0, 0), 1: (100, 0), 2: (125, 0), 3: (300, 0), 4: (100, -100), 5: (125, 80), 6: (100, 100)}
    st = {"kind": "street_unknown", "representation": "street_centerline"}
    e = _edges([
        {"u": 0, "v": 1, **st}, {"u": 1, "v": 2, **st}, {"u": 2, "v": 3, **st},
        {"u": 4, "v": 1, **st}, {"u": 1, "v": 6, **st},
        {"u": 5, "v": 2, "kind": "service", "representation": "street_centerline"},
    ], xy)
    nodes = make_nodes(xy)
    nodes["on_removed_road"] = False
    signals = _points([(100.0, 0.0)], STATUS=["Active"])
    roadway = gpd.GeoDataFrame({"TOTALCROSSSECTIONWIDTH": [40.0]}, geometry=[box(9e5, 9e5, 9e5 + 1, 9e5 + 1).boundary],
                               crs=ANALYSIS_CRS)
    ramps = _points([(9e5, 9e5)])
    ps = _points([(9e5, 9e5)], label_type=["CurbRamp"])
    enrich.enrich_implicit_crossings(e, nodes, signals, roadway, ps, ramps)
    assert e["xing_v_control"].iat[0] == "signal"  # the intersection itself
    assert e["xing_v"].iat[5] and e["xing_v_control"].iat[5] is None  # the driveway: unknown


# ---------------------------------------------------------------- sidewalks estimated from a survey


def _one_side_streets(far_y: float):
    """Three streets: a sidewalk 5 m to the left only; one at ``far_y`` m to the left only;
    sidewalks on both sides. No inventory coverage, so a missing side proves nothing."""
    cap = pd.Timestamp("2017-01-01").value // 10**6
    lines = [LineString([(0, 0), (100, 0)]), LineString([(0, 500), (100, 500)]), LineString([(0, 1000), (100, 1000)])]
    edges = gpd.GeoDataFrame({
        "edge_id": [0, 1, 2], "representation": ["street_centerline"] * 3, "kind": ["street_unknown"] * 3,
        "sidewalk_left": [None] * 3, "sidewalk_right": [None] * 3, "covered_planimetric": [False] * 3,
        "oneway": [None] * 3,
    }, geometry=lines, crs=ANALYSIS_CRS)
    polys = [box(-5, 4, 105, 6), box(-5, 500 + far_y - 1, 105, 500 + far_y + 1), box(-5, 1004, 105, 1006), box(-5, 994, 105, 996)]
    planim = gpd.GeoDataFrame({"DESCRIPTION": ["Sidewalk"] * 4, "CAPTUREYEAR": [cap] * 4}, geometry=polys, crs=ANALYSIS_CRS)
    return edges, planim


def test_a_sidewalk_found_on_one_side_is_recorded_as_at_least_one_side_only_near_the_street():
    edges, planim = _one_side_streets(far_y=22.0)
    enrich.enrich_centerline_sidewalks(edges, planim, "survey")
    assert edges["sidewalk_presence"].tolist() == ["at_least_one_side", None, "both"]
    assert edges["sidewalk_presence_status"].tolist() == ["verified", "unknown", "verified"]
    # a street with no sidewalk found anywhere stays unknown: the survey's silence proves nothing
    assert enrich.ONE_SIDE_MAX_OFFSET_M < 22.0


def test_estimated_sidewalk_lines_lie_on_the_survey_side_and_skip_a_side_osm_maps():
    edges, planim = _one_side_streets(far_y=22.0)
    osm = gpd.GeoDataFrame({"edge_id": [3], "representation": ["pedestrian_way"], "kind": ["sidewalk"],
                            "sidewalk_left": [None], "sidewalk_right": [None], "covered_planimetric": [False],
                            "oneway": [None]}, geometry=[LineString([(0, 995), (100, 995)])], crs=ANALYSIS_CRS)
    edges = pd.concat([edges, osm], ignore_index=True)
    enrich.enrich_centerline_sidewalks(edges, planim, "survey")
    lines = enrich.estimate_survey_sidewalk_lines(edges, planim, "survey")
    got = sorted(zip(lines["edge_id"], lines["side"]))
    # street 0: its left side; street 1: too far out to draw; street 2: left only, OSM maps the right
    assert got == [(0, "left"), (2, "left")]
    first = lines[lines["edge_id"] == 0].iloc[0]
    assert 4.0 <= first.geometry.centroid.y <= 6.5 and first["status"] == "inferred" and first["as_of"] == "2017-01-01"


def test_without_a_survey_no_sidewalk_lines_are_estimated():
    edges, _ = _one_side_streets(far_y=22.0)
    assert enrich.estimate_survey_sidewalk_lines(edges, gpd.GeoDataFrame(), None).empty
