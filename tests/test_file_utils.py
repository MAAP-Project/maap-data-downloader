"""Tests for maap_data_downloaders.file_utils."""

from maap_data_downloaders.file_utils import extract_metadata


def test_extract_netcdf_bbox(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    assert meta["bbox"] == [-125.0, 24.0, -66.0, 49.0]


def test_extract_netcdf_temporal(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    assert meta["time_coverage_start"] == "2020-01-01T00:00:00Z"
    assert meta["time_coverage_end"] == "2020-01-31T23:59:59Z"


def test_extract_netcdf_title(tmp_netcdf):
    meta = extract_metadata(tmp_netcdf)
    assert meta["title"] == "Test NetCDF"


def test_extract_hdf5_bbox(tmp_hdf5):
    meta = extract_metadata(tmp_hdf5)
    assert meta["bbox"] == [-180.0, -90.0, 180.0, 90.0]


def test_extract_hdf5_temporal(tmp_hdf5):
    meta = extract_metadata(tmp_hdf5)
    assert meta["time_coverage_start"] == "2020-06-01T00:00:00Z"


def test_missing_attrs_returns_none(tmp_path):
    """Files with no spatial/temporal attrs should return None, not raise."""
    import netCDF4 as nc4  # type: ignore[import]

    path = tmp_path / "empty_attrs.nc"
    with nc4.Dataset(path, "w"):
        pass

    meta = extract_metadata(path)
    assert meta["bbox"] is None
    assert meta["time_coverage_start"] is None
    assert meta["title"] is None
