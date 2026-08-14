# Worked Example

One owned element retrofitted end to end, and one inherited element correctly left untouched. All
minted URIs use `http://example.org/` and are **illustrative** — they are not authoritative terms.

Setting: a schema block `myreg.catalog.record` describes a catalogue record. Its `schema.yaml` looks
like this (abbreviated):

```yaml
allOf:
  - $ref: bblocks://ogc.geo.common.feature   # imported base
type: object
properties:
  title:
    type: string
    description: Human-readable name of the record.
  keywords:
    type: array
    items: { type: string }
    description: Free-text tags describing the record's subject.
  geometry: {}   # constrained here, but defined by the imported feature block
```

---

## Step 1 — Import boundary

- `title` — declared here → **owned, in scope**.
- `keywords` — declared here → **owned, in scope**.
- `geometry` — reachable through `bblocks://ogc.geo.common.feature` → **inherited, out of scope.**
  The schema only narrows it; the meaning of "geometry" belongs to the imported block.

So the worklist is `{ title, keywords }`. `geometry` is deliberately excluded.

---

## Step 2–3 — Source and decide, per owned element

**`title`.** Research (see sourcing.md): the source spec says "a human-readable name." Dublin Core
Terms already defines exactly this: `dct:title` ("A name given to the resource"). → **Reuse.** Mint
nothing.

**`keywords`.** The spec says "free-text subject tags." `dct:subject` is close but its range is a
concept/resource, whereas these values are plain strings — not an exact fit. → **Mint + align**: a
local `ex:keyword` datatype property, aligned with `skos:closeMatch dct:subject`.

---

## Step 4 — `ontology.ttl` (minted terms only)

```turtle
@prefix ex:   <http://example.org/catalog/> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dct:  <http://purl.org/dc/terms/> .
@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .

ex: a owl:Ontology ;
  dct:title "Catalog Record Vocabulary (illustrative)" ;
  dct:source <https://example.org/spec/catalog-record> .

ex:keyword a owl:DatatypeProperty ;
  rdfs:label "keyword" ;
  skos:definition "A free-text tag describing the record's subject." ;
  rdfs:range xsd:string ;
  rdfs:isDefinedBy ex: ;
  dct:source <https://example.org/spec/catalog-record#keywords> ;
  skos:closeMatch dct:subject .
```

Note there is **no** `ex:title` — `title` reused `dct:title`, so nothing is declared for it. And there
is **no** term for `geometry` — it is inherited.

---

## Step 5 — `context.jsonld` (owned properties only)

```json
{
  "@context": {
    "dct": "http://purl.org/dc/terms/",
    "ex":  "http://example.org/catalog/",
    "title":    "dct:title",
    "keywords": { "@id": "ex:keyword", "@container": "@set" }
  }
}
```

`geometry` is **absent** — its mapping arrives through the assembled context of the imported feature
block. Re-mapping it here would risk shadowing the upstream definition.

---

## Step 6 — Uplift?

Not needed here: both owned properties map cleanly through the context. If, say, `keywords` had been a
single comma-joined string in legacy data, a `jq` pre-step would split it into an array before context
embedding — but that is not the case in this schema.

---

## Result — uplifted RDF (sketch)

```turtle
<record/1> a <.../Feature> ;           # rdf:type from the imported block
  dct:title "Flood extent 2026" ;      # reused upstream term
  ex:keyword "flood", "hydrology" ;    # minted, aligned local term
  <.../geometry> [ … ] .               # predicate from the imported block, untouched
```

The record carries an **upstream** type and geometry predicate (traceable reuse preserved), a **reused**
`dct:title`, and a **minted** `ex:keyword` — exactly the three outcomes the workflow produces.

---

## Variant — an override mapping block

Suppose `myreg.catalog.record` already ships a generic default context mapping `title` and `keywords`
to `schema.org` (`schema:name`, `schema:keywords`). The retrofit above produces *richer* terms
(`dct:title`, `ex:keyword`) for the same properties — so it **overrides** the generic mapping.

Per packaging.md, do not overwrite the schema.org context. Instead:

1. Keep the ontology as its own reusable block.
2. Package the richer `context.jsonld` above as a **new JSON-LD mapping block**, `myreg.catalog.record.
   rich-ld`, that declares dependencies on **both** the schema block and the ontology block.
3. Warn the user that this override replaces the generic semantics for consumers who select it, while
   the schema.org mapping remains available as the default.

Once the ontology is published to a Linked Data environment, a consumer selecting the override mapping
can resolve `ex:keyword` at run-time to its `rdfs:label` (in any language the ontology provides) — e.g.
rendering "Keyword" / "Mot-clé" in a map popup instead of the raw JSON key.
