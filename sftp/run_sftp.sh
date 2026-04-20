#!/bin/bash
# ==============================================================================
# MAAP Wrapper: SFTP Downloader
# Credentials for SFTP are retrieved from MAAP secrets vault at runtime.
# The secret names are passed as --username-secret and --password-secret args.
# ==============================================================================
set -euo pipefail

source activate maap-downloader

echo "[run_sftp] Starting SFTP downloader"

# ---------------------------------------------------------------------------
# Step 1: Create output directory
# ---------------------------------------------------------------------------
mkdir -p "${PWD}/outputs"
export HOME=/home/ops

# ---------------------------------------------------------------------------
# Step 2: Invoke Python CLI
# Credentials are retrieved inside Python via maap-py secrets.
# ---------------------------------------------------------------------------
cd /app
python -m sftp.main --output "${PWD}/outputs" "$@"

echo "[run_sftp] Complete. Output directory:"
ls -lh "${PWD}/outputs/" 2>/dev/null || true
