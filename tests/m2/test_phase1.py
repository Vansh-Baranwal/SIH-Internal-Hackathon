import json
import numpy as np
import rasterio
import pytest
torch = pytest.importorskip("torch")
from rasterio.transform import from_origin
from lunar_hazard_mapper.m2_super_resolution.dataset import SRDataset, ContractValidationError
from lunar_hazard_mapper.m2_super_resolution.metrics import psnr, ssim
from lunar_hazard_mapper.m2_super_resolution.baselines import bicubic_upsample, nearest_upsample, run_baseline

def write_tif(path, data, nodata=None):
    with rasterio.open(path, "w", driver="GTiff", height=data.shape[0], width=data.shape[1], count=1, dtype="float32", nodata=nodata, transform=from_origin(0,0,1,1)) as dst: dst.write(data.astype("float32"),1)

def make_dataset(tmp_path):
    lr=tmp_path/"lr.tif"; hr=tmp_path/"hr.tif"
    write_tif(lr, np.array([[0,1],[2,-9999]],float), -9999); write_tif(hr, np.array([[0,.25, .5, .75],[.25,.5,.75,1],[.5,.75,1,.5],[.75,1,.5,0]],float), -9999)
    manifest=tmp_path/"manifest.json"; manifest.write_text(json.dumps({"pairs":[{"id":"x","lr_path":str(lr),"hr_path":str(hr),"split":"val"}],"total_pairs":1}))
    return SRDataset(manifest,"val")

def test_dataset_shapes_and_nodata(tmp_path):
    item=make_dataset(tmp_path)[0]
    assert item["lr"].shape==(1,2,2) and item["hr"].shape==(1,4,4)
    assert item["lr"][0,1,1]==0 and not item["lr_mask"][0,1,1]

def test_blocked_manifest(tmp_path):
    p=tmp_path/"m.json"; p.write_text(json.dumps({"pairs":[],"total_pairs":0,"status":"blocked_no_validated_pairs"}))
    with pytest.raises(ContractValidationError): SRDataset(p,"val")

def test_metrics():
    x=torch.zeros(1,2,2); y=torch.ones(1,2,2)
    assert psnr(x,y)==0
    assert psnr(x,x)==float("inf")
    assert abs(ssim(x,x)-1)<1e-6

def test_baselines(tmp_path):
    ds=make_dataset(tmp_path); assert bicubic_upsample(ds[0]["lr"],2).shape==(1,4,4); assert nearest_upsample(ds[0]["lr"],2).shape==(1,4,4)
    assert run_baseline(ds,"bicubic",2)["n"]==1
