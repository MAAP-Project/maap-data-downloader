# Multi-stage build: builder installs conda env, production copies it in
FROM condaforge/miniforge3:25.11.0-0 AS builder

WORKDIR /build

COPY environment.yaml /build/

RUN conda env create -f environment.yaml && \
    conda clean -afy

# Install maap-py separately (not on conda-forge)
RUN /opt/conda/envs/maap-downloader/bin/pip install --no-cache-dir maap-py

# ============================================================================
# Production Stage - Unified image for all four downloaders
# ============================================================================
FROM condaforge/miniforge3:25.11.0-0

LABEL maintainer="MAAP Team <support@maap-project.org>"
LABEL version="1.0.0"
LABEL description="MAAP Data Downloaders - OGC Application Packages (NASA DAAC, SFTP, HTTP, OPeNDAP)"
LABEL org.opencontainers.image.source="https://github.com/MAAP-Project/maap-data-downloaders"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.title="maap-data-downloaders"

COPY --from=builder /opt/conda/envs/maap-downloader /opt/conda/envs/maap-downloader

ENV PATH="/opt/conda/envs/maap-downloader/bin:$PATH"
ENV CONDA_DEFAULT_ENV="maap-downloader"
ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED="1"

WORKDIR /app

COPY src/ /app/src/
COPY pyproject.toml /app/
COPY nasa_daac/ /app/nasa_daac/
COPY sftp/ /app/sftp/
COPY http_download/ /app/http_download/
COPY opendap/ /app/opendap/

RUN chmod +x /app/nasa_daac/run_*.sh \
              /app/sftp/run_*.sh \
              /app/http_download/run_*.sh \
              /app/opendap/run_*.sh && \
    /opt/conda/envs/maap-downloader/bin/pip install -e .

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import maap_data_downloaders; print('OK')" || exit 1

CMD ["/bin/bash"]
