"""Raster metadata inspection and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import rasterio
from rasterio.transform import Affine

from .errors import MetadataValidationError


def _transform_values(transform: Affine) -> list[float]:
    return [float(transform.a), float(transform.b), float(transform.c), float(transform.d), float(transform.e), float(transform.f)]


def _bounds_dict(bounds: Any) -> dict[str, float]:
    return {name: float(getattr(bounds, name)) for name in ("left", "bottom", "right", "top")}


def validate_dataset(dataset: rasterio.DatasetReader, allow_unreferenced: bool = False) -> None:
    if dataset.width <= 0 or dataset.height <= 0 or dataset.count <= 0:
        raise MetadataValidationError(f"Invalid raster dimensions/count: {dataset.width}x{dataset.height}x{dataset.count}")
    if dataset.crs is None and not allow_unreferenced:
        raise MetadataValidationError("Raster has no CRS; pass allow_unreferenced=True only for explicitly unreferenced data")
    transform = dataset.transform
    if not isinstance(transform, Affine) or transform == Affine.identity():
        raise MetadataValidationError(f"Invalid or missing affine transform: {transform!r}")
    if abs(float(transform.a * transform.e - transform.b * transform.d)) <= 0:
        raise MetadataValidationError(f"Affine transform is singular: {transform!r}")
    if abs(transform.a) <= 0 or abs(transform.e) <= 0:
        raise MetadataValidationError(f"Pixel size must be non-zero: {transform!r}")
    if not all(value == value and abs(value) != float("inf") for value in _transform_values(transform)):
        raise MetadataValidationError("Affine transform contains NaN or infinity")


def inspect_raster(path: str | Path, source_id: str | None = None, *, allow_unreferenced: bool = False) -> dict[str, Any]:
    """Inspect a raster without changing it and return stable JSON-compatible metadata."""
    path = Path(path)
    if not path.is_file():
        raise MetadataValidationError(f"Raster does not exist: {path}")
    try:
        with rasterio.open(path) as dataset:
            validate_dataset(dataset, allow_unreferenced=allow_unreferenced)
            tags = {str(key): str(value) for key, value in dataset.tags().items()}
            crs = dataset.crs.to_string() if dataset.crs else None
            pixel_x, pixel_y = abs(float(dataset.transform.a)), abs(float(dataset.transform.e))
            return {
                "schema_version": "1.0", "source_id": source_id or path.stem, "file_path": str(path),
                "width": int(dataset.width), "height": int(dataset.height), "count": int(dataset.count),
                "dtype": str(dataset.dtypes[0]), "crs": crs, "transform": _transform_values(dataset.transform),
                "pixel_size_x": pixel_x, "pixel_size_y": pixel_y, "bounds": _bounds_dict(dataset.bounds),
                "nodata": None if dataset.nodata is None else float(dataset.nodata), "driver": dataset.driver,
                "units": tags.get("units"), "resolution": {"x": pixel_x, "y": pixel_y, "unit": tags.get("unit", "unknown")},
                "metadata": tags,
            }
    except MetadataValidationError:
        raise
    except Exception as exc:
        raise MetadataValidationError(f"Could not inspect raster {path}: {exc}") from exc


def validate_geospatial_consistency(source: dict[str, Any], processed: dict[str, Any]) -> None:
    """Ensure an operation did not silently move or resize a raster."""
    for key in ("crs", "transform", "width", "height", "pixel_size_x", "pixel_size_y", "bounds"):
        if source.get(key) != processed.get(key):
            raise MetadataValidationError(f"Geospatial field changed during processing: {key}")
