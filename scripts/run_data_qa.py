#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[1] / "src"))
import argparse, json
from pathlib import Path
from lunar_hazard_mapper.m1_data.qa import run_qa

def main() -> int:
    p=argparse.ArgumentParser(description="Run Member 1 raster and provenance QA.")
    p.add_argument("--manifest", required=True); p.add_argument("--output", default="results/data_qa/qa_report.json")
    a=p.parse_args(); records=json.loads(Path(a.manifest).read_text())["tiles"]; report=run_qa(records,output=a.output); print(f"QA {report['status']}"); return 0 if report["status"] == "PASS" else 1
if __name__ == "__main__": raise SystemExit(main())
