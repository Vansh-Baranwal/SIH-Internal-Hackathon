"""Dependency-aware tests for Member 2 CNN architecture and trainer."""

import pytest

torch = pytest.importorskip("torch")
from torch.utils.data import DataLoader

from lunar_hazard_mapper.m2_super_resolution.models import ResidualBlock, SimpleSRCNN
from lunar_hazard_mapper.m2_super_resolution.trainer import SRTrainer


def batch():
    return {"lr": torch.rand(1, 8, 8), "hr": torch.rand(1, 32, 32)}


def test_residual_block_shape():
    assert ResidualBlock(8)(torch.rand(2, 8, 8, 8)).shape == (2, 8, 8, 8)

@pytest.mark.parametrize("scale,size", [(4, 32), (8, 64)])
def test_model_shape_and_dtype(scale, size):
    output = SimpleSRCNN(scale, n_residual_blocks=1, n_features=8)(torch.rand(1, 1, 8, 8))
    assert output.shape == (1, 1, size, size)
    assert output.dtype == torch.float32


def test_trainer_checkpoint(tmp_path):
    loader = DataLoader([batch(), batch()], batch_size=1)
    model = SimpleSRCNN(4, n_residual_blocks=1, n_features=4)
    trainer = SRTrainer(model, torch.optim.Adam(model.parameters()), torch.nn.L1Loss(), loader, loader, "cpu", {}, tmp_path)
    trainer.save_checkpoint(1, {"psnr": 1.0}, True)
    assert (tmp_path / "checkpoint_best.pth").exists()
    assert torch.load(tmp_path / "checkpoint_best.pth", weights_only=False)["epoch"] == 1
