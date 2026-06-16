# RDF-Only Blocks

A block does not need a JSON Schema. An RDF-only block defines and validates purely RDF/ontology
content — useful for publishing ontologies, codelists, or vocabulary fragments as first-class
registered blocks.

---

## What an RDF-only block can do

- Define RDF (Turtle) examples of how to use the semantic model
- Apply SHACL shapes to validate examples
- Declare and publish an ontology
- Declare transforms and validate their outputs
- Participate in the register (discovery, imports, profiling)

---

## Ontology declaration

Declare an ontology document in `bblock.json`:

```json
{
  "ontology": "ontology.ttl"
}
```

If `ontology` is not set, the postprocessor auto-detects `ontology.ttl` or `ontology.owl` in the
block directory. The ontology is published in `build/` and included in the register entry.

---

## Semantic annotations

Two metadata fields link a block to RDF concepts and classes:

### `concept`

URIs of RDF concepts this block represents (`skos:closeMatch` in the register):

```json
{
  "concept": [
    "https://www.w3.org/ns/sosa/Observation"
  ]
}
```

### `rdfType`

URIs of RDF classes that instances of this block conform to (`rdfs:subClassOf` in the register):

```json
{
  "rdfType": [
    "https://www.w3.org/ns/sosa/Observation"
  ]
}
```

`concept` and `rdfType` can also be used in blocks that have a JSON Schema — they are not exclusive
to RDF-only blocks.

---

## Turtle examples in `examples.yaml`

RDF-only blocks use Turtle snippets in `examples.yaml`:

```yaml
examples:
  - title: Example Observation
    snippets:
      - language: turtle
        code: |
          @prefix sosa: <http://www.w3.org/ns/sosa/> .
          @prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .
          @prefix eg:   <http://example.org/obs/> .

          eg:obs1 a sosa:Observation ;
            sosa:observedProperty <http://dbpedia.org/ontology/population> ;
            sosa:hasSimpleResult "1234"^^xsd:integer .
```

Turtle and JSON-LD snippets are validated directly against SHACL shapes — no uplift step is needed.

---

## Minimal `bblock.json` for an RDF-only block

```json
{
  "name": "My Ontology Fragment",
  "abstract": "Defines terms for the observation pattern.",
  "status": "experimental",
  "dateTimeAddition": "2024-06-01T00:00:00Z",
  "itemClass": "model",
  "version": "0.1",
  "ontology": "ontology.ttl",
  "concept": ["https://example.org/vocab#ObservationPattern"],
  "shaclShapes": ["shapes.ttl"]
}
```

Note `itemClass: model` — this is the appropriate class for ontology/data model blocks.

---

## `rdfData`

For blocks that associate raw RDF data without defining it as an ontology, use the `rdfData` field:

```json
{
  "rdfData": "data/codelist.ttl"
}
```

`rdfData` is published in the register entry and `build/` output. It does not trigger the same
auto-detection logic as `ontology`.
