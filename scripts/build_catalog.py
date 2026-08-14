#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse
from lunar_hazard_mapper.m1_data.catalog import build_source_catalog

def main() -> int:
    p=argparse.ArgumentParser(description="Build a deterministic source raster catalogue.")
    p.add_argument("--input", nargs="+", required=True); p.add_argument("--output", default="data/manifests/source_manifest.json"); p.add_argument("--allow-unreferenced", action="store_true")
    a=p.parse_args(); build_source_catalog(a.input,a.output,allow_unreferenced=a.allow_unreferenced); print(f"Wrote {a.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
