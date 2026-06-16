---
name: bblocks-authoring
description: "Reference skill for authoring OGC Blocks (bblocks): source file structure, metadata (bblock.json), JSON Schema, examples, tests, JSON-LD contexts, SHACL shapes, semantic uplift, transforms, validation, and register publishing. Use when working with bblock.json, schema.yaml, examples.yaml, bblocks-postprocess, or any OGC Building Blocks register."
---

# OGC Blocks — Authoring Skill

This skill covers how to **author OGC Blocks** (bblocks): how to write, structure, and test the source
files that the postprocessor turns into reusable, machine-readable specification components.

Official branding is **OGC Blocks**. The legacy name is *OGC Building Blocks*. `bblocks` is the
code-level identifier used in file names, identifiers, and tooling.

---

## What is an OGC Block?

An OGC Block is a reusable specification component packaged as a directory of source files. Each block
combines some or all of:

- a **JSON Schema** (the data model)
- a **JSON-LD context** (semantic annotations mapping JSON properties to RDF predicates)
- **SHACL shapes** (RDF graph constraints)
- **examples** with inline or file-referenced snippets
- **test resources** (additional files for automated validation)
- **transforms** (reusable conversion scripts)
- **metadata** (`bblock.json`)

The postprocessor reads these sources and produces:

- annotated schemas with semantic properties inlined
- assembled JSON-LD contexts
- generated HTML documentation
- validation reports
- a `register.json` index

A **register** is a collection of blocks published from a single repository.

---

## Key concepts

| Term | Meaning |
|------|---------|
| **register** | A published collection of blocks from one repo, indexed in `register.json` |
| **identifier** | Globally unique dot-separated string, e.g. `ogc.geo.features.feature` |
| **identifier prefix** | Per-repo string from `bblocks-config.yaml`; concatenated with the block's directory path to form its identifier |
| **annotated schema** | The postprocessor output schema: source schema + inherited `x-jsonld-*` annotations resolved |
| **assembled context** | The merged JSON-LD context built from a block's own context plus all imported blocks' contexts |
| **profile** | A block that specialises another via stricter constraints (see [Imports & Profiles](imports-profiles.md)) |
| **extension point** | A mechanism to substitute referenced blocks inside a base block's schema (see [Extension Points](extension-points.md)) |

---

## Skill map

Start here and follow links for the topic you need:

| File | What questions it answers |
|------|--------------------------|
| [quickstart.md](quickstart.md) | How do I create a new bblocks repo and author my first block? |
| [structure.md](structure.md) | What files go where? How are identifiers constructed? |
| [metadata.md](metadata.md) | What fields does `bblock.json` accept? Which are required? |
| [schema.md](schema.md) | How do I write or reference a JSON Schema for a block? How do I annotate it semantically? |
| [examples.md](examples.md) | How do I write examples? How do they feed into docs and validation? |
| [tests.md](tests.md) | How do I add test resources? What is `tests.yaml`? What are negative tests? |
| [semantic/index.md](semantic/index.md) | JSON-LD contexts, SHACL shapes, semantic uplift — overview and navigation |
| [transforms.md](transforms.md) | How do I declare transforms? What built-in types are available? |
| [transform-plugins.md](transform-plugins.md) | How do I add a custom transform type via a plugin? |
| [validation.md](validation.md) | How does validation work? How do I interpret errors? |
| [validation-plugins.md](validation-plugins.md) | How do I add a custom validator? |
| [imports-profiles.md](imports-profiles.md) | How do I import another register? How do I profile a block? |
| [extension-points.md](extension-points.md) | How do I specialize a block's referenced components? |
| [rdf-only.md](rdf-only.md) | How do I define a block with no JSON Schema — only RDF/ontology content? |
| [outputs.md](outputs.md) | What does the postprocessor produce, and where? |

---

## Schemas (authoritative)

All configuration file schemas live at:

```
https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/
```

| File | Schema |
|------|--------|
| `bblock.json` | [`bblock.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/bblock.schema.yaml) |
| `examples.yaml` | [`examples.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/examples.schema.yaml) |
| `tests.yaml` | [`tests.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/tests.schema.yaml) |
| `transforms.yaml` | [`transforms.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/transforms.schema.yaml) |
| `bblocks-config.yaml` | [`bblocks-config.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/bblocks-config.schema.yaml) |
| `semantic-uplift.yaml` | [`semantic-uplift.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/semantic-uplift.schema.yaml) |
| `transform-plugins.yml` (deprecated) | [`transform-plugins.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/transform-plugins.schema.yaml) |

---

## Example repository

[ogcincubator/bblocks-examples](https://github.com/ogcincubator/bblocks-examples) is the canonical
example register. Its `_sources/` tree is organized by pattern:

| Directory | What it demonstrates |
|-----------|---------------------|
| `feature/` | Schema-only blocks (GeoJSON feature, override context) |
| `semantic-uplift/` | Pre- and post-uplift steps |
| `transforms/` | Transform declarations and reuse |
| `rules/` | SHACL rules |
| `validators/` | Validator plugin integration |
| `observation/` | Blocks importing SOSA/OGC-API blocks |

Concrete snippets from this repo are copied into [examples/](examples/) alongside this skill.
See [examples/index.md](examples/index.md) for the full index with what each example demonstrates.