# Ontology Authoring skill — planning / laundry list

**Working file. Delete before the skill is published** (`build_site.py` zips every file in the
skill directory, so this would ship inside `ontology-authoring.zip`).

## Purpose of this document

Enumerate everything the skill should cover, so we can prune, reorder, and fill gaps before
drafting `SKILL.md` and its sub-files. Items marked **PENDING** need a decision from you.

---

## 0. Framing

The audience is **an LLM that has been asked to write or edit an ontology / controlled vocabulary**
— typically producing a Turtle file from a spreadsheet, a spec document, a UML model, or a
conversation. The skill must therefore be *prescriptive*, not descriptive: "use this predicate",
"this is mandatory", "never do this", with copy-adaptable snippets. It is not a tutorial on
description logics, and not a documentation of the OGC publication pipeline.

The failure modes we're writing against (what an unguided LLM does today):

- Invents `ex:hasName`-style predicates instead of reusing `skos:prefLabel` / `rdfs:label`.
- Uses `rdfs:comment` for everything, so definitions can't be told apart from editorial notes.
- Reaches for `schema.org` because it recognizes it, producing a junk-drawer model.
- Emits a bag of `skos:Concept`s with no `skos:ConceptScheme`, no `inScheme`, no top concepts.
- Writes both `broader` and `narrower` by hand and gets them inconsistent.
- Overuses `rdfs:domain` / `rdfs:range` as if they were constraints.
- Makes up URIs with no namespace policy, inconsistent casing, and no `rdfs:isDefinedBy`.
- Produces no ontology-level metadata at all (no title, license, version, dates).
- Writes definitions that just restate the label ("Catchment: a catchment").

Every section below should be judged by: *does it stop one of these, or enable a correct choice?*

### PENDING — framing decisions

- **P0.1** Skill directory / name. Proposed `ontology/authoring/` → `ontology-authoring.zip`,
  skill name `ontology-authoring`. Covers SKOS vocabularies too, so alternatives are
  `semantics/authoring` or splitting into `ontology/authoring` + `ontology/vocabularies`.
  Recommendation: one skill, name `ontology-authoring`, and make the *description* say
  "ontologies and SKOS controlled vocabularies" so it triggers for both.
- **P0.2** How OGC-specific? Three levels:
  (a) generic RDF/OWL/SKOS best practice, OGC only in examples;
  (b) generic core + one OGC-specifics file (URI policy, `/def/` vs `/ont/`, VocPub-derived MUSTs);
  (c) OGC-first throughout.
  Recommendation: **(b)** — the modeling advice is reusable, and non-OGC users of this repo still
  get value, while an OGC author gets the policy in one place.
- **P0.3** Is the target always Turtle source-of-truth? (Assumed yes throughout. Say so explicitly?)
- **P0.4** `bblocks/authoring` has an `rdf-only.md` about blocks with only RDF content. Per repo
  policy, no cross-links — we just name the other skill in plain text where relevant. Confirm
  there's no content we should deliberately duplicate/diverge on.

---

## 1. Decide what you're building (before writing any triples)

A router section — arguably the single highest-value part of the skill, because picking the wrong
formalism is the expensive mistake.

- **Is an ontology even needed?** Check for an existing one to reuse or profile first. Extending
  beats inventing.
- **Ontology (OWL/RDFS) vs controlled vocabulary (SKOS) vs both.** Decision rule to state plainly:
  - Classes/properties you will *instantiate* and reason over → OWL.
  - A list of named terms used as *values* (codelist, enumeration, taxonomy) → SKOS.
  - A term set that is both (e.g. feature types that are also browsable categories) → author OWL,
    let the SKOS view be derived (OGC does exactly this with `owl2skos` SHACL rules).
- **Codelist vs class hierarchy** — the recurring modeling question. When should a code be an
  `owl:Class`, an individual, or a `skos:Concept`? (OGC's `HY_NameUsage a owl:Class ; rdfs:subClassOf skos:Concept`
  pattern is worth showing, with its trade-offs.)
- **How much OWL is too much.** Recommend staying near RDFS + light OWL (`subClassOf`,
  `equivalentClass`, `inverseOf`, `disjointWith`); flag cardinality/restriction blank-node
  pyramids as a smell unless there's a reasoner in the loop. Constraints belong in SHACL.
- **PENDING P1.1** Do we want an explicit "OWL 2 profile" recommendation (DL vs RL vs EL vs Full)?
  My inclination is to avoid profile jargon and instead give a "constructs you may use" allowlist.
- **PENDING P1.2** Should the skill cover *generating* an ontology from a UML/spreadsheet/JSON
  Schema source, or only hand-authoring? (Affects whether we discuss provenance of derived terms.)

---

## 2. Vocabulary selection policy (which meta-ontologies)

The "don't invent, don't junk-drawer" rules.

- **Tier 1 (use by default):** `rdfs`, `owl`, `skos`, `dcterms`.
- **Tier 2 (use for their specific job):** `prov` (derivation), `vann` (preferred prefix/namespace),
  `skosxl` (only if labels need to be reified — usually no), `dcat` (only when describing datasets,
  not terms), `prof` (profile declarations), `sh` (constraints).
- **Tier 3 / last resort:** `schema.org`. State the reasoning explicitly (loose semantics, no
  domain governance, "junk drawer" accretion) so the LLM doesn't treat the ban as arbitrary and
  route around it.
- **Never:** `dc11` (`/elements/1.1/`) in new work — use `dcterms`. **PENDING P2.1** confirm.
- **Choosing an external vocabulary you don't already know** — the checklist: is it maintained, is
  the namespace resolvable and persistent, is there a governing body, is it already used elsewhere
  in your domain, does it define the term you mean *or just a term with a similar name*?
- **Reuse over redefinition:** if a suitable predicate exists, use it; if it's *nearly* right,
  subproperty it rather than cloning it. Guard against "close enough" reuse that misstates meaning.
- **PENDING P2.2 — the schema.org conflict.** The OGC VocPub validator (`scripts/vocprez.shapes.ttl`
  in NamingAuthority) *requires* `dcterms:creator` / `dcterms:publisher` to point at
  `sdo:Person` / `sdo:Organization` / `sdo:GovernmentOrganization`, with `sdo:name`, `sdo:url`,
  `sdo:email`. That directly contradicts "schema.org is a last resort". How do we present this?
  Options: (i) carve out an exception "agents are the one place schema.org is expected, because the
  validator demands it"; (ii) recommend `prov:Agent` / `foaf` / `org` and flag the validator as
  something to fix; (iii) show both and say which register expects which.
  **This needs your call — it changes what we tell the LLM to emit for every single vocabulary.**
- **PENDING P2.3** Is `foaf` acceptable at all in new OGC work? (It appears in the wild but is
  effectively unmaintained.)
- **PENDING P2.4** Position on `skos:notation` + custom datatypes for codes.

---

## 3. What every term must carry

The core checklist section. Probably the most-consulted file in the skill.

### 3.1 Every term (class, property, concept), without exception

| Concern | Predicate | Notes to write |
|---|---|---|
| Human-readable name | `skos:prefLabel` (+ `rdfs:label`) | **PENDING P3.1** — which is primary? OGC data carries both; VocPub mandates `prefLabel` for SKOS, and `owl2skos` coalesces `dct:title` / `skos:prefLabel` / `rdfs:label` / localname for OWL. Proposal: SKOS concepts → `prefLabel` mandatory, `rdfs:label` optional mirror; OWL classes/properties → `rdfs:label` mandatory, `skos:prefLabel` recommended. |
| Definition | `skos:definition` | Mandatory. Explicitly *not* `rdfs:comment` and *not* `dcterms:description`. Language-tagged. |
| Extra commentary | `rdfs:comment` / `skos:scopeNote` / `skos:editorialNote` / `skos:historyNote` | What goes where; a definition is not a usage note. |
| Home ontology/scheme | `rdfs:isDefinedBy` | Every term points to its ontology. |
| Provenance | `dcterms:source` / `prov:wasDerivedFrom` / `dcterms:provenance` | VocPub wants at least one (warning-level on concepts, error on schemes). |
| Examples | `skos:example` | Encouraged, especially for codes. |
| Status / deprecation | `owl:deprecated`, `dcterms:isReplacedBy`, status vocabulary | See §6. |
| Stable identifier | `dcterms:identifier` | Optional (VocPub info-level). |

- **Definition quality rules** — worth being blunt about, since this is where LLM output is weakest:
  - must not merely restate the label;
  - must not be circular;
  - one sentence stating *what it is*, genus + differentia; usage/constraints go in a scope note;
  - no markup, no bullet lists inside literals;
  - substitutable for the term in a sentence.
  - Note *why* this matters here: OGC's `skos_vocprez.shapes.ttl` silently backfills a missing
    `skos:definition` from `dcterms:description` or, failing that, **the label itself** — so a
    lazy definition doesn't fail validation, it just produces a worthless one. Good motivating example.
- **Language tags**: always tag literals (`@en`); one `prefLabel` per language (`sh:uniqueLang`);
  **PENDING P3.2** do we require `@en` specifically, or accept plain `xsd:string`? (VocPub accepts
  either; the entailment output in `definitions/conceptschemes/` is mixed.)

### 3.2 Classes

- `rdfs:subClassOf` — single clear parent where possible; when to use multiple.
- Disjointness: when it's worth declaring, when it breaks things.
- Restrictions/blank nodes: allowed but keep shallow, and prefer SHACL for validation constraints.
- Naming: `UpperCamelCase`; no type suffix noise (`FooClass`); singular nouns.

### 3.3 Properties

- Pick `owl:ObjectProperty` vs `owl:DatatypeProperty` vs bare `rdf:Property` — say when each.
- `rdfs:domain` / `rdfs:range`: **the big warning** — these are inferential, not constraining.
  Declaring a domain silently types your subjects. Rule: only declare when the property genuinely
  cannot apply elsewhere; otherwise use SHACL `sh:targetClass` + `sh:class`/`sh:datatype`.
- `rdfs:subPropertyOf` for specializing reused predicates.
- `owl:inverseOf` — declare one direction, don't hand-write both instance-level directions.
- Functional/symmetric/transitive: when they earn their keep.
- Naming: `lowerCamelCase`; verb phrases (`hasPart` vs `part` — **PENDING P3.3**, house style?).

### 3.4 Ontology header (`owl:Ontology`)

A complete, copyable template. Fields to require/recommend:

- `dcterms:title`, `dcterms:description`/`skos:definition`, `dcterms:abstract`?
- `dcterms:created`, `dcterms:modified` (VocPub: exactly one each, `xsd:date`/`dateTime`)
- `dcterms:creator`, `dcterms:publisher` (see P2.2), `dcterms:license`, `dcterms:rights`
- `owl:versionIRI`, `owl:versionInfo`, `owl:priorVersion`
- `vann:preferredNamespacePrefix`, `vann:preferredNamespaceUri`
- `owl:imports` — and the discipline of importing as little as possible
- `dcterms:source` / `prov:wasDerivedFrom`
- **PENDING P3.4** — do we mandate a status term (e.g. from OGC's `status` concept scheme)?

---

## 4. SKOS controlled vocabularies

Your stated priorities, plus what the OGC shapes actually enforce.

- **One `skos:ConceptScheme` per file.** (The OGC tooling warns and misbehaves on multiples — the
  scheme URI becomes the named-graph URI and drives the output path.) Good concrete rationale.
- **Scheme requires:** exactly one `skos:prefLabel`, exactly one `skos:definition`,
  `dcterms:created` + `dcterms:modified`, creator + publisher, provenance, **at least one
  `skos:hasTopConcept`**.
- **Every concept requires:** `skos:prefLabel` (unique per language), `skos:definition`, and
  membership via `skos:inScheme` and/or `skos:topConceptOf`.
- **Top concepts:** you asked for `topConceptOf`/`hasTopConcept` to be mandatory — worth stating
  as: author `skos:topConceptOf` on the concept, author `skos:hasTopConcept` on the scheme, or
  both. **PENDING P4.1** — do we tell authors to write both directions, or one and let entailment
  fill the other? (OGC's `skosbasics.shapes.ttl` entails inverses for `broader`/`narrower` but
  **not** for `topConceptOf`/`hasTopConcept` — so if we say "write one", we should say which one is
  safe. My reading: write both, or at minimum `hasTopConcept` on the scheme, since that's what the
  validator checks.)
- **Hierarchy:** `skos:broader`/`skos:narrower` for specialization. Author *one* direction
  consistently (recommend `broader`) — the inverse is entailed. Say this explicitly, because
  hand-writing both is exactly what an LLM does and it drifts.
- Every non-top concept should have a `broader`; no orphans; no cycles; hierarchy stays within
  one scheme (use mapping properties to cross schemes).
- **`skos:Collection`** — grouping without hierarchy; when to use it instead of `broader`;
  collections need `prefLabel` + `definition` too; `skos:OrderedCollection` for ordered lists.
  Collections are *not* concept schemes and are not part of the broader/narrower tree.
- **Labels:** `altLabel` for synonyms/abbreviations, `hiddenLabel` for misspellings/search,
  `notation` for codes. One `prefLabel` per language, hard rule.
- **Mapping to other schemes:** `exactMatch` / `closeMatch` / `broadMatch` / `narrowMatch` /
  `relatedMatch`. Warn against `owl:sameAs` between concepts (OGC's `skos-sameas.shapes.ttl`
  propagates `prefLabel` across `sameAs`, which is a hint at how much it entails) and against
  `exactMatch` used casually.
- **`skos:related`** — non-hierarchical association; must not be used with a broader/narrower pair.
- **Anti-patterns:** concepts with no scheme; scheme with no top concepts; using `broader` to mean
  "part of"; one concept per spreadsheet row with no thought about hierarchy; label-as-definition.
- **PENDING P4.2** — house policy on concept URI form: opaque codes (`/def/foo/0001`) vs readable
  slugs (`/def/foo/HEALPix`)? OGC data uses readable localnames.
- **PENDING P4.3** — do we cover SKOS-XL at all? (I'd say: mention once, recommend against.)

---

## 5. Naming and URIs

- OGC name type specs: `http://www.opengis.net/def/…` for definitions/vocabularies vs
  `http://www.opengis.net/ont/…` for ontology resources (`ResourceSpecificPath = [aggregate "/"]
  ontology ["#" code]` per the NTS for Ontology Resources). Give the rule and a couple of examples.
- Hash (`#code`) vs slash namespaces — trade-offs, and note the OGC ontology NTS uses `#`.
- Casing conventions: classes `UpperCamelCase`, properties `lowerCamelCase`, SKOS concepts —
  **PENDING P5.1** (OGC data is inconsistent: `HEALPix`, `ISEA3H` are label-shaped).
- Persistence rules: URIs are permanent; never re-point a URI at a different meaning; deprecate,
  don't delete; don't encode volatile facts (version, status, org) into the URI.
- Version-in-URI vs `owl:versionIRI`.
- Prefix hygiene: declare a prefix per namespace, keep prefixes stable across files, register the
  prefix (OGC keeps `definitions/conceptschemes/namespaces.ttl`), use `vann:preferredNamespacePrefix`.
- **PENDING P5.2** — should the skill cover non-OGC URI hosting (w3id.org, PURL) or stay silent?

---

## 6. Versioning, deprecation, change management

- What counts as a breaking change to a vocabulary (meaning change vs label fix vs new term).
- Never repurpose a URI. Deprecate with `owl:deprecated true`, keep the triple set, add
  `dcterms:isReplacedBy` / `skos:changeNote`, and keep it in the scheme.
- Maintain `dcterms:modified` on edit (validator requires exactly one).
- `owl:versionIRI` / `owl:priorVersion` conventions; **PENDING P6.1** semver or date-based?
- **PENDING P6.2** Is there an OGC status vocabulary we should point at
  (`definitions/conceptschemes/status.ttl` exists) and is it mandatory for new work?

---

## 7. Modularization, imports, and alignments

- Keep the ontology file self-contained and minimal; don't inline other people's terms.
- `owl:imports` sparingly — importing a large ontology drags in its entire commitment set.
- **Keep alignments/annotations in a separate file from the ontology.** OGC does this
  (`hyf.ttl` + `hyf_anno.ttl`), and it's good general practice: mappings are opinions, the
  ontology is the artifact. Worth promoting as a rule.
- Separate files for: the model, the alignments, the SHACL shapes, the examples.
- **PENDING P7.1** How far do we go into profiles (`prof:isProfileOf`)? Risk of overlapping with
  the bblocks skills. Recommendation: one paragraph, no more.

---

## 8. File and serialization conventions

- Turtle as the authored form; UTF-8; `.ttl`.
- One ontology / one concept scheme per file; filename related to the URI localname.
- Prefix block conventions; consistent prefix set across a repo.
- Formatting for reviewable diffs: one predicate per line, stable ordering, group by subject,
  alphabetize where practical — matters because these files are reviewed in PRs.
- Blank nodes: avoid where a URI would do; they can't be referenced, diffed cleanly, or annotated.
- Don't hand-edit generated/entailed artifacts (`entailed/` trees, derived `.rdf`/`.jsonld`) —
  they're regenerated and your edits are lost. Short, but prevents a real failure.
- **PENDING P8.1** Do we recommend a formatter/canonicalizer? (rdflib round-trip reorders and
  destroys diffs; that's a real problem worth a sentence.)

---

## 9. Checking your work

Deliberately scoped to *self-checking while authoring*, not the publication pipeline.

- A short **pre-commit checklist** the LLM can run mentally over its output (this may be the single
  most valuable file in the skill — a numbered list mapping to §3 and §4 requirements).
- Note that OGC-governed content is validated against a VocPub-derived SHACL profile, and that
  entailment will add inverses/derived views — so *don't* pre-write what gets entailed.
- Mechanical checks worth naming: does every concept have a scheme; does the scheme have a top
  concept; are all `prefLabel`s unique per language; any dangling URIs referencing terms that
  aren't defined; any `broader` cycles; any term missing a definition.
- **PENDING P9.1** Do we include a runnable validation snippet (pySHACL one-liner, or
  `pip install ogc-na` + `update_vocabs`)? Leaning: one short code block, no more — an LLM that can
  run a validator locally is much more useful, but this must not turn into pipeline documentation.
- **PENDING P9.2** Do we ship the OGC SHACL shape files as skill resources, or link to them?
  Repo policy says schemas by URL, not copied — I'd link.

---

## 10. Proposed file layout

| File | Contents | Est. words |
|---|---|---|
| `SKILL.md` | Router: what this covers, the decision table (OWL vs SKOS vs both), the vocabulary tier table, links out | 700 |
| `choosing-a-formalism.md` | §1 — ontology vs vocabulary vs both, codelist patterns, how much OWL | 900 |
| `vocabularies-to-use.md` | §2 — tiers, schema.org policy, how to vet an external vocabulary | 800 |
| `term-metadata.md` | §3.1–3.3 — the per-term checklist, definition quality rules, domain/range warning | 1300 |
| `ontology-header.md` | §3.4 — the `owl:Ontology` block, versioning fields | 600 |
| `skos-vocabularies.md` | §4 — schemes, top concepts, hierarchy, collections, mappings, anti-patterns | 1400 |
| `naming-and-uris.md` | §5 — OGC NTS rules, casing, persistence, prefixes | 800 |
| `versioning.md` | §6 — deprecation and change management | 500 |
| `modularization.md` | §7 + §8 — file layout, imports, alignments, serialization hygiene | 700 |
| `checklist.md` | §9 — the pre-commit checklist and mechanical checks | 500 |
| `examples/` | A minimal-but-complete ontology, a minimal-but-complete concept scheme, and a "bad vs good" pair | — |

Possible merges if this feels too fragmented: `versioning.md` → `ontology-header.md`;
`modularization.md` → `naming-and-uris.md`.

**PENDING P10.1** Does the split look right, and is `examples/` worth the maintenance?
A single well-commented "canonical example" pair may beat a directory of fragments.

---

## Summary of open questions

| # | Question |
|---|---|
| P0.1 | Skill name/directory |
| P0.2 | How OGC-specific (recommend: generic core + one OGC file) |
| P0.3 | Turtle assumed as source of truth? |
| P0.4 | Anything to deliberately mirror from the bblocks skills? |
| P1.1 | Name OWL 2 profiles, or give a construct allowlist? |
| P1.2 | Cover generation from UML/spreadsheet/JSON Schema sources? |
| P2.1 | Ban `dc11` outright? |
| **P2.2** | **schema.org for agents — the VocPub validator requires it. Exception, or push back?** |
| P2.3 | Is `foaf` acceptable in new work? |
| P2.4 | Position on `skos:notation` + custom code datatypes |
| P3.1 | `skos:prefLabel` vs `rdfs:label` — which is primary, for which term types? |
| P3.2 | Require `@en` language tags, or accept plain literals? |
| P3.3 | Property naming house style (`hasPart` vs `part`) |
| P3.4 | Mandate a status term on ontologies/schemes? |
| P4.1 | `topConceptOf` + `hasTopConcept`: author both, or one? |
| P4.2 | Concept URIs: opaque codes or readable slugs? |
| P4.3 | Mention SKOS-XL? |
| P5.1 | Casing convention for SKOS concept localnames |
| P5.2 | Cover w3id.org / PURL hosting? |
| P6.1 | Version identifier scheme (semver vs date) |
| P6.2 | Is the OGC status vocabulary mandatory for new work? |
| P7.1 | How much to say about PROF profiles |
| P8.1 | Recommend a Turtle formatter/canonicalizer? |
| P9.1 | Include a runnable validation snippet? |
| P9.2 | Ship OGC SHACL shapes, or link them? |
| P10.1 | File split, and is `examples/` worth it? |