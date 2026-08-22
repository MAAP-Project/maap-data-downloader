"""Importable library API for downloading Earthdata granules via earthaccess."""

from __future__ import annotations

import os
from pathlib import Path

import earthaccess  # type: ignore[import]

from maap_data_downloaders.auth import get_earthdata_token
from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item


class AuthenticationError(RuntimeError):
    """Raised when Earthdata authentication fails."""


class NoGranulesFoundError(RuntimeError):
    """Raised when a CMR search returns no granules."""


class DownloadError(RuntimeError):
    """Raised when granule search or download fails."""


def download_earthdata(
    short_name: str | None = None,
    concept_id: str | None = None,
    bbox: str | None = None,
    temporal_start: str | None = None,
    temporal_end: str | None = None,
    limit: int = 20,
    collection_id: str | None = None,
    output_dir: str = "outputs",
    auth_strategy: str = "environment",
    token_secret: str = "EARTHDATA_TOKEN",
    verbose: bool = False,
) -> list[str]:
    """Search for and download NASA Earthdata granules via CMR, writing a STAC catalog.

    Args:
        short_name: CMR collection short name (e.g. 'SNDRJ1CrISL1B').
        concept_id: CMR concept ID (alternative to short_name).
        bbox: Bounding box as 'west,south,east,north'.
        temporal_start: Start date YYYY-MM-DD (optional).
        temporal_end: End date YYYY-MM-DD (optional).
        limit: Maximum number of granules to fetch.
        collection_id: STAC collection ID for output catalog (default: short_name or concept_id).
        output_dir: Output directory path.
        auth_strategy: 'environment' (MAAP secrets), 'netrc' (~/.netrc), or 'interactive' (prompt).
        token_secret: MAAP secret name for Earthdata token (only used with auth_strategy='environment').
        verbose: Enable verbose logging.

    Returns:
        List of local filesystem paths for the downloaded granules.

    Raises:
        ValueError: If required arguments are missing or malformed.
        AuthenticationError: If authentication fails.
        NoGranulesFoundError: If no granules match the search.
        DownloadError: If the CMR search or download fails.
    """
    output_path = Path(output_dir)
    data_dir = output_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    if collection_id:
        resolved_collection_id = collection_id
    elif short_name:
        resolved_collection_id = short_name
    elif concept_id:
        resolved_collection_id = concept_id
    else:
        raise ValueError("Must provide short_name, concept_id, or collection_id")

    if not bbox:
        raise ValueError("Must provide bbox")

    if verbose:
        print(f"[earthdata] short_name={short_name} concept_id={concept_id} bbox={bbox}")

    try:
        if auth_strategy == "environment":
            token = get_earthdata_token(token_secret)
            os.environ["EARTHDATA_TOKEN"] = token
            earthaccess.login(strategy="environment")
        elif auth_strategy == "netrc":
            earthaccess.login(strategy="netrc")
        elif auth_strategy == "interactive":
            earthaccess.login(strategy="interactive")
        else:
            raise ValueError(f"Unknown auth_strategy: {auth_strategy!r}")
    except ValueError:
        raise
    except Exception as exc:
        hint = ""
        if auth_strategy == "netrc":
            hint = " Make sure ~/.netrc has credentials for urs.earthdata.nasa.gov."
        raise AuthenticationError(f"Authentication failed: {exc}.{hint}") from exc

    try:
        west, south, east, north = (float(x) for x in bbox.split(","))
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Invalid bbox format: {exc}") from exc

    search_kwargs: dict = {"bounding_box": (west, south, east, north), "count": limit}

    if short_name:
        search_kwargs["short_name"] = short_name
    elif concept_id:
        search_kwargs["concept_id"] = concept_id

    if temporal_start or temporal_end:
        search_kwargs["temporal"] = (temporal_start or "", temporal_end or "")

    try:
        results = earthaccess.search_data(**search_kwargs)
    except Exception as exc:
        raise DownloadError(f"search_data failed: {exc}") from exc

    if not results:
        raise NoGranulesFoundError("No granules found for the given search parameters.")

    if verbose:
        print(f"[earthdata] Found {len(results)} granule(s). Downloading…")

    try:
        downloaded_paths = earthaccess.download(results, local_path=str(data_dir), show_progress=True, force=True)
    except Exception as exc:
        raise DownloadError(f"download failed: {exc}") from exc

    stac_items = []
    for filepath in downloaded_paths:
        try:
            meta = extract_metadata(filepath)
            item = create_stac_item(filepath, meta, resolved_collection_id)
            stac_items.append(item)
        except Exception as exc:
            print(f"[earthdata] WARNING: STAC creation failed for {filepath}: {exc}")

    if not stac_items:
        raise DownloadError("No granules were successfully processed.")

    build_catalog(stac_items, output_path, resolved_collection_id)

    if verbose:
        print(f"[earthdata] Done. {len(stac_items)} file(s) in {output_path}/")

    return [str(p) for p in downloaded_paths]
