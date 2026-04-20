#!/bin/bash
# ==============================================================================
# MAAP Wrapper: NASA DAAC Downloader
# Retrieves Earthdata credentials from MAAP secrets vault, then invokes the
# Python CLI to search CMR and download granules via earthaccess.
# ==============================================================================
set -euo pipefail

source activate maap-downloader

echo "[run_nasa_daac] Starting NASA DAAC downloader"

# ---------------------------------------------------------------------------
# Step 1: Retrieve Earthdata credentials from MAAP secrets vault
# ---------------------------------------------------------------------------
SECRETS_OUTPUT=$(python -c "
from maap.maap import MAAP
maap = MAAP()
print(maap.secrets.get_secret('EARTHDATA_USERNAME'))
print(maap.secrets.get_secret('EARTHDATA_PASSWORD'))
" 2>&1) || {
    echo "[run_nasa_daac] ERROR: Could not retrieve Earthdata credentials from MAAP secrets."
    echo "[run_nasa_daac] Ensure EARTHDATA_USERNAME and EARTHDATA_PASSWORD are set in the MAAP secrets vault."
    exit 1
}

EDL_USERNAME=$(echo "$SECRETS_OUTPUT" | sed -n '1p')
EDL_PASSWORD=$(echo "$SECRETS_OUTPUT" | sed -n '2p')

if [ -z "$EDL_USERNAME" ] || [ -z "$EDL_PASSWORD" ]; then
    echo "[run_nasa_daac] ERROR: Empty credentials retrieved from MAAP secrets." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 2: Write ~/.netrc for earthaccess authentication
# ---------------------------------------------------------------------------
python -c "
import sys
sys.argv = ['auth']
from maap_data_downloaders.auth import write_netrc
write_netrc('${EDL_USERNAME}', '${EDL_PASSWORD}')
"

echo "[run_nasa_daac] Earthdata credentials configured."

# ---------------------------------------------------------------------------
# Step 3: Create output directory
# ---------------------------------------------------------------------------
mkdir -p "${PWD}/outputs"
export HOME=/home/ops

# ---------------------------------------------------------------------------
# Step 4: Invoke Python CLI
# ---------------------------------------------------------------------------
cd /app
python -m nasa_daac.main --output "${PWD}/outputs" "$@"

echo "[run_nasa_daac] Complete. Output directory:"
ls -lh "${PWD}/outputs/" 2>/dev/null || true
