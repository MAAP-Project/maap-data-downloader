# MAAP Data Downloaders — Feature Tracker

Status key: `⬜ pending` | `🔄 in progress` | `✅ done`

---

## Feature A — Shared Core Library

| Status | File | Description |
|--------|------|-------------|
| ✅ done | `environment.yaml` | Conda env `maap-downloader` with all shared deps |
| ✅ done | `pyproject.toml` | Package metadata for `pip install -e .` |
| ✅ done | `src/maap_data_downloaders/__init__.py` | Package init |
| ✅ done | `src/maap_data_downloaders/auth.py` | MAAP secrets + ~/.netrc writer |
| ✅ done | `src/maap_data_downloaders/file_utils.py` | HDF5/NetCDF metadata extraction |
| ✅ done | `src/maap_data_downloaders/stac_utils.py` | pystac Item/Collection/Catalog builder |

---

## Feature B — NASA DAAC Downloader

| Status | File | Description |
|--------|------|-------------|
| ⬜ pending | `nasa_daac/main.py` | CLI: earthaccess search + download + STAC |
| ⬜ pending | `nasa_daac/process.cwl` | OGC Application Package CWL v1.2 |
| ⬜ pending | `nasa_daac/run_nasa_daac.sh` | MAAP wrapper (conda activate → secrets → CLI) |
| ⬜ pending | `nasa_daac/examples/basic.yml` | Example CWL inputs |

---

## Feature C — SFTP Downloader

| Status | File | Description |
|--------|------|-------------|
| ⬜ pending | `sftp/main.py` | CLI: paramiko SFTP transfer + STAC |
| ⬜ pending | `sftp/process.cwl` | OGC Application Package CWL v1.2 |
| ⬜ pending | `sftp/run_sftp.sh` | MAAP wrapper |
| ⬜ pending | `sftp/examples/basic.yml` | Example CWL inputs |

---

## Feature D — HTTP/curl Downloader

| Status | File | Description |
|--------|------|-------------|
| ⬜ pending | `http_download/main.py` | CLI: requests HTTP download + STAC |
| ⬜ pending | `http_download/process.cwl` | OGC Application Package CWL v1.2 |
| ⬜ pending | `http_download/run_http.sh` | MAAP wrapper |
| ⬜ pending | `http_download/examples/basic.yml` | Example CWL inputs |

---

## Feature E — OPeNDAP Downloader

| Status | File | Description |
|--------|------|-------------|
| ⬜ pending | `opendap/main.py` | CLI: xarray OPeNDAP access + subset + STAC |
| ⬜ pending | `opendap/process.cwl` | OGC Application Package CWL v1.2 |
| ⬜ pending | `opendap/run_opendap.sh` | MAAP wrapper |
| ⬜ pending | `opendap/examples/basic.yml` | Example CWL inputs |

---

## Feature F — Dockerfile + Infrastructure

| Status | File | Description |
|--------|------|-------------|
| ⬜ pending | `Dockerfile` | Multi-stage conda build (unified image) |
| ⬜ pending | `README.md` | Full usage documentation |

---

## Tests

| Status | File | Description |
|--------|------|-------------|
| ⬜ pending | `tests/conftest.py` | Fixtures (synthetic HDF5, NC, mock MAAP) |
| ⬜ pending | `tests/test_stac_utils.py` | STAC generation unit tests |
| ⬜ pending | `tests/test_file_utils.py` | Metadata extraction unit tests |

---

## Validation Checklist

- [ ] `python -c "from maap_data_downloaders.stac_utils import create_stac_item"` exits 0
- [ ] `cwltool --validate nasa_daac/process.cwl` passes
- [ ] `cwltool --validate sftp/process.cwl` passes
- [ ] `cwltool --validate http_download/process.cwl` passes
- [ ] `cwltool --validate opendap/process.cwl` passes
- [ ] `docker build -t maap-data-downloaders .` exits 0
