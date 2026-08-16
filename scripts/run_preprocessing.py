#!/usr/bin/env python3
"""Run M1 radiometric normalization using training-only statistics."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lunar_hazard_mapper.m1_data.preprocessing import compute_normalisation_stats, preprocess_directory  # noqa: E402


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    """Compute frozen statistics and normalize all available LR/HR tiles."""
    paths = load_yaml(PROJECT_ROOT / "configs" / "paths.yaml")
    config = load_yaml(PROJECT_ROOT / "configs" / "preprocessing.yaml")
    manifest_path = PROJECT_ROOT / paths.get("manifests", "data/manifests") / "tile_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lr_dir = PROJECT_ROOT / paths.get("processed_tiles", "data/processed/tmc_tiles") / "lr"
    hr_dir = PROJECT_ROOT / paths.get("processed_tiles", "data/processed/tmc_tiles") / "hr"
    lr_paths = sorted(lr_dir.glob("*.tif"))
    if not lr_paths:
        raise FileNotFoundError(f"No LR tiles found in {lr_dir}")
    radiometric = config["radiometric"]
    nodata_value = float(config.get("nodata_value", -9999.0))
    stats = compute_normalisation_stats(lr_paths, float(radiometric["clip_percentile_low"]), float(radiometric["clip_percentile_high"]), nodata_value)
    stats.update({"source": "LR tiles only", "split_policy": "all_available_lr_tiles_training_no_holdout"})
    stats_path = PROJECT_ROOT / paths.get("manifests", "data/manifests") / "normalisation_stats.json"
    stats_path.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    processed_root = PROJECT_ROOT / paths.get("processed_tiles", "data/processed/tmc_tiles")
    lr_results = preprocess_directory(lr_dir, processed_root / "lr_norm", stats, config)
    hr_results = preprocess_directory(hr_dir, processed_root / "hr_norm", stats, config)
    manifest.update({
        "normalisation": {"stats_path": stats_path.as_posix(), "training_tile_count": len(lr_paths), "holdout_available": False},
        "lr_norm": lr_results,
        "hr_norm": hr_results,
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Computed stats from {len(lr_paths)} LR training tiles")
    print(f"Normalized LR tiles: {sum(item['success'] for item in lr_results)}")
    print(f"Normalized HR tiles: {sum(item['success'] for item in hr_results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
