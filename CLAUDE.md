# Maintaining this repository

Instructions for maintainers (and coding agents) working on the build, the
rendering, or the diagrams. **Contributors changing the spec text don't need any
of this** — see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Model: one source, one generated artifact

- [`protocol.md`](./protocol.md) is the **single source of truth** for all
  content — prose, tables, code, callouts, figure captions, section headings, and
  the sidebar labels.
- [`build.py`](./build.py) parses `protocol.md` and writes
  [`index.html`](./index.html). It contains **no spec prose** — only design chrome
  (eyebrow, wordmark, badge, end-marker, page title).
- [`diagrams/`](./diagrams) holds the D2 sources (`*.d2`) and their rendered
  `*.svg`s, which `build.py` inlines into figure boxes.

Never hand-edit `index.html` or a `.svg`. Edit the source and rebuild.

## Build

```sh
# 1. only if a diagram's .d2 changed — re-render to SVG:
./diagrams/render.sh diagrams/*.d2

# 2. regenerate index.html from protocol.md + the committed SVGs:
python3 build.py
```

- `build.py` needs **Python 3 only** (standard library) — it reads the committed
  SVGs, so no fonts or `d2` required just to rebuild the page.
- `diagrams/render.sh` needs [`d2`](https://d2lang.com) and
  [JetBrains Mono](https://www.jetbrains.com/lp/mono/) TTFs installed (it
  auto-detects them; override with `FONT_DIR=/path`).

After any content or diagram change: rebuild and **commit `index.html`** (and any
re-rendered `.svg`). CI (`.github/workflows/build.yml`) re-runs `build.py` and
fails if the committed `index.html` is stale.

## Conventions in `protocol.md` that the renderer relies on

Standard GitHub-Flavored Markdown drives most of the output (headings, tables,
lists, fenced code, `**bold**`, `` `code` ``, `*italic*`). On top of that:

| Markdown | Renders to |
| --- | --- |
| `## N. Title` | section pill (Roman numeral `N`, anchor `#sec-N`) + a sidebar entry |
| `## N. Long title <!-- nav: Short -->` | sidebar label override (default: title with trailing `(…)` and anything after ` - ` dropped) |
| `### Subhead` / `### 8a. …` | subhead (the `Na.` form becomes `Na · …`) |
| `(section 9)`, `(section 8a)`, `(sections 10-16)` | `#9`, `#8a`, `#10`–`#16` anchor links |
| `MUST` / `MUST NOT` / `SHOULD` / `MAY` | RFC-2119 keyword styling |
| ` ```jsonc page object ` | code card; words after the lang become the card label (`jsonc` still highlights on GitHub) |
| `> [!NOTE]` / `[!TIP]` / `[!IMPORTANT]` | green callout; `[!WARNING]` / `[!CAUTION]` → amber |
| `> [!NOTE]` + `> **Lead.** …` | callout label becomes *NOTE · LEAD* |
| ` ```mermaid ` block + `<!-- fig: name \| Caption -->` | swapped for the themed D2 figure `diagrams/name.svg`, captioned `Fig. K — Caption` |

Table cell styling is derived: the first column is mono; a non-first column whose
every non-placeholder cell is `` `backticked` `` renders as a mono identifier
column; cells like `no` / `-` / `always empty …` render muted. Multi-line list
items (wrapped, indented continuations) are folded into one item.

Syntax highlighters exist for `jsonc`, `html`, and `text`/bare fences only.

## Common edits

- **Add a section:** add `## N. Title` in order. The pill, anchor, and sidebar
  entry are automatic. Add `<!-- nav: … -->` only if the auto-shortened label is
  poor.
- **Add a diagram:** write the `.d2` in `diagrams/` (copy an existing file for the
  green theme), `./diagrams/render.sh diagrams/your.d2`, add a ` ```mermaid ` block
  to `protocol.md` for GitHub, and follow it with `<!-- fig: your-name | Caption -->`.
  Figures are numbered automatically by document order.
- **Add a callout:** use the GitHub alert syntax above.

## Diagram theme (keep consistent)

Green palette on the spec's paper. Shapes fill `#FCFBF8` / stroke `#1F7A4D`;
decision diamonds fill `#EFF5F0`; arrows `#23201A`; edge labels italic `#56554d`;
sequence notes fill `#EFF5F0` / stroke `#C2D8C9`. Labels use **JetBrains Mono**
and **ASCII only** (`->`, `-`, `...` — never Unicode arrows/dashes, which tofu in
the font). `render.sh` applies the font; the per-shape colors live in each `.d2`.

## Design fidelity

The page reproduces a fixed visual design (warm paper `#F1EEE7`, card `#FCFBF8`,
green accent `#1F7A4D`, Newsreader + JetBrains Mono, the left binder/sidebar, the
`§19` badge). Changes to `build.py`'s CSS should preserve it — verify visually
after any change to the renderer.
