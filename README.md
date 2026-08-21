# DT&AI.com — local clone

A local, self-contained copy of dtai.com — all 34 content pages (Gatsby build, captured 2026-08-21).
All assets are stored locally; the page makes **no external network requests**.

## Run it

```bash
node serve.js 8080
```

Then open <http://localhost:8080>.

Any port works: `node serve.js 3000`. Node.js is the only requirement (no `npm install` — the
server uses only Node built-ins).

Alternatively, from this directory:

```bash
python3 -m http.server 8080
```

## What's here

| Path | Contents |
|---|---|
| `index.html` | Server-rendered homepage, incl. all inline styled-components CSS |
| `<route>/index.html` | The other 33 pages — products, company, careers, changelog, blog posts |
| `*.js` (71) | Gatsby runtime, framework, app bundle, and every route/vendor chunk |
| `no-external.js` | Guard that blocks any cross-origin request and stubs analytics/reCAPTCHA globals |
| `page-data/` (34) | Gatsby JSON needed for hydration and client-side routing |
| `assets/` | Asset library — see [assets/README.md](assets/README.md) |
| `assets/tokens/tokens.css` | 373 design tokens, grouped by category (reference, not linked) |
| `assets/typography/` | Inter + JetBrains Mono woff2, with their SIL OFL licenses |
| `assets/images/` (156) | Hero, case studies, product, marketing and blog imagery |
| `assets/clips/` (12) | Changelog / product MP4s from the Contentful CDN (~1.7 GB) |
| `serve.js` | Static file server (SPA fallback for extension-less routes) |

Total: 323 files, ~1.7 GB (1.7 GB of that is `assets/clips/`).

## Rebrand (DT&AI)

Visible brand text reads **DT&AI** throughout; domains in the displayed code samples read
`dtai.com`. The replacement was scoped, not a global find-replace — `column` is a CSS keyword
all over this build, so these were deliberately left untouched:

| Left alone | Why |
|---|---|
| `flex-direction:column`, `column-gap`, `grid-template-columns`, `gridColumn` (~5,500) | CSS/JS layout keywords — replacing them destroys every layout |
| `Column-sc-df4skj-0` (690) + `displayName:"Column"` | styled-components identity; the id must match between the pre-rendered HTML and the JS that regenerates it, or styles detach |
| `webpackChunkcolumn` (142) | webpack runtime global; chunk loading breaks if renamed |
| Blog slugs (`/blog/funding-column/`) | real route paths; renaming breaks routing and page-data lookup |

The wordmark was vector artwork (a single 2,501-char bezier path), not text. It is now an SVG
`<text>` element — replaced in both the pre-rendered HTML and the `81025768…` bundle that
re-renders it on hydration. `favicon.ico` is still the original mark: it is a binary raster
icon, so it cannot be text-substituted.

Ampersand encoding is region-aware: `DT&amp;AI` in markup, raw `DT&AI` inside `<script>`
bodies, JS and JSON. Verified: 0 pages render a literal `&amp;`.

### Regulatory copy — stripped

The captured pages asserted FDIC membership, national bank charter status, and insured-deposit
claims that belong to Column and are **not** true of DT&AI. Those have been removed:

| Was | Now |
|---|---|
| `DT&AI NA Member FDIC` (hero badge) | `DT&AI`; the vector "FDIC" glyph is blanked and its box collapsed |
| `The only nationally chartered bank…` | `A platform…` (titles, meta, og/twitter descriptions) |
| `chartered bank`, `nationally chartered` | `platform` |
| `DT&AI N.A.`, `DT&AI National Association` | `DT&AI` |
| `FDIC-insured`, `FDIC insurance`, `FDIC` | `insured`, `deposit insurance` |

Also removed: the six `/legal/` route chunks and `fbd28ed2` (~444 KB). Those pages were never
captured (robots-disallowed), so the chunks were unreachable dead code — but they contained
Column's real privacy/ToS text and a table of ~90 **real third-party banks** by legal name,
which would have implied sweep-network relationships that do not exist.

Three `FDIC` strings remain, all one styled-component identifier
(`_hero__FDIC-sc-lcvkfu-14`). It is invisible to users and must match between the pre-rendered
HTML and the JS that regenerates it, so it is deliberately left alone.

`SWIFT` is left as-is on `/international-wires/` — a payment network, not a claim about
insured or chartered status. Remove it too if you want zero capability claims.

> Still a mockup of another company's site. Stripping the regulatory copy removes the
> misrepresentation risk; it does not change that the markup, layout, copy and imagery are
> Column's. Keep the repo private.

## Fidelity notes

- **Homepage is fully interactive.** Nav dropdown, cookie banner, hero animation, and the
  case-study scenes all run — the real Gatsby bundle is hydrating.
- **React hydration warnings** (`#418`, `#423`) appear in the console. These are expected when
  reusing build-time SSR HTML outside its original build: React discards the mismatched markup
  and re-renders on the client, so the rendered result is correct. Cosmetic only.
- **All 34 sitemap pages are captured** and verified: every one renders with real content, in
  Inter, issuing zero off-origin requests. Both client-side routing and direct deep links work.
- **The 6 `/legal/` pages were deliberately skipped** — dtai.com's `robots.txt` disallows
  `/legal/` and `/docs/extended-api/`. Their route chunks are present, so those links resolve to
  an empty shell rather than content.
- **Nothing leaves the machine.** Every third-party integration has been removed at the source:
  Google Tag Manager, reCAPTCHA (both v3 and Enterprise), the `images.ctfassets.net` preconnect,
  YouTube embeds, and the contact/newsletter `fetch` calls to `api.dtai.com`. Off-site `<a href>`
  targets (docs, dashboard, social) are rewritten to `#`; links to pages *within* the clone stay
  relative and keep working. `no-external.js` loads first and is the backstop — it patches `fetch`,
  `XMLHttpRequest`, `sendBeacon`, and DOM insertion so any cross-origin URL that slipped through is
  logged and blocked rather than requested. Verified: a full page load issues zero off-origin
  requests.
- **Fonts are open source.** The proprietary Suisse Intl / Suisse Neue / Suisse Intl Mono / ryry
  faces were deleted and replaced with **Inter** (text, a close neo-grotesque match) and
  **JetBrains Mono** (code samples), both SIL OFL. Family names in the CSS were renamed to match,
  so nothing still references a Suisse face.
- **Two missing images:** `/assets/images/index/case-studies/brex.jpg` and
  `/assets/images/products/debt-financing/speed.svg` both 404 from dtai.com itself.
- **Videos dominate the folder.** The 12 Contentful MP4s are ~1.7 GB of the 1.7 GB total; the
  entire rest of the site is ~25 MB. Delete `assets/clips/` if you don't need them — the pages still
  render, the `<video>` elements just stay on their poster frames.

## Note on content

The markup, design, copy, imagery, and DT&AI branding here are DT&AI's intellectual property.
This copy is for local reference and development only — don't redeploy or publish it.
