"""GeoTIFF tiling utilities owned by Member 1 (M1)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import rasterio
from rasterio.windows import Window, bounds as window_bounds, transform as window_transform


def _positions(length: int, tile_size: int, step: int) -> list[int]:
    """Return deterministic window starts that cover an image dimension."""
    if length <= 0:
        return []
    positions = list(range(0, max(1, length - tile_size + 1), step))
    final = max(0, length - tile_size)
    if positions[-1] != final:
        positions.append(final)
    return positions


def _tile_record(path: Path, source_path: Path, window: Window, dataset: rasterio.DatasetReader, nodata_fraction: float) -> dict[str, Any]:
    transform = window_transform(window, dataset.transform)
    bounds = window_bounds(window, dataset.transform)
    return {
        "tile_path": path.as_posix(),
        "source_path": source_path.as_posix(),
        "row": int(window.row_off),
        "col": int(window.col_off),
        "width": int(window.width),
        "height": int(window.height),
        "crs": dataset.crs.to_string() if dataset.crs else None,
        "pixel_size_x_m": float(abs(transform.a)),
        "pixel_size_y_m": float(abs(transform.e)),
        "transform": [float(value) for value in tuple(transform)[:6]],
        "bounds": {"west": float(bounds[0]), "south": float(bounds[1]), "east": float(bounds[2]), "north": float(bounds[3])},
        "nodata": float(dataset.nodata) if dataset.nodata is not None else None,
        "nodata_fraction": float(nodata_fraction),
        "origin_x": float(transform.c),
        "origin_y": float(transform.f),
    }


def tile_tiff(
    src_path: Path,
    output_dir: Path,
    tile_size: int,
    overlap: int,
    min_valid_fraction: float,
    nodata_value: float,
) -> list[dict[str, Any]]:
    """Tile one GeoTIFF, padding boundary windows and skipping invalid windows."""
    if tile_size <= 0 or overlap < 0 or overlap >= tile_size:
        raise ValueError("tile_size must be positive and overlap must be in [0, tile_size)")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    step = tile_size - overlap
    records: list[dict[str, Any]] = []
    with rasterio.open(src_path) as source:
        dtype_info = __import__("numpy").dtype(source.dtypes[0])
        fill_value = nodata_value
        if not (dtype_info.kind == "f" or dtype_info.kind == "c"):
            info = __import__("numpy").iinfo(dtype_info)
            fill_value = float(min(max(nodata_value, info.min), info.max))
            if fill_value != nodata_value:
                fill_value = float(info.min)
        output_nodata = fill_value
        positions = [(row, col) for row in _positions(source.height, tile_size, step) for col in _positions(source.width, tile_size, step)]
        for row, col in positions:
            window = Window(col, row, tile_size, tile_size)
            data = source.read(1, window=window, boundless=True, out_shape=(tile_size, tile_size), fill_value=fill_value)
            mask = source.read_masks(1, window=window, boundless=True, out_shape=(tile_size, tile_size))
            valid_rows = max(0, min(tile_size, source.height - row))
            valid_cols = max(0, min(tile_size, source.width - col))
            valid_mask = mask.copy()
            if valid_rows < tile_size:
                valid_mask[valid_rows:, :] = 0
            if valid_cols < tile_size:
                valid_mask[:, valid_cols:] = 0
            nodata_fraction = float((valid_mask == 0).mean())
            # Source products without an explicit mask are valid within image bounds.
            if source.nodata is None and "all_valid" in {flag.name for flag in source.mask_flag_enums[0]}:
                nodata_fraction = 1.0 - (valid_rows * valid_cols) / float(tile_size * tile_size)
            if 1.0 - nodata_fraction < min_valid_fraction:
                continue
            name = f"{Path(src_path).stem}_r{row}_c{col}.tif"
            destination = output_dir / name
            profile = source.profile.copy()
            profile.update(
                driver="GTiff", width=tile_size, height=tile_size, count=1,
                transform=window_transform(window, source.transform), nodata=output_nodata,
                compress="lzw", tiled=False,
            )
            with rasterio.open(destination, "w", **profile) as output:
                output.write(data, 1)
            records.append(_tile_record(destination, Path(src_path), window, source, nodata_fraction))
    return records


def tile_directory(src_dir: Path, output_dir: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Tile every GeoTIFF below a directory using the configured tiling policy."""
    tiling = config.get("tiling", config)
    records: list[dict[str, Any]] = []
    for source in sorted(Path(src_dir).rglob("*.tif"), key=lambda item: item.as_posix().lower()):
        records.extend(tile_tiff(source, output_dir, int(tiling["tile_size_px"]), int(tiling["overlap_px"]), float(tiling["min_valid_fraction"]), float(config.get("nodata_value", -9999.0))))
    return records


def match_hr_to_lr_tile(lr_tile: dict[str, Any], hr_tiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return HR tiles with positive-area overlap with an LR tile."""
    result: list[dict[str, Any]] = []
    left = lr_tile["bounds"]
    for candidate in hr_tiles:
        right = candidate["bounds"]
        width = min(left["east"], right["east"]) - max(left["west"], right["west"])
        height = min(left["north"], right["north"]) - max(left["south"], right["south"])
        if width > 0 and height > 0:
            result.append(candidate)
    return result
