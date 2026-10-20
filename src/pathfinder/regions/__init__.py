"""Regions the pipeline can run on. ``PF_REGION`` picks one (default ``gaithersburg``)."""

from __future__ import annotations

from ..config import REGION_ID
from .base import COVERAGE_FAMILIES, ROLES, Region, Source
from .maryland import FREDERICK, GAITHERSBURG

REGIONS: dict[str, Region] = {r.id: r for r in (GAITHERSBURG, FREDERICK)}


def get(region_id: str) -> Region:
    try:
        return REGIONS[region_id]
    except KeyError:
        raise KeyError(f"unknown region {region_id!r}; known: {', '.join(REGIONS)}") from None


def current() -> Region:
    return get(REGION_ID)


__all__ = ["COVERAGE_FAMILIES", "REGIONS", "ROLES", "Region", "Source", "current", "get"]
