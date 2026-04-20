"""NASA DAAC downloader: search via CMR / earthaccess and download granules."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from maap_data_downloaders.auth import get_earthdata_credentials
from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download NASA DAAC granules via earthaccess and generate STAC metadata."
    )
    p.add_argument("--concept-id", required=True, help="CMR concept ID (e.g. C2036882064-GES_DISC)")
    p.add_argument(
        "--bbox",
        required=True,
        help="Bounding box as 'min_lon,min_lat,max_lon,max_lat'",
    )
    p.add_argument("--temporal-start", default=None, help="Start date YYYY-MM-DD (optional)")
    p.add_argument("--temporal-end", default=None, help="End date YYYY-MM-DD (optional)")
    p.add_argument(
        "--collection-id",
        default=None,
        help="STAC collection ID for output catalog (default: concept-id value)",
    )
    p.add_argument("--output", default="outputs", help="Output directory (default: outputs)")
    p.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    import earthaccess  # type: ignore[import]

    output_dir = Path(args.output)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    collection_id = args.collection_id or args.concept_id

    if args.verbose:
        print(f"[nasa_daac] concept_id={args.concept_id} bbox={args.bbox}")

    # Authenticate via MAAP secrets → write ~/.netrc → earthaccess login
    try:
        username, password = get_earthdata_credentials()
        earthaccess.login(strategy="netrc", persist=False)
        if args.verbose:
            print("[nasa_daac] earthaccess authenticated via MAAP secrets")
    except Exception as exc:
        print(f"[nasa_daac] WARNING: Could not load MAAP credentials ({exc}). "
              "Attempting earthaccess with existing netrc/env.", file=sys.stderr)

    # Build earthaccess search kwargs
    min_lon, min_lat, max_lon, max_lat = [float(v) for v in args.bbox.split(",")]
    search_kwargs: dict = {
        "concept_id": args.concept_id,
        "bounding_box": (min_lon, min_lat, max_lon, max_lat),
    }
    if args.temporal_start or args.temporal_end:
        search_kwargs["temporal"] = (args.temporal_start, args.temporal_end)

    results = earthaccess.search_data(**search_kwargs)
    if not results:
        print("[nasa_daac] No granules found for the given search parameters.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"[nasa_daac] Found {len(results)} granule(s). Downloading…")

    downloaded = earthaccess.download(results, local_path=str(data_dir))

    stac_items = []
    for filepath in downloaded:
        if args.verbose:
            print(f"[nasa_daac] Generating STAC for {filepath}")
        meta = extract_metadata(filepath)
        item = create_stac_item(filepath, meta, collection_id)
        stac_items.append(item)

    build_catalog(stac_items, output_dir, collection_id)
    print(f"[nasa_daac] Done. {len(stac_items)} file(s) in {output_dir}/")


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
