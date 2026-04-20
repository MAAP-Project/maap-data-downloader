"""Tests for maap_data_downloaders.stac_utils."""

import json

import pystac  # type: ignore[import]

from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item


def test_stac_item_required_fields(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    item = create_stac_item(tmp_netcdf, meta, collection_id="test-collection")

    assert item.geometry is not None
    assert item.bbox is not None
    assert item.datetime is not None
    assert "data" in item.assets
    assert item.properties is not None


def test_stac_item_bbox_matches_metadata(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    item = create_stac_item(tmp_netcdf, meta, collection_id="test-collection")
    assert item.bbox == [-125.0, 24.0, -66.0, 49.0]


def test_stac_item_fallback_global_bbox(tmp_path):
    """Files without spatial metadata should default to global extent."""
    import netCDF4 as nc4  # type: ignore[import]
    path = tmp_path / "no_bbox.nc"
    with nc4.Dataset(path, "w"):
        pass

    meta = extract_metadata(path)
    item = create_stac_item(path, meta, collection_id="test-collection")
    assert item.bbox == [-180.0, -90.0, 180.0, 90.0]


def test_stac_item_asset_media_type_nc(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    item = create_stac_item(tmp_netcdf, meta, collection_id="test-collection")
    assert item.assets["data"].media_type == "application/x-netcdf"


def test_stac_item_asset_media_type_h5(tmp_hdf5):
    meta = extract_metadata(tmp_hdf5)
    item = create_stac_item(tmp_hdf5, meta, collection_id="test-collection")
    assert item.assets["data"].media_type == "application/x-hdf5"


def test_build_catalog_creates_files(tmp_netcdf, tmp_path):
    meta = extract_metadata(tmp_netcdf)
    item = create_stac_item(tmp_netcdf, meta, collection_id="my-collection")
    output_dir = tmp_path / "outputs"

    build_catalog([item], output_dir, collection_id="my-collection")

    assert (output_dir / "catalog.json").exists()
    catalog_json = json.loads((output_dir / "catalog.json").read_text())
    assert catalog_json["type"] == "Catalog"


def test_build_catalog_collection_json(tmp_netcdf, tmp_path):
    meta = extract_metadata(tmp_netcdf)
    item = create_stac_item(tmp_netcdf, meta, collection_id="my-collection")
    output_dir = tmp_path / "outputs"

    build_catalog([item], output_dir, collection_id="my-collection")

    collection_dirs = list(output_dir.iterdir())
    collection_dirs = [d for d in collection_dirs if d.is_dir()]
    assert len(collection_dirs) == 1

    collection_json_path = collection_dirs[0] / "collection.json"
    assert collection_json_path.exists()
    col = json.loads(collection_json_path.read_text())
    assert col["type"] == "Collection"


def test_stac_item_collection_id(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    item = create_stac_item(tmp_netcdf, meta, collection_id="my-special-collection")
    assert item.collection_id == "my-special-collection"
