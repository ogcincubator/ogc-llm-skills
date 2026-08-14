# Packaging: Where the Ontology and Mapping Live

The ontology (reusable vocabulary) and the JSON-LD mapping (schema-specific binding) are separate
concerns. This file covers **where each one lives**, the choice you must put to the user, how
dependencies are wired, and the override pattern for generic mappings.

---

## Default to a new block; ask only when ambiguous

**Default (do this unless there is a clear reason not to): create a new block.** The ontology becomes
its own **RDF-only ontology block**; the schema block (or a dedicated mapping block) carries the
context. The reusable ontology is then citable and versionable on its own. Do not prompt the user to
confirm this — it is the prescribed layout.

**Only ask the user when the situation is genuinely ambiguous** — e.g. the vocabulary looks like it has
no reuse value beyond this one schema, the user has signalled they want everything self-contained, or
the target block already embeds vocabulary such that a split would be disruptive. In that case, offer
the alternative:

- **Inline in the target schema block.** The ontology terms and the `context.jsonld` are authored inside
  the existing schema block. Simplest, but the ontology is then not independently reusable.

When you create a new ontology block, it **must be listed as a dependency** of whatever block contains
the JSON-LD mapping — because the mapping references the ontology's terms and cannot be resolved without
it. Declare the dependency the normal way (a `bblocks://` reference / the block's `dependsOn` /
`imports`, per `bblocks-authoring`).

---

## Where the JSON-LD context lives — two arrangements

The context that binds schema→ontology can sit in one of two places:

**A. In the schema block.** The schema block's own `context.jsonld` maps its owned properties to the
ontology's terms. The schema block depends on the ontology block. Good default when there is one
natural mapping for the schema.

**B. In a dedicated JSON-LD mapping block.** The context is packaged as its **own building block that
depends on *both* the schema block and the ontology block.** This is more than tidiness — it enables:

- **Multiple mappings for one schema** — e.g. a default mapping plus one or more alternative mappings.
- **Override of a default mapping** without touching the schema (see below).

The mapping block declares both dependencies so the postprocessor can assemble the full context and so
consumers can discover it.

```
ontology block  ────────────────┐  (reusable vocabulary; no context)
                                 ▼
schema block  ──►  JSON-LD mapping block  ──►  binds schema properties to ontology terms
   (depends on both schema + ontology)
```

---

## Override pattern — WARN the user for generic mappings

A schema is often mapped, by default, to a **generic vocabulary such as schema.org**. That gives broad
but shallow semantics (e.g. everything becomes a `schema:Thing` with `schema:name`). The retrofit's
whole point may be to **replace those generic terms with semantically richer, schema-specific ones**
grounded in the actual design of the schema.

**Explicitly warn the user when you detect this situation** — i.e. when the schema (or an imported
block) already carries a generic/default context (schema.org, a placeholder, or a coarse mapping) and
the new ontology describes the same elements more precisely. Point out that:

- The intent and effect will be to **override** the existing generic mapping.
- The correct vehicle is a **new, specific JSON-LD override block** (arrangement B), not editing the
  generic one — so the generic mapping stays intact for consumers who want it, and the richer one is a
  discoverable alternative that depends on both the schema and the new ontology.

Do not overwrite an inherited/generic context in place; add an override mapping block instead.

---

## Run-time resolution and multilingual labels

Authoring these mappings is only half the value. **When the ontology is published to a Linked Data
environment** (its term URIs resolve to RDF), the mappings can be resolved **at run-time**:

- A consumer resolves each compact property name to its term URI via the JSON-LD context, then fetches
  the term's metadata (label, definition) from the published ontology.
- Because those labels come from the ontology, they can be **multilingual** — the same data renders
  human-readable field names in whatever language the ontology provides.

The value is in the **data becoming self-describing and resolvable** — any consumer can turn a compact
property into a defined, multilingual, human-readable term by resolving it against the published
ontology. This does not depend on any particular tool. As one **illustrative** proof of concept, the
`jsonld-ui-utils` Leaflet plugin turns a GeoJSON `FeatureCollection` into a map whose popups resolve
property names/values against the ontology's labels instead of showing raw JSON keys — but that is just
a demonstration of the payoff, not a required part of the outcome. Design the ontology (rich
`rdfs:label` / `skos:prefLabel`, language tags) with this run-time resolution in mind.

- Guide: `https://ogcincubator.github.io/bblocks-docs/use/linked-data`
- Tooling / map example: `https://ogcincubator.github.io/jsonld-ui-utils/#leaflet-plugin`

---

## Choosing an arrangement — quick guide

| Situation | Arrangement |
|-----------|-------------|
| Vocabulary useful only to this one schema | Inline in schema block (option 1). |
| Reusable vocabulary, one natural mapping | Ontology block + context in schema block (option 2 / A). |
| Multiple or alternative mappings for a schema | Ontology block + dedicated mapping block(s) (option 2 / B). |
| Overriding a generic/default (e.g. schema.org) mapping with a richer one | Ontology block + **override** mapping block; warn the user (see above). |
