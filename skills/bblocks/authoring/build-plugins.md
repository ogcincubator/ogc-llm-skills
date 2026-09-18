# Build Plugins

Build plugins (also called lifecycle-hook plugins) let you run custom code at fixed points in the
postprocessor's own run — before/after each block at each processing stage, and at a handful of
run-level checkpoints (register assembly, semantic uplift, run completion, failure). Use them for
side effects around the pipeline itself: stamping extra fields into `register.json`, triggering a
notification, validating the assembled register against an external system, syncing output
somewhere. They are not a way to change how an individual block is processed — for that, see
[transform-plugins.md](transform-plugins.md) (custom transform types) or
[validation-plugins.md](validation-plugins.md) (custom validators).

---

## Declaration in `bblocks-config.yaml`

```yaml
plugins:
  build:
    - classes: [my_org.my_hooks.MyBuildHooks]
      pip: git+https://github.com/example/my-bblocks-build-plugin.git
```

Unlike `plugins.transforms`/`plugins.validators`, which declare `modules` and get scanned by duck
typing, build plugins declare `classes`: fully-qualified `module.ClassName` strings. Each named
class is imported and instantiated directly — no scanning, no discovery. `pip` accepts anything
`pip install` understands (package name, version constraint, Git URL, local path); `url` optionally
overrides the display URL recorded in `register.json` (derived automatically from `pip` otherwise).

`classes` can list several classes, from one or more `plugins.build` entries. If more than one
implements the same event, they run in declaration order, each seeing the previous one's output.

---

## Package layout

A build plugin is an ordinary installable Python package — no bblocks-specific packaging is needed:

```
my-bblocks-build-plugin/
├── pyproject.toml
└── my_org/
    └── my_hooks.py       # defines the plugin class(es)
```

```toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "my-bblocks-build-plugin"
version = "0.1.0"
dependencies = []
```

A plugin class needs no base class and no constructor arguments — the postprocessor instantiates it
with `ClassName()`. It implements only the lifecycle methods it cares about; any event with no
matching method on the class is simply skipped.

**Local development loop:** point `pip:` at the plugin's local directory while iterating, then run
the postprocessor against a scratch block with `--filter ... --skip-permissions true` (see
[local-iteration.md](local-iteration.md)). Switch back to the published reference before committing.

---

## Lifecycle events

| Method | Signature | Fires |
|---|---|---|
| `before_run` | `before_run(self, register, context)` | Once, after the register/blocks are loaded, before any block is processed. |
| `before_bblock` | `before_bblock(self, stage, bblock, register, context)` | Once per (stage, block), for each of the five processing stages. |
| `after_bblock` | `after_bblock(self, stage, bblock, register, context)` | Once per (stage, block). |
| `after_register` | `after_register(self, register, context)` | Once, after `register.json`'s content is fully assembled, before it's written to disk. |
| `after_uplift` | `after_uplift(self, register, context)` | Once, after JSON-LD/Turtle semantic uplift, before any SPARQL push. |
| `after_run` | `after_run(self, register, context)` | Once, only on a successful run, at the very end (after a SPARQL push, if enabled). |
| `on_error` | `on_error(self, error, register, context)` | Once, only when the run aborts. Mutually exclusive with `after_run` — exactly one of the two fires per run. |

`stage` is one of `ANNOTATE`, `JSONLD`, `FINALIZE`, `TRANSFORMS`, `DOC` (as a string), matching the
order the postprocessing pipeline itself loops through. Processing is **stage-major, not
block-major**: every block's `ANNOTATE` pair fires before any block's `JSONLD` pair, and so on — a
plugin can't assume that seeing `after_bblock(ANNOTATE, X, ...)` means block X's later stages are
close behind.

`after_bblock(FINALIZE, ...)` is the one per-block event guaranteed to fire exactly once for every
block on every run (the only per-block loop that isn't gated by `--steps`) — the natural anchor for
"do something once per block" plugins. At that point a block's metadata is final except for its
`documentation` key, which is generator-owned and gets replaced later during the `doc` stage.

`before_bblock`/`after_bblock` are pure observers — nothing they return is used. **`after_register`
is the one mutation point in the contract**: if it returns a `dict`, that dict replaces the register
seen by the next plugin and, ultimately, what's written to `register.json`. Returning anything else
leaves the register unchanged.

---

## What each hook receives

`context` (present on every event) carries the run's own settings:

```python
{
    'itemsDir': str,             # scanned items directory
    'baseUrl': str | None,
    'registerFile': str | None,
    'steps': list[str] | None,   # --steps value, or None for "all steps"
    'filter': str | None,        # --filter value
    'failOnError': bool,
}
```

For per-block events at `FINALIZE`/`DOC`, `context` additionally carries `'light': bool` — whether
this block is excluded by `--filter` for this stage. It isn't present for run-level checkpoints.

`bblock` (per-block events only) is a plain dict, rebuilt fresh for every call:

```python
{
    'identifier': str,
    'metadata': {...},        # the block's current metadata
    'urlsResolved': bool,      # False through ANNOTATE/JSONLD, True from FINALIZE onward
}
```

`register` is always a plain dict, never a live Python object — same JSON-snapshot boundary as
transform/validator plugins. Its shape differs by event: at `before_run` and at every per-block
event it's just `{'bblocks': [<identifier>, ...]}` (a list of identifiers, not the full register —
the register isn't fully assembled yet). At `after_register`, `after_uplift`, and `after_run` it's
the real, complete `register.json` content.

`error` (`on_error` only) is a plain dict, not an exception object:

```python
{
    'type': str,        # exception class name
    'message': str,
    'traceback': str,
    'phase': str,        # 'before_run' | 'annotate' | 'jsonld' | 'finalize' | 'transforms'
                          # | 'doc' | 'register' | 'after_register' | 'uplift'
}
```

`register` is nullable here (e.g. a failure during `before_run` has no register yet).

---

## Failure semantics

- **Run-level checkpoints** (`before_run`, `after_register`, `after_uplift`, `after_run`): any
  exception always aborts the run, regardless of `--fail-on-error`.
- **Per-block events** (`before_bblock`/`after_bblock`): follow the same rule as the rest of the
  pipeline — with `--fail-on-error` set, an exception aborts the run; otherwise it's logged and
  processing continues, with the block left intact. A non-fatal hook failure leaves only a log
  line — no marker is written into `register.json` or the block's metadata.
- **`on_error`** fires exactly once, only when the whole run aborts, and never together with
  `after_run`. It doesn't fire for non-fatal per-block errors, for a failed SPARQL push (that's
  handled internally and still counts as a successful run), or for failures before plugins are even
  loaded (e.g. a broken `bblocks-config.yaml`).

If you rely on a hook actually running, run with `--fail-on-error` (as this project's own CI does) —
otherwise a failing hook is easy to miss.

---

## Isolation

Each declared class runs in its own isolated subprocess with its own virtualenv (auto-created under
`.bblocks-sandbox/`, same mechanism as transform/validator plugins), spawned lazily on first use and
kept alive for the whole run. This is entirely transparent to a plugin author: write a plain class
with plain-Python method bodies. `print()` inside a hook works normally — output is captured and
surfaced in the pipeline's log, prefixed with the plugin's class path.

Unlike transform/validator plugins (where approving a module approves every class discovered
inside it), a build plugin's interactive permission prompt approves per **class path** — approving
one class in a module does not implicitly approve another class in the same module. `pip` also
supports Node.js-style `npm` dependencies for transform/validator plugins; build plugins are
Python-only. See [security.md](security.md) for the full permission/sandboxing model shared across
plugin kinds.

---

## Minimal example

```python
class MyBuildHooks:

    def before_run(self, register, context):
        print(f"starting run over {len(register.get('bblocks', []))} block(s)")

    def after_register(self, register, context):
        # the one mutation point: stamp a custom field into the register
        result = dict(register)
        result['x-myBuildPlugin'] = {'bblockCount': len(result.get('bblocks', []))}
        return result

    def on_error(self, error, register, context):
        print(f"run failed in phase {error['phase']}: {error['message']}")
```

A fuller, real-world example implementing every event is
[bblocks-build-plugin-sample](https://github.com/ogcincubator/bblocks-build-plugin-sample)
(`SampleBuildHooks`), which stamps a processing timestamp onto the register and every block via
`after_register`.

---

## Plugin metadata in the register

Approved build plugins are recorded in `register.json` under `buildPlugins` (classes, pip
specifier(s), URL) — parallel to the existing `transformPlugins`/`validatorPlugins` keys. This
matters more here than for transform/validator plugins, since `after_register` can silently rewrite
the register: a consumer can see from `buildPlugins` that plugin code had the opportunity to edit it.

A build plugin that stamps a new field/document onto a bblock pairs naturally with a
[tab plugin](tab-plugins.md) on the viewer side: the build plugin emits the data into `json-full`,
the tab plugin renders it as its own tab. The two mechanisms are independent, though — a tab
plugin's `matches()` can key off existing bblock/register metadata with no build plugin involved at
all.
