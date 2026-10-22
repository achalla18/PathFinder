"""The demo launcher and the landing page's numbers (pf demo)."""
import json

from pathfinder import api, demo


def test_landing_page_reads_each_places_evidence_from_its_coverage_report(tmp_path, monkeypatch):
    report = tmp_path / "reports" / "somewhere" / "phase0"
    report.mkdir(parents=True)
    (report / "coverage.md").write_text(
        "| Criterion | Value % | Bar % | Result | Counts |\n|---|---|---|---|---|\n"
        "| 1. Curb evidence at crossing ends, implicit included | 17.1 | 60.0 | misses | 1,670 of 9,771 ends |\n"
        "| 2. Slope verified, share of walkable length | 95.8 | 80.0 | passes |  |\n"
        "| 3. Sidewalk evidence, share of walkable length | 42.2 | 60.0 | misses | ... |\n", encoding="utf-8")
    monkeypatch.setattr(demo, "REPO_ROOT", tmp_path)
    assert demo.evidence("somewhere") == {"curbs": 17.1, "slope": 95.8, "sidewalks": 42.2}
    assert demo.evidence("nowhere") == {"curbs": None, "slope": None, "sidewalks": None}


def test_every_demo_place_is_built_from_open_data_only():
    demo._check_open()  # raises SystemExit if any place holds an internal source
    assert len({p.port for p in demo.PLACES}) == len(demo.PLACES) and demo.LANDING_PORT not in {p.port for p in demo.PLACES}


def test_example_trips_keep_only_well_formed_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "EXAMPLES_DIR", tmp_path)
    good = {"label": "To the library", "note": "avoids a steep block", "from": [-77.41, 39.41, "Home"], "to": [-77.40, 39.42, "Library"]}
    (tmp_path / f"{api.REGION.id}.json").write_text(json.dumps([good, {"label": "broken", "from": [1, 2]}]), encoding="utf-8")
    assert api._examples() == [good]
