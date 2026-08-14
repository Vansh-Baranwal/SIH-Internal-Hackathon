#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse, json
from pathlib import Path
from lunar_hazard_mapper.m1_data.spatial_split import assign_geographic_splits
from lunar_hazard_mapper.m1_data.utils import load_config, write_json

def main() -> int:
    p=argparse.ArgumentParser(description="Assign samples to disjoint geographic blocks.")
    p.add_argument("--input", required=True); p.add_argument("--output", default="data/manifests/split_manifest.json"); p.add_argument("--config", default="configs/preprocessing.yaml")
    a=p.parse_args(); payload=json.loads(Path(a.input).read_text()); records=payload.get("pairs",payload.get("tiles",[])); result=assign_geographic_splits(records,load_config(a.config),a.output); write_json(a.input,payload); print(f"Assigned {len(records)} records"); return 0
if __name__ == "__main__": raise SystemExit(main())
