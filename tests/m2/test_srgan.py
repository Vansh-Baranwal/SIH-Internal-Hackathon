"""Shape and finite-loss checks for the SRGAN architecture."""
import pytest

torch = pytest.importorskip("torch")

from lunar_hazard_mapper.m2_super_resolution.loss import SRGANLoss, VGGPerceptualLoss
from lunar_hazard_mapper.m2_super_resolution.models.srgan import SRGANDiscriminator, SRGANGenerator


def test_generator_shapes():
    x = torch.rand(1, 1, 8, 8)
    assert SRGANGenerator(4, n_residual_blocks=1, n_features=8)(x).shape == (1, 1, 32, 32)
    assert SRGANGenerator(8, n_residual_blocks=1, n_features=8)(x).shape == (1, 1, 64, 64)


def test_discriminator_raw_logit_shape():
    output = SRGANDiscriminator(base_features=8)(torch.rand(2, 1, 32, 32))
    assert output.shape == (2, 1)
    assert not any(isinstance(module, torch.nn.Sigmoid) for module in SRGANDiscriminator(base_features=8).modules())


def test_perceptual_grayscale_and_loss_components():
    pred, target = torch.rand(1, 1, 16, 16), torch.rand(1, 1, 16, 16)
    perceptual = VGGPerceptualLoss(pretrained=False)
    assert perceptual(pred, target).ndim == 0
    result = SRGANLoss(perceptual_loss=perceptual)(pred, target, torch.zeros(1, 1))
    assert set(result) == {"pixel_loss", "perceptual_loss", "adversarial_loss", "total_loss"}
    assert result["total_loss"].ndim == 0 and torch.isfinite(result["total_loss"])
