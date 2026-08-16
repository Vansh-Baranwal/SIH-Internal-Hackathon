"""Neural super-resolution models owned by Member 2."""

from __future__ import annotations

try:
    import torch
    from torch import nn
except ImportError as exc:  # pragma: no cover - exercised in dependency-light environments
    raise ImportError("M2 CNN models require PyTorch; install the project's deep-learning dependencies") from exc


class ResidualBlock(nn.Module):
    """Two-convolution residual block used by the CNN baseline."""

    def __init__(self, n_features: int) -> None:
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(n_features, n_features, 3, padding=1),
            nn.BatchNorm2d(n_features),
            nn.ReLU(inplace=True),
            nn.Conv2d(n_features, n_features, 3, padding=1),
            nn.BatchNorm2d(n_features),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.block(x)


class SimpleSRCNN(nn.Module):
    """Small residual CNN with PixelShuffle upsampling."""

    def __init__(self, scale_factor: int, n_residual_blocks: int = 8,
                 n_features: int = 64, in_channels: int = 1) -> None:
        super().__init__()
        if scale_factor < 1 or scale_factor & (scale_factor - 1):
            raise ValueError("scale_factor must be a positive power of two")
        if n_residual_blocks < 0 or n_features < 1:
            raise ValueError("model dimensions must be positive")
        self.scale_factor = scale_factor
        self.in_channels = in_channels
        self.head = nn.Conv2d(in_channels, n_features, 3, padding=1)
        self.residuals = nn.Sequential(*(ResidualBlock(n_features) for _ in range(n_residual_blocks)))
        stages = []
        factor = scale_factor
        while factor > 1:
            stages.extend([nn.Conv2d(n_features, n_features * 4, 3, padding=1), nn.PixelShuffle(2), nn.ReLU(inplace=True)])
            factor //= 2
        self.upsampler = nn.Sequential(*stages)
        self.tail = nn.Conv2d(n_features, in_channels, 3, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x.float()
        head = self.head(x)
        features = self.residuals(head)
        return self.tail(self.upsampler(features))
