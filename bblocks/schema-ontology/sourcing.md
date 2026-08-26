# Sourcing Definitions

An ontology cannot be invented at the keyboard. The classes and properties that describe a schema's
elements must be **gleaned from authoritative sources**, and **existing terms must be reused in
preference to minting new ones.** Budget real time in documentation and code repositories before
writing any Turtle. This is the single most important habit for a defensible retrofit.

---

## Where definitions come from (priority order)

1. **The schema block's own artifacts.** `schema.yaml` (property names, types, `description` text,
   `$ref` / `bblocks://` imports), `bblock.json` (`abstract`, `description`, any existing `concept` /
   `rdfType`), and any existing `context.jsonld` (URIs already chosen). This is also where you draw the
   **import boundary** — anything reachable only through an import is inherited and must not be
   re-described (see [workflow.md](workflow.md) step 1).

2. **Upstream vocabularies the schema already leans on.** For example Dublin Core / DCTERMS, SKOS,
   PROV-O, GeoSPARQL, SOSA/SSN, OWL-Time, Schema.org. Fetch their **published ontology documents and
   Turtle** to reuse exact term URIs, labels, and definitions rather than paraphrasing them.

3. **The source standard / specification** the schema derives from — the authoritative human-readable
   meaning of each element, and the wording your `skos:definition` should reflect.

4. **Reference code repositories** — implementations, sibling registers, the postprocessor — to see how
   candidate terms are actually used and constrained in practice, which often disambiguates a
   definition the prose leaves vague.

Use web fetch/search and repository browsing as normal parts of this work.

---

## Reuse vs. mint — deciding per element

For every **owned** element in the inventory, resolve one of:

| Finding | Decision | Encoding |
|---------|----------|----------|
| An upstream term means exactly this | **Reuse** | Point the context at the external URI; declare nothing locally. |
| An upstream term is close but not exact | **Mint + align** | New local term with `rdfs:subClassOf` / `rdfs:subPropertyOf` / `skos:closeMatch` to the upstream term. |
| Nothing suitable exists | **Mint** | New local term with a full definition and provenance. |

**Reuse-first** yields a small, interoperable ontology. Minting is the exception and each mint should be
justified by a real gap you can name.

Reusing an external term for the schema's *own* property is legitimate and expected — it is different
from re-describing an *inherited* block element (which is never allowed). The test is ownership: does
*this* schema declare the element, or does it arrive through a `bblocks://` import?

---

## SKOS concepts: definitions and examples

When an owned element is a fixed, extension-defined enumeration (see workflow.md step 2's "Enumeration /
codelist" row), each value becomes a `skos:Concept`. Two annotations are easy to skip and both come
straight out of the sourcing work you already did — do not skip them:

- **`skos:definition`** on every concept, not just a `skos:prefLabel`. A bare label ("Cirrus") is not a
  definition; copy or tightly paraphrase the authority's own wording (a spec table cell, a README
  paragraph) the same way you would for an OWL term's `rdfs:comment`. If the source gives a bare
  enum value with no prose at all, say so rather than inventing meaning.
- **`skos:example`** wherever the source material actually shows one — a worked value from the spec's own
  example JSON/data, a named real-world instance the docs call out (an instrument, a model, a dataset).
  Do not add `skos:example` just to fill the slot: a fabricated example is worse than none. It is normal
  for some concepts in a scheme to carry one and others not to, depending on what the source actually
  offers.

Both annotations are sourced the same way as everything else in this file — never invented, always
traceable to something you read.

---

## Recording sources in `bblock.json`

The ontology block's `bblock.json` must carry a `sources` array (same shape as any schema block's, see
`bblocks-authoring`'s `metadata.md`) listing the actual documents consulted while authoring it — typically
the extension/spec's GitHub repository, the specific versioned schema document (e.g. a `schema.json` at a
pinned tag), and its README if definitions were drawn from prose rather than the schema alone:

```json
"sources": [
  { "title": "GitHub Repository", "link": "https://github.com/<org>/<extension>" },
  { "title": "JSON Schema (v2.0.0)", "link": "https://.../v2.0.0/schema.json" }
]
```

Add an entry for every distinct document you actually fetched and used — not a single generic repo link
standing in for all of them. This is what lets a future reader (human or agent) re-verify or update the
ontology against the same authority without re-discovering where the definitions came from.

---

## No fabrication

- **Never invent a URI or a definition.** A plausible-looking URI that resolves to nothing, or a
  paraphrase that drifts from the authority, is worse than an honest gap.
- If an authoritative definition cannot be found, mark the term **provisional** (e.g. a `skos:editorial
  Note`) and surface it for human review rather than guessing.
- Copy definitions faithfully and cite them with `dct:source` / `prov:wasDerivedFrom`.

---

## Pre-writing checklist

Complete all of these before authoring `ontology.ttl`:

- [ ] Import boundary drawn: every element classified **owned** or **inherited**.
- [ ] Inherited elements explicitly excluded from the worklist.
- [ ] Each owned element has an authoritative definition located (spec / docs / code).
- [ ] Each owned element checked against upstream vocabularies for an existing reusable term.
- [ ] Reuse-vs-mint decided per owned element, with each mint justified by a named gap.
- [ ] A source/provenance URI captured for every minted term.
- [ ] Every `skos:Concept` has a `skos:definition`; `skos:example` added wherever the source shows one.
- [ ] `bblock.json`'s `sources` array lists every document actually consulted (repo, versioned schema,
      README), not a single placeholder link.
