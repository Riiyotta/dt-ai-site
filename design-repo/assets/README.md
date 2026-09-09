# Asset roles

This folder documents the *role* each asset group plays in the section and component
contracts defined in `../sections/` and `../components/` — not a raw file catalog. The
156 images + 12 clips + tokens.css / typography license files this role registry describes
live in the source Gatsby build's own `assets/` folder (one level above this repo, on the
machine where the original measurement pass was run) — deliberately NOT vendored into this
design-repo. At ~1.7GB of clips alone, copying every real binary asset into a JSON-Schema
spec repo would defeat the point of a lightweight, generation-facing role registry; a
PageSpec is only ever expected to reference an asset by its role (below), never by a literal
file path, so this repo never needs to open or ship the actual files to be self-contained for
its own purpose (validating and generating PageSpecs). See CHANGELOG.md's Round 3 entry for
the self-containment audit that reached this conclusion.

See `asset-roles.json` for the machine-readable role -> path -> usage mapping referenced
by `sections/*.json` `generation.componentRefs` / section `contentModel.optional.visual`
fields.

## Why roles, not files

A generated PageSpec references an asset by its **role** (e.g. `hero.illustration`,
`product.icon`), never a literal filename — the same way it references a token by
canonical path, never a raw hex value. This keeps generated pages portable across a
reskin or a new product launch without hardcoding today's specific image filenames.
