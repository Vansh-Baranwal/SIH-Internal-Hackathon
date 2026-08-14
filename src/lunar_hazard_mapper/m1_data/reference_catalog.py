"""Reference raster registration and CRS-aware overlap."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pyproj import Transformer
from shapely.geometry import box
from shapely.ops import transform as shapely_transform

from .checksums import calculate_sha256
from .metadata import inspect_raster
from .utils import write_json


def register_references(paths: list[str | Path], output: str | Path, *, source_type: str = "unknown",
                         usable_for_training: bool = True, usable_for_validation: bool = True,
                         allow_unreferenced: bool = False) -> dict[str, Any]:
    records = []
    for path in sorted(Path(p) for p in paths):
        meta = inspect_raster(path, allow_unreferenced=allow_unreferenced)
        records.append({
            "reference_id": meta["source_id"], "path": str(path), "source_type": source_type,
            "resolution": {"x": meta["pixel_size_x"], "y": meta["pixel_size_y"], "unit": "unknown"},
            "crs": meta["crs"], "bounds": meta["bounds"], "source_metadata": meta["metadata"],
            "checksum": calculate_sha256(path), "usable_for_training": usable_for_training,
            "usable_for_validation": usable_for_validation, "notes": "Registered caller-provided reference raster.",
        })
    result = {"schema_version": "1.0", "references": records, "available": bool(records)}
    write_json(output, result)
    return result


def _footprint(record: dict[str, Any], target_crs: str | None = None):
    bounds = record["bounds"]
    geom = box(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"])
    if target_crs and record.get("crs") and record["crs"] != target_crs:
        transformer = Transformer.from_crs(record["crs"], target_crs, always_xy=True)
        geom = shapely_transform(transformer.transform, geom)
    return geom


def calculate_overlap(tmc: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    ref_geom = _footprint(reference, tmc.get("crs"))
    tmc_geom = _footprint(tmc)
    intersection = tmc_geom.intersection(ref_geom)
    area = float(intersection.area)
    return {
        "tmc_source_id": tmc.get("source_id"), "reference_id": reference.get("reference_id"),
        "overlaps": not intersection.is_empty and area > 0, "overlap_area": area,
        "tmc_area": float(tmc_geom.area),
        "overlap_percentage": 0.0 if tmc_geom.area == 0 else area / float(tmc_geom.area) * 100.0,
        "geometry": None if intersection.is_empty else intersection.__geo_interface__,
        "crs": tmc.get("crs"),
    }
