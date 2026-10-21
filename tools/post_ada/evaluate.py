"""Score the post-ADA ramp rule against the City of Frederick's ramp survey, once.

The rule (``pathfinder.graph.post_ada``) is computed from parcels alone, as if the survey did not
exist, then compared with the survey where the survey has records:

- junctions inside the city line with at least 2 survey records within 20 m: correct when
  none of them is "No ramp";
- crossing ends with a survey record within 8 m: correct when the nearest is a ramp.

The bar was fixed on 2026-10-21 before any parcel was fetched (docs/PROGRESS.md, Decisions
log). Criterion 4 of that bar (a street-level photo check) is separate.

Usage (after `pf fetch` and `pf enrich`, PF_REGION=frederick):  python tools/post_ada/evaluate.py
Writes reports/<region>/post_ada/ (internal: it is built on the city's survey, rule 7).
"""
from __future__ import annotations

import json
import math
import sys

import geopandas as gpd
import pandas as pd

from pathfinder.config import ANALYSIS_CRS, GRAPH_DIR, REPORTS_DIR
from pathfinder.fetch import raw_path
from pathfinder.graph import post_ada, roles
from pathfinder.graph.enrich import JUNCTION_RAMP_RADIUS_M, RAMP2010_RADIUS_M, _crossing_outer_ends
from pathfinder.sources import REGION

OUT = REPORTS_DIR / "post_ada"
MIN_PRECISION = 95.0
MIN_WILSON_LB = 92.0
MIN_N = 100
NEW_YEAR, NEW_MIN_N = 2005, 30  # bar criterion 3: the newest neighbourhoods, like the blocked corners


def wilson_lb(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    return 100 * (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def score(df: pd.DataFrame) -> dict:
    pos = df[df["post_ada"]]
    k, n = int(pos["correct"].sum()), len(pos)
    return {"rule_positive": n, "correct": k, "precision_pct": round(100 * k / n, 1) if n else None,
            "wilson_lb_pct": round(wilson_lb(k, n), 1), "test_places": len(df)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    edges = gpd.read_parquet(GRAPH_DIR / "edges.parquet")
    nodes = gpd.read_parquet(GRAPH_DIR / "nodes.parquet").set_index("node_id")
    line = gpd.read_parquet(raw_path(REGION.boundary)).to_crs(ANALYSIS_CRS).union_all()
    # the parcels play a role in the pipeline only once the rule has passed; read the source itself
    parcels = gpd.read_parquet(raw_path(f"{REGION.id}_parcels")).to_crs(ANALYSIS_CRS)
    built = post_ada.built_parcels(parcels)
    ramps, _ = roles.read("ramps")
    is_ramp = ramps["KERB"].eq("ramp_present")

    # --- places: flagged junction nodes and the outer ends of mapped crossings
    jn_ids = sorted(set(edges.loc[edges["xing_u"].fillna(False), "u"]) | set(edges.loc[edges["xing_v"].fillna(False), "v"]))
    jn = gpd.GeoSeries(nodes.geometry.loc[jn_ids].values, index=pd.Index(jn_ids, name="node_id"), crs=edges.crs)
    _, end_a, end_b = _crossing_outer_ends(edges)
    ends = gpd.GeoSeries(pd.concat([end_a, end_b]).values, crs=edges.crs)
    J = post_ada.neighbourhood(jn, built).assign(inside=jn.within(line).to_numpy())
    C = post_ada.neighbourhood(ends, built).assign(inside=ends.within(line).to_numpy())

    # --- truth from the survey, where it has records
    rec = gpd.GeoDataFrame({"ramp": is_ramp.to_numpy()}, geometry=ramps.geometry.values, crs=ramps.crs)
    zone = gpd.GeoDataFrame({"node_id": jn.index}, geometry=jn.buffer(JUNCTION_RAMP_RADIUS_M).values, crs=edges.crs)
    jr = gpd.sjoin(rec, zone, predicate="within").groupby("node_id")["ramp"].agg(["size", "all"])
    J = J.join(jr)
    jtest = J[J["inside"] & J["size"].ge(2)].assign(correct=lambda d: d["all"].astype(bool))
    near = gpd.sjoin_nearest(gpd.GeoDataFrame(geometry=ends, crs=edges.crs), rec, how="inner",
                             max_distance=RAMP2010_RADIUS_M, distance_col="d")
    near = near.sort_values("d")[~near.sort_values("d").index.duplicated()]
    C = C.join(near["ramp"])
    ctest = C[C["ramp"].notna()].assign(correct=lambda d: d["ramp"].astype(bool))

    sj, sc = score(jtest), score(ctest)
    both = pd.concat([jtest[["post_ada", "oldest", "correct"]], ctest[["post_ada", "oldest", "correct"]]])
    sn = score(both[both["oldest"] >= NEW_YEAR])
    checks = {
        "1_junctions": sj["rule_positive"] >= MIN_N and (sj["precision_pct"] or 0) >= MIN_PRECISION and sj["wilson_lb_pct"] >= MIN_WILSON_LB,
        "2_crossing_ends": sc["rule_positive"] >= MIN_N and (sc["precision_pct"] or 0) >= MIN_PRECISION and sc["wilson_lb_pct"] >= MIN_WILSON_LB,
        "3_newest": sn["rule_positive"] >= NEW_MIN_N and (sn["precision_pct"] or 0) >= MIN_PRECISION,
    }
    passed = all(checks.values())

    # --- what the rule would fill: places whose curb no source records today
    unknown_j = set(edges.loc[edges["xing_u"].fillna(False) & edges["xing_u_kerb"].eq("unknown"), "u"]) | \
        set(edges.loc[edges["xing_v"].fillna(False) & edges["xing_v_kerb"].eq("unknown"), "v"])
    Ju = J.loc[J.index.isin(unknown_j)]
    fills = {"unknown_junctions": len(Ju), "post_ada": int(Ju["post_ada"].sum()),
             "post_ada_inside_line": int((Ju["post_ada"] & Ju["inside"]).sum()),
             "post_ada_outside_line": int((Ju["post_ada"] & ~Ju["inside"]).sum())}
    wl = pd.read_csv(REPORTS_DIR / "blocked" / "worklist.csv")
    wl_j = wl[wl["place"].str.startswith("junction:")]
    wl_ids = wl_j["place"].str.split(":").str[1].astype("int64")
    wl_post = J.reindex(wl_ids)
    worklist = {"junctions": len(wl_j), "post_ada": int(wl_post["post_ada"].fillna(False).sum()),
                "by_place": {f"junction:{i}": {"n_built": int(r.n_built), "oldest": None if pd.isna(r.oldest) else int(r.oldest),
                                               "post_ada": bool(r.post_ada)} for i, r in wl_post.iterrows()}}

    out = {"bar_passed": passed, "checks": checks, "junctions": sj, "crossing_ends": sc, f"oldest_{NEW_YEAR}_or_later": sn,
           "parcels_built": len(built), "parcel_as_of": post_ada.as_of(parcels), "fills": fills, "worklist": worklist,
           "protocol": {"year": post_ada.POST_ADA_YEAR, "radius_m": post_ada.PARCEL_RADIUS_M, "min_built": post_ada.MIN_BUILT_PARCELS}}
    (OUT / "evaluation.json").write_text(json.dumps(out, indent=1))
    # test-set years, to see how far the test reaches into the newest neighbourhoods
    yrs = pd.cut(both.loc[both["post_ada"], "oldest"], [1994, 1999, 2004, 2009, 2014, 2026]).value_counts().sort_index()
    row = lambda name, s: f"| {name} | {s['test_places']} | {s['rule_positive']} | {s['correct']} | {s['precision_pct']} | {s['wilson_lb_pct']} |"  # noqa: E731
    md = [f"# Post-ADA ramp rule: evaluation ({REGION.name})", "",
          "_Generated by `tools/post_ada/evaluate.py`. Do not edit by hand. **Internal:** scored against the City of "
          "Frederick's ramp survey (rule 7)._", "",
          f"Rule: at least {post_ada.MIN_BUILT_PARCELS} built parcels within {post_ada.PARCEL_RADIUS_M:.0f} m, the oldest from "
          f"{post_ada.POST_ADA_YEAR} or later. Parcels: {len(built):,} with a year built (SDAT, {post_ada.as_of(parcels)}).", "",
          f"**Bar: {'PASSED' if passed else 'NOT PASSED'}** ({', '.join(f'{k}: {v}' for k, v in checks.items())})", "",
          "| test | places with survey truth | rule-positive | correct | precision % | Wilson 95% lower bound % |",
          "|---|---|---|---|---|---|", row("1. junctions (≥ 2 records within 20 m)", sj), row("2. crossing ends (record within 8 m)", sc),
          row(f"3. oldest building {NEW_YEAR} or later", sn), "",
          "Rule-positive test places by the oldest nearby building:", "", "| oldest building | places |", "|---|---|",
          *[f"| {iv.left + 1:.0f}–{iv.right:.0f} | {n} |" for iv, n in yrs.items()], "",
          f"Would fill: {fills['post_ada']} of {fills['unknown_junctions']} junctions with no curb record "
          f"({fills['post_ada_inside_line']} inside the line, {fills['post_ada_outside_line']} outside). "
          f"Worklist junctions it calls post-ADA: {worklist['post_ada']} of {worklist['junctions']}.", ""]
    (OUT / "evaluation.md").write_text("\n".join(md), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")  # the report has ≥ and en dashes; Windows consoles default to cp1252
    print("\n".join(md))


if __name__ == "__main__":
    main()
