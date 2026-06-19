# The Inertia Protocol (v3)

A language-agnostic specification for implementing the **server side** of
[Inertia](https://inertiajs.com) v3 — what your server must send and accept so
that the official Inertia client (`@inertiajs/core` v3 and its framework
adapters) works unmodified.

It is written for people building a server adapter in any language or framework
(PHP, Ruby, Python, Go, Rust, a new JS framework, …). It describes the wire
contract — headers, the page object, prop evaluation, partial reloads, deferred
/ optional / merge / once / scroll props, redirects, versioning, validation
errors, and history control — not any one framework's API.

## Read the spec

- **Canonical source:** [`protocol.md`](./protocol.md) — the normative
  specification. This is what issues and pull requests reference.
- **Rendered version:** [`index.html`](./index.html) — a styled, browsable
  build of the same content, with diagrams. Once GitHub Pages is enabled for
  this repository it is served at
  **https://thetutlage.github.io/inertia-protocol/**.

Requirement levels (**MUST** / **SHOULD** / **MAY**) follow
[RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Scope

This documents the **existing** v3 protocol — the behaviour the official client
already implements. The goal is a faithful, unambiguous description that a new
server adapter can be built against. It is therefore mostly *descriptive*:
changes should clarify or correct the spec to match how the client actually
behaves, not invent new protocol semantics the client does not support. See
[CONTRIBUTING.md](./CONTRIBUTING.md).

## Building locally

The rendered `index.html` is generated; the diagrams are [D2](https://d2lang.com)
sources rendered to SVG.

**Requirements**

- Python 3 (standard library only — no packages)
- [`d2`](https://d2lang.com) — `brew install d2` (only needed to re-render diagrams)
- [JetBrains Mono](https://www.jetbrains.com/lp/mono/) TTFs installed (only
  needed to re-render diagrams)

**Commands**

```sh
# 1. (only if you changed a diagram) re-render the D2 sources to SVG
./diagrams/render.sh diagrams/*.d2

# 2. rebuild index.html from the build script + the rendered SVGs
python3 build.py
```

`build.py` inlines the SVGs (stripping their white background) and writes
`index.html`. It uses only the standard library.

## Repository layout

| Path | What it is |
| --- | --- |
| [`protocol.md`](./protocol.md) | The canonical specification (normative) |
| [`index.html`](./index.html) | Generated styled rendering of the spec |
| [`build.py`](./build.py) | Builds `index.html` (inlines diagrams, applies the design) |
| [`diagrams/`](./diagrams) | D2 diagram sources (`*.d2`), rendered `*.svg`, and `render.sh` |
| [`design/reference.html`](./design/reference.html) | The original visual design reference the rendering reproduces |

## Contributing

Found an ambiguity, an error, or behaviour the spec gets wrong versus the real
client? Please [open an issue](../../issues/new/choose) or a pull request. Start
with [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

[MIT](./LICENSE) © Harminder Virk. Implementations of this protocol are
unencumbered — build a server adapter in any language, for any purpose.
