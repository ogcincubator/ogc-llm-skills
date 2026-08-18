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

## No fabrication

- **Never invent a URI or a definition.** A plausible-looking URI that resolves to nothing, or a
  paraphrase that drifts from the authority, is worse than an honest gap.
- If an authoritative definition cannot be found, mark the term **provisional** (e.g. a
  `skos:editorialNote`) and surface it for human review rather than guessing.
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
