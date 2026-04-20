cwlVersion: v1.2

# ==============================================================================
# MAAP NASA DAAC Downloader - OGC Application Package
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
    id: maap-nasa-daac-downloader
    label: MAAP NASA DAAC Downloader

    doc: |
      Downloads granules from any NASA DAAC using earthaccess (CMR search).
      Authentication is handled via MAAP secrets vault (EARTHDATA_USERNAME /
      EARTHDATA_PASSWORD). Produces data files and a STAC metadata catalog.

      Inputs: CMR concept_id + bounding box + optional temporal range.
      Outputs: data files in outputs/data/ + STAC catalog at outputs/catalog.json.

    inputs:

      concept_id:
        type: string
        label: CMR Concept ID
        doc: |
          NASA CMR concept ID identifying the dataset collection.
          Example: C2036882064-GES_DISC (MERRA-2), C2036882063-GES_DISC (GPM)
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

      collection_id:
        type: string?
        label: STAC Collection ID
        doc: |
          Identifier for the output STAC collection.
          If omitted, defaults to the concept_id value.
          Example: my-merra2-download

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
          concept_id: concept_id
          bbox: bbox
          temporal_start: temporal_start
          temporal_end: temporal_end
          collection_id: collection_id
          verbose: verbose
        out: [outputs_result, stac_catalog]

  # ============================================================================
  # COMMANDLINETOOL (Execution Step)
  # ============================================================================

  - class: CommandLineTool
    id: main
    label: NASA DAAC Downloader Tool

    doc: |
      Executes the NASA DAAC downloader inside Docker.
      Credentials are retrieved from MAAP secrets vault at runtime.

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

      concept_id:
        type: string
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

    baseCommand: ["/app/nasa_daac/run_nasa_daac.sh"]
    successCodes: [0]
