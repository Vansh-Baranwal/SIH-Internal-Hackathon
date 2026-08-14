"""Downstream-safe loading helpers for M1 tile artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import rasterio

from .contract import TileContract, load_tile_contract


def load_tmc_tile(path: str | Path) -> tuple[Any, TileContract]:
    """Load a tile array and its validated sidecar contract.

    The returned array is unchanged from the raster; geospatial information is
    carried by the validated contract rather than inferred from pixel values.
    """
    raster_path = Path(path)
    contract_path = raster_path.with_suffix(".json")
    contract = load_tile_contract(contract_path)
    with rasterio.open(raster_path) as dataset:
        data = dataset.read()
    return data, contract


__all__ = ["load_tmc_tile"]
