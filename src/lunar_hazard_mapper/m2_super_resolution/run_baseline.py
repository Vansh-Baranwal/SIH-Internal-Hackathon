"""Run and record Member 2 interpolation baselines."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

try:
    from .dataset import ContractValidationError, SRDataset
except ModuleNotFoundError as exc:  # Allow blocked-contract reporting without PyTorch.
    if exc.name != "torch":
        raise
    ContractValidationError = ValueError
    SRDataset = None

try:
    from .baselines import run_baseline
except ModuleNotFoundError as exc:  # Allow blocked-contract reporting without PyTorch.
    if exc.name != "torch":
        raise
    run_baseline = None


def _manifest_is_blocked(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("status") == "blocked_no_validated_pairs" or payload.get("total_pairs", 0) == 0


def _blocked_payload(args, reason: str) -> dict:
    return {"status": "blocked_no_validated_pairs", "metrics_type": "none", "split": args.split,
            "reason": reason, "results": {}}


def _write_config(path: Path, payload: dict) -> None:
    if yaml is not None:
        path.write_text(yaml.safe_dump(payload, sort_keys=False))
    else:
        path.write_text(json.dumps(payload, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/training_pairs/manifest.json"))
    parser.add_argument("--split", default="val")
    parser.add_argument("--scale-factor", type=int, default=None)
    parser.add_argument("--output-root", type=Path, default=Path("experiments"))
    args = parser.parse_args(argv)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    experiment_dir = args.output_root / f"bicubic_baseline_{timestamp}"
    experiment_dir.mkdir(parents=True, exist_ok=True)
    config = {"manifest_path": str(args.manifest), "split": args.split, "timestamp": timestamp,
              "status": "blocked_no_validated_pairs", "metrics_type": "production"}
    if _manifest_is_blocked(args.manifest):
        reason = "M1-to-M2 contract is blocked_no_validated_pairs: no production SR training is permitted."
        (experiment_dir / "metrics.json").write_text(json.dumps(_blocked_payload(args, reason), indent=2))
        _write_config(experiment_dir / "config.yaml", config)
        print(f"Baseline blocked: {reason}")
        return 2
    if run_baseline is None:
        raise RuntimeError("PyTorch is required to run baselines; install project deep-learning dependencies")
    try:
        dataset = SRDataset(args.manifest, args.split)
        scale = args.scale_factor
        if scale is None:
            raise ContractValidationError("--scale-factor is required because the manifest has no validated pair metadata")
        results = {method: run_baseline(dataset, method, scale) for method in ("bicubic", "nearest")}
        payload = {"status": "completed", "metrics_type": "production", "split": args.split, "results": results}
        config["status"] = "completed"
    except ContractValidationError as exc:
        payload = {"status": "blocked_no_validated_pairs", "metrics_type": "none", "split": args.split,
                   "reason": str(exc), "results": {}}
        print(f"Baseline blocked: {exc}")
        _write_config(experiment_dir / "config.yaml", config)
        (experiment_dir / "metrics.json").write_text(json.dumps(payload, indent=2))
        return 2
    config["scale_factor"] = scale
    _write_config(experiment_dir / "config.yaml", config)
    (experiment_dir / "metrics.json").write_text(json.dumps(payload, indent=2, allow_nan=False))
    print("Method | PSNR | SSIM")
    for name, result in results.items():
        print(f"{name} | {result['psnr_mean']:.4f} | {result['ssim_mean']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
