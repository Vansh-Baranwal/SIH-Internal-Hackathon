"""Geographic block assignment and leakage checks."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

from shapely.geometry import box

from .errors import SpatialLeakageError
from .utils import write_json


def _region_id(record: dict[str, Any], width: float, height: float) -> str:
    bounds = record["bounds"]
    x = int(bounds["left"] // width)
    y = int(bounds["bottom"] // height)
    return f"block_{x}_{y}"


def _split_for_region(region: str, seed: int, train: float, validation: float) -> str:
    digest = hashlib.sha256(f"{seed}:{region}".encode()).hexdigest()
    value = int(digest[:16], 16) / 16**16
    if value < train:
        return "train"
    if value < train + validation:
        return "validation"
    return "test"


def validate_split_leakage(records: list[dict[str, Any]], tolerance: float = 1e-9) -> None:
    by_split: dict[str, list[Any]] = defaultdict(list)
    for record in records:
        if record.get("split") not in {"train", "validation", "test"}:
            raise SpatialLeakageError(f"Missing or invalid split for {record.get('pair_id', record.get('tile_id'))}")
        bounds = record["bounds"]
        by_split[record["split"]].append(box(bounds["left"], bounds["bottom"], bounds["right"], bounds["top"]))
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        for first in by_split[left]:
            for second in by_split[right]:
                if first.intersection(second).area > tolerance:
                    raise SpatialLeakageError(f"Geographic overlap between {left} and {right}")


def assign_geographic_splits(records: list[dict[str, Any]], config: dict[str, Any], output: str) -> dict[str, Any]:
    settings = config.get("split", config)
    fractions = [float(settings.get(k, 0)) for k in ("train_fraction", "validation_fraction", "test_fraction")]
    if abs(sum(fractions) - 1.0) > 1e-6:
        raise ValueError("split fractions must sum to 1")
    regions = {}
    for record in records:
        region = _region_id(record, float(settings.get("block_width", 1000)), float(settings.get("block_height", 1000)))
        regions[region] = _split_for_region(region, int(settings.get("seed", 42)), fractions[0], fractions[1])
        record["spatial_region_id"] = region
        record["split"] = regions[region]
    # Blocks are disjoint by construction; this also catches malformed input records.
    validate_split_leakage(records, float(settings.get("tolerance", 1e-9)))
    result = {"split_version": "v1", "seed": int(settings.get("seed", 42)), "method": "geographic_blocks",
              "region_assignments": dict(sorted(regions.items())),
              "train_regions": sorted(r for r, s in regions.items() if s == "train"),
              "validation_regions": sorted(r for r, s in regions.items() if s == "validation"),
              "test_regions": sorted(r for r, s in regions.items() if s == "test"),
              "leakage_check": {"passed": True}}
    write_json(output, result)
    return result
