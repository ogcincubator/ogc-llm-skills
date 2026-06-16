# Block Metadata (`bblock.json`)

Schema:
[`bblock.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/bblock.schema.yaml)

---

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | User-friendly display name. |
| `abstract` | string | Short summary shown in the register. Markdown allowed. |
| `status` | string | Lifecycle status — see [Status values](#status-values) below. |
| `dateTimeAddition` | string | ISO 8601 date-time when the block was first added (e.g. `2024-06-01T00:00:00Z`). |
| `itemClass` | string | Type of block — see [Item classes](#item-classes) below. |
| `version` | string | Version string (e.g. `0.1`, `1.0.0`). |

**Never set `itemIdentifier` manually** — it is auto-generated from the register prefix and directory path.

---

## Status values

| Value | Meaning |
|-------|---------|
| `under-development` | Work in progress, not yet stable |
| `experimental` | Stable enough for testing, may still change |
| `stable` | Production-ready |
| `superseded` | Replaced by a newer block (see `successor`) |
| `retired` | No longer in use |
| `invalid` | Found to be incorrect |
| `reserved` | Slot reserved, block not yet authored |
| `submitted` | Submitted for review |

---

## Item classes

| Value | Description |
|-------|-------------|
| `schema` | JSON Schema object type or feature type |
| `datatype` | Simple JSON Schema data type |
| `path` | OpenAPI path |
| `parameter` | OpenAPI parameter |
| `header` | OpenAPI header |
| `cookie` | OpenAPI cookie |
| `response` | OpenAPI response |
| `api` | Partial or full OpenAPI document |
| `model` | Ontology or data model |
| `requirements-class` | ModSpec requirements class (standard authoring) |
| `clause` | Prose-only clause (scope, conventions, informative annex) |
| `terms` | Terms and definitions clause |
| `references` | Normative/informative references clause |

> The allowed values are defined in `bblock.schema.yaml` and may grow over time. Check the schema
> if a value you expect is not listed here.

---

## Optional fields by category

### Identity and discovery

| Field | Description |
|-------|-------------|
| `dateOfLastChange` | ISO 8601 date of last change. Auto-detected from git; falls back to `dateTimeAddition`. |
| `tags` | Array of free-text strings for categorization. |
| `group` | Short string to visually group related blocks in the register viewer. |
| `highlighted` | Boolean — marks this block as featured on the register homepage. |
| `sources` | Array of `{ title, link }` objects listing specs or papers this block is based on. |
| `link` | Single URL to external documentation. |
| `links` | Array of `{ title, href, rel?, notes? }` objects for richer link sets. |

### Lifecycle and relationships

> **Cross-block references:** fields that reference other blocks (`isProfileOf`, `dependsOn`,
> `predecessor`, `successor`, `seeAlso`) accept either a `bblocks://` URI (e.g.
> `bblocks://ogc.geo.features.feature`) or a bare identifier (e.g. `ogc.geo.features.feature`).
> **Prefer `bblocks://` URIs** — they are consistent with schema `$ref` usage and make it
> unambiguous that the value is a block reference rather than a free-text string.

| Field | Description |
|-------|-------------|
| `predecessor` | `bblocks://` URI or bare identifier of the block this one supersedes; full URI for external resources. |
| `successor` | `bblocks://` URI or bare identifier of the block that supersedes this one; full URI for external resources. |
| `dependsOn` | Array of `bblocks://` URIs (or bare identifiers) for blocks this one has a runtime dependency on (distinct from `isProfileOf`). |
| `seeAlso` | Array of `bblocks://` URIs or bare identifiers for related blocks, or full URIs for external resources. |
| `isProfileOf` | `bblocks://` URI(s) (or bare identifier(s)) of the block(s) this one profiles — a stricter, backward-compatible specialization. See [imports-profiles.md](imports-profiles.md). |

### Schema and API artifacts

| Field | Description |
|-------|-------------|
| `schema` | URL to the JSON Schema. Auto-derived when `schema.yaml` or `schema.json` is present. |
| `openAPIDocument` | URL or path to an OpenAPI document. |
| `ldContext` | URL to the JSON-LD context. Auto-derived when `context.jsonld` is present. See [semantic/context.md](semantic/context.md). |
| `extends` | Schema inheritance from another block. See [extension-points.md](extension-points.md). |
| `extensionPoints` | Substitution mappings for referenced blocks. See [extension-points.md](extension-points.md). |

### Validation

| Field | Description |
|-------|-------------|
| `shaclShapes` | Array of SHACL shape files (paths or URLs). `shapes.ttl` in the block directory is auto-detected. `shaclRules` is a deprecated alias — treat as `shaclShapes`. |
| `shaclClosures` | Array of RDF files or URLs merged into every test snippet as a SHACL closure. See [semantic/shacl.md](semantic/shacl.md). |
| `requirementClasses` | Array of ModSpec requirement class URIs for validation. |
| `conformanceClasses` | Array of ModSpec conformance class URIs this block refers to. |

### Semantic / RDF

| Field | Description |
|-------|-------------|
| `ontology` | Path or URL to an RDF ontology file. `ontology.ttl` or `ontology.owl` are auto-detected. See [rdf-only.md](rdf-only.md). |
| `concept` | Array of URIs for RDF concepts this block represents (`skos:closeMatch`). |
| `rdfType` | Array of URIs for RDF classes that instances conform to (`rdfs:subClassOf`). |

### External resources

| Field | Description |
|-------|-------------|
| `resources` | Array of external artifacts (data files, vocabularies, XSD schemas…). Each entry has `ref` (URL or relative path), `format`, and optionally `role` and `conformsTo`. Use `role: validation` to expose resources to validator plugins via `meta.context.validation_resources`; use `role: data` for associated RDF data files (replaces the deprecated `rdfData` field). |
| `rdfData` | **Deprecated.** Use `resources` with `role: data` instead. May appear in older repositories. |

---

## Minimal `bblock.json`

```json
{
  "name": "My Block",
  "abstract": "A one-sentence description.",
  "status": "under-development",
  "dateTimeAddition": "2024-06-01T00:00:00Z",
  "itemClass": "schema",
  "version": "0.1"
}
```

## Example with common optional fields

```json
{
  "name": "GeoJSON Feature",
  "abstract": "A GeoJSON Feature with semantic uplift.",
  "status": "stable",
  "dateTimeAddition": "2023-01-01T00:00:00Z",
  "itemClass": "schema",
  "version": "1.0",
  "tags": ["geojson", "feature"],
  "sources": [
    { "title": "GeoJSON (RFC 7946)", "link": "https://www.rfc-editor.org/rfc/rfc7946" }
  ],
  "isProfileOf": "bblocks://ogc.geo.json-fg.feature",
  "shaclShapes": ["shapes.ttl"],
  "shaclClosures": ["vocabs/my-codelist.ttl"],
  "concept": ["https://www.opengis.net/def/metamodel/ogc-na/Feature"],
  "rdfType": ["http://www.w3.org/ns/sosa/Sample"]
}
```
