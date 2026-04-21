#!/bin/bash
# ==============================================================================
# MAAP Wrapper: OPeNDAP Downloader
# No authentication required for public OPeNDAP endpoints.
# Uses xarray + PyDAP with dask chunking to handle large datasets safely.
# ==============================================================================
set -euo pipefail

if [ -f /opt/conda/etc/profile.d/conda.sh ]; then
    source /opt/conda/etc/profile.d/conda.sh
fi
conda activate maap-downloader

echo "[run_opendap] Starting OPeNDAP downloader"

export HOME=/root

# Capture output path before cd /app so CWL's `glob: outputs` resolves correctly.
OUT_DIR="${PWD}/outputs"
mkdir -p "$OUT_DIR"

cd /app
python -m opendap.main --output "$OUT_DIR" "$@"

echo "[run_opendap] Complete. Output directory:"
ls -lh "$OUT_DIR/" 2>/dev/null || true
