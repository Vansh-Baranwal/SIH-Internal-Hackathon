# M1 - Data Acquisition & Preprocessing

Responsibilities: TMC imagery/data ingestion, CRS, tiling, reference data.

## Scientific and data contract

M1 provides a reproducible geospatial foundation for downstream members. It preserves each source raster's CRS, affine transform, resolution, bounds, dimensions, nodata semantics, and measurement basis. Missing metadata is recorded as unknown only where explicitly allowed; otherwise inspection fails clearly. A 5 m optical image is not a DEM and does not contain true 1 m measurements. Any high-resolution representation produced by a downstream model is an estimated/reconstructed representation, while M1's reference-derived pairs are explicitly synthetic and are not an exact TMC sensor simulation.

## M1 package and commands

The implementation lives under `src/lunar_hazard_mapper/m1_data/`. It provides metadata inspection, SHA-256 provenance, source cataloguing, window-based GeoTIFF tiling, configured radiometric preprocessing, reference registration and CRS-aware overlap, synthetic training-pair construction, geographic block splits, tile contracts, and QA.

From the repository root:

```bash
python scripts/inspect_tmc.py --input data/raw/example.tif --output metadata.json
python scripts/build_catalog.py --input data/raw --output data/manifests/source_manifest.json
python scripts/create_tiles.py --input data/raw/example.tif --output data/processed/tmc_tiles --tile-size 256 --manifest data/manifests/tile_manifest.json
python scripts/preprocess.py --input data/raw/example.tif --output data/processed/example.tif --config configs/preprocessing.yaml
python scripts/build_reference_catalog.py --input data/reference/reference.tif --source-type OHRC
python scripts/build_training_pairs.py --tmc-manifest data/manifests/tile_manifest.json --reference-manifest data/manifests/reference_manifest.json
python scripts/create_spatial_split.py --input data/manifests/training_pairs.json
python scripts/run_data_qa.py --manifest data/manifests/tile_manifest.json
python scripts/run_data_pipeline.py --input data/raw/example.tif --config configs/preprocessing.yaml
```

Generated rasters and manifests belong under ignored output paths; do not commit raw or large data. Synthetic fixtures in tests are development-only and are not lunar measurements.

## Downstream tile contract

Each generated tile has a same-stem JSON sidecar with schema version `1.0`, including `path`, `width`, `height`, `crs`, six-coefficient `transform`, pixel sizes, origin, nodata, source ID/checksum, preprocessing configuration hash, and reference availability. Downstream code can load it through:

```python
from lunar_hazard_mapper.m1_data import load_tile_contract
contract = load_tile_contract("data/processed/tmc_tiles/tile.json")
```

M2 must retain horizontal geospatial alignment when producing a reconstruction. M3 must not interpret optical intensity as elevation; an elevation product needs its own vertical units, uncertainty, CRS, transform, and provenance.

## Reproducibility and QA

Configuration is YAML-driven, checksums are streamed with SHA-256, and geographic splits assign whole blocks rather than random adjacent patches. QA fails on invalid dimensions/transforms, missing critical CRS/provenance, checksum mismatches, NaN/Inf values, invalid contracts, or spatial leakage.
