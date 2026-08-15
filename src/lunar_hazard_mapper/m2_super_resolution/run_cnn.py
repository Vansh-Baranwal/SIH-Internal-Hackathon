"""CLI entry point for Member 2 CNN training on validated pairs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/training_pairs/manifest.json"))
    parser.add_argument("--config", type=Path, default=Path("configs/sr_training.yaml"))
    parser.add_argument("--device", default=None, help="cpu, cuda, or auto")
    args = parser.parse_args(argv)
    try:
        import torch
        import yaml
        from torch.utils.data import DataLoader
        from .dataset import SRDataset
        from .models import SimpleSRCNN
        from .trainer import SRTrainer
    except ModuleNotFoundError as exc:
        print(f"CNN training unavailable: install PyTorch and dependencies ({exc.name})")
        return 2
    config = yaml.safe_load(args.config.read_text())
    manifest = json.loads(args.manifest.read_text())
    if manifest.get("status") == "blocked_no_validated_pairs" or manifest.get("total_pairs", 0) == 0:
        print("CNN training blocked: M1 manifest has no validated pairs; run M1 pair validation first.")
        return 2
    scale = int(config["model"]["scale_factor"])
    train_ds, val_ds = SRDataset(args.manifest, "train"), SRDataset(args.manifest, "val")
    device_name = args.device or config.get("device", "auto")
    device = "cuda" if device_name == "auto" and torch.cuda.is_available() else ("cpu" if device_name == "auto" else device_name)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    experiment_dir = Path("experiments") / f"{timestamp}_cnn"
    experiment_dir.mkdir(parents=True, exist_ok=True)
    (experiment_dir / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    kwargs = {"batch_size": config["training"]["batch_size"], "num_workers": config["training"]["num_workers"]}
    model = SimpleSRCNN(scale, config["model"]["n_residual_blocks"], config["model"]["n_features"])
    optimizer = torch.optim.Adam(model.parameters(), lr=config["training"]["learning_rate"])
    trainer = SRTrainer(model, optimizer, torch.nn.L1Loss(), DataLoader(train_ds, **kwargs), DataLoader(val_ds, **kwargs), device, config["training"], experiment_dir)
    metrics = trainer.run(config["training"]["epochs"])
    (experiment_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
