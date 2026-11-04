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

When you create a new ontology block, the block that contains the JSON-LD mapping declares
`isDescribedBy` pointing at it (per `bblocks-authoring`). The mapping references the ontology's terms
and cannot be resolved without it; `isDescribedBy` is also a dependency, so nothing else needs to be
declared (no `dependsOn` entry), apart from `imports` if the ontology block lives in another register.

---

## Where the JSON-LD context lives — two arrangements

The context that binds schema→ontology can sit in one of two places:

**A. In the schema block.** The schema block's own `context.jsonld` maps its owned properties to the
ontology's terms. The schema block declares `isDescribedBy` towards the ontology block. Good default when there is one
natural mapping for the schema.

**B. In a dedicated JSON-LD mapping block.** The context is packaged as its **own building block.**
This is more than tidiness — it enables:

- **Multiple mappings for one schema** — e.g. a default mapping plus one or more alternative mappings.
- **Override of a default mapping** without touching the schema (see below).

Give the mapping block a `schema.yaml` of its own that `allOf`/`$ref`s the target schema block
(`bblocks://<schema-block>`) — that schema composition is what makes the postprocessor assemble the
mapping block's context against the schema's own and, in the override case, win per the postprocessor's
branch-order rule. Set `isProfileOf` on the mapping block too, so the relationship is recorded in the
register for discovery. Declare `isDescribedBy` on the mapping block, pointing at the ontology block —
the ontology's terms aren't reached through the schema graph, so this link is what makes the ontology a
dependency of the mapping block.

```
schema block  ◄──allOf/$ref──  JSON-LD mapping block  ──isDescribedBy──►  ontology block
                               (binds schema properties                   (reusable vocabulary;
                                to ontology terms)                         no context)
```

---

## One ontology, many schemas

The same model is often encoded by several different schemas. Keep **one ontology block** for it and let
every schema point at it, instead of copying the vocabulary into each schema block:

- Each schema (arrangement A) or its mapping block (arrangement B) declares `isDescribedBy` towards the
  same ontology block, and has its **own** `context.jsonld` binding that schema's properties to the
  ontology's terms. Property names can differ between schemas; they bind to the same terms.
- The ontology block becomes the hub for the model: every schema that describes it is listed against it
  (the viewer shows them as the blocks it "describes"), terms are defined once, and data in any of the
  schemas uplifts to the same classes and properties.
- A schema's binding to the ontology can be **overridden**: add an override mapping block for that schema
  (arrangement B) that re-maps its properties, leaving the original binding available to consumers
  who want it. The warning and procedure are in the next section.

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
- The correct vehicle is a **new, specific JSON-LD override block** (arrangement B) whose own
  `schema.yaml` `allOf`/`$ref`s the target schema — not editing the generic mapping in place — so the
  generic mapping stays intact for consumers who want it, and the richer one is a discoverable
  alternative that composes the schema and re-maps its properties to the new ontology.

Do not overwrite an inherited/generic context in place; add an override mapping block instead, wired as
described above.

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
| Several schemas encode the same model | One ontology block; each schema (or its mapping block) declares `isDescribedBy` towards it. |
| Overriding a generic/default (e.g. schema.org) mapping, or a schema's existing binding, with a richer one | Ontology block + **override** mapping block; warn the user (see above). |
