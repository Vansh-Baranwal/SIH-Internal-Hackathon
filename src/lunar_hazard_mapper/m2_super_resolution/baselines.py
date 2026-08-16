"""Non-learned interpolation baselines for Member 2."""

from __future__ import annotations

import torch
import torch.nn.functional as F

from .metrics import evaluate_batch


def _batched(tensor: torch.Tensor) -> tuple[torch.Tensor, bool]:
    if tensor.ndim == 3:
        return tensor.unsqueeze(0), True
    if tensor.ndim == 4:
        return tensor, False
    raise ValueError("Expected tensor with shape (C,H,W) or (B,C,H,W)")


def bicubic_upsample(lr_tensor: torch.Tensor, scale_factor: int) -> torch.Tensor:
    """Upsample with bicubic interpolation."""
    if scale_factor < 1:
        raise ValueError("scale_factor must be positive")
    batch, squeeze = _batched(lr_tensor)
    result = F.interpolate(batch, scale_factor=scale_factor, mode="bicubic", align_corners=False)
    result = result.to(dtype=lr_tensor.dtype)
    return result.squeeze(0) if squeeze else result


def nearest_upsample(lr_tensor: torch.Tensor, scale_factor: int) -> torch.Tensor:
    """Upsample with nearest-neighbour interpolation."""
    if scale_factor < 1:
        raise ValueError("scale_factor must be positive")
    batch, squeeze = _batched(lr_tensor)
    result = F.interpolate(batch, scale_factor=scale_factor, mode="nearest").to(dtype=lr_tensor.dtype)
    return result.squeeze(0) if squeeze else result


def run_baseline(dataset, method: str, scale_factor: int) -> dict:
    """Run one baseline over every dataset sample and summarize metrics."""
    methods = {"bicubic": bicubic_upsample, "nearest": nearest_upsample}
    if method not in methods:
        raise ValueError(f"Unknown baseline {method!r}; choose bicubic or nearest")
    preds, targets, masks = [], [], []
    for sample in dataset:
        pred = methods[method](sample["lr"], scale_factor)
        target = sample["hr"]
        if pred.shape != target.shape:
            raise ValueError(f"Upsampled LR shape {pred.shape} does not match HR shape {target.shape}")
        mask = sample.get("hr_mask")
        preds.append(pred)
        targets.append(target)
        masks.append(mask)
    result = evaluate_batch(preds, targets, masks)
    return {"method": method, "scale_factor": scale_factor, **result}
