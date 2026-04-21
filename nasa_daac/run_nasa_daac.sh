#!/bin/bash
# ==============================================================================
# MAAP Wrapper: NASA DAAC Downloader
# Retrieves Earthdata credentials from MAAP secrets vault, then invokes the
# Python CLI to search CMR and download granules via earthaccess.
# ==============================================================================
set -euo pipefail

if [ -f /opt/conda/etc/profile.d/conda.sh ]; then
    source /opt/conda/etc/profile.d/conda.sh
fi
conda activate maap-downloader

echo "[run_nasa_daac] Starting NASA DAAC downloader"

# HOME must be set before any Python call that resolves Path.home() (write_netrc).
export HOME=/root

# Capture the CWL job working directory's outputs path before `cd /app`,
# so CWL's `outputBinding.glob: outputs` can find the results.
OUT_DIR="${PWD}/outputs"
mkdir -p "$OUT_DIR"

# Fetch Earthdata credentials from MAAP secrets vault and write ~/.netrc.
# Secrets stay inside the Python process (no shell interpolation).
python - <<'PY'
from maap_data_downloaders.auth import get_earthdata_credentials, write_netrc
user, pw = get_earthdata_credentials()
write_netrc(user, pw)
print("[run_nasa_daac] Earthdata credentials configured.")
PY

cd /app
python -m nasa_daac.main --output "$OUT_DIR" "$@"

echo "[run_nasa_daac] Complete. Output directory:"
ls -lh "$OUT_DIR/" 2>/dev/null || true
