"""OPeNDAP downloader: subset and save NetCDF from an OPeNDAP URL via xarray."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Subset and download data from an OPeNDAP URL, then generate STAC metadata."
    )
    p.add_argument("--url", required=True, help="OPeNDAP dataset URL")
    p.add_argument(
        "--variables",
        default=None,
        help="Comma-separated variable names to subset (omit for all)",
    )
    p.add_argument(
        "--bbox",
        default=None,
        help="Spatial subset as 'min_lon,min_lat,max_lon,max_lat' (requires lat/lon dims in dataset)",
    )
    p.add_argument("--temporal-start", default=None, help="Temporal subset start (YYYY-MM-DD)")
    p.add_argument("--temporal-end", default=None, help="Temporal subset end (YYYY-MM-DD)")
    p.add_argument(
        "--chunks",
        default='{"time": 1}',
        help='Dask chunks as JSON string (default: \'{"time": 1}\')',
    )
    p.add_argument(
        "--collection-id",
        default=None,
        help="STAC collection ID (default: dataset name from URL)",
    )
    p.add_argument("--output", default="outputs", help="Output directory (default: outputs)")
    p.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return p.parse_args(argv)


def _guess_dim(ds, candidates: list[str]) -> str | None:
    """Return the first candidate dimension/coordinate found in dataset."""
    for name in candidates:
        if name in ds.dims or name in ds.coords:
            return name
    return None


def run(args: argparse.Namespace) -> None:
    import xarray as xr  # type: ignore[import]
    import pandas as pd  # type: ignore[import]

    output_dir = Path(args.output)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        chunks = json.loads(args.chunks)
    except json.JSONDecodeError:
        print(f"[opendap] Invalid --chunks JSON: {args.chunks}", file=sys.stderr)
        sys.exit(1)

    parsed = urlparse(args.url)
    dataset_name = Path(parsed.path).stem or "opendap-subset"
    collection_id = args.collection_id or dataset_name

    if args.verbose:
        print(f"[opendap] Opening {args.url} with chunks={chunks}")

    ds = xr.open_dataset(args.url, engine="pydap", chunks=chunks)

    # Variable subsetting
    if args.variables:
        var_list = [v.strip() for v in args.variables.split(",")]
        ds = ds[var_list]

    # Spatial subsetting
    if args.bbox:
        min_lon, min_lat, max_lon, max_lat = [float(v) for v in args.bbox.split(",")]
        lon_dim = _guess_dim(ds, ["lon", "longitude", "x", "nav_lon"])
        lat_dim = _guess_dim(ds, ["lat", "latitude", "y", "nav_lat"])
        if lon_dim and lat_dim:
            ds = ds.sel(
                {
                    lon_dim: slice(min_lon, max_lon),
                    lat_dim: slice(min_lat, max_lat),
                }
            )
        elif args.verbose:
            print("[opendap] WARNING: Could not find lat/lon dims for spatial subset.")

    # Temporal subsetting
    if args.temporal_start or args.temporal_end:
        time_dim = _guess_dim(ds, ["time", "Time", "t"])
        if time_dim:
            ds = ds.sel({time_dim: slice(args.temporal_start, args.temporal_end)})
        elif args.verbose:
            print("[opendap] WARNING: Could not find time dim for temporal subset.")

    out_file = data_dir / f"{dataset_name}.nc"
    if args.verbose:
        print(f"[opendap] Writing subset to {out_file}")

    # Encode with zlib compression
    encoding = {v: {"zlib": True, "complevel": 4} for v in ds.data_vars}
    ds.to_netcdf(str(out_file), encoding=encoding)
    ds.close()

    meta = extract_metadata(out_file)
    item = create_stac_item(out_file, meta, collection_id)
    build_catalog([item], output_dir, collection_id)

    print(f"[opendap] Done. Output in {output_dir}/")


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
