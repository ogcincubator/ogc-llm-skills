# Repository Structure

## Top-level layout

```
my-bblocks-repo/
  bblocks-config.yaml      # register-level configuration (required)
  bblocks-config-local.yml # local URL mappings for testing (gitignored, optional)
  _sources/                # all block source files live here
    group1/
      my-block/
        bblock.json        # block metadata (required)
        schema.yaml        # JSON Schema (optional)
        context.jsonld     # JSON-LD context (optional)
        shapes.ttl         # SHACL shapes (optional)
        examples.yaml      # examples (optional)
        tests.yaml         # explicit test resources (optional)
        tests/             # auto-detected test files (optional)
        transforms.yaml    # transforms (optional)
        semantic-uplift.yaml # semantic uplift config (optional)
        assets/            # static files (images, etc.) — optional, no fixed name required
        description.md     # long-form Markdown documentation (optional)
  build/                   # NEVER edit — postprocessor output (tracked by git for CI publishing)
```

## `bblocks-config.yaml`

Register-level configuration. Key fields:

```yaml
name: My Register                     # short display name
identifier-prefix: myorg.myproject.   # dot-separated prefix ending with "."
imports:
  - default                           # the main OGC register; or a URL to register.json
abstract: |
  A short description of this register.
```

`imports` controls which other registers are available for `$ref` resolution via the `bblocks://` scheme
and for inheriting JSON-LD contexts and SHACL shapes. If `imports` is omitted, the main OGC register
is imported by default. Use an empty array `[]` to import nothing.

The `viewer` sub-key controls how the Building Blocks Viewer displays imported blocks:

```yaml
viewer:
  show-imported-depth: 0   # 0 = local only; 1+ = N levels deep; -1 = all
```

## Identifier construction

Block identifiers are auto-generated — never set `itemIdentifier` manually:

```
{identifier-prefix}{dot-separated-path-from-_sources}
```

Examples:

| Prefix | Source path | Identifier |
|--------|-------------|------------|
| `myorg.p.` | `_sources/geo/point/bblock.json` | `myorg.p.geo.point` |
| `ogc.geo.` | `_sources/features/feature/bblock.json` | `ogc.geo.features.feature` |

Directory names become identifier segments. Intermediate directories without a `bblock.json` are
treated as namespaces and are part of the identifier but have no block of their own.

**Identifiers must be stable** — changing them breaks all downstream `$ref`s, imports, and profiles.

## Source files vs. build outputs

`_sources/` contains what authors write. `build/` contains what the postprocessor generates.

The `build/` directory **must never be edited by hand**. Applications and other registers should
reference resources from `build/`, not `_sources/`.

## Static assets

Any files in an `assets/` subdirectory (or any subdirectory, really — the name is a convention) are
copied directly to the GitHub Pages output alongside the block. Use them for images referenced in
`description.md` or other documentation. These are served as-is and are not post-processed.

## Local URL mappings

`bblocks-config-local.yml` (gitignored) allows redirecting remote URLs to local paths during testing:

```yaml
url-mappings:
  'https://example.com/imported/': '/local/path/to/imported-register/'
  'https://example.com/relative/': '../../other-register'
```

When running via Docker, local paths must also be mounted as volumes:

```bash
docker run ... -v "/local/path/to/imported-register:/local/path/to/imported-register" ...
```

If using `build.sh`, add entries to a `.volumes` file instead:

```
/absolute/path:/container/mount
../relative/path:/container/mount2
```
