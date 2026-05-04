#!/bin/bash
# ==============================================================================
# MAAP Wrapper: HTTP/HTTPS Downloader
# Optional auth credentials are retrieved from MAAP secrets vault at runtime.
# Public URLs require no credentials.
# ==============================================================================
set -euo pipefail

echo "[run_http] Starting HTTP downloader"

export HOME=/root

# Capture output path before cd /app so CWL's `glob: outputs` resolves correctly.
OUT_DIR="${PWD}/outputs"
mkdir -p "$OUT_DIR"

# Auth credentials (if needed) are retrieved inside Python via maap-py secrets.
cd /app
python -m http_download.main --output "$OUT_DIR" "$@"

echo "[run_http] Complete. Output directory:"
ls -lh "$OUT_DIR/" 2>/dev/null || true
