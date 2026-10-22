"""The demo: a landing page to choose a place, and each place's navigation app behind it.

A server serves one region (``PF_REGION`` is read once, at import), so ``pf demo`` starts one
``pf serve`` per place on its own port and serves the landing page itself. Every place shown is
built from open data only (rule 7): DC, and the Maryland towns' public builds.

    pf demo            # http://127.0.0.1:8000, then pick a place

Local only: it is for recording the demo video, not for deployment.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass

import requests

from .config import REPO_ROOT
from .regions import REGIONS, is_internal

LANDING_DIR = REPO_ROOT / "web" / "landing"
HOST = "127.0.0.1"
LANDING_PORT = 8000


@dataclass(frozen=True)
class Place:
    region: str
    name: str
    port: int
    md6: bool          # in Maryland's 6th congressional district
    blurb: str

    @property
    def url(self) -> str:
        return f"http://{HOST}:{self.port}/"


PLACES = (
    Place("dc", "Washington, DC", 8001, False,
          "A city that publishes its sidewalks, curb ramps, signals and terrain as open data."),
    Place("gaithersburg_public", "Gaithersburg", 8002, True,
          "Montgomery County. Built from OpenStreetMap and public terrain data."),
    Place("frederick_public", "Frederick", 8003, True,
          "Frederick County. Built from OpenStreetMap and public terrain data."),
)

# coverage.md's accessibility-bar rows: "| 1. Curb evidence ... | 17.1 | 60.0 | misses | ..."
_ROW = re.compile(r"^\|\s*(\d)\.\s[^|]*\|\s*([\d.]+)\s*\|", re.M)


def evidence(region_id: str) -> dict[str, float | None]:
    """Share of curbs, slope and sidewalks with evidence, from the region's coverage report."""
    path = REPO_ROOT / "reports" / region_id / "phase0" / "coverage.md"
    rows = dict(_ROW.findall(path.read_text(encoding="utf-8"))) if path.exists() else {}
    val = lambda k: float(rows[k]) if k in rows else None  # noqa: E731
    return {"curbs": val("1"), "slope": val("2"), "sidewalks": val("3")}


def places_json() -> list[dict]:
    return [{"id": p.region, "name": p.name, "url": p.url, "md6": p.md6, "blurb": p.blurb,
             "image": f"img/{p.region}.png", "evidence": evidence(p.region)} for p in PLACES]


def landing_app():
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="PathFinder demo", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def fresh(request, call_next):
        # the page is edited between takes: never let the browser show a stale copy
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/places")
    def places() -> list[dict]:
        return places_json()

    app.mount("/", StaticFiles(directory=LANDING_DIR, html=True), name="landing")
    return app


def _check_open() -> None:
    """Refuse to start if any place would show data held back under rule 7."""
    for p in PLACES:
        held = [s.id for s in REGIONS[p.region].sources.values() if is_internal(s)]
        if held:
            raise SystemExit(f"{p.region} holds internal sources {held}; the demo shows open data only")


def _wait(url: str, procs: list[subprocess.Popen], timeout_s: float = 120) -> None:
    end = time.time() + timeout_s
    while time.time() < end:
        if any(p.poll() is not None for p in procs):
            raise SystemExit("a place's server stopped while starting; see its log above")
        try:
            if requests.get(url + "api/health", timeout=2).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise SystemExit(f"{url} did not answer within {timeout_s:.0f} s")


def run(open_browser: bool = True) -> None:
    import uvicorn

    _check_open()
    home = f"http://{HOST}:{LANDING_PORT}/"
    procs = []
    try:
        for p in PLACES:
            env = {**os.environ, "PF_REGION": p.region, "PF_HOME": home}
            procs.append(subprocess.Popen([sys.executable, "-m", "pathfinder.cli", "serve", "--port", str(p.port)], env=env))
        for p in PLACES:
            _wait(p.url, procs)
            print(f"  {p.name}: {p.url}")
        print(f"PathFinder demo: {home}  (Ctrl-C stops everything)")
        if open_browser:
            threading.Timer(1.0, webbrowser.open, args=(home,)).start()
        uvicorn.run(landing_app(), host=HOST, port=LANDING_PORT, log_level="warning")
    finally:
        for proc in procs:
            proc.terminate()
        for proc in procs:
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
