"""Contract-aware LR/HR dataset for Member 2 super-resolution experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import torch
from torch.utils.data import Dataset


class ContractValidationError(ValueError):
    """Raised when the M1-to-M2 training-pair contract cannot be consumed."""


@dataclass(frozen=True)
class PairRecord:
    """One validated manifest pair."""

    identifier: str
    lr_path: Path
    hr_path: Path


def _resolve_path(raw: str, manifest_path: Path) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        # Contract paths are project-root relative; also support fixture-local paths.
        project_root = manifest_path.parent.parent.parent
        candidate = project_root / path
        path = candidate if candidate.exists() else manifest_path.parent / path
    return path.resolve()


class SRDataset(Dataset[dict[str, Any]]):
    """Read only validated pairs listed by the M1 training-pair manifest."""

    def __init__(self, manifest_path: Path, split: str, transform=None):
        self.manifest_path = Path(manifest_path).resolve()
        self.split = split
        self.transform = transform
        try:
            payload = json.loads(self.manifest_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise ContractValidationError(f"Unable to read M2 manifest {self.manifest_path}: {exc}") from exc
        self._validate_manifest(payload)
        records = []
        for item in payload["pairs"]:
            if item.get("split") != split:
                continue
            if not item.get("id") or not item.get("lr_path") or not item.get("hr_path"):
                raise ContractValidationError(f"Pair in {self.manifest_path} is missing id/lr_path/hr_path")
            lr_path = _resolve_path(item["lr_path"], self.manifest_path)
            hr_path = _resolve_path(item["hr_path"], self.manifest_path)
            if not lr_path.is_file() or not hr_path.is_file():
                raise ContractValidationError(
                    f"Pair {item['id']} references missing files: LR={lr_path}, HR={hr_path}"
                )
            records.append(PairRecord(str(item["id"]), lr_path, hr_path))
        if not records:
            raise ContractValidationError(
                f"No validated '{split}' pairs are available in {self.manifest_path}. "
                "M1 status is blocked or the split is empty; do not pair independent tile directories."
            )
        self.records = records

    @staticmethod
    def _validate_manifest(payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("pairs"), list):
            raise ContractValidationError("M2 manifest must contain a 'pairs' list")
        if payload.get("status") == "blocked_no_validated_pairs" or payload.get("total_pairs", len(payload["pairs"])) == 0:
            raise ContractValidationError(
                "M1-to-M2 contract is blocked_no_validated_pairs: no production SR training is permitted."
            )

    @staticmethod
    def _read(path: Path) -> tuple[torch.Tensor, torch.Tensor]:
        with rasterio.open(path) as src:
            array = src.read(1).astype(np.float32)
            nodata = src.nodata
        valid = np.isfinite(array)
        if nodata is not None:
            valid &= array != nodata
        data = np.where(valid, array, 0.0).astype(np.float32)
        return torch.from_numpy(data[None]), torch.from_numpy(valid[None])

    def __getitem__(self, idx: int) -> dict[str, Any]:
        record = self.records[idx]
        lr, lr_mask = self._read(record.lr_path)
        hr, hr_mask = self._read(record.hr_path)
        item = {"lr": lr, "hr": hr, "lr_mask": lr_mask, "hr_mask": hr_mask,
                "id": record.identifier, "lr_path": str(record.lr_path), "hr_path": str(record.hr_path)}
        return self.transform(item) if self.transform is not None else item

    def __len__(self) -> int:
        return len(self.records)
