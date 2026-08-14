"""End-to-end orchestration for the independently testable M1 stages."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .catalog import build_source_catalog
from .qa import run_qa
from .tiling import create_tiles, write_tile_manifest
from .utils import load_config, write_json

LOGGER = logging.getLogger(__name__)


def run_pipeline(source: str | Path, config_path: str | Path = "configs/preprocessing.yaml") -> dict[str, Any]:
    config = load_config(config_path)
    manifest_dir = Path(config.get("paths", {}).get("manifest_output", "data/manifests"))
    tile_dir = Path(config.get("paths", {}).get("tile_output", "data/processed/tmc_tiles"))
    qa_dir = Path(config.get("paths", {}).get("qa_output", "results/data_qa"))
    source_manifest = build_source_catalog([source], manifest_dir / "source_manifest.json",
                                           allow_unreferenced=bool(config.get("allow_unreferenced", False)))
    tiling = config.get("tiling", {})
    records = create_tiles(source, tile_dir, tile_width=int(tiling.get("tile_width", 256)),
                           tile_height=int(tiling.get("tile_height", 256)), overlap=int(tiling.get("overlap", 0)),
                           padding=bool(tiling.get("padding", False)))
    write_tile_manifest(records, manifest_dir / "tile_manifest.json")
    report = run_qa(records, output=qa_dir / "qa_report.json")
    if report["status"] != "PASS":
        raise RuntimeError(f"M1 QA failed: {report['errors']}")
    return {"source_manifest": source_manifest, "tiles": records, "qa": report}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run the Member 1 data pipeline.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", default="configs/preprocessing.yaml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_pipeline(args.input, args.config)
    LOGGER.info("Member 1 pipeline completed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
