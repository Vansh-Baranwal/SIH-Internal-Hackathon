#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse
from lunar_hazard_mapper.m1_data.metadata import inspect_raster
from lunar_hazard_mapper.m1_data.utils import write_json

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect TMC/GeoTIFF metadata without modifying the raster.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    parser.add_argument("--allow-unreferenced", action="store_true")
    args = parser.parse_args()
    print("Loading raster..."); print("Inspecting metadata..."); print("Checking CRS...")
    metadata = inspect_raster(args.input, allow_unreferenced=args.allow_unreferenced)
    print("Checking transform..."); print("Checking pixel size..."); print("Checking nodata..."); print("Checking dimensions...")
    print("\nMetadata summary:")
    for key in ("source_id", "width", "height", "count", "dtype", "crs", "pixel_size_x", "pixel_size_y", "nodata", "bounds"):
        print(f"  {key}: {metadata[key]}")
    if args.output: write_json(args.output, metadata)
    return 0
if __name__ == "__main__": raise SystemExit(main())
