#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse
from lunar_hazard_mapper.m1_data.reference_catalog import register_references

def main() -> int:
    p=argparse.ArgumentParser(description="Register caller-provided high-resolution reference rasters.")
    p.add_argument("--input", nargs="*", default=[]); p.add_argument("--output", default="data/manifests/reference_manifest.json"); p.add_argument("--source-type", default="unknown")
    a=p.parse_args(); register_references(a.input,a.output,source_type=a.source_type); print(f"Wrote {a.output}"); return 0
if __name__ == "__main__": raise SystemExit(main())
