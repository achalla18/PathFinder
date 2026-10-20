"""Score the Tile2Net pilot against the frozen test set (bar fixed in docs/PROGRESS.md).

Usage: python score.py <frederick_pilot_results.zip> <testset_labelled.parquet>

Decision rule (fixed before any detection was seen): on a test street side, detected sidewalk
polygons found by the side probes (``build.sidewalk_side_coverage``) within 15 m covering at
least 60% of it -> "sidewalk"; at most 10% -> "none"; otherwise the detector abstains.
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from pathfinder.graph.build import sidewalk_side_coverage

REACH_M = 15.0
YES, NO = 0.6, 0.1
MIN_ANSWERS, MIN_PRECISION = 30, 0.95


def detected_sidewalks(zip_path: Path) -> gpd.GeoDataFrame:
    """Every sidewalk polygon Tile2Net wrote, in EPSG:26985."""
    tmp = Path(tempfile.mkdtemp())
    zipfile.ZipFile(zip_path).extractall(tmp)
    frames = []
    for f in list(tmp.rglob("*.shp")) + list(tmp.rglob("*.geojson")) + list(tmp.rglob("*.gpkg")):
        g = gpd.read_file(f)
        if g.empty or not g.geom_type.isin(["Polygon", "MultiPolygon"]).any():
            continue
        g = g[g.geom_type.isin(["Polygon", "MultiPolygon"])]
        kind = next((c for c in ("f_type", "feature", "class", "type") if c in g), None)
        if kind is not None:
            g = g[g[kind].astype(str).str.contains("sidewalk", case=False)]
        elif "sidewalk" not in f.name.lower():
            continue
        frames.append(g.to_crs(26985)[["geometry"]].assign(file=f.name))
    if not frames:
        raise SystemExit("no sidewalk polygons found in the results zip")
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=26985)


def answers(test: gpd.GeoDataFrame, polys: gpd.GeoDataFrame) -> pd.Series:
    cl, cr = sidewalk_side_coverage(test.geometry, polys.geometry, REACH_M, REACH_M)
    cov = np.where(test["side"].eq("left"), cl, cr)
    return pd.Series(np.where(cov >= YES, "sidewalk", np.where(cov <= NO, "none", "abstain")), index=test.index)


def main(zip_path: str, test_path: str) -> None:
    test = gpd.read_parquet(test_path)
    test = test[test["truth"].notna()].copy()
    test["answer"] = answers(test, detected_sidewalks(Path(zip_path)))
    core = test[test["cls"].eq("pos_agree") | test["truth"].eq("none")]  # the bar's test set
    rows = []
    for name, df in (("bar test set (survey+OSM sidewalks, hand-labelled none)", core),
                     ("also: silent sides with a sidewalk (hand-labelled)", test[test["cls"].eq("silent") & test["truth"].eq("sidewalk")])):
        print(f"\n== {name}: {len(df)} sides")
        print(pd.crosstab(df["truth"], df["answer"], margins=True))
    # Amended 2026-10-16 before any detection existed: precision is measured over every
    # labelled side, the silent sides that do have a sidewalk included. Measured on the core
    # set alone, a detector that misses exactly the sidewalks the survey misses would pass
    # (the survey itself did, in the dry run).
    for ans in ("sidewalk", "none"):
        a = test[test["answer"].eq(ans)]
        prec = (a["truth"] == ans).mean() if len(a) else float("nan")
        ok = len(a) >= MIN_ANSWERS and prec >= MIN_PRECISION
        rows.append((ans, len(a), prec, ok))
        print(f'"{ans}" answers: {len(a)}, correct {prec:.1%} -> {"meets" if ok else "misses"} '
              f"(need >= {MIN_ANSWERS} answers, >= {MIN_PRECISION:.0%} correct)")
    print("\nBAR:", "PASSES (then the 20-answer imagery check)" if all(r[3] for r in rows) else "FAILS")
    test.drop(columns="geometry").to_csv(Path(test_path).with_name("pilot_answers.csv"), index=False)


if __name__ == "__main__":
    main(*sys.argv[1:3])
