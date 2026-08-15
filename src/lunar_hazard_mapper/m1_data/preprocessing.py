"""Deterministic radiometric preprocessing owned by Member 1 (M1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio


def compute_normalisation_stats(tile_paths: list[Path], clip_low: float, clip_high: float, nodata: float) -> dict[str, Any]:
    """Compute global clipping percentiles from the explicitly supplied tiles."""
    if not 0 <= clip_low < clip_high <= 100:
        raise ValueError("clip percentiles must satisfy 0 <= low < high <= 100")
    values: list[np.ndarray] = []
    for path in tile_paths:
        with rasterio.open(path) as dataset:
            data = dataset.read(1).astype(np.float32, copy=False)
            valid = np.isfinite(data) & (data != nodata)
            if valid.any():
                values.append(data[valid])
    if not values:
        raise ValueError("cannot compute normalization statistics: all supplied tiles are nodata")
    flattened = np.concatenate(values)
    return {
        "p_low": float(np.percentile(flattened, clip_low)),
        "p_high": float(np.percentile(flattened, clip_high)),
        "clip_percentile_low": float(clip_low),
        "clip_percentile_high": float(clip_high),
        "computed_from_n_tiles": len(tile_paths),
        "valid_pixel_count": int(flattened.size),
    }


def normalise_tile(data: np.ndarray, nodata_mask: np.ndarray, p_low: float, p_high: float, nodata_value: float = -9999.0) -> np.ndarray:
    """Clip and rescale an array to float32 [0, 1], preserving nodata."""
    if p_high < p_low:
        raise ValueError("p_high must be greater than or equal to p_low")
    result = np.full(data.shape, nodata_value, dtype=np.float32)
    valid = ~nodata_mask & np.isfinite(data)
    if valid.any():
        clipped = np.clip(data[valid].astype(np.float32), p_low, p_high)
        if p_high == p_low:
            result[valid] = 0.0
        else:
            result[valid] = ((clipped - p_low) / (p_high - p_low)).astype(np.float32)
    return result


def preprocess_tile(src_path: Path, dst_path: Path, stats: dict[str, Any], nodata_value: float) -> dict[str, Any]:
    """Normalize one GeoTIFF while preserving its geospatial metadata."""
    src_path, dst_path = Path(src_path), Path(dst_path)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with rasterio.open(src_path) as source:
            data = source.read(1)
            nodata_mask = ~source.read_masks(1).astype(bool)
            if source.nodata is not None:
                nodata_mask |= data == source.nodata
            normalized = normalise_tile(data, nodata_mask, float(stats["p_low"]), float(stats["p_high"]), nodata_value)
            profile = source.profile.copy()
            profile.update(dtype="float32", count=1, nodata=nodata_value, compress="lzw")
            with rasterio.open(dst_path, "w", **profile) as output:
                output.write(normalized, 1)
                output.update_tags(preprocessing="radiometric_normalisation_v1")
        return {"src_path": src_path.as_posix(), "dst_path": dst_path.as_posix(), "success": True, "error_msg": None}
    except (OSError, ValueError, KeyError, rasterio.errors.RasterioIOError) as error:
        return {"src_path": src_path.as_posix(), "dst_path": dst_path.as_posix(), "success": False, "error_msg": str(error)}


def preprocess_directory(src_dir: Path, dst_dir: Path, stats: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize all GeoTIFFs in a directory in deterministic order."""
    nodata_value = float(config.get("nodata_value", -9999.0))
    results = []
    for src_path in sorted(Path(src_dir).glob("*.tif"), key=lambda path: path.name.lower()):
        results.append(preprocess_tile(src_path, Path(dst_dir) / src_path.name, stats, nodata_value))
    return results
