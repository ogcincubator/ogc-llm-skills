# View Plugins

The [bblocks-viewer](https://github.com/opengeospatial/bblocks-viewer) renders a few content-based
visualizations out of the box — a map view for GeoJSON, a 3D view, and a web view for HTML content.
A **view plugin** lets a register add its own custom visualization for example snippets or
transform outputs, without that code living inside the viewer itself.

A view plugin is a small client-side ES module the viewer loads at runtime (`import()`) and matches
against the resolved content of an example snippet or transform output. If it matches, the viewer
adds an extra tab that renders the plugin's own view. This is a purely client-side mechanism —
distinct from [transform plugins](transform-plugins.md) / [validator plugins](validation-plugins.md),
which run server-side in the postprocessor.

---

## Declaring plugins in a register

```yaml
# bblocks-config.yaml
viewer:
  view-plugins:
    - url: https://example.org/my-plugin/dist/index.js
      export: MyPlugin   # optional
      weight: 100         # optional
```

- `url` (required) — the plugin's ES module URL, fetched via a runtime `import()`. Must be served
  with permissive CORS (GitHub Pages does this by default).
- `export` (optional) — which export(s) to use as plugin classes: a single name, an array of names
  (to pull in several plugin classes from one bundle), or omitted/`null`/`""`/`[]` for the module's
  default export.
- `weight` (optional, default `0`) — controls tab ordering among plugin tabs; higher sorts earlier.
  The viewer's own built-in plugins (map/3D/web) always sort first regardless of `weight`.

This is written through to `register.json` as `viewer.viewPlugins` (kebab-case → camelCase, same
pattern as `show-imported-depth` → `showImported`; see [register-config.md](register-config.md)).
Multiple config entries can point at the same `url` with different `export` values — the browser's
module cache dedupes the actual fetch by URL.

Only the local register's own `viewer.view-plugins` is consulted; imported registers' plugins are
never loaded. Declaring a plugin's URL is equivalent to embedding a `<script>` on a page you
control — no sandboxing is applied, so only point at code you trust.

### Out-of-the-box plugins

The viewer's built-in map, 3D, and web views are themselves ordinary view plugins, published as
[bblocks-viewer-base-plugins](https://github.com/ogcincubator/bblocks-viewer-base-plugins):

| Export | Matches | Notes |
|---|---|---|
| `GeoJsonMapPlugin` | `application/geo+json`, `application/json`, `application/ld+json` content that parses as a GeoJSON `Feature`/`FeatureCollection` with geometry | Leaflet map; semantically-enriched popups when a JSON-LD context is available (via `context.bblock.ldContext`, falling back to the content's own inline `@context`). |
| `ThreeDPlugin` | Same types, content containing 3D geometry (GeoJSON with Z coordinates, or a CityJSON-like topology) | Three.js scene with orbit controls and grid/wireframe/edges/vertices toggles. |
| `WebViewPlugin` | `text/html` content with an absolute `http(s)://` url | Sandboxed iframe pointed at the url. |

These ship with the viewer automatically — a register does **not** need to declare them. Declare
`bblocks-viewer-base-plugins` explicitly (as in the config example above, pointed at its built
`dist/index.js` with `export: [GeoJsonMapPlugin, ThreeDPlugin, WebViewPlugin]`) only if you want one
of these visualizations for a media type it doesn't match by default.

---

## Writing a view plugin

Start from [bblocks-view-plugin-starter](https://github.com/ogcincubator/bblocks-view-plugin-starter)
(usable as a GitHub template, or `git clone`d directly). It provides a minimal plugin skeleton in
both TypeScript and JavaScript, two complete worked examples (a JSON tree view, a CSV table view),
the full interface as types (`src/view-plugin.d.ts`), and a Vite build producing a single deployable
`dist/index.js`.

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
interface ViewPluginCandidate {
  type: string | null;     // resolved MIME type, e.g. 'application/geo+json'; never a bare
                            // language slug — the host resolves it, or passes the raw declared
                            // value through verbatim if no MIME type is known
  content: string | null;  // resolved text, or null if not (yet) available
  url: string | null;      // absolute URL the content was (or would be) fetched from, if any
  label: string;           // human-readable label (snippet language, or transform id) — UI only,
                            // not meant for matching logic
}

interface ViewPluginContext {
  bblock: Record<string, unknown> | null;       // full bblock (json-full shape); null if unavailable
  viewerConfig: Record<string, unknown> | null;  // viewer's resolved runtime config; null if unavailable
}

interface ViewPluginInstance {
  // Content-based filter, for when the static supportedTypes soft filter isn't precise enough
  // (e.g. "the type says application/json, but does it actually parse into what I need?"). Only
  // called for candidates whose content resolved. Return false to withdraw the match entirely (no
  // tab added). Omit this method to always match once the static type filter passes. Takes no
  // arguments — it's a yes/no on the whole instance (which already has all candidates from the
  // constructor), not a per-candidate filter.
  matches?(): boolean;

  // el: an empty <div> the plugin owns, sized to the viewer's plugin-tab chrome (small box with a
  // fullscreen toggle the host provides). May be async — the host awaits it before treating the
  // tab as ready.
  render(el: HTMLElement): void | Promise<void>;

  // Optional teardown when the tab/component unmounts. Not called automatically on re-render, only
  // on actual unmount.
  destroy?(el: HTMLElement): void;
}

interface ViewPluginClass {
  // Constructed fresh per matching candidate set — never a global singleton, never reused across
  // examples/transform-outputs. This lets a plugin do content inspection during construction (see
  // matches()) and reuse whatever it computed (parsed data, detected geometry) during render(),
  // without re-parsing.
  new(candidates: ViewPluginCandidate[], context?: ViewPluginContext): ViewPluginInstance;

  // Soft filter: MIME types this plugin might handle, checked against each candidate's `type`
  // BEFORE the class is instantiated. Supports wildcards ('text/*', '*/*'). Required — a class
  // with no overlapping type is never instantiated (its constructor/matches()/render() never run).
  supportedTypes: string[];

  // Tab label. Falls back to the class name if omitted.
  viewName?: string;

  // MDI icon name (e.g. 'mdi-map') for the tab. Falls back to 'mdi-puzzle-outline' if omitted.
  icon?: string;
}
```

`candidates` always holds every available representation of the same underlying content — one
entry per example snippet language, or a single-element array for a transform output — nothing is
pre-filtered to "the best one." A plugin picks whichever candidate(s) it wants in the constructor.
`content` can be `null` even for a matching `type` (the host resolves content on a best-effort
basis before matching runs); a plugin should treat a null-content candidate as unusable rather than
attempting its own fetch of `url`.

### Host-side matching flow

1. Every declared plugin module is `import()`-ed unconditionally (not gated on any config-level
   type hint) — cheap in practice since the browser's module cache dedupes the fetch per session.
2. Soft filter: the class's `static supportedTypes` is checked against the candidates' types. If no
   overlap, the class is skipped entirely — never instantiated.
3. If there's overlap, the class is instantiated with all matching candidates and the context object.
4. `matches()` is called (default `true` if unimplemented). If it returns `false`, the plugin is
   skipped — no tab added.
5. Otherwise a tab is added; `render(el)` runs when the tab is activated.
6. A plugin that throws during construction, `matches()`, or `render()` is logged to the console and
   skipped — never breaks the rest of the match pass or any other plugin's tab.

### Validating whether a candidate plugin implementation is correct

To check whether some given JS/TS source is a valid view plugin (e.g. before recommending it, or
after generating one), verify:

- It's a genuine ES module (`export`/`export default`) — no IIFE/UMD/global-script form is
  supported.
- The exported class (or each named export listed in `export:`) has a non-empty static
  `supportedTypes` array of MIME-type strings (wildcards `'text/*'`/`'*/*'` allowed).
- The constructor accepts `(candidates, context)` and does not throw for an empty or
  partially-null-content `candidates` array — the constructor may run before content resolves.
- If `matches()` is implemented, it takes no arguments and returns a plain boolean synchronously.
- `render(el)` mounts into the given element (directly, or via `el.appendChild(...)`) — it must not
  assume any host CSS framework (Vuetify, Material icons) is available, since the plugin runs
  outside the host's component tree.
- Any third-party dependency is imported from within the module itself (bundled, or lazily
  `import()`-ed inside `render()`), not assumed to be a global provided by the host page.
- If the plugin injects CSS, it does so via a **static**, top-level `import css from './file.css?raw'`
  guarded against duplicate injection — a *dynamic* `import()` of a `?raw` CSS asset is rejected by
  the browser (most static hosts serve it with a Content-Type that fails module-script MIME
  checking).

### Third-party dependencies

Bundle dependencies into the plugin's own module rather than assuming the host viewer provides
them — a plugin is a self-contained embeddable widget, not code sharing the host app's runtime.
Import heavy dependencies (mapping/3D libraries, parsers) lazily, inside `render()`, so they're only
downloaded once a plugin that needs them actually renders:

```js
class MyPlugin {
  async render(el) {
    const { default: L } = await import('leaflet');
    // use L
  }
}
```

A lightweight top-level import is fine — every declared plugin module gets imported unconditionally
just to read `static supportedTypes`, so this only matters for genuinely heavy dependencies.

### Injecting CSS

A plugin can't rely on a host `<link>` tag — it injects its own `<style>` element at runtime, via a
static top-level `?raw` import:

```js
import css from './my-plugin.css?raw';   // must be static, not inside render()

let injected = false;
function injectCss() {
  if (injected) return;
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);
  injected = true;
}
```

### Building and testing

```bash
npm run build
```

Produces `dist/index.js` plus separate chunk files for any lazily-imported dependency. **Deploy the
whole `dist/` directory together** — chunk files are fetched relative to `index.js`'s own URL.

For local testing, serve `dist/` from any static file server (same-origin as the register/build
directory being previewed is simplest) and point a local viewer instance's register config at it. A
GitHub Gist's raw URL does **not** work as a plugin source (served as `text/plain` regardless of
extension, rejected as a module script by the browser) — use a real repository (e.g. GitHub Pages)
instead.

### Reference material

- [bblocks-view-plugin-starter](https://github.com/ogcincubator/bblocks-view-plugin-starter) —
  starter template: skeleton plugins, two worked examples, typed interface, build setup.
- [bblocks-viewer-base-plugins](https://github.com/ogcincubator/bblocks-viewer-base-plugins) — the
  viewer's own map/3D/web-view plugins, a larger real-world reference against the same interface.