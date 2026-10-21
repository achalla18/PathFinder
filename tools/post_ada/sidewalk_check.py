"""Test the post-ADA sidewalk rule, once, against street photos, OSM tags and the city survey.

The rule (``pathfinder.graph.post_ada``: a subdivision street whose every nearby building is
from 1995 on has sidewalks on both sides) and its bar were fixed on 2026-10-21 before any
result was computed (docs/PROGRESS.md, Decisions log). The city's survey records only
sidewalks that exist, so it cannot show a missing one; photos decide:

    python tools/post_ada/sidewalk_check.py sample        # the blind photo sheet (and its key)
    python tools/post_ada/sidewalk_check.py thumbs <dir>  # each edge's photos on one image
    (judge every row of reports/<region>/post_ada/sidewalk_sample.csv: both / one_side / none / unclear)
    python tools/post_ada/sidewalk_check.py score         # the one scored run, all three tests

The sheet mixes edges the rule would fill with control edges it leaves, unlabelled; the key
(sidewalk_key.csv) is read only by ``score``. Needs PF_MAPILLARY_TOKEN in the repo's
.env. Photo ids and dates are kept, never the uploader. Internal: the survey helps choose the
edges and is one of the tests (rule 7).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from PIL import Image, ImageDraw

from pathfinder.analysis.coverage import BAR, accessibility_bar
from pathfinder.config import GRAPH_DIR, REPORTS_DIR, WGS84
from pathfinder.fetch import raw_path
from pathfinder.graph import post_ada
from pathfinder.sources import REGION

sys.path.insert(0, str(Path(__file__).parent))
from evaluate import wilson_lb  # noqa: E402
from mapillary_check import GRAPH, TILE_ZOOM, TILES, _tile  # noqa: E402

import mapbox_vector_tile  # noqa: E402

OUT = REPORTS_DIR / "post_ada"
SHEET, KEY = OUT / "sidewalk_sample.csv", OUT / "sidewalk_key.csv"
SEED = 202610212
N_RULE, N_CONTROL = 100, 25
PHOTO_RADIUS_M = 15.0  # within a street's half-width plus a sidewalk: the photo is on this street
PHOTOS_PER_EDGE = 4
ALONG_MAX_DEG = 30.0  # a camera within this of the street's direction sees both sides
VERDICTS = ("both", "one_side", "none", "unclear")
# the bar (Decisions log, 2026-10-21)
PHOTO_MIN_JUDGED, PHOTO_MAX_UNCLEAR = 75, 30
MIN_PRECISION, MIN_WILSON_LB = 95.0, 92.0
OSM_MIN_N, SURVEY_MIN_N, SURVEY_MIN_PRECISION = 30, 100, 90.0
SURVEY_SOURCE = f"{REGION.id}_sidewalks"


def edges_and_rule() -> gpd.GeoDataFrame:
    """Candidate edges with the rule computed from parcels alone (n_built, oldest, post_ada)."""
    e = gpd.read_parquet(GRAPH_DIR / "edges.parquet")
    e = e[post_ada.sidewalk_candidates(e)]
    e = e[~e.geometry.to_wkb().duplicated()]
    # the parcels play a role in the pipeline only once the rule has passed; read the source itself
    parcels = gpd.read_parquet(raw_path(f"{REGION.id}_parcels")).to_crs(e.crs)
    nb = post_ada.neighbourhood(e.geometry, post_ada.built_parcels(parcels))
    return e.join(nb)


def photos(area_ll: gpd.GeoSeries, token: str) -> gpd.GeoDataFrame:
    """Every Mapillary photo in the coverage tiles over the area: id, date, heading, panorama.
    The uploader's id, which the tiles carry, is never kept."""
    z, n = TILE_ZOOM, 2 ** TILE_ZOOM
    w, s, e, nn = area_ll.total_bounds
    x0, y0 = _tile(nn, w, z)
    x1, y1 = _tile(s, e, z)
    rows = []
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
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
                             "heading": pr.get("compass_angle"), "pano": bool(pr.get("is_pano")),
                             "geometry": gpd.points_from_xy([lon], [lat])[0]})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=WGS84)


def _bearing_deg(g) -> float:
    """The edge's direction from north, 0-180 (a street runs both ways)."""
    c = np.asarray(g.coords)
    return math.degrees(math.atan2(c[-1, 0] - c[0, 0], c[-1, 1] - c[0, 1])) % 180


def _weighted_sample(df: pd.DataFrame, k: int, w: np.ndarray) -> pd.DataFrame:
    """k rows without replacement, each drawn with probability proportional to w
    (Efraimidis-Spirakis: the k largest u ** (1 / w)); pandas refuses large weights."""
    u = np.random.default_rng(SEED).random(len(df))
    return df.iloc[np.argsort(-u ** (1 / w))[:k]]


def sample(token: str) -> None:
    e = edges_and_rule()
    unknown = e["sidewalk_presence_status"].eq("unknown")
    rule = e[unknown & e["post_ada"]].assign(group="rule")
    ctrl = e[unknown & ~e["post_ada"] & e["n_built"].ge(post_ada.MIN_BUILT_PARCELS)].assign(group="control")
    pool = pd.concat([rule, ctrl])
    ph = photos(pool.geometry.to_crs(WGS84), token).to_crs(e.crs)
    j = gpd.sjoin(gpd.GeoDataFrame(pool[["edge_id", "group", "oldest", "length_m"]], geometry=pool.geometry),
                  ph, predicate="dwithin", distance=PHOTO_RADIUS_M)
    j = j[pd.to_datetime(j["taken"]).dt.year > j["oldest"]]
    ok = pool[pool["edge_id"].isin(j["edge_id"])]
    pick = pd.concat([_weighted_sample(g, k, g["length_m"].to_numpy())
                      for g, k in ((ok[ok["group"].eq("rule")], N_RULE), (ok[ok["group"].eq("control")], N_CONTROL))])
    pick = pick.sample(frac=1, random_state=SEED).reset_index(drop=True)
    mid = pick.geometry.interpolate(0.5, normalized=True).to_crs(WGS84)
    sheet, key = [], []
    for n, (r, pt) in enumerate(zip(pick.itertuples(), mid), start=1):
        mine = j[j["edge_id"].eq(r.edge_id)].copy()
        b = _bearing_deg(r.geometry)
        off = (mine["heading"].astype(float) - b) % 180
        mine["along"] = mine["pano"] | np.minimum(off, 180 - off).le(ALONG_MAX_DEG)
        mine = mine.sort_values(["along", "taken"], ascending=False).head(PHOTOS_PER_EDGE)
        sheet.append({"n": n, "lat": round(pt.y, 6), "lon": round(pt.x, 6), "photo_ids": " ".join(mine["photo_id"]),
                      "newest_photo": str(mine["taken"].max()), "verdict": "", "notes": ""})
        key.append({"n": n, "edge_id": int(r.edge_id), "group": r.group, "oldest_building": int(r.oldest),
                    "length_m": round(r.length_m, 1), "inside_line": not bool(r.outside_region)})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sheet).to_csv(SHEET, index=False)
    pd.DataFrame(key).to_csv(KEY, index=False)
    print(f"{len(rule)} edges the rule would fill, {len(ctrl)} controls; {len(ph)} photos; "
          f"with a usable photo: {ok['group'].eq('rule').sum()} rule, {ok['group'].eq('control').sum()} control; "
          f"sheet of {len(sheet)} written (the key is not printed)")


def thumbs(token: str, dest: Path) -> None:
    """One image per sheet row: its photos side by side, captioned by row number, and each
    photo by where it stands and looks relative to the edge (a photo at a corner may show the
    cross street). Only the key's edge ids are read, to place the edge; never its groups."""
    s = pd.read_csv(SHEET, dtype=str, keep_default_na=False)
    eid = pd.read_csv(KEY, usecols=["n", "edge_id"], dtype={"n": str}).set_index("n")["edge_id"]
    edges = gpd.read_parquet(GRAPH_DIR / "edges.parquet").set_index("edge_id")
    raw = dest / "photos"
    raw.mkdir(parents=True, exist_ok=True)
    for _, r in s.iterrows():
        g = edges.geometry.loc[eid[r["n"]]]
        b = _bearing_deg(g)
        ims, caps = [], []
        for pid in r["photo_ids"].split():
            f = raw / f"{pid}.jpg"
            if not f.exists():
                meta = requests.get(f"{GRAPH}/{pid}", timeout=60, params={"access_token": token, "fields": "thumb_1024_url"}).json()
                if "error" in meta:
                    sys.exit(f"Mapillary refused photo {pid}: {meta['error'].get('message')}")
                f.write_bytes(requests.get(meta["thumb_1024_url"], timeout=60).content)
            ims.append(Image.open(f).convert("RGB"))
            m = requests.get(f"{GRAPH}/{pid}", timeout=60, params={
                "access_token": token, "fields": "computed_geometry,computed_compass_angle,compass_angle,captured_at,is_pano"}).json()
            xy = (m.get("computed_geometry") or {}).get("coordinates")
            ang = m.get("computed_compass_angle", m.get("compass_angle"))
            pt = gpd.GeoSeries(gpd.points_from_xy([xy[0]], [xy[1]]), crs=WGS84).to_crs(edges.crs).iloc[0] if xy else None
            d = f"{pt.distance(g):.0f} m from edge, {100 * g.project(pt, normalized=True):.0f}% along" if pt is not None else "?"
            if m.get("is_pano"):
                look = "panorama"
            elif ang is None:
                look = "heading ?"
            else:
                off = (float(ang) - b) % 180
                look = f"{min(off, 180 - off):.0f} deg off the street"
            caps.append(f"{m.get('captured_at') and str(pd.Timestamp(int(m['captured_at']), unit='ms').date())}, {d}, {look}")
        h, cap_h = 384, 16
        ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
        cols = 2
        w = max(sum(im.width for im in ims[i:i + cols]) for i in range(0, len(ims), cols))
        rows = math.ceil(len(ims) / cols)
        out = Image.new("RGB", (w, rows * (h + cap_h) + 24), "white")
        draw = ImageDraw.Draw(out)
        for k, im in enumerate(ims):
            x = sum(o.width for o in ims[k - k % cols:k])
            y = 24 + (k // cols) * (h + cap_h)
            draw.text((x + 6, y + 2), f"photo {k + 1}: {caps[k]}", fill="black")
            out.paste(im, (x, y + cap_h))
        draw.text((6, 6), f"#{r['n']}  ({r['lat']}, {r['lon']})  edge {g.length:.0f} m long, runs {b:.0f} deg from north",
                  fill="black")
        out.save(dest / f"{int(r['n']):03d}.jpg", quality=85)


def _score(correct: pd.Series) -> dict:
    k, n = int(correct.sum()), len(correct)
    return {"n": n, "correct": k, "precision_pct": round(100 * k / n, 1) if n else None, "wilson_lb_pct": round(wilson_lb(k, n), 1)}


def score() -> None:
    s = pd.read_csv(SHEET, dtype=str, keep_default_na=False)
    bad = s[~s["verdict"].isin(VERDICTS)]
    if len(bad):
        sys.exit(f"{len(bad)} rows have no verdict from {VERDICTS} (first: row {bad['n'].iat[0]}); judge every row first")
    sk = s.merge(pd.read_csv(KEY, dtype={"n": str}), on="n")
    e = edges_and_rule()
    pos = e[e["post_ada"]]

    ph = sk[sk["group"].eq("rule")]
    judged = ph[ph["verdict"].ne("unclear")]
    t1 = _score(judged["verdict"].eq("both")) | {"sampled": len(ph), "unclear": int(ph["verdict"].eq("unclear").sum()),
                                                 "verdicts": ph["verdict"].value_counts().to_dict()}
    ctrl = sk[sk["group"].eq("control")]
    t1_ctrl = ctrl["verdict"].value_counts().to_dict()
    osm = pos[pos["sidewalk_presence_source"].eq("osm_" + REGION.id)]
    t2 = _score(osm["sidewalk_presence"].eq("both")) | {"values": osm["sidewalk_presence"].value_counts().to_dict()}
    sv = pos[pos["sidewalk_presence_source"].eq(SURVEY_SOURCE)]
    t3 = _score(sv["sidewalk_presence"].eq("both")) | {"values": sv["sidewalk_presence"].value_counts().to_dict()}
    checks = {
        "1_photos": t1["sampled"] >= N_RULE and t1["n"] >= PHOTO_MIN_JUDGED and t1["unclear"] <= PHOTO_MAX_UNCLEAR
                    and (t1["precision_pct"] or 0) >= MIN_PRECISION and t1["wilson_lb_pct"] >= MIN_WILSON_LB,
        "2_osm_tags": True if t2["n"] < OSM_MIN_N else (t2["precision_pct"] or 0) >= MIN_PRECISION,
        "3_survey": t3["n"] >= SURVEY_MIN_N and (t3["precision_pct"] or 0) >= SURVEY_MIN_PRECISION,
    }
    passed = all(checks.values())

    # what the rule would fill, and criterion 3 with it (not part of the bar)
    full = gpd.read_parquet(GRAPH_DIR / "edges.parquet")
    fill_ids = set(pos.loc[pos["sidewalk_presence_status"].eq("unknown"), "edge_id"])
    fill = full["edge_id"].isin(fill_ids) & full["sidewalk_presence_status"].eq("unknown")
    stats = {"largest_component_share_of_length": float("nan")}
    before = accessibility_bar(full, stats)[2]
    after_e = full.copy()
    after_e.loc[fill, "sidewalk_presence"], after_e.loc[fill, "sidewalk_presence_status"] = post_ada.SIDEWALK_CLAIM, "inferred"
    after = accessibility_bar(after_e, stats)[2]
    inside = fill & ~full["outside_region"].astype(bool)
    fills = {"edges": int(fill.sum()), "km": round(full.loc[fill, "length_m"].sum() / 1000, 1),
             "km_inside_line": round(full.loc[inside, "length_m"].sum() / 1000, 1),
             "criterion_3_before_pct": before["value_pct"], "criterion_3_after_pct": after["value_pct"],
             "criterion_3_bar_pct": BAR["sidewalk_evidence"]}

    out = {"bar_passed": passed, "checks": checks, "photos": t1, "photo_controls": t1_ctrl, "osm_tags": t2, "survey": t3,
           "fills": fills, "protocol": {"highways": list(post_ada.SIDEWALK_HIGHWAYS), "year": post_ada.POST_ADA_YEAR,
                                        "radius_m": post_ada.PARCEL_RADIUS_M, "min_built": post_ada.MIN_BUILT_PARCELS,
                                        "seed": SEED, "photo_radius_m": PHOTO_RADIUS_M}}
    (OUT / "sidewalk_evaluation.json").write_text(json.dumps(out, indent=1))
    row = lambda name, t: f"| {name} | {t['n']} | {t['correct']} | {t['precision_pct']} | {t['wilson_lb_pct']} |"  # noqa: E731
    md = [f"# Post-ADA sidewalk rule: evaluation ({REGION.name})", "",
          "_Generated by `tools/post_ada/sidewalk_check.py score`. Do not edit by hand. **Internal:** the City of "
          "Frederick's survey helps choose the edges and is test 3 (rule 7)._", "",
          f"Rule: a `{'`, `'.join(post_ada.SIDEWALK_HIGHWAYS)}` street with at least {post_ada.MIN_BUILT_PARCELS} built "
          f"parcels within {post_ada.PARCEL_RADIUS_M:.0f} m, the oldest from {post_ada.POST_ADA_YEAR} or later, has "
          f"sidewalks on both sides.", "",
          f"**Bar: {'PASSED' if passed else 'NOT PASSED'}** ({', '.join(f'{k}: {v}' for k, v in checks.items())})", "",
          "| test | edges | correct (both sides) | precision % | Wilson 95% lower bound % |", "|---|---|---|---|---|",
          row("1. street photos (judged, rule-positive)", t1), row("2. OSM tags", t2), row("3. city survey (positive-only truth)", t3), "",
          f"Photo verdicts, rule-positive ({t1['sampled']} sampled): {t1['verdicts']}. Controls (rule leaves them): {t1_ctrl}.", "",
          f"Would fill {fills['edges']} edges, {fills['km']} km ({fills['km_inside_line']} km inside the line). "
          f"Criterion 3 would go from {fills['criterion_3_before_pct']}% to {fills['criterion_3_after_pct']}% "
          f"(bar {fills['criterion_3_bar_pct']:.0f}%; not part of the rule's bar).", ""]
    (OUT / "sidewalk_evaluation.md").write_text("\n".join(md), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    cmd = sys.argv[1:2]
    if cmd == ["score"]:
        score()
        sys.exit()
    tok = os.environ.get("PF_MAPILLARY_TOKEN")
    if not tok:
        sys.exit("PF_MAPILLARY_TOKEN is not set (repo .env)")
    if cmd == ["sample"]:
        sample(tok)
    elif cmd == ["thumbs"]:
        thumbs(tok, Path(sys.argv[2]))
    else:
        sys.exit(__doc__)
