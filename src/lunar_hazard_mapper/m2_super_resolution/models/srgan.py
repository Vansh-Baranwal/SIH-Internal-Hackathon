"""SRGAN generator and discriminator architectures for Member 2."""
from __future__ import annotations

import torch
from torch import nn


def _validate_scale(scale_factor: int) -> None:
    if scale_factor < 1 or scale_factor & (scale_factor - 1):
        raise ValueError("scale_factor must be a positive power of two")


class SRResidualBlock(nn.Module):
    def __init__(self, n_features: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(n_features, n_features, 3, padding=1),
            nn.BatchNorm2d(n_features),
            nn.PReLU(n_features),
            nn.Conv2d(n_features, n_features, 3, padding=1),
            nn.BatchNorm2d(n_features),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.block(x)


class SRGANGenerator(nn.Module):
    """Grayscale-capable SRGAN generator with power-of-two upsampling."""
    def __init__(self, scale_factor: int, n_residual_blocks: int = 16,
                 n_features: int = 64, in_channels: int = 1) -> None:
        super().__init__()
        _validate_scale(scale_factor)
        if n_residual_blocks < 1 or n_features < 1 or in_channels < 1:
            raise ValueError("model dimensions must be positive")
        self.scale_factor = scale_factor
        self.in_channels = in_channels
        self.head = nn.Sequential(nn.Conv2d(in_channels, n_features, 9, padding=4), nn.PReLU(n_features))
        self.residuals = nn.Sequential(*(SRResidualBlock(n_features) for _ in range(n_residual_blocks)))
        self.post_residual = nn.Sequential(nn.Conv2d(n_features, n_features, 3, padding=1), nn.BatchNorm2d(n_features))
        stages = []
        factor = scale_factor
        while factor > 1:
            stages.extend([nn.Conv2d(n_features, n_features * 4, 3, padding=1), nn.PixelShuffle(2), nn.PReLU(n_features)])
            factor //= 2
        self.upsampler = nn.Sequential(*stages)
        self.tail = nn.Conv2d(n_features, in_channels, 9, padding=4)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.float()
        residual = self.head(x)
        features = residual + self.post_residual(self.residuals(residual))
        return self.tail(self.upsampler(features))


class DiscriminatorBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, stride: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, stride=stride, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class SRGANDiscriminator(nn.Module):
    def __init__(self, in_channels: int = 1, base_features: int = 64) -> None:
        super().__init__()
        if in_channels < 1 or base_features < 1:
            raise ValueError("model dimensions must be positive")
        b = base_features
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, b, 3, padding=1), nn.LeakyReLU(0.2, inplace=True),
            DiscriminatorBlock(b, b, 2), DiscriminatorBlock(b, b * 2, 1),
            DiscriminatorBlock(b * 2, b * 2, 2), DiscriminatorBlock(b * 2, b * 4, 1),
            DiscriminatorBlock(b * 4, b * 4, 2), DiscriminatorBlock(b * 4, b * 8, 1),
            DiscriminatorBlock(b * 8, b * 8, 2), nn.AdaptiveAvgPool2d((6, 6)),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(b * 8 * 36, 1024), nn.LeakyReLU(0.2, inplace=True), nn.Linear(1024, 1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(x.float()))
