# JSON-LD Context

A JSON-LD context maps JSON property names to RDF predicates (URIs), enabling JSON documents
to be parsed as RDF without any changes to the JSON structure itself.

---

## Declaring a context

Place a `context.jsonld` file in the block directory. The postprocessor auto-detects it.

Alternatively, override the path or use a remote URL via `ldContext` in `bblock.json`:

```json
{ "ldContext": "https://example.org/my-context.jsonld" }
```

Or point the schema to the context file using `x-jsonld-context` in `schema.yaml`:

```yaml
x-jsonld-context: ../my-context.jsonld   # relative to schema.yaml
```

All three approaches produce the same result — the context is linked to the block and included in
the assembled output context. Using `context.jsonld` in the block directory is the simplest.

---

## Basic context structure

```json
{
  "@context": {
    "ex": "https://example.org/vocab#",
    "name": "ex:name",
    "value": {
      "@id": "ex:hasValue",
      "@type": "xsd:double"
    },
    "unit": {
      "@id": "ex:hasUnit",
      "@type": "@vocab"
    },
    "observedProperty": {
      "@id": "https://www.w3.org/ns/sosa/observedProperty",
      "@type": "@id"
    }
  }
}
```

Key JSON-LD patterns:

| Pattern | Meaning |
|---------|---------|
| `"prop": "prefix:localName"` | Maps `prop` to a predicate URI |
| `"@type": "xsd:..."` | Declares the datatype of the value |
| `"@type": "@id"` | The value is a URI (not a literal) |
| `"@type": "@vocab"` | The value is expanded as a vocabulary term |
| `"@container": "@set"` | The value is always treated as an array |
| `"@container": "@list"` | The value is an ordered list |

---

## Modularity: how contexts compose

When a block imports another block via `bblocks://` in its schema, the postprocessor automatically
assembles a combined `context.jsonld` that includes the imported block's context. This means:

- **You only need to map the properties your block adds.** Inherited properties from the imported
  block's context are already handled.
- **Property name conflicts across imported contexts must be avoided.** If two imported blocks map
  the same JSON property name to different URIs, the result is undefined.

The assembled context is written to `build/.../context.jsonld` and is the canonical context to use
when processing instances of this block.

---

## Local contexts and `@base`

For complex schemas with nested sub-schemas, use local contexts to scope property mappings:

```json
{
  "@context": {
    "ex": "https://example.org/vocab#",
    "Feature": "ex:Feature",
    "properties": {
      "@id": "ex:properties",
      "@context": {
        "name": "ex:featureName",
        "type": "ex:featureType"
      }
    }
  }
}
```

This prevents the inner `name` mapping from conflicting with a top-level `name` mapping in an
enclosing context.

---

## Mapping an identifier field to `@id`

If the schema has an identifier property (commonly `id`), map it to JSON-LD's `@id` keyword rather
than to a regular predicate:

```json
{
  "@context": {
    "id": "@id"
  }
}
```

This makes the property's value the subject IRI of the entity instead of a literal/predicate value,
which is usually what's intended — linked data entities need an IRI to be referenced from elsewhere
and to merge correctly across graphs. Map **at most one** property per object to `@id`; mapping two
is invalid JSON-LD (or ambiguous, depending on the processor) and only one can hold the entity's
identity anyway.

---

## Testing your context

Use these tools while developing:

- [JSON-LD Playground](https://json-ld.org/playground/) — paste your JSON + context and inspect the
  expanded/compacted RDF
- [SHACL Validator](https://shacl-play.sparna.fr/play/validate) — validate the uplifted Turtle output

After postprocessing, the uplifted `.jsonld` and `.ttl` files for each example and test case are
written to `build/tests/`. Inspect these to verify your context maps properties correctly.

---

**Example:** [examples/with-context/context.jsonld](../examples/with-context/context.jsonld) — maps simple scalar properties and a SPARQL-derived property to RDF predicates.

---

## Common mistakes

- **Mapping a property to the wrong type**: e.g. forgetting `"@type": "@id"` for URI-valued properties
  means the value will be treated as a string literal in RDF.
- **Shadowing imported context properties**: If an imported block maps `type` to some URI, and your
  block's context also maps `type` to a different URI, one will silently win. Use local (nested)
  contexts to scope your overrides.
- **Using `context.jsonld` for the assembled output**: The file in your source directory is the
  *source* context. The *assembled* context (which includes inherited mappings) is in `build/`. Do
  not copy the build output back into `_sources/`.
