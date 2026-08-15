#!/usr/bin/env python3
"""Build the evidence-gated M1-to-M2 training-pair contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lunar_hazard_mapper.m1_data.pairs import build_pairs_manifest, co_register_pair, spatial_split  # noqa: E402


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def main() -> int:
    """Attempt only catalogue-supported pairs and always publish a manifest."""
    paths = _load(PROJECT_ROOT / "configs" / "paths.yaml")
    config = _load(PROJECT_ROOT / "configs" / "preprocessing.yaml")
    manifests = PROJECT_ROOT / paths.get("manifests", "data/manifests")
    tile_manifest = json.loads((manifests / "tile_manifest.json").read_text(encoding="utf-8"))
    output = PROJECT_ROOT / paths.get("training_pairs", "data/training_pairs")
    records: list[dict[str, Any]] = []
    failures: list[str] = []
    hr_by_path = {item["tile_path"]: item for item in tile_manifest.get("hr_tiles", [])}
    for lr in tile_manifest.get("lr_tiles", []):
        if not lr.get("reference_available"):
            continue
        for hr_path in lr.get("reference_hr_paths", []):
            hr = hr_by_path.get(hr_path)
            if hr is None:
                failures.append(f"missing HR tile metadata: {hr_path}")
                continue
            pair_id = Path(lr["tile_path"]).stem
            result = co_register_pair(lr, hr, output / "lr" / f"{pair_id}.tif", output / "hr" / f"{pair_id}.tif")
            if result is None:
                failures.append(f"co-registration failed: {pair_id}")
            else:
                result["id"] = pair_id
                records.append(result)
    if records:
        records = spatial_split(records, config)
    status = "ready" if records else "blocked_no_validated_pairs"
    manifest = build_pairs_manifest(records, output / "manifest.json", status=status, failure_reasons=failures or ["No validated TMC-to-HR spatial correspondences were present in the Phase 4 manifest."])
    print(f"Training pairs: {manifest['total_pairs']}")
    print(f"Splits: train={manifest['train_count']} val={manifest['val_count']} test={manifest['test_count']}")
    print(f"Failed or unavailable correspondences: {len(manifest['failure_reasons'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
