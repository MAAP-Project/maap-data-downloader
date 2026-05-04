"""Earthdata downloader: search and download granules via earthaccess."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import earthaccess

from maap_data_downloaders.auth import get_earthdata_token
from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download Earthdata granules via earthaccess and generate STAC metadata."
    )
    p.add_argument("--short-name", default=None, help="CMR collection short name (e.g. GEDI02_A)")
    p.add_argument("--concept-id", default=None, help="CMR concept ID (alternative to short-name)")
    p.add_argument(
        "--bbox",
        required=True,
        help="Bounding box as 'min_lon,min_lat,max_lon,max_lat'",
    )
    p.add_argument("--temporal-start", default=None, help="Start date YYYY-MM-DD (optional)")
    p.add_argument("--temporal-end", default=None, help="End date YYYY-MM-DD (optional)")
    p.add_argument("--limit", type=int, default=20, help="Max granules to fetch (default: 20)")
    p.add_argument(
        "--collection-id",
        default=None,
        help="STAC collection ID for output catalog (default: short-name or concept-id)",
    )
    p.add_argument("--output", default="outputs", help="Output directory (default: outputs)")
    p.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    p.add_argument(
        "--token-secret",
        default="EARTHDATA_TOKEN",
        help="MAAP secret name for Earthdata token (default: EARTHDATA_TOKEN)",
    )
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Determine collection_id (used for STAC)
    if args.collection_id:
        collection_id = args.collection_id
    elif args.short_name:
        collection_id = args.short_name
    elif args.concept_id:
        collection_id = args.concept_id
    else:
        print("[earthdata] ERROR: Must provide --short-name, --concept-id, or --collection-id", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"[earthdata] short_name={args.short_name} concept_id={args.concept_id} bbox={args.bbox}")

    # Auth: get token from MAAP secrets and set env var for earthaccess
    try:
        token = get_earthdata_token(args.token_secret)
    except Exception as exc:
        print(f"[earthdata] ERROR: Failed to retrieve token: {exc}", file=sys.stderr)
        sys.exit(1)

    os.environ["EARTHDATA_TOKEN"] = token
    try:
        earthaccess.login(strategy="environment")
    except Exception as exc:
        print(f"[earthdata] ERROR: earthaccess login failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Build earthaccess search kwargs
    try:
        west, south, east, north = (float(x) for x in args.bbox.split(","))
    except (ValueError, IndexError) as exc:
        print(f"[earthdata] ERROR: Invalid bbox format: {exc}", file=sys.stderr)
        sys.exit(1)

    search_kwargs: dict = {"bounding_box": (west, south, east, north), "count": args.limit}

    if args.short_name:
        search_kwargs["short_name"] = args.short_name
    elif args.concept_id:
        search_kwargs["concept_id"] = args.concept_id

    if args.temporal_start or args.temporal_end:
        search_kwargs["temporal"] = (args.temporal_start or "", args.temporal_end or "")

    try:
        results = earthaccess.search_data(**search_kwargs)
    except Exception as exc:
        print(f"[earthdata] ERROR: search_data failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("[earthdata] No granules found for the given search parameters.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"[earthdata] Found {len(results)} granule(s). Downloading…")

    # Batch download all granules
    try:
        downloaded_paths = earthaccess.download(results, local_path=str(data_dir))
    except Exception as exc:
        print(f"[earthdata] ERROR: download failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Build STAC items from downloaded files
    stac_items = []
    for filepath in downloaded_paths:
        try:
            meta = extract_metadata(filepath)
            item = create_stac_item(filepath, meta, collection_id)
            stac_items.append(item)
        except Exception as exc:
            print(f"[earthdata] WARNING: STAC creation failed for {filepath}: {exc}", file=sys.stderr)

    if not stac_items:
        print("[earthdata] No granules were successfully processed.", file=sys.stderr)
        sys.exit(1)

    build_catalog(stac_items, output_dir, collection_id)
    print(f"[earthdata] Done. {len(stac_items)} file(s) in {output_dir}/")


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
