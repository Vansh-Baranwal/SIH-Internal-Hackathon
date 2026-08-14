#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse
from lunar_hazard_mapper.m1_data.tiling import create_tiles, write_tile_manifest

def main() -> int:
    p=argparse.ArgumentParser(description="Create deterministic georeferenced raster tiles.")
    p.add_argument("--input", required=True); p.add_argument("--output", required=True); p.add_argument("--tile-size", type=int); p.add_argument("--tile-width", type=int); p.add_argument("--tile-height", type=int); p.add_argument("--overlap", type=int, default=0); p.add_argument("--padding", action="store_true"); p.add_argument("--manifest")
    a=p.parse_args(); size=a.tile_size or 256; records=create_tiles(a.input,a.output,tile_width=a.tile_width or size,tile_height=a.tile_height or size,overlap=a.overlap,padding=a.padding)
    if a.manifest: write_tile_manifest(records,a.manifest)
    print(f"Generated {len(records)} tiles"); return 0
if __name__ == "__main__": raise SystemExit(main())
