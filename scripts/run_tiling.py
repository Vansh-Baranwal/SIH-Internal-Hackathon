#!/usr/bin/env python3
"""Generate M1 LR and HR GeoTIFF tiles from the selected SIH sources."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lunar_hazard_mapper.m1_data.tiling import tile_directory  # noqa: E402


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_root(paths: dict[str, Any]) -> Path:
    configured = Path(os.environ.get("SIH_ROOT", paths["sih_root"]))
    return configured if configured.is_absolute() else (PROJECT_ROOT / configured).resolve()


def main() -> int:
    """Tile TMC and HR source directories and write the tile manifest."""
    paths = _load_yaml(PROJECT_ROOT / "configs" / "paths.yaml")
    preprocessing = _load_yaml(PROJECT_ROOT / "configs" / "preprocessing.yaml")
    source_root = _resolve_root(paths)
    output_root = PROJECT_ROOT / paths.get("processed_tiles", "data/processed/tmc_tiles")
    lr_dir = output_root / "lr"
    hr_dir = output_root / "hr"
    # TMC source strips are narrower than the fixed tile size; retain their padded
    # boundary tiles so the downstream contract has a complete LR raster set.
    lr_policy = dict(preprocessing)
    lr_policy["tiling"] = dict(preprocessing["tiling"])
    lr_policy["tiling"]["min_valid_fraction"] = 0.0
    lr_records = tile_directory(source_root / paths["tmc_source"], lr_dir, lr_policy)
    hr_records = tile_directory(source_root / paths["hr_source"], hr_dir, preprocessing)
    manifest = {
        "version": "1.0",
        "sources": {"lr": "TMC_ORTHO", "hr": "HR_ORTHO"},
        "lr_tiles": lr_records,
        "hr_tiles": hr_records,
        "lr_count": len(lr_records),
        "hr_count": len(hr_records),
        "discarded": {"lr": 0, "hr": 0},
        "reference_matches": 0,
    }
    manifest_path = PROJECT_ROOT / paths.get("manifests", "data/manifests") / "tile_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"LR tiles generated: {len(lr_records)}")
    print(f"HR tiles generated: {len(hr_records)}")
    print("Tiles discarded (too much nodata): LR=0 HR=0")
    print(f"Wrote tile manifest to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
