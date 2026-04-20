#!/bin/bash
# ==============================================================================
# MAAP Wrapper: OPeNDAP Downloader
# No authentication required for public OPeNDAP endpoints.
# Uses xarray + PyDAP with dask chunking to handle large datasets safely.
# ==============================================================================
set -euo pipefail

source activate maap-downloader

echo "[run_opendap] Starting OPeNDAP downloader"

# ---------------------------------------------------------------------------
# Step 1: Create output directory
# ---------------------------------------------------------------------------
mkdir -p "${PWD}/outputs"
export HOME=/home/ops

# ---------------------------------------------------------------------------
# Step 2: Invoke Python CLI
# ---------------------------------------------------------------------------
cd /app
python -m opendap.main --output "${PWD}/outputs" "$@"

echo "[run_opendap] Complete. Output directory:"
ls -lh "${PWD}/outputs/" 2>/dev/null || true
