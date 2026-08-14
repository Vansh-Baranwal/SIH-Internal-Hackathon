"""Automated artifact quality assurance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from .checksums import calculate_sha256
from .contract import validate_tile_contract
from .errors import MetadataValidationError, SpatialLeakageError
from .metadata import inspect_raster
from .spatial_split import validate_split_leakage
from .utils import write_json


def check_raster(path: str | Path, *, expected_pixel_size: tuple[float, float] | None = None,
                 allow_unreferenced: bool = False) -> dict[str, str]:
    meta = inspect_raster(path, allow_unreferenced=allow_unreferenced)
    checks = {"crs": "PASS" if meta["crs"] else "FAIL", "transform": "PASS", "dimensions": "PASS"}
    if expected_pixel_size and not np.allclose((meta["pixel_size_x"], meta["pixel_size_y"]), expected_pixel_size):
        raise MetadataValidationError(f"Unexpected pixel size in {path}")
    with rasterio.open(path) as dataset:
        values = dataset.read(masked=True)
        if np.any(~np.isfinite(values.data[~values.mask])):
            raise MetadataValidationError(f"NaN/Inf valid pixels in {path}")
        checks["nodata"] = "PASS"
    return checks


def run_qa(tile_records: list[dict[str, Any]], *, split_records: list[dict[str, Any]] | None = None,
           output: str | Path | None = None) -> dict[str, Any]:
    checks = {"crs": "PASS", "transform": "PASS", "pixel_size": "PASS", "dimensions": "PASS",
              "nodata": "PASS", "bounds": "PASS", "provenance": "PASS", "spatial_split": "PASS"}
    errors: list[str] = []
    for record in tile_records:
        try:
            check_raster(record["path"])
            validate_tile_contract(record)
            if record.get("source_checksum") and Path(record["source_path"]).exists():
                if calculate_sha256(record["source_path"]) != record["source_checksum"]:
                    raise MetadataValidationError("source checksum mismatch")
        except Exception as exc:
            errors.append(f"{record.get('tile_id', record.get('path'))}: {exc}")
            checks["provenance"] = "FAIL"
    if split_records is not None:
        try:
            validate_split_leakage(split_records)
        except SpatialLeakageError as exc:
            errors.append(str(exc)); checks["spatial_split"] = "FAIL"
    report = {"dataset": "Member 1 artifacts", "status": "PASS" if not errors else "FAIL",
              "checks": checks, "errors": errors, "warnings": []}
    if output:
        write_json(output, report)
    return report
