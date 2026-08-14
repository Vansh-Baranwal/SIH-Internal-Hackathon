"""Stable metadata boundary consumed by downstream members."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import DataContractError
from .utils import write_json

REQUIRED_FIELDS = (
    "schema_version", "tile_id", "path", "width", "height", "pixel_size_x",
    "pixel_size_y", "crs", "transform", "origin", "nodata", "source_id",
    "source_checksum", "preprocessing_config", "reference_data_available",
)


@dataclass(frozen=True)
class TileContract:
    schema_version: str
    tile_id: str
    path: str
    width: int
    height: int
    pixel_size_x: float
    pixel_size_y: float
    crs: str
    transform: tuple[float, ...]
    origin: dict[str, int]
    nodata: float | None
    source_id: str
    source_checksum: str
    preprocessing_config: str | dict[str, Any]
    reference_data_available: bool

    @classmethod
    def from_dict(cls, metadata: dict[str, Any]) -> "TileContract":
        validate_tile_contract(metadata)
        return cls(**{key: metadata[key] for key in REQUIRED_FIELDS})


def validate_tile_contract(metadata: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_FIELDS if key not in metadata]
    if missing:
        raise DataContractError(f"Missing tile contract fields: {', '.join(missing)}")
    if metadata["schema_version"] != "1.0":
        raise DataContractError(f"Unsupported tile contract schema: {metadata['schema_version']}")
    if not isinstance(metadata["transform"], (list, tuple)) or len(metadata["transform"]) != 6:
        raise DataContractError("transform must contain six affine coefficients")
    if metadata["width"] <= 0 or metadata["height"] <= 0:
        raise DataContractError("width and height must be positive")
    if not metadata["crs"]:
        raise DataContractError("crs is required")
    if not isinstance(metadata["origin"], dict) or not {"x", "y"} <= metadata["origin"].keys():
        raise DataContractError("origin must contain x and y")
    if not metadata["source_checksum"]:
        raise DataContractError("source_checksum is required")


def load_tile_contract(path: str | Path) -> TileContract:
    import json
    with Path(path).open() as handle:
        metadata = json.load(handle)
    return TileContract.from_dict(metadata)


def write_tile_contract(path: str | Path, metadata: dict[str, Any]) -> None:
    validate_tile_contract(metadata)
    write_json(path, metadata)
