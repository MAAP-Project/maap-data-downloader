#!/bin/bash
# ==============================================================================
# MAAP Wrapper: Earthdata Downloader
# Invokes the Python CLI to search Earthdata and download granules via MAAP.
# ==============================================================================
set -euo pipefail

if [ -f /opt/conda/etc/profile.d/conda.sh ]; then
    source /opt/conda/etc/profile.d/conda.sh
fi
conda activate maap-downloader

echo "[run_earthdata] Starting Earthdata downloader"

# HOME must be set before any Python call that resolves Path.home().
export HOME=/root

# Capture the CWL job working directory's outputs path before `cd /app`,
# so CWL's `outputBinding.glob: outputs` can find the results.
OUT_DIR="${PWD}/outputs"
mkdir -p "$OUT_DIR"

cd /app
python -m earthdata.main --output "$OUT_DIR" "$@"

echo "[run_earthdata] Complete. Output directory:"
ls -lh "$OUT_DIR/" 2>/dev/null || true
