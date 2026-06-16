# Register Configuration (`bblocks-config.yaml`)

`bblocks-config.yaml` lives at the root of a bblocks register and controls register-wide settings:
identifier prefix, imports, viewer behaviour, and SPARQL push.

Schema: [`bblocks-config.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/bblocks-config.schema.yaml)

---

## Fields

```yaml
# Human-readable name for this register (required)
name: My OGC Building Blocks Repository

# Short abstract shown in the viewer (optional, Markdown)
abstract: |
  One or two sentences. A "Tell me more" link appears if `description` is also set.

# Longer description (optional, Markdown)
description: |
  Full explanation with **Markdown** and [links](https://example.com).

# Prefix prepended to every block's path to form its identifier (required)
identifier-prefix: myorg.myproject.

# Registers to import blocks from (required; "default" = main OGC BBR)
imports:
  - default

# Generate OAS 3.0-compatible schemas in addition to the default OAS 3.1 output (optional)
schema-oas30-downcompile: false

# Viewer settings (optional)
viewer:
  show-imported-depth: 0   # 0 = local only, N = N levels deep, -1 = all

# SPARQL push (optional — see section below)
sparql:
  push:  https://example.com/gsp
  graph: https://my.bblocks.example.com/
  query: https://example.com/sparql
  resources:
    ontologies: true
```

### `identifier-prefix`

- Must end with `.`
- First component should identify your org (`ogc.`, `myorg.`)
- Appended to each block's `_sources/` directory path to form the full identifier
- **Identifiers must be stable** — changing breaks all downstream references

Example: `myorg.myproject.` + `_sources/geom/point/` → `myorg.myproject.geom.point`

### `imports`

Each entry is either:
- `"default"` — alias for the main OGC Building Blocks Register
- A URL to another register's `register.json`

Imported blocks can be referenced via `bblocks://` URIs in schemas and are available for profiling.

### `viewer.show-imported-depth`

Controls which imported blocks appear in the published viewer:
- `0` (default) — only local blocks
- `N` — local + imported up to N levels deep
- `-1` — show all imported blocks

---

## SPARQL push

When enabled, the postprocessor uploads the register's RDF output to a triplestore after each
successful build.

### `bblocks-config.yaml` settings

```yaml
sparql:
  push:  https://example.com/gsp   # SPARQL Graph Store Protocol (GSP) endpoint
  graph: https://my.bblocks.example.com/  # Named graph to upload into
                                          # Defaults to the register's base URL if omitted
  query: https://example.com/sparql # SPARQL query endpoint (informational — written to register.json)
  resources:
    ontologies: true   # Also upload ontology files (not just block metadata)
```

`push` is the only field required to enable uploading. `graph` is recommended to avoid
collisions when multiple registers share a triplestore.

### Authentication (GitHub Secrets)

The workflow passes credentials via repository secrets, not `bblocks-config.yaml` (which is
checked into version control). Add two secrets to your GitHub repository:

| Secret name | Value |
|---|---|
| `sparql_username` | Username for the triplestore |
| `sparql_password` | Password for the triplestore |

If the `gh` CLI is available, secrets can be set without leaving the terminal:

```bash
gh secret set sparql_username --body "myuser"
gh secret set sparql_password --body "mypassword"
```

In `.github/workflows/process-bblocks.yml`, pass them to the reusable workflow:

```yaml
jobs:
  validate-and-process:
    uses: opengeospatial/bblocks-postprocess/.github/workflows/validate-and-process.yml@master
    secrets:
      sparql_username: ${{ secrets.sparql_username }}
      sparql_password: ${{ secrets.sparql_password }}
```

The template ships with this already wired — you only need to add the secrets in GitHub:
**Repository → Settings → Secrets and variables → Actions → New repository secret**.

### Enabling SPARQL push in CI

SPARQL push runs automatically when both conditions are met:
1. The `sparql.push` field is set in `bblocks-config.yaml`
2. The `sparql_username` / `sparql_password` secrets are present (or the endpoint is public)

### Enabling SPARQL push locally

Pass `--enable-sparql true` to the postprocessor CLI. Credentials are read from the environment:

```bash
SPARQL_USERNAME=user SPARQL_PASSWORD=pass \
  docker run --rm --pull=always -v "$(pwd):/register" \
    ghcr.io/opengeospatial/bblocks-postprocess \
    --enable-sparql true
```
