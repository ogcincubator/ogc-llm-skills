# Quickstart — Authoring Your First OGC Block

This is a step-by-step, opinionated guide for creating a new bblocks register and authoring your first block.
For reference documentation see [structure.md](structure.md), [metadata.md](metadata.md), etc.

---

## 1. Create a new register repository

1. Go to [github.com/opengeospatial/bblock-template](https://github.com/opengeospatial/bblock-template)
   and click **Use this template** (not Fork).
2. Name your repository and create it under your account or org.
3. Enable GitHub Pages: **Settings → Pages → Source → GitHub Actions**.

---

## 2. Configure the register

Edit `bblocks-config.yaml`:

```yaml
name: My Blocks Register
identifier-prefix: myorg.myproject.
imports:
  - default   # imports the main OGC Building Blocks register
```

**Identifier prefix rules:**
- The first component should identify your org (e.g. `ogc.`, `myorg.`).
- Subsequent components scope the collection (e.g. `apis.myapi.v1.`).
- It must end with a `.`.
- The directory path inside `_sources/` is appended automatically to form the full block identifier.
- **Identifiers must be stable** — changing them breaks all downstream references.

Example: prefix `myorg.myproject.` + directory `_sources/geom/point/bblock.json`
→ identifier `myorg.myproject.geom.point`

---

## 3. Create a block directory

Inside `_sources/`, create a directory for your block. Its path becomes part of the identifier:

```
_sources/
  geom/
    point/
      bblock.json
      schema.yaml
      examples.yaml
```

---

## 4. Write the metadata (`bblock.json`)

```json
{
  "name": "Point Geometry",
  "abstract": "A simple 2D or 3D point geometry in GeoJSON format.",
  "status": "under-development",
  "dateTimeAddition": "2024-06-01T00:00:00Z",
  "itemClass": "schema",
  "version": "0.1"
}
```

Required fields: `name`, `abstract`, `status`, `dateTimeAddition`, `itemClass`, `version`.
See [metadata.md](metadata.md) for the full field reference.

---

## 5. Write the schema (`schema.yaml`)

```yaml
"$schema": https://json-schema.org/draft/2020-12/schema
title: Point
type: object
required:
  - type
  - coordinates
properties:
  type:
    type: string
    enum: [Point]
  coordinates:
    type: array
    minItems: 2
    maxItems: 3
    items:
      type: number
```

See [schema.md](schema.md) for how to reference other blocks with `bblocks://` URIs and add semantic
annotations with `x-jsonld-*` properties.

---

## 6. Add examples (`examples.yaml`)

```yaml
examples:
  - title: A 2D point
    content: A simple longitude/latitude point.
    snippets:
      - language: json
        code: |
          {
            "type": "Point",
            "coordinates": [125.6, 10.1]
          }
  - title: A 3D point
    snippets:
      - language: json
        ref: examples/point-3d.json
```

Examples are included in generated documentation and automatically validated against the schema.
See [examples.md](examples.md) for the full format.

---

## 7. Test locally

```bash
docker run --pull=always --rm --workdir /workspace \
  -v "$(pwd):/workspace" \
  ghcr.io/opengeospatial/bblocks-postprocess \
  --clean true --base-url http://localhost:9090/register/
```

Outputs go to `build/` (or `build-local/` — see [outputs.md](outputs.md)).

To preview in the viewer:

```bash
docker run --rm --pull=always -v "$(pwd):/register" -p 9090:9090 \
  ghcr.io/ogcincubator/bblocks-viewer
```

Use `--log-level DEBUG` on the postprocessor for verbose output when debugging.

---

## 8. Commit and push

The GitHub Actions workflow in the template will run automatically on push, post-process all blocks,
and deploy the output to GitHub Pages.

---

## Next steps

- Add a JSON-LD context to enable semantic interoperability → [semantic/context.md](semantic/context.md)
- Add SHACL shapes for RDF validation → [semantic/shacl.md](semantic/shacl.md)
- Import and reference other blocks → [imports-profiles.md](imports-profiles.md)
- Add transforms → [transforms.md](transforms.md)
