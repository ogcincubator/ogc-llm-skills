# Tab Plugins

A **view plugin** ([view-plugins.md](view-plugins.md)) adds a custom visualization for one example
snippet or one transform output. A **tab plugin** is a separate, parallel mechanism: it adds a
whole new top-level tab to a bblock's detail page, driven by the full bblock (and its register)
rather than a single piece of content. Reach for a tab plugin when what you want doesn't fit "one
visualization for one example" — a custom summary/report panel, a view over data a
[build plugin](build-plugins.md) stamped onto `json-full`, or a view over the bblock/register's own
metadata.

A tab plugin is a small client-side ES module the viewer loads at runtime (`import()`) and matches
against the whole bblock, once per bblock. If it matches, the viewer adds an extra tab, after every
built-in tab, that renders the plugin's own content full-page. This is a purely client-side
mechanism — distinct from [transform plugins](transform-plugins.md) / [validator
plugins](validation-plugins.md) / [build plugins](build-plugins.md), which all run server-side in
the postprocessor.

---

## Declaring plugins in a register

```yaml
# bblocks-config.yaml
viewer:
  tab-plugins:
    - url: https://example.org/my-plugin/dist/index.js
      export: MyTabPlugin   # optional
      weight: 100            # optional
```

- `url` (required) — the plugin's ES module URL, fetched via a runtime `import()`. Must be served
  with permissive CORS (GitHub Pages does this by default).
- `export` (optional) — which export(s) to use as plugin classes: a single name, an array of names
  (to pull in several plugin classes from one bundle — a single bundle can mix view-plugin and
  tab-plugin classes, declared separately under `view-plugins`/`tab-plugins`), or
  omitted/`null`/`""`/`[]` for the module's default export.
- `weight` (optional, default `0`) — controls ordering among other *tab* plugins matched for the
  same bblock; higher sorts earlier. Tab plugins always render after every built-in tab, regardless
  of weight.

This is written through to `register.json` as `viewer.tabPlugins` (kebab-case → camelCase, same
pattern as `view-plugins` → `viewPlugins`; see [register-config.md](register-config.md)). Multiple
config entries can point at the same `url` with different `export` values — the browser's module
cache dedupes the actual fetch by URL.

Only the local register's own `viewer.tab-plugins` is consulted; imported registers' plugins are
never loaded — same trust model as view plugins. Declaring a plugin's URL is equivalent to
embedding a `<script>` on a page you control — no sandboxing is applied, so only point at code you
trust.

There are no built-in tab plugins (unlike view plugins' map/3D/web) — every built-in tab
(About, Examples, Data structure, JSON Schema, OpenAPI, Ontology, Semantic uplift, Validation,
Transforms) is implemented directly in the viewer, not as a tab plugin.

---

## Writing a tab plugin

Start from the same [bblocks-view-plugin-starter](https://github.com/ogcincubator/bblocks-view-plugin-starter)
template used for view plugins — it includes two worked tab-plugin examples alongside the
view-plugin ones: `dependents-tab-plugin.js` (plain JS — a "Used by" reverse-dependency tab) and
`register-info-tab-plugin.ts` (TS+Vue — a "Register info" tab with a small piece of reactive
state). The full interface as types comes from
[bblocks-viewer-plugin-types](https://github.com/ogcincubator/bblocks-viewer-plugin-types) (see
`tab-plugin.d.ts`, alongside `view-plugin.d.ts` for the view-plugin contract), the canonical,
dependency-free source — same devDependency arrangement as view plugins.

```bash
git clone https://github.com/ogcincubator/bblocks-view-plugin-starter my-plugin
cd my-plugin
npm install
npm run typecheck   # if using TypeScript
npm run build       # -> dist/index.js
```

### Plugin interface

A plugin module exports one or more classes (default export, or named exports referenced by
`export` in `bblocks-config.yaml`). Each class must satisfy this contract:

```ts
interface TabPluginContext {
  bblock: Record<string, unknown>;         // full, already-fetched bblock (json-full shape)
  register: Record<string, unknown> | null; // full, already-constructed register object
  viewerConfig: Record<string, unknown> | null; // viewer's resolved runtime config
  depResolver?: DependencyResolver;  // optional shared-dependency cache; same mechanism as view plugins
  fetchDocument(bblock: Record<string, unknown>, property: string): Promise<unknown>;
  fetchDocumentByUrl(bblock: Record<string, unknown>, url: string, options?: {maxSize?: number}): Promise<unknown>;
  getBBlock(itemIdentifier: string): Promise<Record<string, unknown> | undefined>;
  getBBlocks(includeRemote?: boolean): Promise<Record<string, Record<string, unknown>>>;
}

interface TabPluginInstance {
  // Whole-context predicate deciding whether this plugin contributes a tab for this bblock — not
  // bound to checking a single named field; can test anything in context (a field's presence,
  // register metadata, bblock status/itemClass, etc). May be async — return boolean or
  // Promise<boolean>. Default true if unimplemented. A throwing/rejecting matches() is logged and
  // skipped (no tab), same posture as a throwing view-plugin matches().
  matches?(): boolean | Promise<boolean>;

  // el: an empty container the plugin owns for the *entire* tab body — not a small chrome-wrapped
  // box like a view plugin gets (no fullscreen-toggle chrome is provided; a plugin wanting
  // overlay/fullscreen behavior implements it itself). May be async.
  render(el: HTMLElement): void | Promise<void>;

  // Teardown. Called when the user navigates to a *different* bblock always; called on a
  // same-bblock tab switch only if the class declares `static cacheable = false` (see below).
  destroy?(el: HTMLElement): void;
}

interface TabPluginClass {
  // Constructed once per bblock, reused across repeated matches()/render() calls for that bblock —
  // unlike a view plugin, which is constructed fresh per matching candidate set.
  new(context: TabPluginContext): TabPluginInstance;

  // Route `section` slug and tab key. Recoverable if missing: the host synthesizes one by
  // slugifying tabLabel (or the module export name as a last resort), then runs it through the
  // same collision-suffix scheme described below — but declare it explicitly for a link stable
  // across rebuilds (same reason viewName is required for view plugins; never rely on the class
  // name itself, which a minified build can rename).
  tabId?: string;

  // v-tab display text. Required — unlike tabId, there's no sensible placeholder, so a class
  // missing this is skipped entirely (logged), not given a fallback.
  tabLabel: string;

  // MDI icon name (e.g. 'mdi-puzzle-outline') for the tab. Falls back to 'mdi-puzzle-outline' if omitted.
  icon?: string;

  // Ordering among other matched tab plugins for the same bblock. Default 0, higher sorts first.
  weight?: number;

  // Whether the instance + rendered DOM persist across same-bblock tab switches (true, default) or
  // are torn down (destroy()) the moment the tab is left and rebuilt (render()) on reactivation
  // (false). Set false only for something holding a live connection/poller that shouldn't keep
  // running in a backgrounded tab.
  cacheable?: boolean;
}
```

Unlike a view plugin, there's no `supportedTypes` soft filter and no per-candidate constructor
argument — a tab plugin is instantiated once per bblock with the whole `TabPluginContext`, and
`matches()` alone carries the whole decision (there's no cheap pre-filter to skip, since there's
only ever one instantiation to make per bblock per plugin).

### Host-side matching flow

1. Tab-plugin modules are `import()`-ed as soon as the register itself finishes loading (not
   lazily, unlike view plugins) — this races the plugin-module fetch in parallel with the user's
   first navigation instead of starting after it, narrowing (not eliminating) a pre-load flash on
   the very first bblock page visited in a session.
2. Once the full `json-full` bblock is fetched, every loaded tab-plugin class is instantiated with
   `(context)` and `matches()` is awaited, wrapped in a try/catch (log-and-skip on throw/reject —
   same soft-fail posture as view plugins, never breaks the page or another plugin's tab).
3. Each plugin whose `matches()` resolves `true` contributes one tab, sorted by `weight` after
   every built-in tab. All matching plugins get a tab — there's no "first match wins" for two
   plugins that both match the same bblock.
4. `tabId` collisions (against a built-in tab id, or another loaded plugin's `tabId`) are resolved
   deterministically: append the colliding plugin's module `export` name as a suffix
   (`my-tab--MyPlugin`), then a counter if that still collides (`my-tab--MyPlugin-2`) — never a
   silent last-write-wins overwrite.
5. On tab activation, `render(el)` runs into a bare container (no chrome). A synchronous throw from
   `render()` is caught: the host tears down whatever mounted and shows a visible error banner in
   the tab (plus a console error), same as a view plugin's `render()` throw. This only covers
   synchronous throws — an error from the plugin's own async code afterward is outside anything the
   host can catch.
6. `destroy()` fires when the user navigates to a different bblock, always. For a same-bblock tab
   switch, it fires only if the class declared `static cacheable = false`; otherwise the mounted
   instance/DOM persists untouched while the user is on a different tab (`cacheable: true` is the
   default).

### Validating whether a candidate plugin implementation is correct

To check whether some given JS/TS source is a valid tab plugin (e.g. before recommending it, or
after generating one), verify:

- It's a genuine ES module (`export`/`export default`) — no IIFE/UMD/global-script form is
  supported.
- The exported class (or each named export listed in `export:`) has a non-empty static `tabLabel`
  string — a class missing it is skipped by the host with a console warning. `tabId`, unlike
  `tabLabel`, is optional (the host synthesizes one if missing), but a real plugin should still set
  it explicitly rather than relying on the fallback.
- The constructor accepts a single `context` argument (not `(candidates, context)` like a view
  plugin) and does not throw for a context whose `register` is `null` (a bblock in a register the
  viewer couldn't fully resolve) — a tab plugin should treat that as "no register info available,"
  not assume it's always populated.
- If `matches()` is implemented, it returns a plain boolean or a `Promise<boolean>` and takes no
  arguments — it must not expect `el` (matching is a pure decision step, no DOM access).
- `render(el)` mounts into the given element (directly, `el.appendChild(...)`, or by mounting a
  framework root into it) and does not assume any host CSS framework (Vuetify, Material icons) is
  available, since the plugin runs outside the host's component tree — same constraint as a view
  plugin.
- If `static cacheable = false` is declared, `destroy(el)` actually releases whatever `render(el)`
  set up (event listeners, timers, a live connection/poller) — this is the whole point of opting
  out of the default cacheable behavior; a plugin that declares `cacheable: false` but leaves
  something running past `destroy()` defeats its own purpose.
- Any third-party dependency (including a UI framework, if the plugin mounts one — `render(el)` is
  a plain DOM-element handoff, so `createApp(...).mount(el)`/React's
  `createRoot(el).render(...)` are both valid) is bundled into the module itself or lazily
  `import()`-ed, not assumed to be a global the host page provides. See view-plugins.md's "Third
  party dependencies" / "Sharing a dependency via `context.depResolver`" / "Injecting CSS" sections
  — all of that guidance applies identically here, just substitute `TabPluginContext` for
  `ViewPluginContext`.

### Building and testing

Identical to view plugins — see [view-plugins.md](view-plugins.md#building-and-testing) for the
`npm run build` output shape, local-testing setup (same-origin static server, GitHub Gist raw URLs
don't work as a module source), and publishing `dist/` via jsDelivr. The only difference is which
`bblocks-config.yaml` key (`tab-plugins` vs `view-plugins`) the built `dist/index.js` gets declared
under.

### Reference material

- [bblocks-viewer-plugin-types](https://github.com/ogcincubator/bblocks-viewer-plugin-types) —
  the canonical, single-source-of-truth, dependency-free type contract for both mechanisms
  (`tab-plugin.d.ts`'s `TabPluginContext`/`TabPluginInstance`/`TabPluginClass`, alongside
  `view-plugin.d.ts`'s view-plugin equivalents).
- [bblocks-view-plugin-starter](https://github.com/ogcincubator/bblocks-view-plugin-starter) —
  starter template: the two tab-plugin worked examples described above, alongside the view-plugin
  skeleton/examples.
- [view-plugins.md](view-plugins.md) — the parallel mechanism this document deliberately does not
  duplicate guidance from (dependency bundling, CSS injection, publishing).
- [build-plugins.md](build-plugins.md) — a build plugin that stamps a new field/document onto a
  bblock's `json-full` output pairs naturally with a tab plugin that renders it, though the two
  mechanisms are independent — a tab plugin's `matches()` can key off anything, not only a field a
  build plugin added.
