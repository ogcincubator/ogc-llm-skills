# Using examples and generated docs instead of raw schema

Reading a raw JSON Schema to understand what a block represents is slow and error-prone — annotated
schemas are dense with resolved `$ref`s and inlined `x-jsonld-*` annotations. For most "what does this
block look like / how do I produce valid data for it" questions, prefer these cheaper sources first.

## Bundled examples

A block's full metadata (`documentation['json-full'].url`) includes an `examples` array. Each example
has one or more language-tagged snippets (JSON, sometimes other formats) that are known-valid sample
data for the block — they're checked by the register's own CI. These are good few-shot material:
fetch the full block, pull a snippet, use it directly as a template for new data, or as grounding when
asking an LLM to generate data conforming to the block.

## Generated documentation

Each block also publishes human-readable docs, generated from the same metadata:

- `documentation['markdown'].url` — a single Markdown file: description, schema property table,
  examples rendered inline. Usually the fastest way for an agent to "read" a block.
- `documentation['json-full'].url` — **the canonical, complete view of a block.** Same data the
  Markdown is rendered from, but structured. It carries every field from the `bblocks[]` summary (see
  [register.md](register.md)) minus `documentation` itself, plus:

  | Extra field | Meaning |
  |---|---|
  | `description` | Long-form Markdown description (vs. `abstract`'s short summary). |
  | `examples` | Array of bundled examples — see above. |
  | `examplePrefixes` | Namespace prefixes used when rendering example snippets, if declared. |
  | `annotatedSchema` | The annotated schema's contents inlined as text (not just a URL to it). |
  | `semanticUplift` | `{additionalSteps: [...]}` — pre/post uplift step definitions, see [semantic-uplift.md](semantic-uplift.md). |
  | `transforms` | Declared transforms, if any — same as the summary field. |
  | `gitRepository`, `gitPath` | Source repo URL and path to this block's source directory. |

  Prefer fetching this single document over separately fetching the schema, the context, and the
  examples — it's already assembled, and it's the most complete artifact published for a block.

## When to fall back to the raw schema

Use the annotated schema directly (not the docs) when you need exact validation behavior — required
fields, enum values, format constraints — i.e. when correctness matters more than speed of
understanding. Docs and examples are for orientation; the schema is the source of truth for validation
(see [validation.md](validation.md)).
