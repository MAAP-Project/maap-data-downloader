#!/bin/bash
# ==============================================================================
# MAAP Wrapper: SFTP Downloader
# Credentials for SFTP are retrieved from MAAP secrets vault at runtime.
# The secret names are passed as --username-secret and --password-secret args.
# ==============================================================================
set -euo pipefail

echo "[run_sftp] Starting SFTP downloader"

export HOME=/root

# Capture output path before cd /app so CWL's `glob: outputs` resolves correctly.
OUT_DIR="${PWD}/outputs"
mkdir -p "$OUT_DIR"

# Credentials are retrieved inside Python via maap-py secrets.
cd /app
python -m sftp.main --output "$OUT_DIR" "$@"

echo "[run_sftp] Complete. Output directory:"
ls -lh "$OUT_DIR/" 2>/dev/null || true
