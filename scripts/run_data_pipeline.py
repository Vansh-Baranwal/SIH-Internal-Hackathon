#!/usr/bin/env python3
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
from lunar_hazard_mapper.m1_data.pipeline import main
if __name__ == "__main__": raise SystemExit(main())
