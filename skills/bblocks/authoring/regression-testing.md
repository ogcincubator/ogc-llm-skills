# Regression-testing downstream registers against an unreleased upstream change

Covers how to check, before publishing, whether a change to one register (typically a fork or
working copy of a widely imported register) breaks the registers that import it — directly or
through a chain of imports. Built on local URL mappings (`bblocks-config-local.yml` + `.volumes`,
introduced in [imports-profiles.md](imports-profiles.md#local-url-mappings-offline--restricted-registers)).

Worked shape used throughout:

```
upstream (changed) ──► mid-a ──► mid-b ──► leaf
          └──────────► other-leaf
```

---

## Why mapping only in the top-level repo is not enough

`url-mappings` intercepts every URL the postprocessor fetches while processing the repo it is run
in, including registers reached transitively. It is tempting to map only `upstream` in `leaf`'s
config. **That does not test the change.** The published outputs of the intermediate registers are
frozen against the *old* upstream:

- an assembled `context.jsonld` inlines the terms of every imported block's context;
- annotated schemas embed resolved `x-jsonld-*` annotations and refs as they were at build time;
- `register.json` records each block's inherited `shaclShapes`.

So `leaf` would see the new upstream only where it fetches upstream directly, and the old one
through `mid-a`/`mid-b`. A valid regression test **rebuilds every register in the chain, in
dependency order**, each against the local build of the one before it.

## 1. Build each imported register with `build-local.sh`

Each register that something else imports (`upstream`, `mid-a`, `mid-b`) is built into its
`build-local/` with its **real public base URL**, so that the self-referencing URLs stamped into
its annotated schemas and contexts (`<base-url>build-local/annotated/...`) are ones its consumers
can map. Repos scaffolded from [bblocks-template](https://github.com/opengeospatial/bblocks-template)
have a `build-local.sh` for exactly this:

```bash
./build-local.sh                                              # base URL autodetected from the git remote
./build-local.sh --base-url https://example.org/upstream/     # on a fork: the ORIGINAL register's URL
```

If the repo has no `build-local.sh`, it is a one-line wrapper around `build.sh` (whose `"$@"` is
passed to the postprocessor, and a later `--base-url` overrides `build.sh`'s; an empty one falls
back to autodetection):

```bash
#!/bin/bash
exec "$(dirname "$0")/build.sh" --base-url "" "$@"
```

Do not run plain `build.sh` in a register that others are consuming: it rewrites `build-local/`
with the `http://localhost:9090/register/` viewer base URL, whose `$ref`s fail inside the
consumer's container. On a fork, autodetection yields the *fork's* GitHub Pages URL, which no
consumer imports — always pass `--base-url` there.

## 2. Map each locally built register once

Whenever url-mappings are active, the import resolver also tries
`<import-url>/build-local/register.json` and prefers it over the published `build/register.json`
if its `modified` timestamp is newer. So a single mapping of the dependency's base URL to its
**checkout root** covers everything a consumer fetches from it — `register.json`, annotated schemas
and contexts under `build-local/`, and SHACL shapes, which imported blocks publish as
`<base-url>/_sources/<path>` rather than compiling into the build output:

```yaml
# consumer's bblocks-config-local.yml
url-mappings:
  'https://example.org/upstream/': '/imports/upstream'
```

```
# consumer's .volumes (read by build.sh; relative paths resolve against the repo)
../upstream:/imports/upstream
```

`leaf`'s config maps `upstream`, `mid-a` **and** `mid-b`; `mid-b`'s maps `upstream` and `mid-a`;
and so on. Relative `.volumes` paths work from both Git Bash and WSL; absolute ones (`/c/...` vs
`/mnt/c/...`) don't. Only scripts that read `.volumes` (`build.sh` and its wrappers) mount them —
a hand-written `docker run` without the mounts fails with `Local file /imports/... does not exist`.

Unmapped URLs still go to the network, so only the registers you rebuilt are local. Use
`--log-level DEBUG` to see `Intercepted URL ... -> ...` lines confirming each redirect. While
resolving an import's `register.json` the resolver swallows a missing local file and tries its next
candidate URL (possibly over the network), so check the log rather than assuming a broken mapping
fails loudly; the final error lists every location tried.

## 3. Run baseline and candidate builds, then diff

A regression is a test that passed against the published upstream and fails against the change,
so build each downstream repo twice with the **same image** and compare:

| Run | Local config | Output directory |
|---|---|---|
| baseline | `bblocks-config-local.yml` absent | `build-local-baseline/` (pass `--register-file`, `--annotated-path`, `--generated-docs-path`, `--test-outputs-path`) |
| candidate | mappings installed | `build-local/` (`build-local.sh` for intermediates, `build.sh` for leaves) |

The postprocessor always reads `bblocks-config-local.yml` from the working directory and has no
CLI flag to select or disable it, so the baseline run must rename it out of the way first (and
restore it afterwards). Order:

1. Baselines of every downstream repo — independent, can run in parallel.
2. Candidate `upstream` (`build-local.sh`).
3. Candidate `mid-a` (`build-local.sh`) and `other-leaf` (parallel), then `mid-b`, then `leaf` —
   each only after everything it imports has been rebuilt.

Baselines only need re-running when the downstream repos or the published upstream change.
Never run two builds of the *same* repo concurrently (they share `.bblocks-sandbox/`).

Compare `tests/report.json` per test item, keyed by `(bblockId, source filename)`, classifying each
as REGRESSION (pass → fail), FIXED, still-failing-but-errors-changed, NEW or GONE:

```python
import json
def items(path):
    r = json.load(open(path, encoding='utf-8'))
    return {(bid, it['source']['filename'].rsplit('/', 1)[-1]): it['result']
            for bid, b in r['bblocks'].items() for it in b['items']}
base = items('build-local-baseline/tests/report.json')
cand = items('build-local/tests/report.json')
for k in sorted(base.keys() | cand.keys()):
    if base.get(k) != cand.get(k):
        print({True: 'FIXED', False: 'REGRESSION'}.get(cand.get(k), 'NEW/GONE'), k)
```

Also diff each block's `globalErrors`: a dependency-level problem (e.g. an unloadable SHACL file)
shows up there and fails *every* item of the block, including negative tests, which then look like
dozens of unrelated regressions. Fix or work around global errors first, then re-diff to see the
real per-item regressions.

## 4. Typical causes and fixes

- **A dependency tightened a schema** (new `required`, strict `pattern`/`format`): downstream
  examples now fail with JSON Schema errors. Fix the data if it was actually invalid, or move the
  consumer to a lenient variant if the upstream offers one.
- **Lenient variants exposed as `$defs`**: an upstream may split a strict standalone schema from
  a lenient one for use inside collections (e.g. members whose mandatory properties are supplied
  by the collection). Reference it with a fragment: `bblocks://<id>#/$defs/<name>` works, as does
  `<url>/schema.yaml#/$defs/<name>`. Note this couples the consumer to the new upstream: a
  baseline built against the *published* upstream will fail to resolve the fragment until the
  change is released.
- **Block identifiers removed or renamed upstream**: check before building by comparing the
  candidate's `register.json` `itemIdentifier` set with the published one, and grepping
  downstream `_sources/` for `bblocks://` refs to the missing ids.
- **Unloadable inherited SHACL** (`globalErrors.SHACL`: `Error processing <path>: No such file or
  directory`): inspect the dependency's `register.json` `shaclShapes` — every entry must be an
  absolute URL. See the profile-validation caveat in [transforms.md](transforms.md#output-profile-validation).

To find the real cause behind a `oneOf`/`anyOf` failure, see
[validation.md](validation.md#drilling-into-anyof--oneof-failures).

## Windows (Git Bash) notes

- Prefix `build.sh` / `docker run` with `MSYS_NO_PATHCONV=1`, otherwise Git Bash rewrites
  container paths (`/workspace`, `/imports/...`) into Windows paths and the mounts break.
- Older `build.sh` copies always pass `-it`, which fails without a terminal; current
  bblocks-template only adds it when attached to one (see [local-iteration.md](local-iteration.md)).

## Leaving the setup in place

For repeated runs, keep `bblocks-config-local.yml` and `.volumes` installed in each downstream repo
(they are normally gitignored; also exclude `build-local-baseline/`, e.g. in `.git/info/exclude`)
and script the steps above. While installed, a plain `build.sh` in that repo
also builds against the local chain — remove the files once the upstream change is published.
