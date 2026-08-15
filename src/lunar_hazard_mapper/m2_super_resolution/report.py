"""Truthful SR experiment report generation."""
from __future__ import annotations
import json
from pathlib import Path

def build_report(results: list[dict], output_dir: Path) -> dict:
    valid=[r for r in results if r.get("status")=="completed" and r.get("psnr") is not None]
    report={"status":"completed" if valid else "blocked_no_valid_results","results":sorted(results,key=lambda r:r.get("psnr",float("-inf")),reverse=True),"best_model":valid[0].get("model") if valid else None,"caveats":[] if valid else ["No validated production results were available; no best model was selected."]}
    output_dir.mkdir(parents=True,exist_ok=True); (output_dir/"sr_evaluation_report.json").write_text(json.dumps(report,indent=2)); (output_dir/"sr_evaluation_report.txt").write_text("SR evaluation report\nStatus: "+report["status"]+"\n"+"\n".join(f'{r.get("model")}: {r.get("psnr", "n/a")}' for r in report["results"]))
    return report
