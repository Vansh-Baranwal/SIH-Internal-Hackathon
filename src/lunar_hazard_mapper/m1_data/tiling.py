"""Deterministic, georeferenced raster tiling."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import rasterio
from rasterio.windows import Window

from .checksums import calculate_sha256
from .contract import write_tile_contract
from .metadata import inspect_raster
from .utils import write_json


def _tile_starts(length: int, size: int, overlap: int) -> list[int]:
    step = size - overlap
    if step <= 0:
        raise ValueError("overlap must be smaller than tile size")
    return list(range(0, length, step))


def create_tiles(input_path: str | Path, output_dir: str | Path, *, tile_width: int = 256,
                 tile_height: int = 256, overlap: int = 0, padding: bool = False,
                 allow_unreferenced: bool = False) -> list[dict[str, Any]]:
    input_path, output_dir = Path(input_path), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = inspect_raster(input_path, allow_unreferenced=allow_unreferenced)
    checksum = calculate_sha256(input_path)
    records = []
    with rasterio.open(input_path) as src:
        for row, y in enumerate(_tile_starts(src.height, tile_height, overlap)):
            for col, x in enumerate(_tile_starts(src.width, tile_width, overlap)):
                actual_width = min(tile_width, src.width - x)
                actual_height = min(tile_height, src.height - y)
                if not padding and (actual_width <= 0 or actual_height <= 0):
                    continue
                read_width = tile_width if padding else actual_width
                read_height = tile_height if padding else actual_height
                window = Window(x, y, read_width, read_height)
                data = src.read(window=window, boundless=padding, fill_value=src.nodata)
                transform = src.window_transform(window)
                tile_id = f"{source['source_id']}_r{row:04d}_c{col:04d}"
                tile_path = output_dir / f"{tile_id}.tif"
                profile = src.profile.copy()
                profile.update(width=read_width, height=read_height, transform=transform)
                with rasterio.open(tile_path, "w", **profile) as dst:
                    dst.write(data)
                record = {
                    "schema_version": "1.0", "tile_id": tile_id, "path": str(tile_path),
                    "source_id": source["source_id"], "source_path": str(input_path),
                    "source_checksum": checksum, "row": row, "column": col,
                    "origin": {"x": int(x), "y": int(y)}, "window": [int(x), int(y), int(read_width), int(read_height)],
                    "width": int(read_width), "height": int(read_height),
                    "pixel_size_x": source["pixel_size_x"], "pixel_size_y": source["pixel_size_y"],
                    "crs": source["crs"], "transform": [float(transform.a), float(transform.b), float(transform.c), float(transform.d), float(transform.e), float(transform.f)],
                    "bounds": {k: float(v) for k, v in zip(("left", "bottom", "right", "top"), rasterio.windows.bounds(window, src.transform))},
                    "nodata": source["nodata"], "preprocessing_config": "none",
                    "reference_data_available": False,
                }
                write_tile_contract(tile_path.with_suffix(".json"), record)
                records.append(record)
    return records


def write_tile_manifest(records: list[dict[str, Any]], output: str | Path) -> None:
    write_json(output, {"schema_version": "1.0", "tiles": records})
