"""Masked PSNR and SSIM metrics owned by Member 2."""

from __future__ import annotations

import math
from typing import Iterable

import torch
import torch.nn.functional as F


def _prepare(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor | None = None):
    pred, target = pred.float(), target.float()
    if pred.shape != target.shape:
        raise ValueError(f"Prediction and target shapes differ: {pred.shape} != {target.shape}")
    if mask is None:
        mask = torch.ones_like(target, dtype=torch.bool)
    else:
        mask = mask.to(dtype=torch.bool)
        if mask.shape != target.shape:
            mask = mask.expand_as(target)
    mask &= torch.isfinite(pred) & torch.isfinite(target)
    if not torch.any(mask):
        raise ValueError("Metric has no valid pixels")
    return pred, target, mask


def psnr(pred: torch.Tensor, target: torch.Tensor, max_val: float = 1.0, mask: torch.Tensor | None = None) -> float:
    """Return PSNR in dB over valid pixels."""
    if max_val <= 0:
        raise ValueError("max_val must be positive")
    pred, target, mask = _prepare(pred, target, mask)
    mse = torch.mean((pred[mask] - target[mask]) ** 2).item()
    return math.inf if mse == 0 else float(10.0 * math.log10((max_val**2) / mse))


def ssim(pred: torch.Tensor, target: torch.Tensor, window_size: int = 11, mask: torch.Tensor | None = None) -> float:
    """Compute a deterministic local SSIM score, supporting grayscale tensors."""
    pred, target, valid = _prepare(pred, target, mask)
    if window_size < 1 or window_size % 2 == 0:
        raise ValueError("window_size must be a positive odd integer")
    if pred.ndim == 2:
        pred, target, valid = pred[None, None], target[None, None], valid[None, None]
    elif pred.ndim == 3:
        pred, target, valid = pred[None], target[None], valid[None]
    kernel_size = min(window_size, pred.shape[-2], pred.shape[-1])
    if kernel_size % 2 == 0:
        kernel_size -= 1
    kernel_size = max(kernel_size, 1)
    kernel = torch.ones((pred.shape[1], 1, kernel_size, kernel_size), device=pred.device) / (kernel_size**2)
    mu_x = F.conv2d(pred, kernel, padding=kernel_size // 2, groups=pred.shape[1])
    mu_y = F.conv2d(target, kernel, padding=kernel_size // 2, groups=target.shape[1])
    sigma_x = F.conv2d(pred * pred, kernel, padding=kernel_size // 2, groups=pred.shape[1]) - mu_x * mu_x
    sigma_y = F.conv2d(target * target, kernel, padding=kernel_size // 2, groups=pred.shape[1]) - mu_y * mu_y
    sigma_xy = F.conv2d(pred * target, kernel, padding=kernel_size // 2, groups=pred.shape[1]) - mu_x * mu_y
    c1, c2 = 0.01**2, 0.03**2
    score = ((2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)) / ((mu_x**2 + mu_y**2 + c1) * (sigma_x + sigma_y + c2))
    valid = valid & (F.avg_pool2d(valid.float(), kernel_size=1) > 0)
    return float(score[valid].mean().item())


def evaluate_batch(preds: Iterable[torch.Tensor], targets: Iterable[torch.Tensor], masks: Iterable[torch.Tensor] | None = None) -> dict:
    """Evaluate corresponding predictions and targets, returning summary statistics."""
    pred_list, target_list = list(preds), list(targets)
    if len(pred_list) != len(target_list) or not pred_list:
        raise ValueError("preds and targets must be non-empty and have equal length")
    mask_list = list(masks) if masks is not None else [None] * len(pred_list)
    values = [(psnr(p, t, mask=m), ssim(p, t, mask=m)) for p, t, m in zip(pred_list, target_list, mask_list)]
    p, s = torch.tensor([v[0] for v in values]), torch.tensor([v[1] for v in values])
    return {"psnr_mean": float(p.mean()), "psnr_std": float(p.std(unbiased=False)),
            "ssim_mean": float(s.mean()), "ssim_std": float(s.std(unbiased=False)), "n": len(values)}
