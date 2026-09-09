# Changelog

## Round 2 — targeted defect sweep (PageSpec ↔ contract alignment, assets, compatibility graph)

This repo had no CHANGELOG.md before this entry — it is created here for the first time.
Three parallel research-only audits (tokens/assets/LLM-allowlist, sections-vs-PageSpec-schema,
templates-vs-compatibility-graph) surfaced 50 raw findings; the fixes below are the subset
confirmed as real contract violations, applied directly to the repo's JSON files. A handful of
findings were deliberately left unfixed — see "Deferred" below — because forcing a fix would
have meant inventing UI/data that was never actually measured on the live site, which this
repo's own stated principle ("measured, not guessed") rules out.

### schema/pagespec.schema.json — 43 fixes

**Missing required fields** (the section's own `contentModel.required` in `sections/*.json`
already required these; PageSpec had silently made them optional):
`site-header.signInLink`, `hero-product.eyebrow`+`description`, `hero-campaign.eyebrow`+
`description`, `hero-narrative.category` (see rename below), `hero-home.description`,
`related-products-grid.eyebrow`, `feature-box.eyebrow`, `contact-form-panel.description`,
`infrastructure-feature-grid.eyebrow`, `audience-selector-tabs.eyebrow`,
`product-grid-panel.eyebrow`, `trust-logo-band.eyebrow`.

**Missing properties entirely** (the section or its component declared these; PageSpec had no
field for them at all): `hero-home.brandName` (required string), `final-cta-footer.logo`
(required string), `site-footer.logo` (required string), `contact-form-panel.companyLogos`
(optional array), `feature-box.visual.alt` (optional string), `workflow-feature-panel.bulletList`
(optional array, mirroring the near-identical `benefit-narrative.bulletList`),
`blog-index-grid.posts[].thumbnail` (optional, matches `components/blog-post-card.json`).

**Field-name mismatches vs. the real component** (renamed PageSpec's side to match — the
component contract is the source of truth): `hero-narrative.eyebrow` → `category` (matches
`sections/hero-narrative.json`'s own field name), `customer-quote-panel.companyLogo` → `logo`
(matches `components/testimonial-panel.json`'s `logo` prop), `case-study-carousel.cards[]`:
removed the invented `attribution` object (absent from `components/case-study-card.json`),
replaced with `logo: {assetRole, alt}` (the field the component actually defines).

**Wrong min/maxItems vs. the section's own stated range**: `site-header.navLinks` 3–6 → exactly
4 (section requires `navLinks[4]`), `final-cta-footer.footerSitemap` unbounded → exactly 4,
`site-footer.footerSitemap` unbounded → exactly 4, `stats-band.stats` min 2 → min 3,
`logo-credentials-band.items` no max → max 6, `faq-accordion.items` no max → max 8,
`infrastructure-feature-grid.items` no max → max 8, `audience-selector-tabs.tabs` no max → max
6, `trust-logo-band.logos` no minimum at all → min 3, `product-grid-panel.products` min
3/no max → min 10/max 17 (the sharpest gap found — the section requires 10–17 products,
PageSpec would have accepted as few as 3).

**Copy-paste maxWords errors**: `product-cross-sell-panel.heading`/`.body` and
`dashboard-preview-panel.heading`/`.body` both carried the exact same `10`/`90`
`x-maxWordsRoleBound` values as the adjacent `workflow-feature-panel` block — corrected to
`8`/`60` and `8`/`40` respectively (each section's own real cap). `hero-product.eyebrow` and
`stat-callout-panel.stats[].value` both had a stray `4` where the section/component contract
says `3` — corrected.

**Missing accessibility enforcement**: `hero-product.heroVisual` is now required, and its `alt`
is now required with `minLength:1` (was a plain optional string, contradicting
`sections/hero-product.json`'s own `accessibility.altText` note that this alt is required —
now matches the pattern already correctly used by `dashboard-preview-panel.screenshot.alt`).

**Bare-string asset references converted to the structured `{assetRole, alt}` pattern** used
elsewhere in the same schema (`heroVisual`, `visual`, `companyLogo`/`logo`, `screenshot`):
`site-header.logo`, `logo-credentials-band.items[].logoOrLabel`, `trust-logo-band.logos[]`,
`related-products-grid.products[].icon`, `infrastructure-feature-grid.items[].icon`,
`product-grid-panel.products[].icon`.

**Item-level required fields added**: `product-cross-sell-panel.products[]` had no `required`
array at all (an empty `{}` would have validated) — added `required: ["title","href"]`.

`schema/example.pagespec.json` was updated to match every shape change above (site-header logo
now an object, related-products-grid icons now objects, final-cta-footer now has a `logo` and 4
footer-sitemap columns).

### compatibility/graph.json — 4 fixes

- `rhythm.heroRequiredUnless` was missing two templates that genuinely have no hero section
  by design (`blog-post`, a `site-header` + `long-form-content` page; `protected-deposits-page`,
  a `site-header` + `benefit-narrative`/`comparison-table-panel`/`faq-accordion` page) — both
  added to the exemption list.
- `adjacency.benefit-narrative.canPrecede` was missing `contact-form-panel`, which
  `templates/campaign-product-page.json` actually places directly after it — added.
- `adjacency.sticky-feature-showcase.canPrecede` was missing `product-cross-sell-panel`, which
  `templates/narrative-landing-page.json` actually places directly after it — added.

### assets/asset-roles.json — 2 fixes

- `blog.author`'s usage note claimed it was an "author avatar" used by `blog-post-card` and
  `long-form-content` — but neither component/section has an image field for it (both model
  `author` as plain text). Reworded the usage note to state this accurately and flag it for a
  future design decision (add a real avatar field, or retire the asset) rather than leaving a
  false claim in place.
- Added a `blog.thumbnail` role for `components/blog-post-card.json`'s existing `thumbnail`
  prop, which had no asset-role entry at all.

### components/stat-tile.json — 1 fix

- `props.value` referenced typography role `display.hero`, which does not exist anywhere in
  `tokens/10-semantic/typography-roles.json`. Changed to `heading.xl` (the closest real role;
  the component's own tighter `maxWords 3` override is preserved on top of it, same pattern
  used elsewhere in this repo for narrowing a role's default bound).

### Deferred (flagged, not force-fixed)

- **`customer-quote-panel.attribution`**: PageSpec models it as a structured
  `{name, role, company}` object; the component (`testimonial-panel.json`) declares it as a
  flat `Text role=label.md, maxWords 6` string. Both shapes appear intentional at different
  layers (PageSpec wants structured fields; the component measures it as rendered text) — fixing
  this requires a design decision about which is authoritative, not a mechanical rename.
- **`stat-tile.json` vs `stats-band` maxWords disagreement**: the shared `stat-tile` component
  says `value` maxWords 3; `stat-callout-panel` agrees (fixed above), but `stats-band` had
  already set its own override to 4 before this pass. This is a genuine cross-section
  disagreement about the same component's contract, left for the component-contract owner to
  resolve rather than silently picking a side.
- **`logo-credentials-band`'s stale `componentRefs`**: the section file points at
  `components/logo-band.json`, whose declared shape (`eyebrow` + `logos: Image[]`) doesn't match
  the section's real contract (`items[3..6]: {logoOrLabel, sublabel}`, which PageSpec correctly
  implements). This is a stale reference inside the section file itself, not a PageSpec defect.
- **`product-cross-sell-panel`/`blog-index-grid` component prop drops**: `components/product-
  card.json` declares `icon`/`description` props that neither the section contract nor PageSpec
  actually exposes; `components/blog-post-card.json` has no `href` prop even though every
  consumer (PageSpec, the section contract) requires one. Both are cross-file component/section
  disagreements about scope, not schema bugs — flagged for the component-contract owner.

### Verification

- `python3 verification/verify_all.py` — 5-part sweep, **all clean** (92/92 JSON files parse,
  0 dangling refs, allowlist⇄registry parity holds both directions, 0 maxWords/role-ceiling
  violations, 0 phantom template/graph references).
- `python3 schema/validate_schema.py` — the repo's existing 8-case adversarial suite, **8/8
  still pass** after these changes (nothing regressed).
- `python3 verification/round2_adversarial_tests.py` — **10 new cases added this pass**, one
  per major fix category (missing-required, item-count bounds, bare-string→asset-ref,
  footer-logo, cross-sell item shape), **10/10 pass**.
- `schema/example.pagespec.json` re-validated clean against the updated schema (0 errors).
- A full re-run of the templates-vs-graph rule check (alwaysFirst/alwaysLast, mutually
  exclusive, hero-follows-header, maxOnePerPage, onlyOnHomepage/BlogIndex/etc.,
  adjacency.canPrecede, maxConsecutiveSameType) across all 10 `templates/*.json` files: **0
  issues remaining** (was 4 before this pass).

## Round 3 — adversarial recheck (self-containment, semantic validation, escape hatches, packaging)

Round 2 fixed PageSpec↔contract shape mismatches but left several categories unexamined:
whether the repo and its verification tooling are actually self-contained; whether
compatibility/graph.json's rules are enforced by anything that keeps running, or just a
one-off manual audit; whether the `{assetRole, alt}` pattern Round 2 introduced actually
constrains `assetRole` to real roles; whether `x-maxWordsRoleBound` is enforced anywhere;
and packaging hygiene. This pass extracted the repo's own zip into an isolated `/tmp`
directory with no sibling folders and tried to break it, the way a skeptical frontend lead
would. Every fix below is proven with a passing/failing adversarial test, not just prose.

### 1. Self-containment — P0, fixed

**Found:** `verification/verify_all.py`, `schema/validate_schema.py`, and
`verification/round2_adversarial_tests.py` all hardcoded
`REPO = "/Users/riyaghosh/Projects/dt&ai/design-repo"` as an absolute path. Proof this is a
real, not theoretical, problem: the repo's own zip was extracted into
`/tmp/dtai_extract_test2/design-repo` (isolated, no sibling folders), a JSON file was
deliberately corrupted **only in that extracted copy**, and `verify_all.py` was run *from
that copy* — it printed `=== ALL CHECKS CLEAN ===` anyway, because the hardcoded path made
it silently re-read and re-validate the ORIGINAL repo at the author's absolute path instead
of the broken copy it was actually invoked from. On a machine without that exact path (or
CI, or a teammate's checkout) the scripts would instead hard-crash with `FileNotFoundError`.
Either way, the "self-contained, verifiable" promise these scripts exist to make was false
for anyone other than the original author on the original machine.

**Fixed:** all three scripts now derive `REPO` from `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
— the script's own location — never a hardcoded path. Re-proved clean: extracted a fresh
copy to `/tmp`, ran `verify_all.py` from inside it (clean), corrupted
`schema/example.pagespec.json` in that copy only (now correctly reported as a PARSE ERROR
against the real broken file), restored it (clean again). Also softened absolute,
machine-specific paths in `README.md` (the wireframe-serving `cd` command, the intro
paragraph) and `assets/README.md` (a reference to the sibling source-build folder) so the
docs read correctly regardless of whose machine or username the repo is checked out under.

**Reviewed and NOT changed (by design, not oversight):** `assets/asset-roles.json`'s `path`
values (e.g. `assets/images/`, `assets/clips/`) describe where the *real* 156 images + 12
video clips (~1.7GB) live in the source Gatsby build, one directory above this repo — they
are intentionally not vendored here. `assets/README.md` already documents why: a PageSpec
only ever references an asset by **role**, never a literal file path (see "Why roles, not
files" in that file), so this repo's own validity (schema + verification scripts) never
needs those binaries to exist locally. Vendoring ~1.7GB of clips into a JSON-Schema spec
repo would contradict the repo's own stated purpose. This was inspected, not assumed.

### 2. Semantic/structural PageSpec validation — P0, fixed

**Found:** JSON Schema cannot express "exactly one node of this type," "must be
first/last," "must precede/follow," or rhythm limits — that's exactly why
`compatibility/graph.json` exists. But grepping every `*.py` file in the repo for the rule
names it declares (`alwaysFirst`, `maxOnePerPage`, `canPrecede`, etc.) returned **zero
hits** before this pass, despite Round 2's own CHANGELOG entry claiming "a full re-run of
the templates-vs-graph rule check... 0 issues remaining." That re-run was a one-off manual
pass with no persisted script — nothing would have caught a future template edit that
silently violated the graph's own rules.

Manually testing the 3 required mutations against `schema/example.pagespec.json` with
`jsonschema.Draft7Validator` confirmed the gap precisely as expected: duplicating the
`maxOnePerPage` node `customer-quote-panel` validates cleanly; removing `site-header` and
`final-cta-footer` (`alwaysFirst`/`alwaysLast`) validates cleanly; reordering
`related-products-grid`/`final-cta-footer` (breaking `adjacency.canPrecede`) validates
cleanly. Schema validation alone catches none of the 3.

While building the checker to close this gap, running it against every `templates/*.json`
surfaced a second, real, previously-invisible defect: `templates/blog-index.json`,
`templates/blog-post.json`, and `templates/long-form-page.json` all ended their `nodes` list
without a footer, silently violating `rules.alwaysLast`. This was not one of README's
documented "Known gaps" (that section only excuses `protected-deposits-page.json` and
`templates/simple-page.json`, which measured no footer landmark on purpose). Checking the
live served build directly confirmed all three DO render a real footer
(`Footer__FooterEnd`/`Footer__ListLink`/etc. classes present in
`/blog/index.html`, `/blog/co-rate-exportation/index.html`, `/changelog/index.html`,
`/svb-update/index.html`) — so this was a genuine, measured, fixable omission, not a case
requiring an invented/unmeasured UI decision.

**Fixed:**
- Added `verification/graph_rules_check.py` — a persisted, re-runnable implementation of
  every rule category in `compatibility/graph.json` (`alwaysFirst`, `alwaysLast`,
  `mutuallyExclusive`, `heroTypes`/`heroMustFollowHeader`, `maxOnePerPage`, `onlyOnHomepage`/
  `onlyOnChangelogOrSvbUpdateOrBlogPost`/`onlyOnBlogIndex`, `adjacency.canPrecede`,
  `rhythm.maxConsecutiveSameType`, `rhythm.minSectionsPerPage`, `rhythm.heroRequiredUnless`)
  against an ordered sequence of section types. Wired into `verify_all.py` as check `[6]`
  and run against `schema/example.pagespec.json` and all 10 `templates/*.json` files.
- Added a trailing `site-footer` node to `templates/blog-index.json`,
  `templates/blog-post.json`, and `templates/long-form-page.json`, each with a `notes` entry
  citing the live-build evidence. Updated `compatibility/graph.json`'s `adjacency` so
  `long-form-content`/`blog-index-grid` can precede `site-footer` and `site-footer` can
  follow them.
- Added `rules.alwaysLastUnless: ["protected-deposits-page", "simple-page"]` to
  `compatibility/graph.json` — a documented exemption list (mirroring the existing
  `rhythm.heroRequiredUnless` pattern) for the two templates README's Known Gaps section
  already says were deliberately measured without a captured footer boundary. Without this,
  the new checker would either force-add an unmeasured footer to those two (violating
  "measured, not guessed") or the checker itself would need to stay silently wrong forever.
- `verification/verify_all.py`'s existing check `[5]` (phantom typeId resolution) was
  updated to exclude `alwaysLastUnless` from its typeId scan, since that key holds template
  ids, not section typeIds (the same treatment `rhythm.heroRequiredUnless` already got by
  living outside the `rules` dict).

Proven in `verification/round3_adversarial_tests.py`: all 3 required mutations now show
schema-silent/checker-catches for each category (duplicate maxOnePerPage, missing
alwaysFirst+alwaysLast, illegal reorder), plus a clean-baseline check.

### 3. Escape-hatch enum verification (`assetRole`) — P0, fixed

**Found:** every `assetRole` field Round 2 converted to the `{assetRole, alt}` structured
pattern (19 occurrences across `schema/pagespec.schema.json`) was left as a bare
`{"type": "string"}` — **zero** of them had an `enum` constraining the value to a real role
in `assets/asset-roles.json`. Round 2 fixed the *shape* (object vs. bare string) but not the
*content* — an LLM could still write `"assetRole": "anything-it-invents"` and pass
validation. Confirmed programmatically: `assetRole enum: None` at all 19 locations before
this fix.

While mapping each field to its correct role (cited against `assets/asset-roles.json`'s own
`usage` notes and the matching `components/*.json` prop docs), 8 further phantom fields
turned up with **zero basis** in either the section's `contentModel` or its
`generation.componentRefs` — fields an LLM could add that have no connection to anything
actually measured on the live site:
- `hero-campaign.heroVisual`, `hero-narrative.heroVisual` — neither section's `contentModel`
  or `componentRefs` mention an image at all (componentRefs are Text/Button/Badge only).
- `hero-simple.heroVisual`, `hero-simple.eyebrow` — `hero-simple.json`'s own purpose text is
  "short headline, **no elaborate visual**"; `componentRefs` is `primitives/Text.json` only.
- `hero-home.heroVisual`, `hero-home.eyebrow` — `componentRefs` is Text+Button only, no
  Image; `contentModel.required` lists exactly `brandName`/`headline`/`description`/
  `primaryCta`/`secondaryCta`, no `eyebrow`.
- `dashboard-preview-panel.visual` — a second, undocumented field sitting alongside the
  section's one real, required `screenshot` field; `contentModel` never mentions `visual`.
- `product-cross-sell-panel.visual` — `contentModel.required` is exactly
  `heading`/`body`/`products[]: {title, href}`; no `visual` anywhere.

This gap was compounded by a repo-wide systemic issue found while investigating it:
`additionalProperties` was **never used anywhere** in `schema/pagespec.schema.json` (0
occurrences across all 75 object schemas). Every object in the document — page-level, node
content, nested objects like `primaryCta`/`footerSitemap` items — silently accepted any
extra property an LLM chose to add, with no rejection. This is a far larger escape hatch
than `assetRole` alone: it meant none of Round 2's or Round 3's "the field doesn't exist in
this schema" fixes were actually enforced as *closed* — a generator could just add the field
back under any name and still validate.

**Fixed:**
- Added a scoped `enum` to `assetRole` at all 14 fields with a real, documented role: e.g.
  `site-header.logo` → `["logo.wordmark"]`, `hero-product.heroVisual` →
  `["hero.illustration"]`, `customer-quote-panel.logo` → `["customer.logo"]`,
  `dashboard-preview-panel.screenshot` → `["dashboard.screenshot"]`,
  `blog-index-grid.posts[].thumbnail` → `["blog.thumbnail"]`, and 9 more — each cited to
  `assets/asset-roles.json`'s own `usage` text or the matching component's prop doc (see
  `/tmp` working notes / this session's tool history for the full per-field citation table).
- Removed the 8 phantom fields listed above from `schema/pagespec.schema.json` entirely.
- Added `"additionalProperties": false` to all 75 object schemas in
  `schema/pagespec.schema.json` (page level, node level, every per-type `content` block, and
  every nested object inside them). `schema/example.pagespec.json` re-validates with **0
  errors** against the fully locked-down schema, confirming the example was already 100%
  compliant with real fields only.

Proven in `verification/round3_adversarial_tests.py`: a made-up `assetRole` string is now
rejected; a real-but-wrong-for-that-field role (`customer.logo` on `hero-product.heroVisual`)
is now rejected; the correct role still validates; re-adding a removed phantom field
(`hero-simple.heroVisual`) is now rejected via `additionalProperties: false`.

### 4. Open-ended tint/palette references — not applicable, checked

`schema/pagespec.schema.json` has no color/tint/palette field anywhere — `theme` is the only
color-adjacent field and it's already a single-value `enum` (`["dtai-light"]`, Round 2).
Color is fully derived from the theme token, never authored per-instance in a PageSpec.
Also checked `schema/example.pagespec.json` field-by-field for the sibling-repo bug pattern
(a fake placeholder reference-path string used as if it were a real resolved value in some
field): none found. The dotted `tokens.10-semantic.motion-roles.roles.*` strings under
`motion.role` are reference paths used *by design* (see `assets/README.md`'s "Why roles, not
files" — the repo's own stated methodology is to reference tokens/roles by canonical path,
never a raw resolved value), not a masquerading placeholder.

### 5. Reduced-motion / animation documentation accuracy — 1 real inaccuracy found and fixed

Cross-checked every claim in `tokens/10-semantic/motion-roles.json` against the actual
served build (`grep`'d for `prefers-reduced-motion`/`matchMedia` across every `*.js` bundle
and `assets/tokens/tokens.css` in the source build one directory above this repo).

- The global claim ("every role resolves to the tokens.css `@media (prefers-reduced-motion:
  reduce)` block: `animation-duration`/`transition-duration` forced to `0.01ms`,
  `scroll-behavior: auto`") is **verified accurate** — `assets/tokens/tokens.css` lines
  425-434 match exactly.
- `sticky.scrollLinked`'s claim (`sections/sticky-feature-showcase.json`:
  `"reducedMotionFallback": "REQUIRED — static stacked layout (position:sticky removed)..."`)
  is **verified INACCURATE**. `position: sticky` is a layout property, not an
  animation/transition duration, so the global tokens.css mechanism cannot affect it. A full
  search of the live property-management bundle
  (`component---src-pages-property-management-tsx-*.js`) found zero `matchMedia` calls and
  confirmed none of its several `@media (prefers-reduced-motion: reduce)` blocks touch the
  `position:sticky` declaration — they only reset `transform`/`opacity`/`transition` on
  unrelated decorative layers. The only thing that actually removes the sticky pin is an
  unrelated mobile viewport-width breakpoint.
- Other role-specific claims (`decorative.gradientHue`, etc.) rely only on
  animation/transition properties the global tokens.css rule *can* legitimately neutralize —
  no further inaccuracy found there.

**Fixed:** corrected `tokens/10-semantic/motion-roles.json`'s `sticky.scrollLinked` entry and
`sections/sticky-feature-showcase.json`'s `reducedMotionFallback` to state the verified
reality (the fallback is not implemented; this is an open accessibility gap) instead of an
unverified claim, and added a general caveat that the tokens.css mechanism only ever affects
animation/transition timing, never a persistent layout property like `position`.

### 6. maxWords enforcement scope — P0, fixed

**Found:** `x-maxWordsRoleBound` (72 occurrences in `schema/pagespec.schema.json`) is a
custom "x-" prefixed JSON Schema keyword — by convention, and confirmed by inspection of
every validator call site in this repo, standard JSON Schema validators (including this
repo's own `Draft7Validator` usage) treat it as a pure annotation and never enforce it.
Grepping every `*.py` file in the repo for `maxWordsRoleBound`/word-splitting logic returned
**zero hits**: nothing anywhere counted words in an actual content string against its
declared bound — not a runtime check on a hypothetical generated PageSpec, and not even a
static check on the one example this repo ships. (`verify_all.py`'s existing `[4] maxWords
vs typography-role ceiling` check is a different, narrower thing — it cross-checks each
*section's* declared `constraints.maxWords` against a typography-role ceiling *group*; it
never looks at a real string's word count.)

**Fixed:** added `verification/maxwords_check.py` — walks each node's matching schema
branch alongside its actual `content` payload, finds every field carrying
`x-maxWordsRoleBound`, counts words with `str.split()`, and flags overages. Wired into
`verify_all.py` as check `[7]`, run against `schema/example.pagespec.json` (0 violations —
the shipped example's real content is confirmed compliant, which was never actually checked
before). Proven in `round3_adversarial_tests.py`: blowing `hero-product.headline` (bound 12)
out to 30 words validates cleanly under schema alone (confirming the gap) and is caught by
`maxwords_check.py` (confirming the fix).

### 7. Typography role binding per field — not applicable, checked

PageSpec never exposes a freely-authorable "role" property on a text field (unlike
`motion.role`, which is a real per-instance field with a pattern constraint). Which
typography role a field renders with is fixed by the section/component contract at the
field's *position* in the schema (documented inline as `role=heading.lg` etc. in each
section's `contentModel`), not something an LLM chooses per instance in the generated
document. There is no field in the generated PageSpec where a wrong-but-differently-valid
role could be substituted — the escape hatch this category describes does not exist here.

### 8. Licensing/attribution consistency — not applicable, checked

No licensing section exists in `README.md`; `assets/asset-roles.json`'s two font roles
correctly and consistently cite `"license": "SIL OFL"`; `assets/README.md`'s note about the
`blog.author` role's unused status (fixed in Round 2) is consistent with its usage text. No
contradiction found between any README and any generated-vs-real-asset claim.

### 9. Manifest field-naming implying unearned approval — not applicable, checked

Searched every `*.json` file for `approved`/`pending`/`unreviewed`-style fields. The only
hit is `schema/pagespec.schema.json`'s `theme` enum description ("Only the single measured,
generation-approved production theme is enumerated...") — accurate prose describing a real,
singly-measured, singly-enumerated state, not a field name implying broader approval than
exists. No `registry.manifest.json` or equivalent with a field like `generationApprovedThemes`
sitting beside a pending/unreviewed status exists in this repo.

### 10. Packaging cleanliness — 1 real defect found and fixed

**Found:** the existing `/Users/riyaghosh/Projects/dt&ai/design-repo.zip` contains an
`__MACOSX` directory (880KB) when extracted — confirmed by extracting it into an isolated
`/tmp` directory and inspecting the result. No `.DS_Store` files were found inside it. No
`changeHistory`/`entryPoint`-style manifest field exists anywhere in this repo (there is no
such field to check for nullness).

**Fixed:** repackaged with command-line `zip`, explicitly excluding `__MACOSX` and
`.DS_Store` (via `COPYFILE_DISABLE=1 zip -X -r ... -x '*.DS_Store' -x '__MACOSX/*'`), saved
to `/Users/riyaghosh/Projects/UI repo/dt&ai/design-repo.zip`. Proven by extracting that new
zip into an isolated `/tmp` directory with no sibling folders and confirming (a) no
`__MACOSX`/`.DS_Store` present, and (b) `python3 verification/verify_all.py` run from inside
that extraction reports `ALL CHECKS CLEAN` against the files actually in the zip.

### Verification (Round 3)

- `python3 verification/verify_all.py` — now a **7-part** sweep (added `[6]` graph-rule
  enforcement, `[7]` maxWords runtime enforcement), **all clean**.
- `python3 schema/validate_schema.py` — **8/8** still pass (portability fix only; nothing
  regressed).
- `python3 verification/round2_adversarial_tests.py` — **10/10** still pass.
- `python3 verification/graph_rules_check.py` — **0 issues** across
  `schema/example.pagespec.json` and all 10 `templates/*.json` (was un-runnable/nonexistent
  before this pass).
- `python3 verification/maxwords_check.py` — **0 violations** against
  `schema/example.pagespec.json` (was never checked before this pass).
- `python3 verification/round3_adversarial_tests.py` — **14 new adversarial cases**, one or
  more per fixed category — **14/14 pass**.
- Self-containment re-proved end-to-end: repo's zip extracted to an isolated `/tmp` with no
  sibling folders, `verify_all.py` run from inside it — clean; a file corrupted in that copy
  only — correctly caught; restored — clean again.

### Deferred (flagged, not force-fixed)

- **`feature-box.visual`/`workflow-feature-panel.visual`/`product-cross-sell-panel`'s
  underlying `product-card` `icon`/`description` props, and `blog-post-card`'s missing
  `href`**: these are the same class of stale/mismatched `componentRefs` Round 2 already
  identified and deliberately left to the component-contract owner (see Round 2's
  "Deferred" section) — re-confirmed still present, not re-litigated as new PageSpec bugs.
- **`sticky.scrollLinked`'s missing real reduced-motion fallback** (section 5 above): the
  documentation is now accurate about what's NOT implemented, but the underlying
  accessibility gap in the live site itself (the sticky pin never respects
  `prefers-reduced-motion`) is a live-site engineering fix, not something a design-repo
  correction can implement — flagged for the component owner rather than force-inventing a
  fallback that was never built.
- **Per-field `assetRole` enums were scoped to a single best-documented role each**, not
  independently re-verified against every possible legitimate design variation (e.g.
  whether `feature-box.visual` might one day also legitimately accept `hero.illustration`
  for a larger campaign treatment). If a future section genuinely needs a second valid role
  for one of these fields, extending the `enum` list is a one-line schema change with an
  obvious blast radius — deferred rather than guessed at now.
