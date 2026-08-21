# Asset Library

Everything the site loads, plus the design-token source of truth.

| Path | Contents |
|---|---|
| `tokens/tokens.css` | 373 design tokens extracted from the build, grouped by category |
| `typography/` | Inter (400/500/600) + JetBrains Mono (400/500) woff2, with SIL OFL licenses |
| `images/` | 156 files — hero, case studies, product, marketing, blog |
| `clips/` | 12 MP4s (~1.7 GB) — changelog and product video |
| `footer-logo-mask.svg` | CSS `mask-image` for the footer wordmark |
| `ryanbot.jpg` | Blog author asset |

Served at `/assets/…`. All references are absolute, so anything moved here needs its
references rewritten in the pages, the JS bundles *and* `page-data/`.

## Tokens

`tokens/tokens.css` is documentation, not a dependency — it is deliberately **not** linked
into the pages. The captured build declares these same tokens inline in every page's
styled-components CSS, which is how the original ships; linking the file as well would
duplicate all 373 declarations. Read it to learn the visual language, and edit the inline
CSS when you need to change rendered output.

Scope is `:root` only — the global design layer. Component-scoped custom properties stay with
their components.

### Idiom

Extend in this project's naming, not a generic vocabulary:

```css
/* Color — channel triplets, then semantic colors that reference them */
--rgb-blue-800: 17,26,74;
--color-blue-800: rgba(var(--rgb-blue-800), 1);
```

That indirection is the point: a hue changes in exactly one place. Keep it when adding colors.

| Family | Category |
|---|---|
| `--rgb-*`, `--color-*`, `--bg-*`, `--line-*` | Color |
| `--font-*`, `--text-*`, `--lh-*`, `--letter-spacing-*` | Typography |
| `--space-*` (and negative `--space-n*`) | Spacing |
| `--radii-*` | Radius |
| `--cols-*`, `--span-*` | Container |
| `--btn-*`, `--form-*`, `--icon-*`, `--link-*` | Controls |
| `--card-*`, `--blog-*`, `--header-*`, `--dot-*` | Components |
| `--shadow-*` | Shadows |
| `--screen-*` | Responsive |

Two gaps worth knowing about, both inherited from the captured build:

- **No motion tokens.** Durations and easings are inlined per styled-component. A new
  animation should add tokens rather than another inline literal.
- **No accessibility tokens.** `tokens.css` adds a `prefers-reduced-motion` block, which the
  original build did not have.

`--tw-*` properties in the bundles are Tailwind runtime plumbing (ring offsets and similar),
not design tokens, and are excluded.
