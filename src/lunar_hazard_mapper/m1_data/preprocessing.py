"""Explicit, deterministic raster preprocessing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from .checksums import calculate_sha256
from .contract import write_tile_contract
from .metadata import inspect_raster, validate_geospatial_consistency
from .utils import config_hash


def preprocess_raster(
    input_path: str | Path,
    output_path: str | Path,
    config: dict[str, Any],
    *,
    allow_unreferenced: bool = False,
) -> dict[str, Any]:
    input_path, output_path = Path(input_path), Path(output_path)
    source = inspect_raster(input_path, allow_unreferenced=allow_unreferenced)
    settings = config.get("preprocessing", config)
    output_dtype = np.dtype(settings.get("dtype", {}).get("output", "float32"))

    with rasterio.open(input_path) as src:
        data = src.read().astype(output_dtype, copy=False)
        nodata = src.nodata
        valid = np.isfinite(data)
        if nodata is not None:
            valid &= data != nodata

        if settings.get("nodata", {}).get("enabled", True):
            data[~valid] = np.nan if np.issubdtype(output_dtype, np.floating) else 0

        normalization = settings.get("normalization", {})
        if normalization.get("enabled", False):
            if normalization.get("method") != "percentile":
                raise ValueError("Only percentile normalization is supported")
            values = data[valid]
            if values.size == 0:
                raise ValueError(f"No valid pixels available for normalization: {input_path}")
            low = float(np.percentile(values, float(normalization.get("lower", 1))))
            high = float(np.percentile(values, float(normalization.get("upper", 99))))
            if not high > low:
                raise ValueError("Normalization percentile range is empty")
            data[valid] = np.clip((data[valid] - low) / (high - low), 0.0, 1.0)

        profile = src.profile.copy()
        profile.update(dtype=output_dtype.name, count=src.count, nodata=nodata)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(data)

    processed = inspect_raster(output_path, allow_unreferenced=allow_unreferenced)
    validate_geospatial_consistency(source, processed)
    processed.update(
        {
            "schema_version": "1.0",
            "tile_id": source["source_id"],
            "path": str(output_path),
            "source_id": source["source_id"],
            "source_path": str(input_path),
            "source_checksum": calculate_sha256(input_path),
            "preprocessing_config": config_hash(config),
            "reference_data_available": False,
            "origin": {"x": 0, "y": 0},
        }
    )
    write_tile_contract(output_path.with_suffix(".json"), processed)
    return processed


def preprocess_radiometry(image):
    """Compatibility wrapper; use :func:`preprocess_raster` for georeferenced data."""
    return image


__all__ = ["preprocess_raster", "preprocess_radiometry"]
