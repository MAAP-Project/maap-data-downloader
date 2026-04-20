"""Extract spatial/temporal metadata from HDF5 and NetCDF files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def extract_metadata(filepath: str | os.PathLike) -> dict[str, Any]:
    """Return a metadata dict from an HDF5 or NetCDF file.

    Returned keys (all optional if not present in file):
      bbox: [min_lon, min_lat, max_lon, max_lat] or None
      time_coverage_start: ISO-8601 string or None
      time_coverage_end: ISO-8601 string or None
      title: str or None
      attrs: full dict of global attributes
    """
    path = Path(filepath)
    suffix = path.suffix.lower()

    if suffix in {".nc", ".nc4", ".nc3"}:
        return _extract_netcdf(path)
    if suffix in {".h5", ".hdf5", ".hdf"}:
        return _extract_hdf5(path)

    try:
        return _extract_xarray(path)
    except Exception:
        return {"bbox": None, "time_coverage_start": None, "time_coverage_end": None, "title": None, "attrs": {}}


def _extract_xarray(path: Path) -> dict[str, Any]:
    import xarray as xr  # type: ignore[import]
    with xr.open_dataset(path, chunks={}) as ds:
        return _attrs_to_metadata(dict(ds.attrs))


def _extract_netcdf(path: Path) -> dict[str, Any]:
    try:
        import xarray as xr  # type: ignore[import]
        with xr.open_dataset(path, chunks={}) as ds:
            return _attrs_to_metadata(dict(ds.attrs))
    except Exception:
        import netCDF4 as nc4  # type: ignore[import]
        with nc4.Dataset(path, "r") as ds:
            attrs = {k: getattr(ds, k) for k in ds.ncattrs()}
            return _attrs_to_metadata(attrs)


def _extract_hdf5(path: Path) -> dict[str, Any]:
    import h5py  # type: ignore[import]
    with h5py.File(path, "r") as f:
        attrs: dict[str, Any] = {}
        for k, v in f.attrs.items():
            attrs[k] = v.decode() if isinstance(v, bytes) else v
        return _attrs_to_metadata(attrs)


def _attrs_to_metadata(attrs: dict[str, Any]) -> dict[str, Any]:
    """Map common CF/HDF global attribute names to our standard metadata dict."""
    return {
        "bbox": _extract_bbox(attrs),
        "time_coverage_start": _first(attrs, [
            "time_coverage_start", "TimeCoverageStart", "RangeBeginningDate",
        ]),
        "time_coverage_end": _first(attrs, [
            "time_coverage_end", "TimeCoverageEnd", "RangeEndingDate",
        ]),
        "title": _first(attrs, ["title", "Title", "LongName", "long_name"]),
        "attrs": attrs,
    }


def _extract_bbox(attrs: dict[str, Any]) -> list[float] | None:
    """Try common attribute naming conventions for spatial coverage."""
    candidates = [
        ("geospatial_lon_min", "geospatial_lat_min", "geospatial_lon_max", "geospatial_lat_max"),
        ("westBoundLongitude", "southBoundLatitude", "eastBoundLongitude", "northBoundLatitude"),
        ("WestBoundingCoordinate", "SouthBoundingCoordinate", "EastBoundingCoordinate", "NorthBoundingCoordinate"),
    ]
    for min_lon_k, min_lat_k, max_lon_k, max_lat_k in candidates:
        if all(k in attrs for k in (min_lon_k, min_lat_k, max_lon_k, max_lat_k)):
            try:
                return [
                    float(attrs[min_lon_k]),
                    float(attrs[min_lat_k]),
                    float(attrs[max_lon_k]),
                    float(attrs[max_lat_k]),
                ]
            except (TypeError, ValueError):
                continue
    return None


def _first(attrs: dict[str, Any], keys: list[str]) -> str | None:
    for k in keys:
        if k in attrs and attrs[k]:
            return str(attrs[k])
    return None
