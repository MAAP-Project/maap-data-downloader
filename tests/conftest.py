"""Shared fixtures for maap_data_downloaders tests."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture()
def tmp_netcdf(tmp_path):
    """Create a minimal NetCDF file with CF global attributes."""
    import netCDF4 as nc4  # type: ignore[import]

    path = tmp_path / "test_file.nc"
    with nc4.Dataset(path, "w") as ds:
        ds.title = "Test NetCDF"
        ds.geospatial_lon_min = -125.0
        ds.geospatial_lat_min = 24.0
        ds.geospatial_lon_max = -66.0
        ds.geospatial_lat_max = 49.0
        ds.time_coverage_start = "2020-01-01T00:00:00Z"
        ds.time_coverage_end = "2020-01-31T23:59:59Z"
    return path


@pytest.fixture()
def tmp_hdf5(tmp_path):
    """Create a minimal HDF5 file with CF-style global attributes."""
    import h5py  # type: ignore[import]

    path = tmp_path / "test_file.h5"
    with h5py.File(path, "w") as f:
        f.attrs["title"] = "Test HDF5"
        f.attrs["geospatial_lon_min"] = -180.0
        f.attrs["geospatial_lat_min"] = -90.0
        f.attrs["geospatial_lon_max"] = 180.0
        f.attrs["geospatial_lat_max"] = 90.0
        f.attrs["time_coverage_start"] = "2020-06-01T00:00:00Z"
        f.attrs["time_coverage_end"] = "2020-06-30T23:59:59Z"
    return path
