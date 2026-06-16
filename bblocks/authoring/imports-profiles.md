# Imports and Profiles

## Importing other registers

A bblocks repository can import any other register so that references to blocks in those registers
(via `bblocks://` URIs in schemas, or in `bblock.json` metadata) are automatically resolved.

Imports are declared in `bblocks-config.yaml`:

```yaml
imports:
  - default                                             # the main OGC Building Blocks register
  - https://example.org/other-register/build/register.json
```

- If `imports` is **omitted**, the main OGC register is imported by default.
- `default` is an alias for the main OGC register.
- An **empty array** `[]` imports nothing.
- If the URL ends with `build/register.json` or `register.json`, you can omit the suffix — the
  postprocessor tries the base URL and common suffixes automatically.

### What importing gives you

- `bblocks://` URIs in schema `$ref` are resolved to the imported block's annotated schema URL.
- `bblocks://` URIs in metadata fields (`isProfileOf`, `dependsOn`, `extensionPoints`) are resolved to the referenced block. Bare identifiers are also accepted in these fields, but `bblocks://` URIs are preferred for consistency.
- The imported block's JSON-LD context is inherited into the assembled context.
- The imported block's SHACL shapes are inherited for validation.

---

## `isProfileOf` — declaring a profile

A **profile** is a block that specialises another: it is a stricter, backward-compatible
extension. Any data valid for the profile is also valid for the base block.

Declare this relationship in `bblock.json`:

```json
{
  "isProfileOf": "bblocks://ogc.geo.features.feature"
}
```

Or as an array for multiple bases:

```json
{
  "isProfileOf": [
    "bblocks://ogc.geo.features.feature",
    "bblocks://ogc.ogc-utils.geojson"
  ]
}
```

Bare identifiers (e.g. `"ogc.geo.features.feature"`) are also accepted.

`isProfileOf` is a metadata declaration — it records the relationship in the register and
exposes it to tools and validators. The actual stricter constraints are expressed through the
block's JSON Schema (using `allOf` and additional constraints) and SHACL shapes.

---

## `isProfileOf` vs. `dependsOn`

| | `isProfileOf` | `dependsOn` |
|-|---------------|-------------|
| Semantic meaning | This block specialises (is a stricter subset of) the referenced block | This block requires the referenced block at runtime |
| Inherits context / shapes | Yes | No |
| Constraint relationship | Implied (profile is stricter) | None |

---

## `extends` vs. `isProfileOf`

| | `isProfileOf` | `extends` |
|-|---------------|-----------|
| Where declared | `bblock.json` | `bblock.json` |
| What it does | Metadata relationship declaration | Schema compilation with extension points |
| Schema output | None directly | Compiled schema with substituted references |
| Experimental | No | Yes |

See [extension-points.md](extension-points.md) for `extends` / `extensionPoints`.

---

## Conformance and requirement classes

For blocks that relate to OGC/ModSpec specifications:

- `requirementClasses`: URIs of requirement classes that can be used to validate this block.
- `conformanceClasses`: URIs of conformance classes that this block refers to.

These are informational metadata — they are recorded in the register and can be used by
conformance testing tools, but the postprocessor does not enforce them directly.

---

**Example:** [examples/importing-block/](examples/importing-block/) — imports the SOSA register, then profiles two SOSA blocks in a single schema using `bblocks://`.

---

## `bblocks://` URI scheme in schemas

To reference another block's schema from your own:

```yaml
"$ref": "bblocks://ogc.geo.features.feature"
```

At postprocessing time, this is resolved to the actual annotated schema URL from the imported register.
The referenced block's JSON-LD context and SHACL shapes are automatically inherited.

This only works for blocks in imported registers. If the register is not listed in `imports`, the
`bblocks://` URI will fail to resolve.
