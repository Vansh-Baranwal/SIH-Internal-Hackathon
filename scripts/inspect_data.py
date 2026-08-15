#!/usr/bin/env python3
"""Generate M1 GeoTIFF inspection manifests for the selected SIH reference data."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml
from tabulate import tabulate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lunar_hazard_mapper.m1_data.metadata import inspect_directory, summarise  # noqa: E402


DATASETS = {
    "TMCORTHO5-1": "tmc_source",
    "ORTHONAC0.5-1": "hr_source",
    "NAC": "nac_source",
    "TMCDTM": "dem_source",
}


def load_paths() -> dict[str, Any]:
    """Load path configuration and resolve the canonical SIH root."""
    with (PROJECT_ROOT / "configs" / "paths.yaml").open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    configured_root = Path(os.environ.get("SIH_ROOT", config["sih_root"]))
    config["sih_root"] = configured_root if configured_root.is_absolute() else PROJECT_ROOT / configured_root
    return config


def main() -> int:
    """Inspect all configured datasets and write manifests."""
    config = load_paths()
    manifest_dir = PROJECT_ROOT / config.get("manifests", "data/manifests")
    manifest_dir.mkdir(parents=True, exist_ok=True)
    all_summaries: dict[str, dict[str, Any]] = {}

    for label, config_key in DATASETS.items():
        source = Path(config["sih_root"]) / config[config_key]
        if not source.is_dir():
            raise FileNotFoundError(f"Configured {label} directory does not exist: {source}")
        records = inspect_directory(source)
        summary = summarise(records)
        all_summaries[label] = summary
        payload = {"dataset": label, "source": source.as_posix(), "records": records, "summary": summary}
        output = manifest_dir / f"inspection_{label}.json"
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(tabulate([[label, summary["total_files"], summary["total_size_mb"], summary["pixel_size_range"]]], headers=["dataset", "files", "size_mb", "pixel_size_m"]))

    combined = manifest_dir / "inspection_summary.json"
    combined.write_text(json.dumps(all_summaries, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote inspection manifests to {manifest_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
