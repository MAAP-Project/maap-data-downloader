cwlVersion: v1.2

# ==============================================================================
# MAAP SFTP Downloader - OGC Application Package
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
    id: maap-sftp-downloader
    label: MAAP SFTP Downloader

    doc: |
      Downloads files from a remote server via SFTP (SSH File Transfer Protocol).
      Credentials are retrieved from the MAAP secrets vault.
      Produces downloaded data files and a STAC metadata catalog.

    inputs:

      host:
        type: string
        label: SFTP Hostname
        doc: |
          Hostname or IP of the SFTP server.
          Example: sftp.example-daac.org

      remote_path:
        type: string
        label: Remote Path
        doc: |
          Path to a file or directory on the remote server.
          If a directory, all non-hidden files are downloaded.
          Example: /data/science/2020/

      port:
        type: int?
        default: 22
        label: SFTP Port
        doc: "SSH port (default: 22)."

      username_secret:
        type: string?
        default: "SFTP_USERNAME"
        label: Username Secret Name
        doc: MAAP secrets vault key holding the SFTP username.

      password_secret:
        type: string?
        default: "SFTP_PASSWORD"
        label: Password Secret Name
        doc: MAAP secrets vault key holding the SFTP password.

      collection_id:
        type: string?
        label: STAC Collection ID
        doc: |
          Identifier for the output STAC collection.
          Defaults to the SFTP hostname if omitted.

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
          host: host
          remote_path: remote_path
          port: port
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
    label: SFTP Downloader Tool

    doc: |
      Executes the SFTP downloader inside Docker.
      SFTP credentials are retrieved from the MAAP secrets vault at runtime.

    requirements:
      DockerRequirement:
        dockerPull: ghcr.io/maap-project/maap-data-downloaders:latest

      ResourceRequirement:
        coresMin: 1
        ramMin: 4096
        tmpdirMin: 5120
        outdirMin: 20480

      NetworkAccess:
        networkAccess: true

      EnvVarRequirement:
        envDef:
          PYTHONUNBUFFERED: "1"

    inputs:

      host:
        type: string
        label: SFTP Hostname
        inputBinding:
          prefix: --host

      remote_path:
        type: string
        label: Remote Path
        inputBinding:
          prefix: --remote-path

      port:
        type: int?
        default: 22
        label: SFTP Port
        inputBinding:
          prefix: --port

      username_secret:
        type: string?
        default: "SFTP_USERNAME"
        label: Username Secret Name
        inputBinding:
          prefix: --username-secret

      password_secret:
        type: string?
        default: "SFTP_PASSWORD"
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

    baseCommand: ["/app/sftp/run_sftp.sh"]
    successCodes: [0]
