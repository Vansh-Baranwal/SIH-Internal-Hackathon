"""Automated quality checks for Member 1 geospatial outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio


def _result(name: str, passed: bool, details: Any) -> dict[str, Any]:
    return {"check_name": name, "passed": bool(passed), "details": details}


def check_crs_exists(tile_path: Path) -> dict[str, Any]:
    try:
        with rasterio.open(tile_path) as src:
            return _result("crs_exists", src.crs is not None, str(src.crs))
    except (OSError, rasterio.errors.RasterioIOError) as exc:
        return _result("crs_exists", False, str(exc))


def check_transform_exists(tile_path: Path) -> dict[str, Any]:
    try:
        with rasterio.open(tile_path) as src:
            passed = src.transform is not None and not src.transform.is_identity
            return _result("transform_exists", passed, tuple(src.transform)[:6])
    except (OSError, rasterio.errors.RasterioIOError) as exc:
        return _result("transform_exists", False, str(exc))


def check_pixel_size(tile_path: Path, expected_m: float, tolerance_fraction: float = 0.05) -> dict[str, Any]:
    try:
        with rasterio.open(tile_path) as src:
            actual = (abs(src.transform.a) + abs(src.transform.e)) / 2
            passed = abs(actual - expected_m) <= abs(expected_m) * tolerance_fraction
            return _result("pixel_size", passed, {"actual": actual, "expected": expected_m})
    except (OSError, rasterio.errors.RasterioIOError) as exc:
        return _result("pixel_size", False, str(exc))


def check_nodata_mask(tile_path: Path, nodata_value: float) -> dict[str, Any]:
    try:
        with rasterio.open(tile_path) as src:
            data = src.read(1)
            mask = src.read_masks(1) == 0
            expected = data == nodata_value
            passed = bool(np.all(mask == expected))
            return _result("nodata_mask", passed, {"masked_pixels": int(mask.sum()), "nodata_value": nodata_value})
    except (OSError, rasterio.errors.RasterioIOError) as exc:
        return _result("nodata_mask", False, str(exc))


def check_value_range(tile_path: Path, min_val: float, max_val: float) -> dict[str, Any]:
    try:
        with rasterio.open(tile_path) as src:
            data = src.read(1).astype(np.float32)
            valid = (src.read_masks(1) != 0) & np.isfinite(data)
            values = data[valid]
            passed = bool(values.size and values.min() >= min_val and values.max() <= max_val)
            return _result("value_range", passed, {"min": float(values.min()) if values.size else None, "max": float(values.max()) if values.size else None})
    except (OSError, rasterio.errors.RasterioIOError) as exc:
        return _result("value_range", False, str(exc))


def check_pair_alignment(lr_path: Path, hr_path: Path) -> dict[str, Any]:
    try:
        with rasterio.open(lr_path) as lr, rasterio.open(hr_path) as hr:
            same_crs = lr.crs is not None and lr.crs == hr.crs
            contains = hr.bounds.left <= lr.bounds.left and hr.bounds.bottom <= lr.bounds.bottom and hr.bounds.right >= lr.bounds.right and hr.bounds.top >= lr.bounds.top
            lr_size = (abs(lr.transform.a) + abs(lr.transform.e)) / 2
            hr_size = (abs(hr.transform.a) + abs(hr.transform.e)) / 2
            passed = same_crs and contains and hr_size < lr_size
            return _result("pair_alignment", passed, {"same_crs": same_crs, "contains_lr": contains, "lr_pixel_size": lr_size, "hr_pixel_size": hr_size})
    except (OSError, rasterio.errors.RasterioIOError) as exc:
        return _result("pair_alignment", False, str(exc))


def run_qa_suite(manifest_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Run checks over manifest tiles and pairs, returning aggregate results."""
    import json
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    for pair in manifest.get("pairs", []):
        checks.extend([check_crs_exists(pair["lr_path"]), check_transform_exists(pair["lr_path"]), check_crs_exists(pair["hr_path"]), check_transform_exists(pair["hr_path"]), check_pair_alignment(pair["lr_path"], pair["hr_path"])])
    result = {"passed": sum(item["passed"] for item in checks), "failed": sum(not item["passed"] for item in checks), "checks": checks, "pair_count": len(manifest.get("pairs", [])), "status": manifest.get("status")}
    return result
