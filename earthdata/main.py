"""Earthdata downloader CLI: search and download granules via earthaccess."""

from __future__ import annotations

import argparse
import sys

from maap_data_downloaders.earthdata import download_earthdata


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
        "--auth-strategy",
        default="environment",
        choices=["environment", "netrc", "interactive"],
        help="Authentication strategy: 'environment' (MAAP secrets), 'netrc' (~/.netrc), or 'interactive' (prompt)",
    )
    p.add_argument(
        "--token-secret",
        default="EARTHDATA_TOKEN",
        help="MAAP secret name for Earthdata token (only used with --auth-strategy=environment)",
    )
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    """CLI wrapper around download_earthdata()."""
    try:
        files = download_earthdata(
            short_name=args.short_name,
            concept_id=args.concept_id,
            bbox=args.bbox,
            temporal_start=args.temporal_start,
            temporal_end=args.temporal_end,
            limit=args.limit,
            collection_id=args.collection_id,
            output_dir=args.output,
            auth_strategy=args.auth_strategy,
            token_secret=args.token_secret,
            verbose=args.verbose,
        )
    except Exception as exc:
        print(f"[earthdata] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[earthdata] Done. {len(files)} file(s) downloaded")


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
