#!/usr/bin/env python3
"""Run M1 QA, checksums, and downstream contract generation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from lunar_hazard_mapper.m1_data.checksums import build_checksum_manifest, save_checksum_manifest  # noqa: E402
from lunar_hazard_mapper.m1_data.qa import run_qa_suite  # noqa: E402


def main() -> int:
    paths = yaml.safe_load((PROJECT_ROOT / "configs" / "paths.yaml").read_text(encoding="utf-8")) or {}
    config: dict[str, Any] = yaml.safe_load((PROJECT_ROOT / "configs" / "preprocessing.yaml").read_text(encoding="utf-8")) or {}
    manifests = PROJECT_ROOT / paths.get("manifests", "data/manifests")
    pair_manifest_path = PROJECT_ROOT / paths.get("training_pairs", "data/training_pairs") / "manifest.json"
    report = run_qa_suite(pair_manifest_path, config)
    qa_path = manifests / "qa_report.json"
    qa_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    pair_manifest = json.loads(pair_manifest_path.read_text(encoding="utf-8"))
    pair_root = pair_manifest_path.parent
    files = [Path(pair["lr_path"]) for pair in pair_manifest.get("pairs", [])] + [Path(pair["hr_path"]) for pair in pair_manifest.get("pairs", [])]
    checksum_path = manifests / "checksums.json"
    save_checksum_manifest(build_checksum_manifest(files), checksum_path)
    stats = {}
    stats_path = manifests / "normalisation_stats.json"
    if stats_path.exists():
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
    pairs = pair_manifest.get("pairs", [])
    first = pairs[0] if pairs else {}
    contract = {"version": "1.0", "produced_by": "Member 1", "consumed_by": "Member 2", "training_pairs_root": "data/training_pairs/", "manifest_path": "data/training_pairs/manifest.json", "lr_pixel_size_m": first.get("lr_pixel_size_m"), "hr_pixel_size_m": first.get("hr_pixel_size_m"), "scale_factor": first.get("scale_factor"), "crs": first.get("crs"), "normalisation": {"method": "percentile_clip_to_01", "stats_path": "data/manifests/normalisation_stats.json"}, "split_counts": {"train": pair_manifest.get("train_count", 0), "val": pair_manifest.get("val_count", 0), "test": pair_manifest.get("test_count", 0)}, "qa_report_path": "data/manifests/qa_report.json", "checksums_path": "data/manifests/checksums.json", "status": pair_manifest.get("status"), "ready_for_m2": bool(pair_manifest.get("total_pairs")), "limitation": "No validated TMC-to-HR spatial correspondences are currently available."}
    (manifests / "data_contract_m1_to_m2.json").write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(f"QA: passed={report['passed']} failed={report['failed']}")
    print(f"Checksums: {len(files)} files")
    print(f"M2 contract status: {contract['status']}")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
