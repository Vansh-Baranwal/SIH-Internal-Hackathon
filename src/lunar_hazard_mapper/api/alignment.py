import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

def align_rasters(source_path, reference_path, output_path, is_dem=False):
    """
    Reproject and resample the source raster to exactly match the 
    geospatial footprint, CRS, and resolution of the reference raster.
    """
    with rasterio.open(reference_path) as ref:
        ref_crs = ref.crs
        ref_transform = ref.transform
        ref_width = ref.width
        ref_height = ref.height
        
    with rasterio.open(source_path) as src:
        source_array = src.read(1)
        source_crs = src.crs
        source_transform = src.transform
        source_nodata = src.nodata
        
        # Output array
        aligned_array = np.zeros((ref_height, ref_width), dtype=src.dtypes[0])
        
        # Reproject
        reproject(
            source=source_array,
            destination=aligned_array,
            src_transform=source_transform,
            src_crs=source_crs,
            src_nodata=source_nodata,
            dst_transform=ref_transform,
            dst_crs=ref_crs,
            dst_nodata=source_nodata,
            resampling=Resampling.bilinear if is_dem else Resampling.nearest
        )
        
        # Save aligned raster
        profile = src.profile.copy()
        profile.update({
            'crs': ref_crs,
            'transform': ref_transform,
            'width': ref_width,
            'height': ref_height
        })
        
        if output_path:
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(aligned_array, 1)
            
    return aligned_array, ref_transform, ref_crs
