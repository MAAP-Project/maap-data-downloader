cwlVersion: v1.2

# ==============================================================================
# MAAP Earthdata Downloader - OGC Application Package
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
    id: maap-earthdata-downloader
    label: MAAP Earthdata Downloader

    doc: |
      Downloads granules from Earthdata using MAAP search capabilities.
      Supports search by CMR short name or concept ID with spatial and temporal filtering.
      Produces data files and a STAC metadata catalog.

      Inputs: Short name or concept ID + bounding box + optional temporal range.
      Outputs: data files in outputs/data/ + STAC catalog at outputs/catalog.json.

    inputs:

      short_name:
        type: string?
        label: CMR Short Name
        doc: |
          NASA CMR collection short name identifying the dataset.
          Example: GEDI02_A, MERRA2, GPM_3IMERGHH
          Find short names at: https://cmr.earthdata.nasa.gov/search/collections

      concept_id:
        type: string?
        label: CMR Concept ID
        doc: |
          NASA CMR concept ID identifying the dataset collection.
          Example: C2036882064-GES_DISC (MERRA-2)
          Mutually exclusive with short_name.
          Find IDs at: https://cmr.earthdata.nasa.gov/search/collections

      bbox:
        type: string
        label: Bounding Box
        doc: |
          Spatial bounding box as 'min_lon,min_lat,max_lon,max_lat'.
          Example: '-180,-90,180,90' (global)
          Example: '-125,24,-66,49' (CONUS)

      temporal_start:
        type: string?
        label: Temporal Start
        doc: |
          Start date for temporal filtering (optional).
          Format: YYYY-MM-DD
          Example: 2020-01-01

      temporal_end:
        type: string?
        label: Temporal End
        doc: |
          End date for temporal filtering (optional).
          Format: YYYY-MM-DD
          Example: 2020-12-31

      limit:
        type: int?
        default: 20
        label: Granule Limit
        doc: |
          Maximum number of granules to download.
          Default: 20

      collection_id:
        type: string?
        label: STAC Collection ID
        doc: |
          Identifier for the output STAC collection.
          If omitted, defaults to the short_name or concept_id value.
          Example: my-gedi-download

      verbose:
        type: boolean?
        default: false
        label: Verbose Logging
        doc: Enable detailed progress output.

    outputs:

      outputs_result:
        type: Directory
        doc: |
          Output directory containing downloaded data and STAC catalog.

          Directory structure:
            outputs/
            ├── catalog.json              # Root STAC catalog
            ├── {collection_id}/
            │   ├── collection.json       # STAC collection
            │   └── items/
            │       └── {item_id}.json   # STAC item per file
            └── data/
                └── *.nc / *.h5         # Downloaded granules
        outputSource: download_step/outputs_result

      stac_catalog:
        type: File
        doc: Root STAC catalog JSON file (outputs/catalog.json).
        outputSource: download_step/stac_catalog

    steps:
      download_step:
        run: "#main"
        in:
          short_name: short_name
          concept_id: concept_id
          bbox: bbox
          temporal_start: temporal_start
          temporal_end: temporal_end
          limit: limit
          collection_id: collection_id
          verbose: verbose
        out: [outputs_result, stac_catalog]

  # ============================================================================
  # COMMANDLINETOOL (Execution Step)
  # ============================================================================

  - class: CommandLineTool
    id: main
    label: Earthdata Downloader Tool

    doc: |
      Executes the Earthdata downloader inside Docker.
      Uses MAAP API for search and data retrieval.

    requirements:
      DockerRequirement:
        dockerPull: ghcr.io/maap-project/maap-data-downloaders:latest

      ResourceRequirement:
        coresMin: 2
        ramMin: 8192
        tmpdirMin: 10240
        outdirMin: 51200

      NetworkAccess:
        networkAccess: true

      EnvVarRequirement:
        envDef:
          PYTHONUNBUFFERED: "1"

    inputs:

      short_name:
        type: string?
        label: CMR Short Name
        inputBinding:
          prefix: --short-name

      concept_id:
        type: string?
        label: CMR Concept ID
        inputBinding:
          prefix: --concept-id

      bbox:
        type: string
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

      limit:
        type: int?
        default: 20
        label: Granule Limit
        inputBinding:
          prefix: --limit

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

    baseCommand: ["/app/earthdata/run_earthdata.sh"]
    successCodes: [0]
