# Validator Plugins

The built-in validators cover JSON Schema, JSON-LD context, and SHACL. For any other file type or
custom validation logic — ZIP integrity, WKT geometry, XSD schema, custom business rules — you can
add validator plugins.

---

## Declaration in `bblocks-config.yaml`

```yaml
plugins:
  validators:
    - pip: git+https://github.com/example/my-bblocks-validator-plugin.git
      modules:
        - my_bblocks_validator_plugin
```

`pip` accepts any specifier that `pip install` understands.

---

## Package layout

A validator plugin is an ordinary installable Python package — no entry points, decorators, or
special package metadata are needed. `pip` just needs to be able to install it; the postprocessor
then imports the module(s) listed under `modules` and scans them by duck typing.

Minimal layout:

```
my-bblocks-validator-plugin/
├── pyproject.toml
└── my_bblocks_validator_plugin/
    └── __init__.py       # defines the validator class(es)
```

```toml
# pyproject.toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "my-bblocks-validator-plugin"
version = "0.1.0"
dependencies = []          # runtime deps the validator code needs, e.g. "shapely"
```

The distribution name (`my-bblocks-validator-plugin`) and the importable module name
(`my_bblocks_validator_plugin`, listed under `modules`) don't have to match.

**Local development loop:** while iterating, point `pip:` at the plugin's local directory instead
of a Git URL — a relative path resolves from wherever you invoke the postprocessor (the register
root, with the standard Docker invocation). The postprocessor reinstalls from that path on every
run, so edits take effect immediately with no publish step:

```yaml
plugins:
  validators:
    - pip: ../my-bblocks-validator-plugin
      modules:
        - my_bblocks_validator_plugin
```

Then run the postprocessor against a scratch block with `--filter ... --skip-permissions true`
(see [local-iteration.md](local-iteration.md)) to exercise the plugin end to end. Switch `pip:`
back to the published Git URL/version before committing `bblocks-config.yaml`.

---

## How a plugin is recognized

The postprocessor scans listed modules for classes with:

- `mime_types` and/or `file_extensions`: lists of strings declaring which files the class handles
- `validate(self, meta)`: a callable accepting a metadata object

At least one of `mime_types` or `file_extensions` must be present. Recognition is by duck typing.

`file_extensions` entries may include or omit the leading dot (`.zip` and `zip` are both accepted).

---

## The `meta` object

| Attribute | Type | Description |
|-----------|------|-------------|
| `input_path` | `str` | Absolute path to the file to validate |
| `mime_type` | `str` \| `None` | MIME type (from extension or `media-type` in `tests.yaml`) |
| `display_filename` | `str` | Original filename for error messages |
| `schema_ref` | `str` \| `None` | Schema ref from the test entry |
| `context` | namespace | Block context (see below) |

**`meta.context` attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `bblock_id` | `str` | Block identifier |
| `bblock_name` | `str` \| `None` | Human-readable name |
| `register_base_url` | `str` \| `None` | Base URL of the register |
| `validation_resources` | `list` | Resources with `role: validation` from `bblock.json` — each is a dict with `ref`, `format`, and optionally `conformsTo` |
| `bblock_metadata` | `dict` \| `None` | Full block metadata snapshot |

---

## Return value

Return a list of entry dicts:

```python
[
    {"message": "File is valid", "severity": "info"},
    {"message": "Checksum mismatch", "severity": "error"},
    {"message": "Timestamps are in the future", "severity": "warning"},
    {"message": "Invalid geometry on line 3", "severity": "error", "payload": {"line": 3}},
]
```

- `severity`: `"info"`, `"warning"` or `"error"` (case-insensitive). Only `error` entries fail validation; `warning` entries are advisory (reported as warnings, block still passes).
- Legacy `is_error` (bool) is still accepted when `severity` is absent (`True` → `error`, `False` → `info`). If both are given and disagree, `severity` wins. An unrecognized `severity` is ignored (note added to the message) and falls back to `is_error`.
- `severity` needs bblocks-postprocess ≥ v1.2.4; older versions ignore it, so send `is_error` too if the plugin must run on them.

- Return `None` or `[]` — validator did not apply or found nothing to flag (not an error).
- Raise any exception — unexpected failure; full traceback is captured and reported as an error.

`payload` is optional structured metadata, merged into the entry in the JSON report. `"subsection"` groups entries under a sub-heading in the HTML report. The keys `op`, `isError`, `severity`, `message` and `plugin` are reserved and ignored. Entries always go in the **Plugin** section (no `section` key).

---

## File matching

The postprocessor calls `validate()` only for files whose extension or MIME type appears in
`mime_types` or `file_extensions`. Files not matched by any validator are silently skipped.

For non-standard extensions, declare the type explicitly in `tests.yaml`:

```yaml
- ref: assets/my-geometry.wkt
  media-type: text/wkt
```

---

## Using validation resources

Plugins can be driven by per-block configuration rather than hard-coded schemas, via resources
declared with `role: validation` in `bblock.json`:

```json
{
  "resources": [
    {
      "role": "validation",
      "ref": "assets/schema.xsd",
      "format": "application/xml",
      "conformsTo": "https://www.w3.org/2001/XMLSchema"
    }
  ]
}
```

Access in the plugin:

```python
resources = getattr(meta.context, 'validation_resources', None) or []
xsd_specs = [r for r in resources if r.get('conformsTo') == 'https://www.w3.org/2001/XMLSchema']
```

---

## Isolation

Each plugin runs in its own isolated virtualenv (auto-created under `.bblocks-sandbox/plugins/`).

---

## Minimal plugin example

```python
# my_bblocks_validator_plugin/__init__.py
import zipfile

class ZipValidator:
    mime_types = ['application/zip', 'application/x-zip-compressed']
    file_extensions = ['.zip']

    def validate(self, meta):
        try:
            with zipfile.ZipFile(meta.input_path) as zf:
                bad_file = zf.testzip()
        except zipfile.BadZipFile as exc:
            return [{'message': f'Invalid ZIP: {exc}', 'severity': 'error'}]
        if bad_file is not None:
            return [{'message': f'Corrupt entry: {bad_file}', 'severity': 'error'}]
        return [{'message': 'ZIP is valid', 'severity': 'info'}]
```

A real-world example with multiple validators (ZIP, WKT geometry, XSD):
[bblocks-sample-validator-plugins](https://github.com/ogcincubator/bblocks-sample-validator-plugins)

---

**Examples:**
- [examples/validator-plugins/bblock.json](examples/validator-plugins/bblock.json) — declares an XSD resource with `role: validation`.
- [examples/validator-plugins/bblocks-config.yaml](examples/validator-plugins/bblocks-config.yaml) — registers the sample validator plugin package.
- [examples/validator-plugins/examples.yaml](examples/validator-plugins/examples.yaml) — examples for ZIP, WKT, and XML snippets.

---

## Reports

Entries produced by plugins appear in a **Plugin** section of the HTML, text and JSON reports (with their `severity`).
Each entry is attributed to `module.ClassName` for traceability.

To see plugin `print()` output, run the postprocessor with `--log-level DEBUG`.
