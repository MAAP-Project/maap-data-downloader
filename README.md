# MAAP Data Downloaders

A collection of reusable **OGC Application Packages** for downloading scientific data in the NASA MAAP (Multi-Mission Algorithm and Analysis Platform) environment. Each downloader is independently deployable as a MAAP DPS job.

## Overview

| Downloader | Directory | Use Case |
|---|---|---|
| NASA DAAC | `nasa_daac/` | Any CMR-indexed NASA dataset via earthaccess |
| SFTP | `sftp/` | Arbitrary SFTP server |
| HTTP/HTTPS | `http_download/` | Public or authenticated HTTP URLs |
| OPeNDAP | `opendap/` | Subset data from OPeNDAP/THREDDS catalogs |

Every downloader:
- Retrieves credentials from the **MAAP secrets vault** (`maap.secrets.get_secret()`) — no hardcoded passwords
- Generates a **STAC metadata catalog** for every downloaded file
- Outputs to `outputs/` in a standard structure compatible with MAAP DPS

## Repository Structure

```
maap-data-downloaders/
├── environment.yaml              # Conda env (shared by all downloaders)
├── pyproject.toml                # Python package metadata
├── Dockerfile                    # Multi-stage conda build (unified image)
├── FEATURES.md                   # Feature tracker for parallel development
├── src/
│   └── maap_data_downloaders/    # Shared core library
│       ├── auth.py               # MAAP secrets + ~/.netrc writer
│       ├── file_utils.py         # HDF5/NetCDF metadata extraction
│       └── stac_utils.py         # pystac Item/Collection/Catalog builder
├── nasa_daac/
│   ├── main.py                   # CLI: earthaccess search + download
│   ├── process.cwl               # OGC Application Package
│   ├── run_nasa_daac.sh          # MAAP wrapper script
│   └── examples/basic.yml
├── sftp/
│   ├── main.py
│   ├── process.cwl
│   ├── run_sftp.sh
│   └── examples/basic.yml
├── http_download/
│   ├── main.py
│   ├── process.cwl
│   ├── run_http.sh
│   └── examples/basic.yml
├── opendap/
│   ├── main.py
│   ├── process.cwl
│   ├── run_opendap.sh
│   └── examples/basic.yml
└── tests/
    ├── conftest.py
    ├── test_file_utils.py
    └── test_stac_utils.py
```

## Output Structure

All downloaders write to the same structure:

```
outputs/
├── catalog.json                  # Root STAC catalog
├── {collection_id}/
│   ├── collection.json           # STAC collection
│   └── items/
│       └── {item_id}.json        # STAC item per downloaded file
└── data/
    └── *.nc / *.h5               # Downloaded data files
```

## Prerequisites

**MAAP Secrets** — set before running any downloader:

```python
from maap.maap import MAAP
maap = MAAP()

# For NASA DAAC downloads
maap.secrets.add_secret("EARTHDATA_USERNAME", "your_edl_username")
maap.secrets.add_secret("EARTHDATA_PASSWORD", "your_edl_password")

# For SFTP downloads
maap.secrets.add_secret("SFTP_USERNAME", "your_sftp_user")
maap.secrets.add_secret("SFTP_PASSWORD", "your_sftp_password")
```

## Usage

### NASA DAAC Downloader

Download any CMR-indexed dataset by concept ID:

```bash
python -m nasa_daac.main \
  --concept-id C1276812812-GES_DISC \
  --bbox "-125,24,-66,49" \
  --temporal-start 2020-01-01 \
  --temporal-end 2020-01-31 \
  --collection-id merra2-conus-jan2020
```

**CWL input** (`nasa_daac/examples/basic.yml`):
```yaml
concept_id: "C1276812812-GES_DISC"
bbox: "-125,24,-66,49"
temporal_start: "2020-01-01"
temporal_end: "2020-01-31"
collection_id: "merra2-conus-jan2020"
```

### SFTP Downloader

```bash
python -m sftp.main \
  --host sftp.example-daac.org \
  --remote-path /data/science/2020/ \
  --username-secret SFTP_USERNAME \
  --password-secret SFTP_PASSWORD \
  --collection-id example-sftp-data
```

### HTTP Downloader

```bash
# Public URL (no auth)
python -m http_download.main \
  --url https://data.example.gov/file.nc \
  --collection-id example-nc

# Bearer token auth
python -m http_download.main \
  --url https://protected.example.gov/data.nc \
  --auth-type bearer \
  --token-secret MY_API_TOKEN \
  --collection-id protected-data
```

### OPeNDAP Downloader

```bash
python -m opendap.main \
  --url https://thredds.server.org/dodsC/dataset.nc \
  --variables Temperature,Salinity \
  --bbox "-125,24,-66,49" \
  --temporal-start 2020-01-01 \
  --temporal-end 2020-01-31 \
  --chunks '{"time": 1}' \
  --collection-id ocean-subset
```

## Running with CWL (cwltool)

```bash
# Validate CWL
cwltool --validate nasa_daac/process.cwl

# Run locally (requires Docker)
cwltool nasa_daac/process.cwl nasa_daac/examples/basic.yml
```

## Docker

```bash
# Build
docker build -t maap-data-downloaders .

# Verify environment
docker run --rm maap-data-downloaders python -c "import earthaccess, pystac, paramiko; print('OK')"

# Run NASA DAAC downloader in container
docker run --rm -v $(pwd)/outputs:/outputs maap-data-downloaders \
  /app/nasa_daac/run_nasa_daac.sh \
    --concept-id C1276812812-GES_DISC \
    --bbox "-125,24,-66,49"
```

## Running Tests

```bash
conda activate maap-downloader
pip install -e .
pytest tests/ -v
```

## Resource Requirements

| Downloader | CPU | RAM | Output Space |
|---|---|---|---|
| NASA DAAC | 2 cores | 8 GB | 50 GB |
| SFTP | 1 core | 4 GB | 20 GB |
| HTTP | 1 core | 2 GB | 20 GB |
| OPeNDAP | 2 cores | 8 GB | 20 GB |

## Credential Security

Credentials are never stored in CWL files or environment variables. The flow is:

1. MAAP secrets vault → `maap.secrets.get_secret("KEY")`
2. Wrapper script writes `~/.netrc` (mode 600) if needed by earthaccess
3. Python CLI reads credentials only at runtime

## Adding a New Downloader

1. Create `{source}/main.py` with a CLI that calls `extract_metadata()` + `create_stac_item()` + `build_catalog()`
2. Create `{source}/process.cwl` following the pattern in `nasa_daac/process.cwl`
3. Create `{source}/run_{source}.sh` following the wrapper pattern
4. Add `COPY {source}/ /app/{source}/` and `chmod +x` to `Dockerfile`
5. Update `FEATURES.md`
