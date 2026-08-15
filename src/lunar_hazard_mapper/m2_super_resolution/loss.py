"""SRGAN content and adversarial losses."""
from __future__ import annotations

import torch
from torch import nn


class VGGPerceptualLoss(nn.Module):
    """Frozen VGG feature loss, with an offline-safe lightweight fallback."""
    def __init__(self, layer: int = 18, pretrained: bool = False) -> None:
        super().__init__()
        self.layer = layer
        try:
            from torchvision import models
            weights = models.VGG19_Weights.DEFAULT if pretrained else None
            net = models.vgg19(weights=weights).features
            self.features = net[:layer].eval()
        except (ImportError, RuntimeError):
            self.features = nn.Sequential(
                nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(),
                nn.Conv2d(16, 16, 3, padding=1), nn.ReLU(),
            ).eval()
        for parameter in self.features.parameters():
            parameter.requires_grad_(False)

    @staticmethod
    def _three_channels(x: torch.Tensor) -> torch.Tensor:
        if x.shape[1] == 1:
            return x.repeat(1, 3, 1, 1)
        if x.shape[1] != 3:
            raise ValueError("perceptual loss expects one or three channels")
        return x

    def forward(self, pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        pred_features = self.features(self._three_channels(pred.float()))
        with torch.no_grad():
            target_features = self.features(self._three_channels(target.float()))
        return nn.functional.mse_loss(pred_features, target_features)


class SRGANLoss(nn.Module):
    def __init__(self, pixel_weight: float = 1.0, perceptual_weight: float = 1.0,
                 adversarial_weight: float = 1e-3, perceptual_loss: nn.Module | None = None) -> None:
        super().__init__()
        self.pixel_weight = pixel_weight
        self.perceptual_weight = perceptual_weight
        self.adversarial_weight = adversarial_weight
        self.perceptual = perceptual_loss or VGGPerceptualLoss()
        self.adversarial = nn.BCEWithLogitsLoss()

    def forward(self, pred: torch.Tensor, target: torch.Tensor, disc_pred_on_fake: torch.Tensor) -> dict[str, torch.Tensor]:
        pixel = nn.functional.l1_loss(pred, target)
        perceptual = self.perceptual(pred, target)
        adversarial = self.adversarial(disc_pred_on_fake, torch.ones_like(disc_pred_on_fake))
        total = self.pixel_weight * pixel + self.perceptual_weight * perceptual + self.adversarial_weight * adversarial
        return {"pixel_loss": pixel, "perceptual_loss": perceptual, "adversarial_loss": adversarial, "total_loss": total}
