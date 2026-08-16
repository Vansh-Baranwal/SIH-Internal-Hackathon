import pytest
import torch
import numpy as np
from pathlib import Path
from lunar_hazard_mapper.m2_super_resolution.models.csasr import CSASR
from lunar_hazard_mapper.m2_super_resolution.inference import load_csasr_stages, tiled_inference, CSASRArgs

CHECKPOINT_DIR = Path("checkpoints")

def test_checkpoint_exists():
    assert (CHECKPOINT_DIR / 'CSASR_model_stage1_v1_state_dict.pth').exists()
    assert (CHECKPOINT_DIR / 'CSASR_model_stage2_v1_state_dict.pth').exists()

def test_checkpoint_loads_strict():
    # Will fail if strict=True fails
    stage1, stage2 = load_csasr_stages(CHECKPOINT_DIR)
    assert isinstance(stage1, CSASR)
    assert isinstance(stage2, CSASR)

def test_scale_correct_and_shapes():
    stage1, stage2 = load_csasr_stages(CHECKPOINT_DIR)
    
    # 24x24 -> 96x96 for each stage independently
    dummy_input = torch.randn(1, 3, 24, 24).to(CSASRArgs().device)
    
    with torch.no_grad():
        out1 = stage1(dummy_input)
        assert out1.shape == (1, 3, 96, 96)
        
        out2 = stage2(dummy_input)
        assert out2.shape == (1, 3, 96, 96)

def test_finite_output_no_nan_inf():
    stage1, stage2 = load_csasr_stages(CHECKPOINT_DIR)
    dummy_input = torch.randn(1, 3, 24, 24).to(CSASRArgs().device)
    
    with torch.no_grad():
        out1 = stage1(dummy_input)
        assert torch.isfinite(out1).all()
        assert not torch.isnan(out1).any()
        
        out2 = stage2(dummy_input)
        assert torch.isfinite(out2).all()
        assert not torch.isnan(out2).any()

def test_deterministic_inference():
    stage1, stage2 = load_csasr_stages(CHECKPOINT_DIR)
    dummy_input = torch.randn(1, 3, 24, 24).to(CSASRArgs().device)
    
    with torch.no_grad():
        outA = stage1(dummy_input)
        outB = stage1(dummy_input)
        assert torch.allclose(outA, outB)

def test_tiled_inference_pipeline():
    stage1, stage2 = load_csasr_stages(CHECKPOINT_DIR)
    
    # Test on a small 100x100 input
    dummy_image = torch.rand(1, 100, 100)
    
    out = tiled_inference(dummy_image, stage1, stage2, tile_size=80, device=CSASRArgs().device)
    
    # 100 * 32 = 3200
    assert out.shape == (1, 3200, 3200)
    assert torch.isfinite(out).all()
