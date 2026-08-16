"""Tensor and GeoTIFF inference helpers with metadata-preserving output."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import torch

def run_inference(model, image: torch.Tensor, device="cpu") -> torch.Tensor:
    model.eval(); tensor=image if image.ndim==4 else image.unsqueeze(0)
    with torch.no_grad(): output=model(tensor.to(device))
    return output.cpu() if image.ndim==4 else output[0].cpu()

def infer_geotiff(model, input_path: Path, output_path: Path, scale_factor: int, device="cpu") -> None:
    import rasterio
    with rasterio.open(input_path) as src:
        array=src.read(1).astype("float32"); profile=src.profile.copy(); transform=src.transform
        nodata=src.nodata; tensor=torch.from_numpy(np.nan_to_num(array,nan=0.0))[None,None]
        result=run_inference(model,tensor,device)[0].numpy()
        profile.update(height=result.shape[0],width=result.shape[1],transform=transform * transform.scale(1/scale_factor,1/scale_factor),count=1,dtype="float32")
        with rasterio.open(output_path,"w",**profile) as dst: dst.write(result.astype("float32"),1); dst.nodata=nodata
