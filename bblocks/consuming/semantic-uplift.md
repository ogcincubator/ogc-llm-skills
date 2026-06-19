# Semantic uplift: JSON → JSON-LD → RDF

## Why you'd do this

A block's JSON Schema describes syntax; its JSON-LD context describes meaning (which property maps to
which RDF predicate/class). "Uplift" is the process of combining a JSON document with a block's
context to get JSON-LD, then parsing that into an RDF graph — which you can then SHACL-validate,
SPARQL-query, or merge with other linked data.

## Which context to use

Each block has **two** context documents:

- **source context** (`sourceLdContext` / the block's own `context.jsonld` in its source tree) — only
  the mappings this block itself defines.
- **assembled context** (`ldContext` in the summary) — the source context merged with every imported
  block's context, transitively. **Use this one.** A JSON document conforming to the block's full
  schema will have properties from imported blocks too, which only the assembled context can map.

## The uplift steps

1. Fetch the assembled context (`ldContext` URL).
2. Wrap your JSON data with it: `{"@context": <fetched context>, **your_data}` (if your data already
   has a top-level `@context`, you need to merge rather than overwrite — check whether one is already
   present).
3. Parse the result as JSON-LD into an RDF graph (e.g. `rdflib.Graph().parse(data=..., format="json-ld")`).
4. Some blocks declare additional **pre-uplift** or **post-uplift** steps in their metadata
   (`semantic_uplift` / `semanticUplift`), of type `shacl`, `sparql-update`, `sparql-construct`, or
   `jq`. These run before/after step 3 respectively, and may be inline code or fetched from a `ref`
   URL. Skip this unless the block you're consuming actually declares such steps — most don't.

## Then validate

Once you have an RDF graph, run SHACL validation against it using the block's `shaclShapes` — see
[validation.md](validation.md#shacl-validation). A payload can pass JSON Schema validation but fail
SHACL validation (or vice versa, for SHACL constraints that JSON Schema can't express) — they check
different things and both are meaningful.

## Worked example

See [snippets/uplift_json.py](snippets/uplift_json.py) for a runnable version of steps 1–3 using
`bblocks-client-python`, and [no-library.md](no-library.md) for the equivalent without it.
