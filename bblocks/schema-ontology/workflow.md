# Retrofit Workflow

The end-to-end process for adding a formal semantic layer to an existing schema block. Steps 1 and 2
are where retrofits most often go wrong; do not shortcut them.

---

## Step 1 — Find the import boundary

Before describing anything, determine which elements the schema block **owns** versus which it
**inherits**. Only owned elements are in scope for the new ontology.

- Read `schema.yaml` and list every `$ref`. A `bblocks://<identifier>` ref (and any resolved external
  `$ref`) pulls in another block's schema **and its semantics** — its properties are already mapped by
  that block's context and, often, already described by that block's ontology.
- Mark every property/object reachable only through an import as **inherited → out of scope**.
- Mark properties the schema itself declares as **owned → in scope**.
- When a schema *narrows* an inherited element (a stricter `const`, `enum`, `minItems`), the element is
  still inherited. Add a constraint (SHACL), do not re-describe the term.

**Why this matters:** re-describing an inherited element mints a second definition of something already
defined upstream, silently competing with it and destroying the traceable reuse the import expressed.
The import *is* the semantic statement "this element means what that block says it means."

---

## Step 2 — Inventory the owned elements

For each in-scope element, record: JSON path, JSON type, cardinality, the schema's own `description`,
and its role:

| Element kind | Becomes |
|--------------|---------|
| Object type | a **class** |
| Property with literal value | a **datatype property** |
| Property with URI/nested value | an **object property** |
| Enumeration / codelist | a **SKOS concept scheme** or `@vocab` target |
| Identifier (`id`, `href`) | JSON-LD `@id` — not a predicate |

This inventory is the worklist for sourcing (see [sourcing.md](sourcing.md)) and for the context.

---

## Step 3 — Decide reuse vs. mint (per owned element)

Driven entirely by the research in [sourcing.md](sourcing.md). Summary:

| Finding | Action |
|---------|--------|
| An exact existing term (upstream vocab) | **Reuse** its URI in the context; mint nothing. |
| A close-but-inexact term | **Mint** a local term, **align** (`rdfs:subClassOf` / `rdfs:subPropertyOf` / `skos:closeMatch`). |
| No suitable term | **Mint** a new term with a full definition and provenance. |

Reuse-first keeps the ontology small and interoperable. Note: reusing an external term is *not* the
same as re-describing an inherited block element — reuse points the schema's *own* property at a
standard predicate; that is exactly what retrofitting is for.

---

## Step 4 — Author `ontology.ttl`

For each **minted** term (reused terms need no local declaration):

- An `owl:Ontology` header: IRI, `dct:title`, `dct:description`, version, `dct:source` → the spec.
- **Classes** (`owl:Class`) for object types; **properties** (`owl:ObjectProperty` /
  `owl:DatatypeProperty`) with `rdfs:domain` and `rdfs:range`.
- For **every** term: `rdfs:label`, a definition (`skos:definition` or `rdfs:comment`),
  `rdfs:isDefinedBy` the ontology, and `dct:source` / `prov:wasDerivedFrom` → the authority.
- **Alignment axioms** to reused vocabularies where the term is a specialization.

Keep the ontology and the data honest with each other: only assert a `domain`/`range` that the context
and uplift will actually satisfy.

---

## Step 5 — Wire the JSON-LD context (the schema↔ontology binding)

The `context.jsonld` **binds this specific schema to the ontology's terms.** It is *not* part of the
ontology block — the ontology must stay schema-agnostic and reusable. The context lives either in the
schema block or in a dedicated JSON-LD mapping block; which one is a choice you offer the user in
[packaging.md](packaging.md). Author the mapping the same way wherever it lands.

Map each **owned** property name to its term URI:

- Literal → `{ "@id": "onto:prop", "@type": "xsd:..." }`
- URI-valued → `{ "@id": "onto:prop", "@type": "@id" }`
- Enumerated → `"@type": "@vocab"`
- Array → `"@container": "@set"` (or `@list` if order matters)
- Identifier → map to `@id`; assert the object's class via a `type`→`@type` mapping or a fixed `@type`
  in a nested `@context`.

**Do not** re-map inherited property names — they arrive through the assembled context built from the
`bblocks://` imports. Re-mapping risks shadowing the upstream definition. It is normal and correct for
a retrofit's source `context.jsonld` to map only a handful of properties.

**If the schema already carries a generic/default mapping** (e.g. to schema.org) and this ontology
describes the same elements more richly, you are about to **override** it — stop and warn the user, and
package the richer mapping as a dedicated override block. See [packaging.md](packaging.md).

---

## Step 6 — Add semantic uplift only where the context can't reach

If the JSON shape cannot be expressed as the intended RDF through a context alone — it needs reshaping,
class assertions the context can't add, an inverted relation, or derived triples — add
`semantic-uplift.yaml`:

- **`jq` pre-step** — reshape JSON before context embedding.
- **`sparql-construct` / `sparql-update` / `shacl` post-step** — assert `rdf:type`, invert relations,
  or derive triples so the graph uses the ontology's terms.

Prefer the context; reach for uplift only when the context genuinely cannot express the target model.
If instances are processed at runtime, these steps must run at runtime too — they are published in
`build/` for that purpose.

---

## Step 7 — Package as blocks (offer the user the choice)

The ontology (reusable) and the mapping (schema-specific) are separate concerns, and the context is
**never** placed inside the ontology block. **Default to creating a new ontology block** — do not
prompt to confirm — and only ask the user about an inline layout when the situation is genuinely
ambiguous. Wire the ontology as a dependency of whatever block holds the mapping, and use a dedicated
mapping block when a schema needs multiple mappings or an override of a generic default.

The full decision — arrangements, dependency wiring, the schema.org override warning, and run-time
Linked Data resolution / multilingual labels — is in [packaging.md](packaging.md).

---

## Step 8 — Add validating examples and SHACL shapes (default: do this)

Give the ontology block worked examples and SHACL shapes that check them, so the vocabulary is
self-testing and consumers get concrete usage. **Do this by default; only skip if the user asks to.**
Tell the user you are adding it (and that they may skip it) rather than silently omitting it.

- **Draw examples from the source/extension documentation**, not invented data — reuse the real example
  instances the upstream spec publishes, so sample values are authoritative and recognizable. Cite them.
- For an **RDF-only ontology block**, add Turtle (or JSON-LD) snippets in `examples.yaml`; these are
  validated directly against the shapes with no uplift step. For a schema block, JSON examples are
  uplifted via the context first.
- Add **SHACL shapes** (e.g. `shapes.shacl`) constraining the ontology's own properties — datatypes,
  cardinalities — and declare them with `"shaclShapes": ["shapes.shacl"]` in the block's `bblock.json`.
- Keep shapes honest with the extension: only constrain what the spec actually requires (e.g. do **not**
  force `maxCount 1` on a field the spec allows to repeat).
- If a shape references terms not expected in the instance (a background vocabulary), supply it via
  `shaclClosures`.

## Step 9 — Validate the round trip

- Run the postprocessor locally and inspect the uplifted `.ttl` / `.jsonld` under `build/tests/`.
- Confirm the RDF uses the **ontology's** URIs and asserts the intended `rdf:type`s, and that
  **inherited** elements still carry their **upstream** URIs (not new local ones).
- Run SHACL shapes; supply the ontology as background data (`shaclClosures`) if shapes reference it.
- Check ontology consistency: domains/ranges vs. actual data, no dangling or unused terms.
