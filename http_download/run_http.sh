#!/bin/bash
# ==============================================================================
# MAAP Wrapper: HTTP/HTTPS Downloader
# Optional auth credentials are retrieved from MAAP secrets vault at runtime.
# Public URLs require no credentials.
# ==============================================================================
set -euo pipefail

source activate maap-downloader

echo "[run_http] Starting HTTP downloader"

# ---------------------------------------------------------------------------
# Step 1: Create output directory
# ---------------------------------------------------------------------------
mkdir -p "${PWD}/outputs"
export HOME=/home/ops

# ---------------------------------------------------------------------------
# Step 2: Invoke Python CLI
# Auth credentials (if needed) are retrieved inside Python via maap-py secrets.
# ---------------------------------------------------------------------------
cd /app
python -m http_download.main --output "${PWD}/outputs" "$@"

echo "[run_http] Complete. Output directory:"
ls -lh "${PWD}/outputs/" 2>/dev/null || true
