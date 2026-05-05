# Multi-stage build: builder installs deps, production is lean
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install .
# Fix earthaccess bug: use get_file for single-file downloads (sync) instead of get (async bulk)
# https://github.com/earthaccess-dev/earthaccess/issues/1331
RUN sed -i \
    's/s3_fs\.get(\[file\], str(temp_name), recursive=False)/s3_fs.get_file(file, str(temp_name))/' \
    /install/lib/python3.12/site-packages/earthaccess/store.py

# ============================================================================
# Production Stage - Unified image for all four downloaders
# ============================================================================
FROM python:3.12-slim

LABEL maintainer="MAAP Team <support@maap-project.org>"
LABEL version="1.0.0"
LABEL description="MAAP Data Downloaders - OGC Application Packages (Earthdata, SFTP, HTTP, OPeNDAP)"
LABEL org.opencontainers.image.source="https://github.com/MAAP-Project/maap-data-downloaders"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.title="maap-data-downloaders"

# Needed by rasterio
RUN apt-get update && apt-get install -y --no-install-recommends \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED="1"

WORKDIR /app

COPY src/ /app/src/
COPY pyproject.toml /app/
COPY earthdata/ /app/earthdata/
COPY sftp/ /app/sftp/
COPY http_download/ /app/http_download/
COPY opendap/ /app/opendap/

RUN chmod +x /app/earthdata/run_*.sh \
              /app/sftp/run_*.sh \
              /app/http_download/run_*.sh \
              /app/opendap/run_*.sh && \
    pip install --no-cache-dir --no-deps -e .

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import maap_data_downloaders; print('OK')" || exit 1

CMD ["/bin/bash"]
