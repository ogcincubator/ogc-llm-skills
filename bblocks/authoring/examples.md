# Examples (`examples.yaml`)

Schema:
[`examples.schema.yaml`](https://raw.githubusercontent.com/opengeospatial/bblocks-postprocess/master/ogc/bblocks/schemas/examples.schema.yaml)

Examples serve two purposes: they appear in generated documentation, and they are automatically
validated against the block's schema, JSON-LD context, and SHACL shapes.

---

## Basic structure

```yaml
examples:
  - title: My first example
    content: |
      A Markdown description of this example. Relative links and images
      are resolved to full URLs when the block is published.
    snippets:
      - language: json
        code: |
          { "type": "Point", "coordinates": [125.6, 10.1] }
```

Each example has:
- `title` (optional but recommended)
- `content` (optional Markdown description)
- `snippets` — one or more code snippets, each with a `language` and either `code` or `ref`

---

## Referencing external files

Instead of inline `code`, use `ref` to point to a file relative to `examples.yaml`:

```yaml
snippets:
  - language: json
    ref: examples/my-feature.json
```

### Extracting part of a file with `json-path`

Use a JSONPath expression to extract a specific value from a JSON or YAML file:

```yaml
snippets:
  - language: json
    ref: my-collection.json
    json-path: $.features[0]
```

The first match is used. If the expression matches nothing, the snippet is skipped with a warning.

---

## Multiple snippets per example

A single example can have snippets in multiple languages or formats — useful when showing the same
data as JSON and Turtle, or JSON and its JSON-LD uplift result:

```yaml
examples:
  - title: Observation in JSON and Turtle
    snippets:
      - language: json
        code: |
          { "observedProperty": "ex:temperature", "result": 22.5 }
      - language: turtle
        code: |
          ex:obs1 sosa:observedProperty ex:temperature ;
                  sosa:hasSimpleResult 22.5 .
```

---

## Prefixes

Declare RDF prefixes to avoid repeating them in Turtle and JSON-LD snippets. Prefixes are used
during semantic uplift but do **not** need to appear in the `@context` — the uplift process
expands them automatically.

```yaml
prefixes:
  # Register-level defaults for all examples
  sosa: http://www.w3.org/ns/sosa/
  xsd: http://www.w3.org/2001/XMLSchema#

examples:
  - title: Example with extra prefixes
    prefixes:
      ex: http://example.org/data/
    snippets:
      - language: turtle
        code: |
          ex:obs1 a sosa:Observation .
```

Prefixes can be declared at the top level (apply to all examples) or inside a specific example
(apply to that example only, merged with top-level prefixes).

---

## Validation behavior

Each JSON snippet is:
1. Validated against the block's JSON Schema (if present)
2. Semantically uplifted by embedding the block's `context.jsonld` (if present), producing `.jsonld` and `.ttl` outputs
3. Validated against SHACL shapes (if defined)

JSON-LD and Turtle snippets skip step 2 (they are already in RDF format) and go directly to SHACL validation.

Snippet outputs are written to `build/tests/` alongside the regular test outputs.

---

## Minimal `examples.yaml`

```yaml
examples:
  - title: Basic example
    snippets:
      - language: json
        code: |
          {
            "type": "Feature",
            "geometry": { "type": "Point", "coordinates": [0, 0] },
            "properties": {}
          }
```
