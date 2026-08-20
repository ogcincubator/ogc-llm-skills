---
name: bblocks-schema-ontology
description: "Workflow for retrofitting formal semantics to an existing schema OGC Block: author a reusable ontology block that describes the schema's own elements, and bind it to the schema with a JSON-LD context that lives in the schema block or in a dedicated JSON-LD mapping block (dependent on both schema and ontology) — never inside the reusable ontology block. Supports overriding default or generic mappings (e.g. schema.org) with semantically richer, schema-specific ones via an override mapping block. Respects schema import dependencies: never redefines elements inherited from other blocks. Use when adding RDF/vocabulary meaning to a schema written without it, when mapping JSON properties to defined predicates, or when semantic uplift must yield a well-formed, validatable RDF model. Note: publishing the ontology to a Linked Data environment lets these mappings resolve at run-time, including multilingual labels."
---

# Retrofitting Formal Semantics to a Schema Block

This skill covers how to give an **existing schema OGC Block** a formal semantic layer: a **reusable
ontology block** that defines classes and properties for the schema's *own* elements, plus a **JSON-LD
context** and optional **semantic uplift** that make instances parse into RDF using those terms.

The base `bblocks-authoring` skill (named here in plain text — install it separately if you need it)
documents the mechanics of each individual file: `ontology.ttl` declaration and `itemClass: model`,
`context.jsonld`, `semantic-uplift.yaml`, `x-jsonld-*` annotations, and SHACL. This skill supplies the
**end-to-end workflow, the block arrangement, and the judgement calls** that mechanical file docs do
not.

## Scope

**In scope:** retrofitting semantics to a schema that already exists and was written without formal RDF
meaning — the common case where the JSON model came first and the vocabulary is added afterward.

**Out of scope:** greenfield co-development, where an ontology and schema are authored together in one
place from the start. That is a valid but different pattern; it does not carry the retrofit constraints
below (chiefly, respecting a pre-existing import graph).

## Three block roles — keep them separate

A retrofit involves up to three distinct roles. Conflation should only occur when the source material already addresses multiple aspects.

| Role | What it is | Reusability |
|------|-----------|-------------|
| **Schema block** | The JSON data model (the retrofit target). | Bound to its serialization. |
| **Ontology block** | Reusable vocabulary — classes/properties describing elements. **Contains no JSON-LD context.** | Reusable across many schemas. |
| **JSON-LD mapping** | The `context.jsonld` that **binds one schema to one ontology**. Lives in the schema block *or* in a dedicated mapping block that depends on **both**. | Specific to a schema+ontology pair. |

**The JSON-LD context is never part of the ontology block.** A context binds a *specific* schema to the
ontology; the ontology itself must stay schema-agnostic so other schemas can reuse it. **Default to a
new, separate ontology block** (do not prompt to confirm); only ask the user about an inline layout when
the situation is genuinely ambiguous. Where the context then lives — schema block or its own mapping
block — is covered in [packaging.md](packaging.md).

## Where this sits — one relationship among several

The outputs of this skill are themselves **interoperability resources**: the ontology is a reusable
*data model / vocabulary*, and the JSON-LD mapping is a *schema→model relationship*. They are
design-time, FAIR, federatable artefacts — meant to be discovered and reused, not accessed as high-load
runtime services (see the bblocks-docs "AI-enabled federation" design note,
`https://ogcincubator.github.io/bblocks-docs/`).

This skill covers only the **schema-model** relationship. Sibling relationship types — **term-term**
(vocabulary crosswalks), **schema-schema** (syntactic/structural transforms), and **model-model**
(ontology alignment) — are **out of scope here** and are candidates for their own focused skills. Keep
this skill sharp rather than folding those in.

## Two governing principles

1. **Authoring an ontology is a research task, not a keyboard task.** Definitions must be gleaned from
   authoritative sources, existing terms **reused** in preference to minting new ones, and a URI or
   definition is **never fabricated**. See [sourcing.md](sourcing.md).

2. **Describe only the schema's *own* elements — never inherited ones.** A schema imports other blocks
   via `bblocks://` `$ref`s that carry their own semantics; re-describing an inherited element breaks
   the intended, traceable reuse. Find the import boundary first and stay inside it. See
   [workflow.md](workflow.md) step 1.

## Navigation

| File | Read it when you need to… |
|------|---------------------------|
| [workflow.md](workflow.md) | Follow the retrofit end to end: import boundary, own-element inventory, reuse-vs-mint, author `ontology.ttl`, wire the context, add uplift only where the context can't reach, validate the round trip. |
| [packaging.md](packaging.md) | Decide where the ontology and mapping live: offer the user the inline-vs-new-block dialog, wire dependencies, use a standalone JSON-LD mapping block to **override** default/generic (e.g. schema.org) mappings, and understand run-time Linked Data resolution. |
| [sourcing.md](sourcing.md) | Do the research that must precede any Turtle: where authoritative definitions come from, reuse vs. mint per element, the pre-writing checklist. |
| [example.md](example.md) | See one schema element retrofitted end to end, alongside an inherited element correctly left untouched. |

## References

- OGC Blocks & Linked Data guide: `https://ogcincubator.github.io/bblocks-docs/use/linked-data`
- Runtime consumption tooling (`jsonld-ui-utils`): `https://ogcincubator.github.io/jsonld-ui-utils/` —
  its Leaflet map plugin is only an **illustrative proof of concept** of the payoff (resolving ontology
  labels at run-time); the value of the mappings does not depend on it.
- Config-file schemas (authoritative):
  `https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/`
