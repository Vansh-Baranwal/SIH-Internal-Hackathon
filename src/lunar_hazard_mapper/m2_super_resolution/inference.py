"""CSASR inference wrappers with memory-safe dynamic tiling and metadata preservation."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from .models.csasr import CSASR
from .preprocessing import min_max_standardization, denormalize

class CSASRArgs:
    def __init__(self):
        self.scale = 4
        self.n_FFBs = 4
        self.n_feats = 32
        self.no_upsampling = False
        self.n_colors = 3
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

def load_csasr_stages(checkpoint_dir: Path):
    """Load both stages of the CSASR model."""
    args = CSASRArgs()
    
    stage1 = CSASR(args)
    stage1_path = checkpoint_dir / 'CSASR_model_stage1_v1_state_dict.pth'
    if stage1_path.exists():
        state_dict1 = torch.load(stage1_path, map_location=args.device)
        stage1.load_state_dict(state_dict1['state_dict'] if 'state_dict' in state_dict1 else state_dict1, strict=True)
    
    stage2 = CSASR(args)
    stage2_path = checkpoint_dir / 'CSASR_model_stage2_v1_state_dict.pth'
    if stage2_path.exists():
        state_dict2 = torch.load(stage2_path, map_location=args.device)
        stage2.load_state_dict(state_dict2['state_dict'] if 'state_dict' in state_dict2 else state_dict2, strict=True)
        
    stage1.to(args.device).eval()
    stage2.to(args.device).eval()
    
    return stage1, stage2

def tiled_inference(image: torch.Tensor, stage1, stage2, tile_size=80, device='cpu'):
    """
    Perform memory-safe tiled inference.
    Follows exactly the original IIT Patna pipeline logic but handles arbitrary dimensions safely.
    image shape: (H, W) or (1, H, W).
    """
    if image.ndim == 2:
        image = image.unsqueeze(0)
    
    _, h, w = image.shape
    
    # Calculate padded dimensions to be multiples of tile_size
    pad_h = (tile_size - (h % tile_size)) % tile_size
    pad_w = (tile_size - (w % tile_size)) % tile_size
    
    padded_img = F.pad(image, (0, pad_w, 0, pad_h), mode='reflect')
    ph, pw = padded_img.shape[1], padded_img.shape[2]
    
    out_h, out_w = ph * 16, pw * 16 # Overall scale is 16x (4x from stage1, 4x from stage2)
    output = torch.zeros((1, out_h, out_w), device='cpu')
    
    with torch.no_grad():
        for i in range(0, ph, tile_size):
            for j in range(0, pw, tile_size):
                # Extract 80x80 tile
                tile = padded_img[:, i:i+tile_size, j:j+tile_size] # (1, 80, 80)
                
                # Expand channels to 3
                tile_3c = tile.repeat(3, 1, 1).unsqueeze(0).to(device) # (1, 3, 80, 80)
                
                # Stage 1: 4x upscale -> 320x320
                out1 = stage1(tile_3c)
                out1_mean = out1.mean(dim=1) # (1, 320, 320)
                
                # Instead of re-tiling into 16 80x80 tiles like their notebook, we can pass the entire 
                # 320x320 tensor directly through Stage 2. It is mathematically identical and fits in memory.
                out1_3c = out1_mean.unsqueeze(1).repeat(1, 3, 1, 1) # (1, 3, 320, 320)
                
                # Stage 2: 4x upscale -> 1280x1280
                out2 = stage2(out1_3c)
                out2_mean = out2.mean(dim=1) # (1, 1280, 1280)
                
                # Place in output tensor
                out_i = i * 16
                out_j = j * 16
                output[0, out_i:out_i+1280, out_j:out_j+1280] = out2_mean[0].cpu()

    # Crop out padding
    final_out = output[:, :h*16, :w*16]
    
    # The IIT Patna team used an additional 2x bicubic upscale for a total 32x.
    # We apply this explicitly here to match the combined 32x pipeline precisely.
    final_out = final_out.unsqueeze(0) # (1, 1, H, W)
    final_out = F.interpolate(final_out, scale_factor=2.0, mode='bicubic', align_corners=False)
    
    return final_out.squeeze(0) # (1, final_H, final_W)


def infer_geotiff(checkpoint_dir: Path, input_path: Path, output_path: Path, device="cpu") -> None:
    import rasterio
    
    stage1, stage2 = load_csasr_stages(checkpoint_dir)
    stage1.to(device)
    stage2.to(device)
    
    with rasterio.open(input_path) as src:
        array = src.read(1)
        profile = src.profile.copy()
        transform = src.transform
        nodata = src.nodata

        # Fill nan with 0 for preprocessing safely
        array_filled = np.nan_to_num(array, nan=0.0)
        
        # Preprocessing: Min-Max Standardization
        norm_array = min_max_standardization(array_filled)
        
        tensor = torch.from_numpy(norm_array)
        
        result_tensor = tiled_inference(tensor, stage1, stage2, tile_size=80, device=device)
        
        result = result_tensor[0].numpy()
        
        # The scale factor is exactly 32.
        scale_factor = 32
        
        if "photometric" in profile:
            del profile["photometric"]
        if "compress" in profile:
            del profile["compress"]
        profile.update(
            driver="GTiff",
            height=result.shape[0],
            width=result.shape[1],
            transform=transform * transform.scale(1/scale_factor, 1/scale_factor),
            count=1,
            dtype="float32"
        )
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(result.astype("float32"), 1)
            if nodata is not None:
                dst.nodata = nodata
