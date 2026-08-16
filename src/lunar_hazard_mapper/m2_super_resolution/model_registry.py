"""Deterministic registry for trained Member 2 checkpoints."""
from __future__ import annotations
import hashlib, json
from pathlib import Path

def register_checkpoint(path: Path, model_type: str, metrics: dict, registry_path: Path) -> dict:
    digest=hashlib.sha256(path.read_bytes()).hexdigest(); record={"model_type":model_type,"checkpoint":str(path),"sha256":digest,"metrics":metrics}
    records=json.loads(registry_path.read_text()) if registry_path.exists() else []; records=[r for r in records if r.get("checkpoint")!=str(path)]+[record]; registry_path.parent.mkdir(parents=True,exist_ok=True); registry_path.write_text(json.dumps(records,indent=2)); return record

def best_checkpoint(registry_path: Path):
    records=json.loads(registry_path.read_text()) if registry_path.exists() else []
    return max(records,key=lambda r:r.get("metrics",{}).get("psnr",float("-inf")),default=None)
