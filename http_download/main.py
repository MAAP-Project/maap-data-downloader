"""HTTP downloader: retrieve files via requests with optional auth."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from maap_data_downloaders.auth import get_maap_secret
from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item

_MAX_RETRIES = 3
_BACKOFF_BASE = 2  # seconds


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download files via HTTP/HTTPS and generate STAC metadata."
    )
    p.add_argument(
        "--url",
        required=True,
        help="Single URL, or path to a .txt file with one URL per line",
    )
    p.add_argument(
        "--auth-type",
        choices=["none", "bearer", "basic"],
        default="none",
        help="Authentication type (default: none)",
    )
    p.add_argument(
        "--token-secret",
        default=None,
        help="MAAP secret name for Bearer token (used when --auth-type=bearer)",
    )
    p.add_argument(
        "--username-secret",
        default=None,
        help="MAAP secret name for username (used when --auth-type=basic)",
    )
    p.add_argument(
        "--password-secret",
        default=None,
        help="MAAP secret name for password (used when --auth-type=basic)",
    )
    p.add_argument(
        "--collection-id",
        default=None,
        help="STAC collection ID (default: hostname from first URL)",
    )
    p.add_argument("--output", default="outputs", help="Output directory (default: outputs)")
    p.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return p.parse_args(argv)


def _build_auth_headers(args: argparse.Namespace) -> dict:
    if args.auth_type == "bearer":
        if not args.token_secret:
            print("[http] --token-secret required for bearer auth", file=sys.stderr)
            sys.exit(1)
        token = get_maap_secret(args.token_secret)
        return {"Authorization": f"Bearer {token}"}
    return {}


def _build_session(args: argparse.Namespace):
    import requests  # type: ignore[import]
    session = requests.Session()
    session.headers.update(_build_auth_headers(args))
    if args.auth_type == "basic":
        if not (args.username_secret and args.password_secret):
            print("[http] --username-secret and --password-secret required for basic auth", file=sys.stderr)
            sys.exit(1)
        from requests.auth import HTTPBasicAuth
        session.auth = HTTPBasicAuth(
            get_maap_secret(args.username_secret),
            get_maap_secret(args.password_secret),
        )
    return session


def _download_url(session, url: str, dest: Path, verbose: bool) -> None:
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            with session.get(url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                with dest.open("wb") as fh:
                    for chunk in resp.iter_content(chunk_size=8192):
                        fh.write(chunk)
            if verbose:
                print(f"[http] Downloaded {url} → {dest}")
            return
        except Exception as exc:
            if attempt == _MAX_RETRIES:
                raise
            wait = _BACKOFF_BASE ** attempt
            print(f"[http] Attempt {attempt} failed ({exc}). Retrying in {wait}s…", file=sys.stderr)
            time.sleep(wait)


def run(args: argparse.Namespace) -> None:
    from urllib.parse import urlparse

    output_dir = Path(args.output)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Resolve URL list
    url_path = Path(args.url)
    if url_path.is_file():
        urls = [u.strip() for u in url_path.read_text().splitlines() if u.strip()]
    else:
        urls = [args.url]

    collection_id = args.collection_id or urlparse(urls[0]).hostname or "http-download"

    session = _build_session(args)

    stac_items = []
    for url in urls:
        filename = Path(urlparse(url).path).name or "download"
        dest = data_dir / filename
        _download_url(session, url, dest, args.verbose)
        meta = extract_metadata(dest)
        item = create_stac_item(dest, meta, collection_id)
        stac_items.append(item)

    build_catalog(stac_items, output_dir, collection_id)
    print(f"[http] Done. {len(stac_items)} file(s) in {output_dir}/")


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
