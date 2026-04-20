"""SFTP downloader: retrieve files via SSH/SFTP using paramiko."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from maap_data_downloaders.auth import get_maap_secret
from maap_data_downloaders.file_utils import extract_metadata
from maap_data_downloaders.stac_utils import build_catalog, create_stac_item


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download files via SFTP and generate STAC metadata."
    )
    p.add_argument("--host", required=True, help="SFTP hostname")
    p.add_argument("--remote-path", required=True, help="Remote directory or file path to download")
    p.add_argument("--port", type=int, default=22, help="SFTP port (default: 22)")
    p.add_argument(
        "--username-secret",
        default="SFTP_USERNAME",
        help="MAAP secret name for SFTP username (default: SFTP_USERNAME)",
    )
    p.add_argument(
        "--password-secret",
        default="SFTP_PASSWORD",
        help="MAAP secret name for SFTP password (default: SFTP_PASSWORD)",
    )
    p.add_argument(
        "--collection-id",
        default=None,
        help="STAC collection ID (default: SFTP hostname)",
    )
    p.add_argument("--output", default="outputs", help="Output directory (default: outputs)")
    p.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return p.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    import paramiko  # type: ignore[import]

    output_dir = Path(args.output)
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    collection_id = args.collection_id or args.host

    username = get_maap_secret(args.username_secret)
    password = get_maap_secret(args.password_secret)

    if args.verbose:
        print(f"[sftp] Connecting to {args.host}:{args.port} as {username}")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(args.host, port=args.port, username=username, password=password)
        sftp = ssh.open_sftp()

        remote = args.remote_path
        try:
            # Try listing as directory
            entries = sftp.listdir_attr(remote)
            files_to_download = [f"{remote}/{e.filename}" for e in entries if not e.filename.startswith(".")]
        except IOError:
            # It's a single file
            files_to_download = [remote]

        if args.verbose:
            print(f"[sftp] {len(files_to_download)} file(s) to download")

        stac_items = []
        for remote_file in files_to_download:
            local_path = data_dir / Path(remote_file).name
            sftp.get(remote_file, str(local_path))
            if args.verbose:
                print(f"[sftp] Downloaded {remote_file} → {local_path}")
            meta = extract_metadata(local_path)
            item = create_stac_item(local_path, meta, collection_id)
            stac_items.append(item)

        sftp.close()
    finally:
        ssh.close()

    build_catalog(stac_items, output_dir, collection_id)
    print(f"[sftp] Done. {len(stac_items)} file(s) in {output_dir}/")


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
