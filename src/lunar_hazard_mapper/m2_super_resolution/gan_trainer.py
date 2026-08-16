"""Reusable two-stage SRGAN training loop."""
from __future__ import annotations
import csv
from pathlib import Path
from typing import Any
import torch
from .loss import SRGANLoss
from .metrics import psnr, ssim

class SRGANTrainer:
    def __init__(self, generator, discriminator, g_optimizer, d_optimizer, train_loader, val_loader, device, config: dict[str, Any], experiment_dir: Path):
        if len(train_loader) == 0 or len(val_loader) == 0: raise ValueError("GAN training requires non-empty loaders")
        self.generator, self.discriminator = generator, discriminator
        self.g_optimizer, self.d_optimizer = g_optimizer, d_optimizer
        self.train_loader, self.val_loader = train_loader, val_loader
        self.device, self.config, self.experiment_dir = torch.device(device), dict(config), Path(experiment_dir)
        self.experiment_dir.mkdir(parents=True, exist_ok=True); self.generator.to(self.device); self.discriminator.to(self.device)
        self.loss = SRGANLoss(config.get("pixel_weight", 1.0), config.get("perceptual_weight", 1.0), config.get("adversarial_weight", 1e-3))
        self.bce = torch.nn.BCEWithLogitsLoss(); self.best_psnr = float("-inf")

    def _batch(self, batch): return batch["lr"].to(self.device), batch["hr"].to(self.device)
    def train_epoch(self, epoch: int, adversarial: bool = True) -> dict[str, float]:
        self.generator.train(); self.discriminator.train(); g_losses=[]; d_losses=[]
        for batch in self.train_loader:
            lr, hr = self._batch(batch); fake = self.generator(lr)
            self.d_optimizer.zero_grad(set_to_none=True)
            real_loss=self.bce(self.discriminator(hr), torch.ones_like(self.discriminator(hr))); fake_loss=self.bce(self.discriminator(fake.detach()), torch.zeros_like(self.discriminator(fake.detach())))
            d_loss=(real_loss+fake_loss)*0.5; d_loss.backward(); self.d_optimizer.step(); d_losses.append(float(d_loss.detach().cpu()))
            self.g_optimizer.zero_grad(set_to_none=True)
            components=self.loss(fake, hr, self.discriminator(fake)) if adversarial else {"total_loss": torch.nn.functional.l1_loss(fake, hr)}
            components["total_loss"].backward(); self.g_optimizer.step(); g_losses.append(float(components["total_loss"].detach().cpu()))
        return {"g_loss": sum(g_losses)/len(g_losses), "d_loss": sum(d_losses)/len(d_losses)}

    @torch.no_grad()
    def validate(self):
        self.generator.eval(); psnrs=[]; ssims=[]
        for batch in self.val_loader:
            pred=self.generator(batch["lr"].to(self.device)).cpu(); target=batch["hr"]
            for p,t in zip(pred,target): psnrs.append(psnr(p,t)); ssims.append(ssim(p,t))
        return {"psnr":sum(psnrs)/len(psnrs), "ssim":sum(ssims)/len(ssims)}

    def save_checkpoint(self, epoch, metrics, is_best=False):
        payload={"epoch":epoch,"generator_state_dict":self.generator.state_dict(),"discriminator_state_dict":self.discriminator.state_dict(),"g_optimizer_state_dict":self.g_optimizer.state_dict(),"d_optimizer_state_dict":self.d_optimizer.state_dict(),"metrics":metrics,"config":self.config,"model_type":"srgan"}
        path=self.experiment_dir/f"checkpoint_epoch_{epoch}.pth"; torch.save(payload,path)
        if is_best: torch.save(payload,self.experiment_dir/"checkpoint_best.pth")
        return path

    def run(self, warmup_epochs: int, adversarial_epochs: int):
        rows=[]; total=warmup_epochs+adversarial_epochs
        with (self.experiment_dir/"training_log.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=["epoch","stage","g_loss","d_loss","psnr","ssim"]); writer.writeheader()
            for epoch in range(1,total+1):
                train=self.train_epoch(epoch, epoch> warmup_epochs); val=self.validate(); best=val["psnr"]>self.best_psnr
                if best:self.best_psnr=val["psnr"]
                self.save_checkpoint(epoch,val,best); row={"epoch":epoch,"stage":"adversarial" if epoch>warmup_epochs else "warmup",**train,**val}; writer.writerow(row); rows.append(row)
        return rows[-1]
