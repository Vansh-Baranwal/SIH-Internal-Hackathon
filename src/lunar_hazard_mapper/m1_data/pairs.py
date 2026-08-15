"""Evidence-gated LR/HR training-pair construction owned by Member 1 (M1)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import rasterio
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, transform_bounds
from rasterio.enums import Resampling


def _crs(record: dict[str, Any]) -> CRS | None:
    try:
        value = record.get("crs")
        return CRS.from_user_input(value) if value else None
    except (TypeError, ValueError):
        return None


def _bounds(record: dict[str, Any]) -> tuple[float, float, float, float] | None:
    value = record.get("bounds")
    if isinstance(value, dict):
        try:
            return tuple(float(value[k]) for k in ("west", "south", "east", "north"))
        except (KeyError, TypeError, ValueError):
            return None
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return tuple(float(v) for v in value)
    return None


def _intersection_fraction(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> float:
    area = max(0.0, left[2] - left[0]) * max(0.0, left[3] - left[1])
    if area == 0:
        return 0.0
    overlap = max(0.0, min(left[2], right[2]) - max(left[0], right[0])) * max(0.0, min(left[3], right[3]) - max(left[1], right[1]))
    return overlap / area


def co_register_pair(lr_tile: dict[str, Any], hr_tile: dict[str, Any], output_lr: Path, output_hr: Path) -> dict[str, Any] | None:
    """Reproject a proven-overlap HR tile onto the normalized LR grid."""
    lr_path, hr_path = Path(lr_tile["tile_path"]), Path(hr_tile["tile_path"])
    output_lr, output_hr = Path(output_lr), Path(output_hr)
    try:
        with rasterio.open(lr_path) as lr, rasterio.open(hr_path) as hr:
            if lr.crs is None or hr.crs is None:
                return None
            hr_bounds = transform_bounds(hr.crs, lr.crs, *hr.bounds)
            coverage = _intersection_fraction((lr.bounds.left, lr.bounds.bottom, lr.bounds.right, lr.bounds.top), hr_bounds)
            if coverage < 0.8:
                return None
            output_lr.parent.mkdir(parents=True, exist_ok=True)
            output_hr.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(lr_path, output_lr)
            profile = lr.profile.copy()
            profile.update(driver="GTiff", dtype="float32", count=1, nodata=lr.nodata, compress="lzw")
            with rasterio.open(output_hr, "w", **profile) as dst:
                reproject(source=rasterio.band(hr, 1), destination=rasterio.band(dst, 1), src_transform=hr.transform, src_crs=hr.crs, dst_transform=lr.transform, dst_crs=lr.crs, resampling=Resampling.bilinear, dst_nodata=lr.nodata)
            lr_size = float((abs(lr.transform.a) + abs(lr.transform.e)) / 2)
            hr_size = float((abs(hr.transform.a) + abs(hr.transform.e)) / 2)
            return {"lr_path": output_lr.as_posix(), "hr_path": output_hr.as_posix(), "crs": lr.crs.to_string(), "lr_pixel_size_m": lr_size, "hr_pixel_size_m": hr_size, "scale_factor": round(lr_size / hr_size), "nodata": lr.nodata, "geographic_bounds": [lr.bounds.left, lr.bounds.bottom, lr.bounds.right, lr.bounds.top], "coverage_fraction": coverage}
    except (KeyError, OSError, ValueError, rasterio.errors.RasterioIOError):
        return None


def spatial_split(pair_records: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Assign pairs to explicitly configured geographic regions."""
    split = config.get("spatial_split", config)
    regions = {name: (split.get(f"{name}_region") or {}).get("bounds") for name in ("train", "val", "test")}
    if pair_records and any(not bounds for bounds in regions.values()):
        raise ValueError("train, val, and test geographic bounds are required for non-empty pairs")
    result = []
    for record in pair_records:
        bounds = record["geographic_bounds"]
        centre = ((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
        matches = [name for name, region in regions.items() if region and region[0] <= centre[0] <= region[2] and region[1] <= centre[1] <= region[3]]
        if len(matches) != 1:
            raise ValueError("pair centre must belong to exactly one spatial split region")
        result.append({**record, "split": matches[0]})
    return result


def build_pairs_manifest(pair_records: list[dict[str, Any]], output_path: Path, *, status: str = "ready", failure_reasons: list[str] | None = None) -> dict[str, Any]:
    """Validate and save the exact M1-to-M2 manifest schema."""
    required = ("id", "lr_path", "hr_path", "crs", "lr_pixel_size_m", "hr_pixel_size_m", "scale_factor", "nodata", "geographic_bounds", "split")
    for pair in pair_records:
        missing = [key for key in required if pair.get(key) is None]
        if missing:
            raise ValueError(f"pair missing required metadata: {missing}")
    manifest = {"version": "1.0", "pairs": pair_records, "spatial_test_region": None, "total_pairs": len(pair_records), "train_count": sum(p.get("split") == "train" for p in pair_records), "val_count": sum(p.get("split") == "val" for p in pair_records), "test_count": sum(p.get("split") == "test" for p in pair_records), "status": status, "failure_reasons": failure_reasons or []}
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest
