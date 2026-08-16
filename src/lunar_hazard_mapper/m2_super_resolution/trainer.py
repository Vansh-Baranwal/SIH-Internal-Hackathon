"""Reusable supervised SR training loop owned by Member 2."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import torch
from torch import nn

from .metrics import psnr, ssim


class SRTrainer:
    """Train a model on validated LR/HR batches and record checkpoints."""

    def __init__(self, model, optimizer, loss_fn, train_loader, val_loader,
                 device, config: dict[str, Any], experiment_dir: Path):
        if len(train_loader) == 0 or len(val_loader) == 0:
            raise ValueError("SR training requires non-empty validated train and val loaders")
        self.model, self.optimizer, self.loss_fn = model, optimizer, loss_fn
        self.train_loader, self.val_loader = train_loader, val_loader
        self.device = torch.device(device)
        self.config = dict(config)
        self.experiment_dir = Path(experiment_dir)
        self.experiment_dir.mkdir(parents=True, exist_ok=True)
        self.model.to(self.device)
        self.best_psnr = float("-inf")

    def train_epoch(self, epoch: int) -> dict[str, float]:
        del epoch
        self.model.train()
        losses = []
        for batch in self.train_loader:
            lr, hr = batch["lr"].to(self.device), batch["hr"].to(self.device)
            self.optimizer.zero_grad(set_to_none=True)
            loss = self.loss_fn(self.model(lr), hr)
            loss.backward()
            self.optimizer.step()
            losses.append(float(loss.detach().cpu()))
        return {"loss": sum(losses) / len(losses)}

    @torch.no_grad()
    def validate(self) -> dict[str, float]:
        self.model.eval()
        losses, psnrs, ssims = [], [], []
        for batch in self.val_loader:
            pred = self.model(batch["lr"].to(self.device))
            target = batch["hr"].to(self.device)
            losses.append(float(self.loss_fn(pred, target).cpu()))
            for p, t in zip(pred.cpu(), target.cpu()):
                psnrs.append(psnr(p, t))
                ssims.append(ssim(p, t))
        return {"loss": sum(losses) / len(losses), "psnr": sum(psnrs) / len(psnrs), "ssim": sum(ssims) / len(ssims)}

    def save_checkpoint(self, epoch: int, metrics: dict[str, float], is_best: bool = False) -> Path:
        payload = {"epoch": epoch, "model_state_dict": self.model.state_dict(),
                   "optimizer_state_dict": self.optimizer.state_dict(), "metrics": metrics, "config": self.config}
        path = self.experiment_dir / f"checkpoint_epoch_{epoch}.pth"
        torch.save(payload, path)
        if is_best:
            torch.save(payload, self.experiment_dir / "checkpoint_best.pth")
        return path

    def run(self, num_epochs: int) -> dict[str, float]:
        log_path = self.experiment_dir / "training_log.csv"
        with log_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["epoch", "train_loss", "val_psnr", "val_ssim"])
            writer.writeheader()
            final = {}
            interval = int(self.config.get("checkpoint_every", 1))
            for epoch in range(1, num_epochs + 1):
                train = self.train_epoch(epoch)
                val = self.validate()
                final = val
                is_best = val["psnr"] > self.best_psnr
                if is_best:
                    self.best_psnr = val["psnr"]
                writer.writerow({"epoch": epoch, "train_loss": train["loss"], "val_psnr": val["psnr"], "val_ssim": val["ssim"]})
                handle.flush()
                if epoch % interval == 0 or is_best:
                    self.save_checkpoint(epoch, val, is_best)
        return final
