# Validation

Building Blocks have automated validation built into the postprocessing pipeline. This file covers
how validation works, how to run it locally, and how to interpret results.

---

## What gets validated

Every JSON, JSON-LD, and Turtle file in `tests/`, every entry in `tests.yaml`, and every example
snippet in `examples.yaml` goes through the validation pipeline:

1. **JSON Schema validation** — if the block has a schema
2. **Semantic uplift** — JSON → `.jsonld` + `.ttl` (if context is present)
3. **SHACL validation** — against `shapes.shacl` / `shaclShapes` (if defined)
4. **Plugin validation** — if [validator plugins](validation-plugins.md) are configured

See [tests.md](tests.md) for how to declare test resources.
See [semantic/shacl.md](semantic/shacl.md) for SHACL details.

---

## Running locally

```bash
docker run -it --pull=always --rm --workdir /workspace \
  -v "$(pwd):/workspace" \
  ghcr.io/opengeospatial/bblocks-postprocess \
  --clean true \
  --base-url http://localhost:9090/register/
```

### Useful flags

| Flag | Description |
|------|-------------|
| `--clean true` | Delete old `build/` before running |
| `--log-level DEBUG` | Verbose output: annotation steps, uplift, SHACL evaluation |
| `--filter <id-or-path>` | Process only one block (by identifier or path to `bblock.json`) |
| `--fail-on-error false` | Continue past errors instead of aborting (omit in CI) |
| `--steps <list>` | Comma-separated subset of steps: `annotate,jsonld,tests,transforms,doc,register` |
| `--skip-permissions true` | Skip interactive prompts for transforms/plugins (required for agent or CI runs) |

For a full flag reference and iterative workflow examples see [local-iteration.md](local-iteration.md).

Running the module directly (without Docker) also works if dependencies are installed:

```bash
python -m ogc.bblocks.bootstrap --clean true --log-level DEBUG
```

---

## Validation output

Results are written to `build/tests/`:

```
build/tests/
  report.html                           # summary report (linked from generated docs)
  report.json                           # machine-readable summary
  <block-id>/
    <testcase>.jsonld                   # uplifted JSON-LD
    <testcase>.ttl                      # uplifted Turtle
    <testcase>.validation_passed.txt    # SHACL report (pass)
    <testcase>.validation_failed.txt    # SHACL report (fail)
```

Open `build/tests/report.html` in a browser for the easiest overview.

---

## Interpreting errors

### JSON Schema errors

```
Validation error: 'coordinates' is a required property
  Instance: examples/my-example.json
  Schema: build/annotated/my.block/schema.json
```

Check:
- Is the instance missing a field declared as `required` in the schema?
- Is a `$ref` resolving to the wrong schema? Check the annotated schema at `build/annotated/...`.

### Uplift errors

```
Error during JSON-LD uplift: ...
```

The JSON-LD context may be malformed or conflict with the JSON structure. Use the
[JSON-LD Playground](https://json-ld.org/playground/) with the **assembled context** (from `build/`)
to debug interactively.

### SHACL errors

```
Validation report:
  sh:result [
    sh:resultSeverity sh:Violation ;
    sh:focusNode <...> ;
    sh:resultPath ex:hasValue ;
    sh:resultMessage "Less than 1 values on <...>->ex:hasValue"
  ]
```

The node and path tell you which subject and predicate violated the constraint. Check:
- Is the property being uplifted correctly? (Check the `.ttl` file)
- Is the SHACL closure missing a vocabulary term that the shape depends on?

---

## Common pitfalls

| Problem | Likely cause |
|---------|-------------|
| Schema validation passes but SHACL fails | The JSON-LD context maps properties to unexpected URIs; inspect the `.ttl` output |
| SHACL reports unknown class / property | Missing SHACL closure; add the vocabulary file to `shaclClosures` |
| `$ref` not resolving | The referenced block's register is not listed in `bblocks-config.yaml` imports, or the identifier is wrong |
| Annotated schema missing `x-jsonld-*` | The property is inside a `$ref` that wasn't resolved; check `build/annotated/.../schema.json` |
| Uplift produces no triples | Context file is not linked; check that `context.jsonld` exists or `ldContext`/`x-jsonld-context` is set |

---

## Online debugging tools

- [JSON Schema validator](https://www.jsonschemavalidator.net/) — paste schema + instance
- [JSON-LD Playground](https://json-ld.org/playground/) — test context + document, see expanded RDF
- [SHACL Validator](https://shacl-play.sparna.fr/play/validate) — test shapes against a Turtle file
