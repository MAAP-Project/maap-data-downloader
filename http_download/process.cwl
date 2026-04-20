cwlVersion: v1.2

# ==============================================================================
# MAAP HTTP Downloader - OGC Application Package
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
    id: maap-http-downloader
    label: MAAP HTTP/HTTPS Downloader

    doc: |
      Downloads files from HTTP/HTTPS URLs with optional authentication
      (Bearer token or HTTP Basic). Supports a single URL or a text file
      containing one URL per line. Includes retry logic with exponential
      backoff (3 attempts). Produces data files and a STAC metadata catalog.

    inputs:

      url:
        type: string
        label: URL or URL List File
        doc: |
          A single HTTP/HTTPS URL to download, or a path to a .txt file
          containing one URL per line (useful for batch downloads).
          Example: https://data.example.gov/file.nc
          Example: /app/input/urls.txt

      auth_type:
        type: string?
        default: "none"
        label: Authentication Type
        doc: |
          Authentication method for the HTTP request.
          Choices:
            none  - No authentication (default, for public data)
            bearer - Bearer token from MAAP secrets vault
            basic  - HTTP Basic auth from MAAP secrets vault

      token_secret:
        type: string?
        label: Token Secret Name
        doc: |
          MAAP secrets vault key holding the Bearer token.
          Only used when auth_type=bearer.

      username_secret:
        type: string?
        label: Username Secret Name
        doc: MAAP secrets vault key for HTTP Basic username.

      password_secret:
        type: string?
        label: Password Secret Name
        doc: MAAP secrets vault key for HTTP Basic password.

      collection_id:
        type: string?
        label: STAC Collection ID
        doc: |
          Identifier for the output STAC collection.
          Defaults to the hostname of the first URL if omitted.

      verbose:
        type: boolean?
        default: false
        label: Verbose Logging
        doc: Enable detailed progress output.

    outputs:

      outputs_result:
        type: Directory
        doc: |
          Output directory with downloaded files and STAC catalog.

          Directory structure:
            outputs/
            ├── catalog.json
            ├── {collection_id}/
            │   ├── collection.json
            │   └── items/
            └── data/
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
          auth_type: auth_type
          token_secret: token_secret
          username_secret: username_secret
          password_secret: password_secret
          collection_id: collection_id
          verbose: verbose
        out: [outputs_result, stac_catalog]

  # ============================================================================
  # COMMANDLINETOOL (Execution Step)
  # ============================================================================

  - class: CommandLineTool
    id: main
    label: HTTP Downloader Tool

    doc: |
      Executes the HTTP downloader inside Docker.
      Auth credentials are retrieved from the MAAP secrets vault at runtime.

    requirements:
      DockerRequirement:
        dockerPull: ghcr.io/maap-project/maap-data-downloaders:latest

      ResourceRequirement:
        coresMin: 1
        ramMin: 2048
        tmpdirMin: 5120
        outdirMin: 20480

      NetworkAccess:
        networkAccess: true

      EnvVarRequirement:
        envDef:
          PYTHONUNBUFFERED: "1"

    inputs:

      url:
        type: string
        label: URL or URL List
        inputBinding:
          prefix: --url

      auth_type:
        type: string?
        default: "none"
        label: Authentication Type
        inputBinding:
          prefix: --auth-type

      token_secret:
        type: string?
        label: Token Secret Name
        inputBinding:
          prefix: --token-secret

      username_secret:
        type: string?
        label: Username Secret Name
        inputBinding:
          prefix: --username-secret

      password_secret:
        type: string?
        label: Password Secret Name
        inputBinding:
          prefix: --password-secret

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

    baseCommand: ["/app/http_download/run_http.sh"]
    successCodes: [0]
