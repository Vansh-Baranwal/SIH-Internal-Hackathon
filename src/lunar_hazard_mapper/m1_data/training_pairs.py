"""Synthetic reference-derived training pair construction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

from .checksums import calculate_sha256
from .reference_catalog import calculate_overlap
from .utils import config_hash, write_json


def build_training_pairs(tmc_records: list[dict[str, Any]], references: list[dict[str, Any]],
                         output_dir: str | Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = config.get("training_pairs", config)
    degradation = settings.get("degradation", {})
    scale = int(degradation.get("downsample", {}).get("scale_factor", 1))
    if scale < 1:
        raise ValueError("scale_factor must be positive")
    records = []
    for tmc in tmc_records:
        for reference in references:
            overlap = calculate_overlap(tmc, reference)
            if not overlap["overlaps"]:
                continue
            with rasterio.open(reference["path"]) as src:
                window = from_bounds(**tmc["bounds"], transform=src.transform)
                window = window.round_offsets().round_lengths()
                hr = src.read(1, window=window, boundless=True, fill_value=src.nodata).astype(np.float32)
                transform = src.window_transform(window)
                if hr.size == 0:
                    continue
                # The pair is explicitly synthetic: this is a controlled degradation, not sensor simulation.
                degraded = hr
                if degradation.get("blur", {}).get("enabled", False):
                    sigma = float(degradation["blur"].get("sigma", 1.0))
                    radius = max(1, int(round(3 * sigma)))
                    coords = np.arange(-radius, radius + 1, dtype=np.float32)
                    kernel = np.exp(-(coords ** 2) / (2 * sigma ** 2)); kernel /= kernel.sum()
                    degraded = np.apply_along_axis(lambda row: np.convolve(row, kernel, mode="same"), 1, degraded)
                    degraded = np.apply_along_axis(lambda col: np.convolve(col, kernel, mode="same"), 0, degraded)
                if scale > 1 and degradation.get("downsample", {}).get("enabled", True):
                    degraded = degraded[::scale, ::scale]
                    lr_transform = transform * rasterio.Affine.scale(scale, scale)
                else:
                    lr_transform = transform
                noise = degradation.get("noise", {})
                if noise.get("enabled", False) and float(noise.get("sigma", 0)) > 0:
                    rng = np.random.default_rng(0)
                    degraded = degraded + rng.normal(0, float(noise["sigma"]), degraded.shape).astype(np.float32)
            pair_id = f"{tmc['source_id']}_{reference['reference_id']}_{len(records):05d}"
            hr_path, lr_path = output_dir / f"{pair_id}_hr.tif", output_dir / f"{pair_id}_lr.tif"
            profile = {"driver": "GTiff", "dtype": "float32", "count": 1, "width": hr.shape[1], "height": hr.shape[0],
                       "crs": reference["crs"], "transform": transform, "nodata": None}
            with rasterio.open(hr_path, "w", **profile) as dst: dst.write(hr, 1)
            profile.update(width=degraded.shape[1], height=degraded.shape[0], transform=lr_transform)
            with rasterio.open(lr_path, "w", **profile) as dst: dst.write(degraded.astype(np.float32), 1)
            records.append({"pair_id": pair_id, "source_reference": reference["reference_id"],
                            "low_resolution_path": str(lr_path), "high_resolution_path": str(hr_path),
                            "low_resolution_checksum": calculate_sha256(lr_path), "high_resolution_checksum": calculate_sha256(hr_path),
                            "scale_factor": scale, "degradation_config": degradation, "degradation_config_hash": config_hash(degradation),
                            "spatial_region_id": None, "split": None, "synthetic": True,
                            "notes": "Synthetic training pair; degradation is not an exact TMC sensor model."})
    return records


def write_training_pair_manifest(records: list[dict[str, Any]], output: str | Path) -> None:
    write_json(output, {"schema_version": "1.0", "pair_type": "synthetic", "pairs": records})
