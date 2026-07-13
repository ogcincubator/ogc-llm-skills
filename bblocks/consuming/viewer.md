# Inspecting a register visually

Before integrating with an unfamiliar register, it's often faster for a human to look at it in
[bblocks-viewer](https://github.com/ogcincubator/bblocks-viewer) than to read raw JSON — and a
published register almost always already has a hosted instance, so there's nothing to set up.

## Use the hosted instance — no setup needed

`register.json`'s top-level `viewerURL` field is the register's own pre-configured viewer instance
(e.g. `https://ogcincubator.github.io/bblocks-examples/`). For a single block, jump straight to it
via its `documentation['bblocks-viewer'].url` (see [register.md](register.md)) — both are plain links
a human can open, nothing to run.

If a register doesn't set `viewerURL` (no hosted instance), running `bblocks-viewer` yourself against
it is a fallback rather than the norm for consuming a published register:

```bash
docker run --rm --pull=always -v "$(pwd):/register" -p 9090:9090 \
  ghcr.io/ogcincubator/bblocks-viewer
```

Point it at any register via the `register` query parameter
(`http://localhost:9090/?register=<register-url>`) if you're not browsing the bundled/mounted one —
this works against any published register, not just one you authored.

## What it shows, mapped to what you'd otherwise fetch yourself

| Viewer tab | Underlying output | Relevant skill page |
|---|---|---|
| About | description, dependency graph (`dependsOn`/`isProfileOf`/extension points) | [register.md](register.md) |
| Examples | bundled example snippets; GeoJSON examples render on a map with semantically-enriched popups via [jsonld-ui-utils](https://github.com/ogcincubator/jsonld-ui-utils) | [examples-and-docs.md](examples-and-docs.md), [semantic-uplift.md](semantic-uplift.md#displaying-uplifted-data) |
| Data structure | resolved schema properties, tabular | [schema-integration.md](schema-integration.md) |
| JSON Schema | source vs. annotated schema, YAML/JSON toggle, clickable `$ref`s | [schema-integration.md](schema-integration.md) |
| Ontology / Semantic uplift | JSON-LD context, uplift steps | [semantic-uplift.md](semantic-uplift.md) |
| Validation | SHACL shapes + pass/fail report | [validation.md](validation.md) |
| Transforms | declared transforms (if any) | [transforms.md](transforms.md) |

Use this as an orientation step, not as a substitute for the programmatic access covered elsewhere in
this skill — the viewer is for humans; an agent should still fetch `register.json` and the per-block
outputs directly.
