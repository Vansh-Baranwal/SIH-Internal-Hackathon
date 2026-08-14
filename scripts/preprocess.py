#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse
from lunar_hazard_mapper.m1_data.preprocessing import preprocess_raster
from lunar_hazard_mapper.m1_data.utils import load_config

def main() -> int:
    p=argparse.ArgumentParser(description="Apply configured deterministic raster preprocessing.")
    p.add_argument("--input", required=True); p.add_argument("--output", required=True); p.add_argument("--config", default="configs/preprocessing.yaml")
    a=p.parse_args(); preprocess_raster(a.input,a.output,load_config(a.config)); print(f"Wrote {a.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
