# Validating data against a block

## What's involved

A block's annotated schema may `$ref` other blocks' annotated schemas (see
[schema-integration.md](schema-integration.md)). A plain JSON Schema validator pointed only at the
top-level schema URL will usually fail to resolve those refs unless it can fetch arbitrary remote
URIs during validation. The core task is: **make every `$ref` the schema (transitively) contains
resolvable**, then run a standard JSON Schema validator.

Two ways to make refs resolvable:

1. **Let the validator fetch them live** — give it a retrieval callback that fetches any URI it
   doesn't already have cached. This is what `bblocks-client-python` does (see
   [python-client.md](python-client.md)).
2. **Pre-fetch and register them** — walk the schema yourself, collect every `$ref` URL, fetch each,
   and register it with the validator's schema store before validating. Useful when you want to
   validate many payloads against the same block without refetching each time, or when you need to
   work offline against a cached copy of the register.

## Minimal pattern (Python, no client library)

```python
import json
from urllib.request import urlopen
import jsonschema
from referencing import Registry, Resource

def fetch(uri):
    with urlopen(uri) as resp:
        return json.load(resp)

def retrieve(uri):
    return Resource.from_contents(fetch(uri))

schema_url = "https://ogcincubator.github.io/bblocks-examples/build/annotated/bbr/examples/feature/geojsonFeature/schema.json"
schema = fetch(schema_url)

registry = Registry(retrieve=retrieve)
validator = jsonschema.Draft202012Validator(schema, registry=registry)

errors = list(validator.iter_errors({"type": "Feature", "...": "..."}))
```

`referencing.Registry(retrieve=...)` lazily fetches any `$ref` target not already in the registry —
this is the same mechanism `bblocks-client-python`'s `validate.py` uses, just without the bblock-aware
caching layer on top.

## SHACL validation

If a block declares `shaclShapes` (dict of identifier → list of `.ttl` URLs), validating an RDF graph
against it is a separate step from JSON Schema validation and only makes sense **after** semantic
uplift (JSON → RDF) — see [semantic-uplift.md](semantic-uplift.md). Fetch and merge every shape graph
listed for the block (and, if relevant, for blocks it depends on) into one `Graph`, then run `pyshacl`
against your data graph and that shapes graph.

## Reading validation results from the register itself

Every block also publishes pre-computed test results (run by the register's own CI against its bundled
examples): `tests/report.json` / `tests/report.html` at the register root, and per-example
`*.validation_passed.txt` / `*.validation_failed.txt` files under `tests/<identifier>/`. These tell you
whether the block's *own* examples currently validate — useful as a sanity check before you build
against a block, but not a substitute for validating your own payloads.
