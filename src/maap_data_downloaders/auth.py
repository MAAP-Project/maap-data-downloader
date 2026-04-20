"""Credential helpers: retrieve secrets from MAAP vault and configure auth files."""

from __future__ import annotations

import os
import stat
from pathlib import Path


def get_maap_secret(secret_name: str) -> str:
    """Retrieve a secret from the MAAP secrets vault."""
    from maap.maap import MAAP  # type: ignore[import]
    maap = MAAP()
    value = maap.secrets.get_secret(secret_name)
    if not value:
        raise RuntimeError(f"MAAP secret '{secret_name}' is empty or not found.")
    return value


def get_earthdata_credentials(
    username_secret: str = "EARTHDATA_USERNAME",
    password_secret: str = "EARTHDATA_PASSWORD",
) -> tuple[str, str]:
    """Return (username, password) from MAAP secrets vault."""
    username = get_maap_secret(username_secret)
    password = get_maap_secret(password_secret)
    return username, password


def write_netrc(username: str, password: str, host: str = "urs.earthdata.nasa.gov") -> None:
    """Write ~/.netrc entry for EDL auth (used by earthaccess / requests)."""
    netrc_path = Path.home() / ".netrc"

    existing = netrc_path.read_text() if netrc_path.exists() else ""
    # Remove any existing entry for this host to avoid duplicates
    lines = [
        line for line in existing.splitlines()
        if host not in line
    ]

    lines += [
        f"machine {host}",
        f"  login {username}",
        f"  password {password}",
        "",
    ]
    netrc_path.write_text("\n".join(lines))
    netrc_path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # chmod 600
