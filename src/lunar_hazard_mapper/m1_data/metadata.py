"""GeoTIFF inspection and metadata summaries owned by Member 1 (M1)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import rasterio
from tqdm import tqdm


_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _relative_path(path: Path) -> str:
    """Return a stable project-relative path when possible."""
    try:
        return path.resolve().relative_to(_PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _valid_transform(transform: Any) -> bool:
    """Return whether a transform contains a usable, non-identity georeference."""
    if transform is None:
        return False
    coefficients = tuple(transform)[:6]
    return len(coefficients) == 6 and all(math.isfinite(float(value)) for value in coefficients) and not transform.is_identity


def inspect_tiff(path: Path) -> dict[str, Any]:
    """Inspect one GeoTIFF and return JSON-serializable geospatial metadata."""
    path = Path(path)
    with rasterio.open(path) as dataset:
        transform = dataset.transform
        mask = dataset.read_masks(1)
        nodata_fraction = float((mask == 0).mean()) if mask.size else 0.0
        crs = dataset.crs
        record = {
            "file_path": _relative_path(path),
            "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "width": int(dataset.width),
            "height": int(dataset.height),
            "count": int(dataset.count),
            "dtype": str(dataset.dtypes[0]),
            "crs": crs.to_string() if crs else None,
            "transform": [float(value) for value in tuple(transform)[:6]],
            "pixel_size_x_m": float(abs(transform.a)) if _valid_transform(transform) else None,
            "pixel_size_y_m": float(abs(transform.e)) if _valid_transform(transform) else None,
            "nodata": float(dataset.nodata) if dataset.nodata is not None else None,
            "bounds": {
                "west": float(dataset.bounds.left),
                "south": float(dataset.bounds.bottom),
                "east": float(dataset.bounds.right),
                "north": float(dataset.bounds.top),
            },
            "has_valid_crs": crs is not None,
            "has_valid_transform": _valid_transform(transform),
            "nodata_fraction": nodata_fraction,
        }
    return record


def inspect_directory(dir_path: Path, pattern: str = "*.tif") -> list[dict[str, Any]]:
    """Inspect matching GeoTIFFs recursively in deterministic order."""
    directory = Path(dir_path)
    files = sorted(directory.rglob(pattern), key=lambda item: item.as_posix().lower())
    return [inspect_tiff(path) for path in tqdm(files, desc=f"Inspecting {directory.name}", unit="file")]


def summarise(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate key inspection facts for a collection of records."""
    pixel_sizes = [
        value
        for record in records
        for value in (record.get("pixel_size_x_m"), record.get("pixel_size_y_m"))
        if value is not None
    ]
    return {
        "total_files": len(records),
        "total_size_mb": round(sum(float(record.get("file_size_mb", 0.0)) for record in records), 2),
        "unique_dtypes": sorted({record.get("dtype") for record in records if record.get("dtype")}),
        "unique_crs_values": sorted({record.get("crs") for record in records if record.get("crs")}),
        "pixel_size_range": {
            "min_m": min(pixel_sizes) if pixel_sizes else None,
            "max_m": max(pixel_sizes) if pixel_sizes else None,
        },
        "any_missing_crs": any(not record.get("has_valid_crs", False) for record in records),
        "any_missing_transform": any(not record.get("has_valid_transform", False) for record in records),
        "bounds": _combined_bounds(records),
    }


def _combined_bounds(records: list[dict[str, Any]]) -> dict[str, float] | None:
    """Return the union of record bounds, or None for an empty collection."""
    bounds = [record["bounds"] for record in records if record.get("bounds")]
    if not bounds:
        return None
    return {
        "west": min(float(item["west"]) for item in bounds),
        "south": min(float(item["south"]) for item in bounds),
        "east": max(float(item["east"]) for item in bounds),
        "north": max(float(item["north"]) for item in bounds),
    }
