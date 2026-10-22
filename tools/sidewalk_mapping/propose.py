"""Sidewalk tag proposals from street photos, for a person to review before anything is uploaded.

For each OSM street on the worklist (``make_worklist.py``), in its first areas, this finds the
Mapillary photos taken on the street that look along it, picks a few spread along its length
(newest first), and puts them on one image per street, each photo captioned with whether it
looks with the way's direction (photo-left is the way's left) or against it. Someone judges each
street (both / left / right / no / unclear), a team member reviews every proposal on the review
page, and only approved tags are uploaded, by a person, in iD (field/sidewalk_mapping.md).

    python tools/sidewalk_mapping/propose.py photos --areas 10     # sheet + one image per street
    (judge each row of reports/<region>/sidewalk_mapping/proposals.csv)
    python tools/sidewalk_mapping/propose.py review                 # the review page

Images and the review page go to <data dir>/sidewalk_review/ (Mapillary's photos stay out of
the repo). Photo ids and dates are kept, never the uploader. Internal: the worklist depends on the
city's survey (rule 7); the tags come only from the photos.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import sys
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from PIL import Image, ImageDraw

from pathfinder.config import ANALYSIS_CRS, DATA_DIR, INTERIM_DIR, REPORTS_DIR, WGS84

sys.path.insert(0, str(Path(__file__).parents[1] / "post_ada"))
from mapillary_check import GRAPH  # noqa: E402
from sidewalk_check import photos as tile_photos  # noqa: E402

OUT = REPORTS_DIR / "sidewalk_mapping"
SHEET = OUT / "proposals.csv"
REVIEW = DATA_DIR / "sidewalk_review"
PHOTO_RADIUS_M = 12.0  # on the street itself: a car or walker on it, not on the next street
ALONG_MAX_DEG = 35.0  # looking along the street (either way) shows both sides
MAX_PHOTOS = 6
PARTS = 3  # photos are picked from each third of a way, so a sidewalk ending partway shows
VERDICTS = ("both", "left", "right", "no", "unclear")
TAG = {"both": "sidewalk=both", "left": "sidewalk=left", "right": "sidewalk=right", "no": "sidewalk=no"}


def _bearing(p0, p1) -> float:
    return math.degrees(math.atan2(p1[0] - p0[0], p1[1] - p0[1])) % 360


def _local_bearing(line, frac: float) -> float:
    """The way's direction (from north, 0-360, in node order) at a fraction of its length."""
    d = frac * line.length
    a, b = line.interpolate(max(0.0, d - 5)), line.interpolate(min(line.length, d + 5))
    return _bearing((a.x, a.y), (b.x, b.y))


def photos_cmd(token: str, n_areas: int) -> None:
    wl = pd.read_csv(OUT / "worklist.csv")
    wl = wl[wl["area_rank"] <= n_areas]
    ways = gpd.read_parquet(INTERIM_DIR / "osm_ways.parquet").set_index("osm_way_id").to_crs(ANALYSIS_CRS)
    ways = ways.loc[ways.index.intersection(wl["osm_way_id"])]
    ph = tile_photos(ways.geometry.to_crs(WGS84), token).to_crs(ANALYSIS_CRS)
    j = gpd.sjoin(gpd.GeoDataFrame(geometry=ways.geometry), ph, predicate="dwithin", distance=PHOTO_RADIUS_M)
    rows, sheet_dir = [], REVIEW / "streets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    for r in wl.itertuples():
        line = ways.geometry.get(r.osm_way_id)
        cand = []
        if line is not None and r.osm_way_id in j.index:
            for p in j.loc[[r.osm_way_id]].itertuples():
                frac = line.project(ph.geometry.loc[p.index_right], normalized=True)  # the join keeps the way's geometry
                off = (float(p.heading) - _local_bearing(line, frac)) % 360 if p.heading is not None else np.nan
                look = "with" if min(off, 360 - off) <= ALONG_MAX_DEG else "against" if abs(off - 180) <= ALONG_MAX_DEG else None
                if look:
                    cand.append({"photo_id": p.photo_id, "taken": p.taken, "frac": frac, "look": look, "pano": p.pano})
        c = pd.DataFrame(cand)
        pick = []
        if len(c):
            c["part"] = np.minimum((c["frac"] * PARTS).astype(int), PARTS - 1)
            c = c.sort_values("taken", ascending=False)
            pick = list(c.groupby("part").head(1).sort_values("frac").itertuples())
            rest = c[~c["photo_id"].isin([p.photo_id for p in pick])]
            pick += list(rest.head(MAX_PHOTOS - len(pick)).itertuples())
            pick = sorted(pick, key=lambda p: p.frac)[:MAX_PHOTOS]
        rows.append({"area_rank": r.area_rank, "osm_way_id": r.osm_way_id, "name": r.name, "highway": r.highway,
                     "length_m": round(line.length) if line is not None else None, "unknown_m": r.unknown_m,
                     "photo_ids": " ".join(p.photo_id for p in pick),
                     "photo_looks": " ".join(f"{p.look}@{p.frac:.2f}" for p in pick),
                     "newest_photo": str(max((p.taken for p in pick), default="")), "verdict": "" if pick else "unclear",
                     "notes": "" if pick else "no photo on the street looking along it"})
        if pick:
            _sheet(token, r, line, pick, sheet_dir / f"{r.osm_way_id}.jpg")
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(SHEET, index=False)
    with_photos = sum(1 for x in rows if x["photo_ids"])
    print(f"{len(rows)} streets in areas 1-{n_areas}; {with_photos} have photos looking along them "
          f"({sum(x['unknown_m'] for x in rows if x['photo_ids']) / 1000:.1f} km); images in {sheet_dir}")


def _thumb_url(token: str, photo_id: str, tries: int = 4) -> str:
    """The photo's download link. Mapillary's graph API fails now and then ("unexpected error,
    retry later"), so it is asked again with a growing wait before giving up."""
    for k in range(tries):
        meta = requests.get(f"{GRAPH}/{photo_id}", timeout=60, params={"access_token": token, "fields": "thumb_1024_url"}).json()
        if "error" not in meta:
            return meta["thumb_1024_url"]
        time.sleep(5 * 2 ** k)
    sys.exit(f"Mapillary refused photo {photo_id} {tries} times: {meta['error'].get('message')}")


def _sheet(token: str, r, line, pick, out: Path) -> None:
    raw = REVIEW / "photos"
    raw.mkdir(parents=True, exist_ok=True)
    ims = []
    for p in pick:
        f = raw / f"{p.photo_id}.jpg"
        if not f.exists():
            f.write_bytes(requests.get(_thumb_url(token, p.photo_id), timeout=60).content)
        ims.append(Image.open(f).convert("RGB"))
    h, cap_h, cols = 384, 16, 2
    ims = [im.resize((int(im.width * h / im.height), h)) for im in ims]
    w = max(sum(im.width for im in ims[i:i + cols]) for i in range(0, len(ims), cols))
    sheet = Image.new("RGB", (w, math.ceil(len(ims) / cols) * (h + cap_h) + 24), "white")
    d = ImageDraw.Draw(sheet)
    for k, (im, p) in enumerate(zip(ims, pick)):
        x, y = sum(o.width for o in ims[k - k % cols:k]), 24 + (k // cols) * (h + cap_h)
        side = "photo-left = way LEFT" if p.look == "with" else "photo-left = way RIGHT"
        d.text((x + 6, y + 2), f"{k + 1}: {p.taken}, {100 * p.frac:.0f}% along, looks {p.look.upper()} the way ({side})"
               + (" [panorama: centre looks that way]" if p.pano else ""), fill="black")
        sheet.paste(im, (x, y + cap_h))
    d.text((6, 6), f"way {r.osm_way_id}  {r.name if isinstance(r.name, str) else '(unnamed)'}  {r.highway}  "
           f"{line.length:.0f} m", fill="black")
    sheet.save(out, quality=85)


def review_cmd() -> None:
    s = pd.read_csv(SHEET, dtype={"osm_way_id": str}, keep_default_na=False)
    bad = s[~s["verdict"].isin(VERDICTS)]
    if len(bad):
        sys.exit(f"{len(bad)} rows have no verdict from {VERDICTS}; judge every row first")
    p = s[s["verdict"].ne("unclear")]
    items = [{"way": r.osm_way_id, "name": r.name or "(unnamed)", "highway": r.highway, "area": int(r.area_rank),
              "m": int(float(r.unknown_m)), "tag": TAG[r.verdict], "notes": r.notes,
              "img": f"streets/{r.osm_way_id}.jpg", "photos": r.photo_ids.split(),
              # a decision holds only for this exact proposal: a changed tag or photo set needs a new one
              "fp": f"{r.osm_way_id}|{TAG[r.verdict]}|{r.photo_ids}"} for r in p.itertuples()]
    REVIEW.mkdir(parents=True, exist_ok=True)
    (REVIEW / "index.html").write_text(_PAGE.replace("__ITEMS__", json.dumps(items).replace("<", "\\u003c")), encoding="utf-8")
    print(f"{len(items)} proposals ({p['unknown_m'].astype(float).sum() / 1000:.1f} km) of {len(s)} streets; "
          f"review page: {REVIEW / 'index.html'}")


_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Sidewalk tag review</title>
<style>
:root{--bg:#fff;--fg:#1b1b1b;--muted:#5c5c5c;--line:#ddd;--ok:#1a7f37;--no:#b42318}
@media (prefers-color-scheme: dark){:root{--bg:#141414;--fg:#eee;--muted:#aaa;--line:#333;--ok:#4ac26b;--no:#ff6b5b}}
body{background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}
h1{font-size:1.4rem;margin:.2rem 0}.muted{color:var(--muted)}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.card{border:1px solid var(--line);border-radius:8px;padding:12px;margin:14px 0}
.card img{width:100%;height:auto;border-radius:4px}
.tag{font-family:ui-monospace,monospace;font-weight:600}
.btns button{font:inherit;padding:6px 14px;margin-right:8px;border-radius:6px;border:1px solid var(--line);background:none;color:var(--fg);cursor:pointer}
.card.approved{border-color:var(--ok)}.card.rejected{border-color:var(--no);opacity:.6}
.card.approved .a{background:var(--ok);color:#fff}.card.rejected .r{background:var(--no);color:#fff}
a{color:inherit}
</style></head><body>
<h1>Sidewalk tag review</h1>
<p class="muted">Each street's tag was proposed from the Mapillary photos shown. Approve only if the photos show it along the whole street.
Captions say whether photo-left is the way's left or right. Internal: do not share.</p>
<div class="bar"><span id="count"></span><button id="dl">Download decisions (CSV)</button></div>
<div id="list"></div>
<script>
const items = __ITEMS__; const KEY = "sidewalk-review";
let dec = {}; try { dec = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(dec)); } catch (e) {} };
const list = document.getElementById("list");
function count(){ const a = items.filter(i => dec[i.fp] === "approve"), r = items.filter(i => dec[i.fp] === "reject");
  document.getElementById("count").textContent = `${a.length} approved (${(a.reduce((s,i)=>s+i.m,0)/1000).toFixed(1)} km), ${r.length} rejected, ${items.length-a.length-r.length} left of ${items.length}`; }
for (const i of items) {
  const c = document.createElement("div"); c.className = "card";
  const esc = s => String(s).replace(/[&<>"]/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[ch]));
  c.innerHTML = `<div><b>${esc(i.name)}</b> <span class="muted">area ${i.area} · ${i.highway} · way ${i.way} · ${i.m} m</span></div>
    <div>Proposed: <span class="tag">${i.tag}</span> <span class="muted">${esc(i.notes)}</span></div>
    <img loading="lazy" src="${i.img}" alt="Photos along ${esc(i.name)}">
    <div class="btns"><button class="a">Approve</button><button class="r">Reject</button>
    <a href="https://www.openstreetmap.org/way/${i.way}" target="_blank" rel="noopener">OSM</a> ·
    ${i.photos.map((p,k)=>`<a href="https://www.mapillary.com/app/?pKey=${p}" target="_blank" rel="noopener">photo ${k+1}</a>`).join(" ")}</div>`;
  const set = v => { dec[i.fp] = dec[i.fp] === v ? undefined : v; save(); paint(); count(); };
  const paint = () => { c.classList.toggle("approved", dec[i.fp] === "approve"); c.classList.toggle("rejected", dec[i.fp] === "reject"); };
  c.querySelector(".a").onclick = () => set("approve"); c.querySelector(".r").onclick = () => set("reject");
  paint(); list.appendChild(c);
}
count();
document.getElementById("dl").onclick = () => {
  const rows = [["osm_way_id","tag","decision"], ...items.map(i => [i.way, i.tag, dec[i.fp] || ""])];
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([rows.map(r => r.join(",")).join("\\n")], {type: "text/csv"}));
  a.download = "sidewalk_review_decisions.csv"; a.click();
};
</script></body></html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("photos").add_argument("--areas", type=int, default=10)
    sub.add_parser("review")
    a = ap.parse_args()
    if a.cmd == "review":
        review_cmd()
    else:
        tok = os.environ.get("PF_MAPILLARY_TOKEN")
        if not tok:
            sys.exit("PF_MAPILLARY_TOKEN is not set (repo .env)")
        photos_cmd(tok, a.areas)
