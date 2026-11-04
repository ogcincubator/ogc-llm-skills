# Relationships between blocks

Block-to-block relationships are fields on each `register.json` entry; there is no separate graph file.
This page lists every relationship type in a normalized form, so code can build, filter or draw a
dependency graph from them.

## Normalized relationships

```yaml
relationships:
  - field: isDescribedBy
    declared_on: the schema block
    direction: schema block -> model block
    register_json: array of bblocks:// URIs
    inverse_label: Describes            # computed from other entries; not stored
    implies_dependency: true            # target is also listed in dependsOn
    precedence: 1                       # lowest number = most specific
    directed: true
    viewer: {label: Described by, color: "#00897b", line: solid, arrowhead: true}
  - field: isProfileOf
    declared_on: the profile block
    direction: profile -> base block
    register_json: array of bblocks:// URIs
    implies_dependency: true
    precedence: 2
    directed: true
    viewer: {label: Profile of, color: blue, line: solid, arrowhead: true}
  - field: dependsOn
    declared_on: any block
    direction: block -> dependency
    register_json: array of bblocks:// URIs
    implies_dependency: true            # is the dependency set itself
    precedence: 3
    directed: true
    viewer: {color: "#aaa", line: solid, arrowhead: true}
  - field: hasFormat
    declared_on: each sibling
    direction: none (symmetric; declared on every sibling)
    register_json: array of identifiers
    implies_dependency: false
    directed: false
    viewer: {color: "#9c27b0", line: dashed, arrowhead: false}
  - field: extensionPoints.baseBuildingBlock          # "extends"
    direction: extending block -> extension base block
    register_json: bblocks:// URI
    implies_dependency: true
    directed: true
    viewer: {color: red, line: dashed, arrowhead: true}
  - field: extensionPoints.extensions                 # {source: target} map
    direction: "extensionTarget: extending block -> target block; extensionSource: target block -> source block"
    register_json: object of bblocks:// URIs
    implies_dependency: true
    directed: true
    viewer: {extensionTarget: {color: "#ff8e03"}, extensionSource: {color: "#ff5a5a"}, line: solid, arrowhead: true}
```

## Reading them

- **`dependsOn` is the complete set of direct dependencies.** Every `isProfileOf`, `isDescribedBy` and
  extension-point target is also in `dependsOn`, so walking `dependsOn` alone finds every dependency.
  Use the typed fields to learn *why* a dependency exists.
- **One relation per pair.** A pair of blocks can appear under several fields. To show or count a
  pair once, keep the field with the lowest `precedence` (`isDescribedBy`, then `isProfileOf`, then
  `dependsOn`).
- **Inverses are not stored.** To list the blocks a given block "describes", or that profile it or
  depend on it, scan the other entries for its identifier in their `isDescribedBy`, `isProfileOf` or
  `dependsOn`.
- **Identifiers.** The `bblocks://` prefix is part of the value; strip it to get the block identifier.
  `hasFormat` values are plain identifiers.
- **Inheritance.** A block inherits SHACL shapes and closure graphs through `dependsOn`,
  `isProfileOf` and `isDescribedBy` alike; `hasFormat` is not a dependency and inherits nothing.

## How the viewer shows them

The viewer's dependency graph draws one edge per relation, colored as in the table above, and the
block header shows `Described by` and `Profile of` as chips. Blocks whose `itemClass` is `model` are
drawn as a rounded square with a table cut-out. The viewer's source of truth for labels and colors is
`src/models/relations.js` in `bblocks-viewer`; treat the direction and precedence rules above as the
stable part, and the colors as presentation that may change.
