cwlVersion: v1.2

# ==============================================================================
# MAAP OPeNDAP Downloader - OGC Application Package
# ==============================================================================

$namespaces:
  s: https://schema.org/

$schemas:
  - http://schema.org/version/latest/schemaorg-current-https.rdf

s:softwareVersion: 1.0.0
s:version: 1.0.0
s:datePublished: 2026-04-20
s:author:
  - class: s:Person
    s:name: MAAP Development Team
    s:email: support@maap-project.org

s:codeRepository: https://github.com/MAAP-Project/maap-data-downloaders
s:license: https://opensource.org/licenses/Apache-2.0

$graph:

  # ============================================================================
  # WORKFLOW (Entry Point) - OGC Application Package Interface
  # ============================================================================

  - class: Workflow
    id: maap-opendap-downloader
    label: MAAP OPeNDAP Downloader

    doc: |
      Subsets and downloads data from an OPeNDAP dataset URL using xarray
      (PyDAP engine). Supports variable, spatial, and temporal subsetting
      at access time to avoid downloading unnecessary data. Uses dask chunking
      to prevent out-of-memory errors on large datasets. Saves as zlib-compressed
      NetCDF (CF-1.8) and produces a STAC metadata catalog.

    inputs:

      url:
        type: string
        label: OPeNDAP Dataset URL
        doc: |
          Full OPeNDAP dataset URL ending in .nc, .nc4, or similar.
          Example: https://opendap.earthdata.nasa.gov/providers/GES_DISC/collections/...

      variables:
        type: string?
        label: Variables to Subset
        doc: |
          Comma-separated list of variable names to include.
          If omitted, all variables are downloaded.
          Example: Temperature,Pressure,Humidity

      bbox:
        type: string?
        label: Spatial Bounding Box
        doc: |
          Spatial subset as 'min_lon,min_lat,max_lon,max_lat'.
          Requires the dataset to have recognizable lat/lon dimensions.
          Example: -125,24,-66,49

      temporal_start:
        type: string?
        label: Temporal Start
        doc: Start of temporal subset (YYYY-MM-DD). Requires a time dimension.

      temporal_end:
        type: string?
        label: Temporal End
        doc: End of temporal subset (YYYY-MM-DD). Requires a time dimension.

      chunks:
        type: string?
        default: '{"time": 1}'
        label: Dask Chunks
        doc: |
          Dask chunk sizes as a JSON string. Controls memory usage.
          Default '{"time": 1}' processes one time step at a time.
          Example: '{"time": 10, "lat": 100, "lon": 100}'

      collection_id:
        type: string?
        label: STAC Collection ID
        doc: |
          Identifier for the output STAC collection.
          Defaults to the dataset filename stem from the URL.

      verbose:
        type: boolean?
        default: false
        label: Verbose Logging
        doc: Enable detailed progress output.

    outputs:

      outputs_result:
        type: Directory
        doc: |
          Output directory with subsetted NetCDF and STAC catalog.

          Directory structure:
            outputs/
            ├── catalog.json
            ├── {collection_id}/
            │   ├── collection.json
            │   └── items/
            │       └── {dataset_name}.json
            └── data/
                └── {dataset_name}.nc   # Zlib-compressed CF-1.8 NetCDF
        outputSource: download_step/outputs_result

      stac_catalog:
        type: File
        doc: Root STAC catalog JSON file (outputs/catalog.json).
        outputSource: download_step/stac_catalog

    steps:
      download_step:
        run: "#main"
        in:
          url: url
          variables: variables
          bbox: bbox
          temporal_start: temporal_start
          temporal_end: temporal_end
          chunks: chunks
          collection_id: collection_id
          verbose: verbose
        out: [outputs_result, stac_catalog]

  # ============================================================================
  # COMMANDLINETOOL (Execution Step)
  # ============================================================================

  - class: CommandLineTool
    id: main
    label: OPeNDAP Downloader Tool

    doc: |
      Executes the OPeNDAP downloader inside Docker.
      No credentials required for public OPeNDAP endpoints.

    requirements:
      DockerRequirement:
        dockerPull: ghcr.io/maap-project/maap-data-downloaders:latest

      ResourceRequirement:
        coresMin: 2
        ramMin: 8192
        tmpdirMin: 10240
        outdirMin: 20480

      NetworkAccess:
        networkAccess: true

      EnvVarRequirement:
        envDef:
          PYTHONUNBUFFERED: "1"

    inputs:

      url:
        type: string
        label: OPeNDAP URL
        inputBinding:
          prefix: --url

      variables:
        type: string?
        label: Variables
        inputBinding:
          prefix: --variables

      bbox:
        type: string?
        label: Bounding Box
        inputBinding:
          prefix: --bbox

      temporal_start:
        type: string?
        label: Temporal Start
        inputBinding:
          prefix: --temporal-start

      temporal_end:
        type: string?
        label: Temporal End
        inputBinding:
          prefix: --temporal-end

      chunks:
        type: string?
        default: '{"time": 1}'
        label: Dask Chunks
        inputBinding:
          prefix: --chunks

      collection_id:
        type: string?
        label: STAC Collection ID
        inputBinding:
          prefix: --collection-id

      verbose:
        type: boolean?
        default: false
        label: Verbose Logging
        inputBinding:
          prefix: --verbose

    outputs:

      outputs_result:
        type: Directory
        outputBinding:
          glob: outputs

      stac_catalog:
        type: File
        outputBinding:
          glob: outputs/catalog.json

    baseCommand: ["/app/opendap/run_opendap.sh"]
    successCodes: [0]
