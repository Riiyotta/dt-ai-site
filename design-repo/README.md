# DT&AI Design Repository

An AI-ready, generation-facing design system extracted from a local Gatsby-build clone
of dtai.com (a fintech / banking-infrastructure marketing site) served from the directory
one level above this repo. Built by measuring the live-served build (`node serve.js 8080`),
not by reading source code or guessing. (Round 3 note: this repo is self-contained — every
file it validates against lives inside this folder; the sentence above describes where the
*source measurements* were originally taken from, on the original author's machine, not a
runtime dependency. See CHANGELOG.md's Round 3 entry and `verification/verify_all.py`,
which is proven to run correctly from any path, including an isolated extraction with no
sibling folders.)

**Status:** design-review-pending — see [`CHANGELOG.md`](CHANGELOG.md) for the audit
history. Round 2 found and fixed 50 real PageSpec↔contract/asset/compatibility-graph defects
(43 in `schema/pagespec.schema.json` alone). Round 3 was an adversarial recheck focused on
what Round 2 didn't cover — self-containment/portability, whole-document semantic rules
JSON Schema can't express, the `assetRole`/`additionalProperties` escape hatches, and
packaging hygiene — and found and fixed further real defects in each of those areas
(see CHANGELOG's Round 3 entry). A handful of findings across both rounds were deliberately
left unfixed pending a design decision — see each round's "Deferred" section rather than
assuming this repo has zero known gaps.

## What was measured

**Routes (34, not 29):** enumerated from Gatsby's own `page-data/` manifest (34
directories, including 9 under `page-data/blog/`), cross-checked against every
`<route>/index.html` present on disk and a live crawl of the homepage's nav/footer links.
Every route was confirmed HTTP 200 from `node serve.js 8080` before measurement. The
`component---src-pages-index-case-studies-*.tsx` bundles visible in the build's file list
are **not** separate routes — `/index-case-studies-account-card/` etc. resolve to a
byte-identical copy of the homepage (confirmed by diffing response bodies), because they're
interactive scene components rendered *inside* the homepage's case-study carousel, not
standalone pages.

Final route list: `/`, `/company/`, `/careers/`, `/press/`, `/security/`, `/changelog/`,
`/svb-update/`, `/blog/` + 8 posts, and 17 single-product pages (`/ach/`, `/wire/`,
`/international-wires/`, `/checks/`, `/book-transfers/`, `/realtime/`, `/card-programs/`,
`/bank-accounts/`, `/ledger/`, `/protected-deposits/`, `/correspondent-banking/`,
`/political-treasury/`, `/title-escrow/`, `/property-management/`, `/debt-financing/`,
`/loan-origination/`, `/loan-purchase/`).

**Tooling:** Playwright (Node), `chromium.launch({channel:'chrome', headless:true})`, at
three breakpoints — 1440x900, 810x1080, 390x844 — with a full programmatic lazy-scroll
pass on every page before extraction. `page.evaluate` tallied every visible text node's
computed font-family/size/weight/line-height/letter-spacing/color; every visible element's
background-color/border-radius/box-shadow/border/gap/padding/max-width/aspect-ratio/
grid-template-columns; the real section sequence (see below); every transition/animation
plus every CSSOM `@keyframes` rule; and every `position: sticky|fixed` element. Raw
per-route dumps and the aggregate tallies live in `extraction/measured-values.json`.

**A section-finding gotcha, and how it was fixed:** this build wraps the entire page in a
chain of single-child `<div>`s down through `#___gatsby` → `#gatsby-focus-wrapper` →
`Layout__Body`, so "walk down while there's exactly one visible child, then take that
node's children as sections" — the first approach tried — collapses the whole page into
one blob. The real section boundaries are `<header>` plus `<main>`'s direct children
(confirmed against the raw HTML: `<main>` wraps every page's content, and the on-page
footer lives as `<main>`'s last child rather than inside a semantic `<footer>` tag). The
measurement script was corrected to target those landmarks directly, and the full 34-route
x 3-breakpoint pass was re-run after the fix — the numbers in `extraction/` are from the
corrected run.

**Source-provided ground truth used directly, not re-derived:** the build ships
`assets/tokens/tokens.css` — 373 already-extracted, documented design-token declarations
(`--rgb-*`/`--color-*` channel-triplet indirection, `--text-*`/`--lh-*`/`--font-*` type
scale, `--space-*` 4px-step spacing scale, `--radii-*`, `--screen-*` breakpoints, `--form-*`
input tokens). Where this file and the live-measured computed styles agreed, `tokens.css`
was used as the 00-foundation source of truth and the measurement pass used to validate
and prioritize it (e.g. `--screen-lg` / 1112px is also the single most common measured
`max-width`, confirming it's the real content-container token).

## Key findings

- **Typography** is entirely Inter (300/400/500/600/700 weights) for UI/body text, plus
  two monospace stacks: `--font-mono` (JetBrains Mono, tokenized) for a handful of code
  callouts, and an **untokenized** `SFMono/"SF Mono"` stack that is in fact the single most
  frequent typography rule on the entire site (3,779+ measured uses at 12px/400) — it
  renders the syntax-highlighted tokens inside the homepage's live API request/response
  demo panel. Documented in `tokens/00-foundation/typography.json` and exposed as
  `code.inline`/`code.block` semantic roles.
- **Color** follows the source build's own `--rgb-*` → `--color-*` indirection (a hue
  changes in exactly one place); reused verbatim rather than renamed. The single most
  common `background-color` on the entire site (13,068 measured uses) is `--color-blue-400`
  — not a UI surface, but the fill of a repeated 8px circular (`border-radius: 50%`, 13,507
  uses) decorative halftone-dot pattern, DT&AI's signature background motif (the source
  build even ships two demo pages for it: `dot-halftone-art-demo`/`dot-halftone-test`).
- **Motion:** no motion tokens exist in `tokens.css` (the source build inlines every
  duration/easing per styled-component, and its comment says as much). 91 distinct
  `@keyframes` rules were captured; most are hashed styled-components identifiers, but 13
  have real names and real purpose (`fadeInUp`, `slideUp`, `blurOut` — scroll entrances;
  `scale-pattern-animation-one`/`-two` — the halftone-dot shimmer; `background-gradient-animation`
  — hero hue-rotate; `ach-show` — accordion row expand; `dotFadeOutIn` — carousel step
  indicator; `check` — SVG checkmark draw-on). All consolidated into 11 named
  `tokens/10-semantic/motion-roles.json` roles, each required to resolve to the site's
  global `@media (prefers-reduced-motion: reduce)` rule (which forces all
  animation/transition durations to 0.01ms — this rule already exists in `tokens.css`).
  One motion pattern — `property-management`'s `sticky-feature-showcase` — uses
  `position: sticky` scroll-linking and gets an explicit, mandatory `reducedMotionFallback`
  (static stacked layout).
- **Do the ~17 product pages share one template? Partially — verified by comparing
  measured section sequences across all of them, not assumed:**
  - **11 of 17** (`ach`, `wire`, `ledger`, `checks`, `book-transfers`, `card-programs`,
    `bank-accounts`, `debt-financing`, `loan-origination`, `loan-purchase`,
    `international-wires`) share one exact spine: header → hero-product → 1-3x
    benefit-narrative → customer-quote-panel → related-products-grid → final-cta-footer.
    This is `templates/product-page.json`.
  - **2 of 17** (`political-treasury`, `title-escrow`) share a second, heavier spine for
    regulated/niche verticals: header → hero-campaign → stat-callout-panel → 2x feature-box
    → benefit-narrative → contact-form-panel → site-footer.
    `templates/campaign-product-page.json`.
  - **2 of 17** (`correspondent-banking`, `property-management`) are long-form,
    largely-bespoke B2B sales narratives sharing only a shell (header, hero-narrative,
    stats-band, contact-form-panel, site-footer) around a variable sequence of mid-page
    sections. `templates/narrative-landing-page.json`.
  - **`realtime`** and **`protected-deposits`** are each one-off enough to get their own
    minimal template (`templates/realtime-page.json`,
    `templates/protected-deposits-page.json`) rather than being forced into the dominant
    template — per the task's scope guidance not to over-invest in one-offs, these reuse
    the same section types as the other templates wherever the content genuinely matches.

## Counts

| | |
|---|---|
| Routes measured | 34 (confirmed HTTP 200, all at 3 breakpoints) |
| Total design-repo files | 199 (92 JSON + 102 wireframe SVGs + 2 Markdown (this README + assets/README) + 2 Python scripts (schema validator + verification sweep) + 1 wireframe gallery HTML) |
| Foundation token files | 8 |
| Semantic token files | 3 (color-roles, typography-roles, motion-roles) |
| Component token files | 6 |
| Layout token files | 3 |
| LLM catalog files | 3 (token-catalog, token-policy, component-allowlist) |
| Primitives | 11 |
| Components | 11 |
| Section types | 30 |
| Templates | 10 |
| Wireframe SVGs | 102 (34 routes x 3 breakpoints) |

## Naming & versioning convention

- Sections are named by **function**, never by the page they were first seen on
  (`hero-product`, not `ach-hero`). `styleTags`/`industryTags` carry the flavor instead.
- Every section/component/primitive/template file carries a `version` (semver, all `1.0.0`
  for this initial extraction) and a `registryId` (`section.<typeId>`,
  `component.<id>`, etc. implied by file path) so a future re-measurement can bump a single
  entry without renumbering the rest.
- Section `typeId` is the single source of truth referenced from `templates/*.json` nodes,
  `compatibility/graph.json`, and `tokens/llm/component-allowlist.json`.

## Token reference convention

Every LLM-facing reference (PageSpec content, `token-catalog.json`,
`component-allowlist.json`, section `generation.tokenRefs`) is a **full canonical path**
(`tokens.10-semantic.color-roles.roles.text.body`), never a bare CSS alias
(`--color-body`). This is enforced by `schema/pagespec.schema.json`'s `motion.role`
pattern and spot-checked by adversarial mutation 4 in `schema/validate_schema.py`.

Layer precedence for a generator: **20-component > 10-semantic > 00-foundation** — reach
for the most specific token available; don't skip a component/semantic token to cite a raw
foundation value when one already covers the case (`tokens/llm/token-policy.json`).

## Validation pipeline (run and passing)

```
python3 schema/validate_schema.py                 # Draft7Validator: baseline + 7 adversarial mutations, 8/8 pass
python3 verification/verify_all.py                # 7-part sweep, all clean
python3 verification/round2_adversarial_tests.py  # Round 2: 10 adversarial cases, 10/10 pass
python3 verification/round3_adversarial_tests.py  # Round 3: 14 adversarial cases, 14/14 pass
python3 verification/graph_rules_check.py         # Round 3: compatibility/graph.json rules vs. example + all templates, 0 issues
python3 verification/maxwords_check.py            # Round 3: real word counts vs. x-maxWordsRoleBound, 0 violations
```

All of the above are self-contained: each derives its own repo root from its own file
location rather than a hardcoded path, so they run correctly from any checkout, any
username, or an isolated zip extraction — this was not true before Round 3 (see
CHANGELOG's Round 3 entry) and is proven by extracting this repo's own zip into a `/tmp`
directory with no sibling folders and running `verify_all.py` from inside it.

Re-run after every schema/graph/asset-roles change — a "passing" result here reflects the
state of the repo as of the last time these were actually run (see `CHANGELOG.md`'s Round 2
and Round 3 entries), not a permanent guarantee. This repo's Round 1 self-audit also claimed
"all clean"; Round 2 found 50 real defects the earlier sweep's checks weren't scoped to
catch; Round 3 found further real defects Round 2's checks weren't scoped to catch either
(a portability bug in the checkers themselves, whole-document rules with no persisted
enforcement, an unconstrained `assetRole` string, and zero real enforcement of
`x-maxWordsRoleBound`) — treat "all clean" as "clean against the checks that exist today,"
not "defect-free."

`schema/validate_schema.py` results (all 8 expected outcomes matched):
1. `example.pagespec.json` validates cleanly against `pagespec.schema.json` — PASS
2. Wrong theme (`dtai-dark`, not in the single-theme enum) — correctly rejected
3. `related-products-grid` product missing its required `href` — correctly rejected
4. `hero-product` with a `motion` block but no `reducedMotionFallback` — correctly rejected
5. Bare-alias motion role (`--fade-up` instead of a full `tokens.10-semantic.motion-roles.roles.*` path) — correctly rejected
6. Unlisted/phantom section type (`hero-parallax-experimental`) — correctly rejected
7. `registryId` missing its required `section.` prefix — correctly rejected
8. A page with only 1 node (below the schema's `minItems: 2`) — correctly rejected

`verification/verify_all.py` results:
1. JSON parse check — 92/92 files parse
2. `ref`/`extends`/`composedOf`/`componentRefs`/`tokenRefs` resolution — 0 dangling
3. Allowlist ⇄ registry parity — 0 missing either direction
4. `constraints.maxWords` vs. bound typography-role ceilings — 0 violations
5. `templates/*.json` node + `compatibility/graph.json` type references vs. real
   `sections/*.json` `typeId`s — 0 phantom references
6. *(Round 3)* `compatibility/graph.json`'s whole-document rules (alwaysFirst/alwaysLast/
   mutuallyExclusive/heroTypes/maxOnePerPage/onlyOnX/adjacency/rhythm) against
   `schema/example.pagespec.json` and all 10 `templates/*.json` — 0 violations
7. *(Round 3)* Real word counts (not just schema annotations) against every
   `x-maxWordsRoleBound` in `schema/example.pagespec.json` — 0 violations

## Known gaps and judgment calls

- **Theme:** only one theme was measured (`dtai-light`) and only one appears in the
  schema's `theme` enum. No dark-mode or alternate palette exists anywhere in the served
  build or in `tokens.css`, so none is offered — this is a deliberate omission, not an
  oversight.
- **`--font-mono-syntax` (the SFMono stack) has no token in the source `tokens.css`**
  despite being the single most-used typography rule measured (see Key Findings). It's
  documented in `tokens/00-foundation/typography.json` and given `code.inline`/`code.block`
  semantic roles, but a future token-authoring pass on the live site should add a real
  `--font-mono-syntax` custom property rather than leaving this as measurement-only.
  Similarly, `--radii-circle` (`50%`) and several `box-shadow` values used hundreds of
  times have no dedicated token in the source file; both are captured as
  `measuredButUntokenized` / `measuredUntokenized` entries in `tokens/00-foundation/`.
- **Two of 34 routes** (`/blog/announcing-column/`, `/blog/test-post/`) resolved to a
  single combined section during measurement instead of the clean header + social-share +
  article-body split every other blog post produced — a transient DOM-timing artifact on
  those specific pages at measurement time, not a structural template difference (6 of the
  other 8 posts resolved cleanly and all 9 posts share `templates/blog-post.json`).
- **No footer landmark** was captured as a distinct `<main>` child on
  `/protected-deposits/`, `/company/`, `/careers/`, `/press/`, or `/security/`. A footer
  almost certainly renders on all of these (every other route has one), but wasn't
  captured as its own section boundary here; `templates/protected-deposits-page.json` and
  `templates/simple-page.json` are documented without a trailing footer node rather than
  guessing its exact content model.
- **`correspondent-banking` and `property-management`** are each highly bespoke long-form
  sales pages. Rather than inventing a distinct section type per unique
  `_clearing__Section`/`_team__Section`/`_workflows__Section`/etc. component name in the
  source, semantically similar bespoke sections were consolidated into general-purpose
  types (`workflow-feature-panel`, `dashboard-preview-panel`, `product-cross-sell-panel`)
  per the task's scope guidance to not over-invest in one-off pages. This trades a small
  amount of per-page content-model precision for a materially smaller, more reusable
  section taxonomy.
- **Word-count budgets (`maxWords`)** on typography roles and section constraints are
  derived heuristically from the measured text-length/role pairing across the corpus
  (see `extraction/measured-values.json`), not from a formal p90 statistical computation
  over every individual instance — with only 1-11 instances of most section types, a
  literal p90 would be noisy; the documented ceilings are a reasonable, conservative
  generation guardrail instead.
- **`long-form-content`** (changelog, SVB update, blog articles) is explicitly
  `maxWordsExempt` in both the section contract and the schema — these are prose articles
  with a >10x length range (2,556px–27,872px measured), not structured marketing sections,
  and a word ceiling on them would be meaningless.

## How to serve the wireframe gallery

```bash
cd wireframes   # from this repo's root
python3 -m http.server 8090
# open http://localhost:8090/
```

`index.html` groups all 34 measured routes by shared template, with a desktop/tablet/mobile
toggle. Every SVG (`svg/<route-slug>__<breakpoint>.svg`) is generated directly from
`wireframes/manifest.json`, which is itself generated from the real per-route,
per-breakpoint section geometry in `extraction/measured-values.json` — box heights, widths,
and labels are measured pixels, not illustrative approximations.
