#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse, json
from pathlib import Path
from lunar_hazard_mapper.m1_data.training_pairs import build_training_pairs, write_training_pair_manifest
from lunar_hazard_mapper.m1_data.utils import load_config

def main() -> int:
    p=argparse.ArgumentParser(description="Build explicitly synthetic low/high-resolution training pairs.")
    p.add_argument("--tmc-manifest", required=True); p.add_argument("--reference-manifest", required=True); p.add_argument("--output", default="data/manifests/training_pairs.json"); p.add_argument("--config", default="configs/preprocessing.yaml")
    a=p.parse_args(); tmc=json.loads(Path(a.tmc_manifest).read_text()).get("tiles",[]); refs=json.loads(Path(a.reference_manifest).read_text()).get("references",[]); records=build_training_pairs(tmc,refs,load_config(a.config).get("training_pairs",{}).get("output","data/processed/training_pairs"),load_config(a.config)); write_training_pair_manifest(records,a.output); print(f"Generated {len(records)} synthetic pairs"); return 0
if __name__ == "__main__": raise SystemExit(main())
