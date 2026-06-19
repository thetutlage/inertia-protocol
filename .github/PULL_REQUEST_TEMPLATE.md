<!--
  Thanks for contributing to the Inertia protocol spec!
  See CONTRIBUTING.md for conventions and the build steps.
-->

## What does this change?

<!-- One or two sentences. Link the issue it fixes, if any. -->

Fixes #

## Type

- [ ] Erratum (typo / factual fix)
- [ ] Ambiguity clarification
- [ ] Fidelity fix (spec corrected to match the real client behaviour)
- [ ] Tooling / build / docs

## For fidelity fixes

<!-- How do you know the client behaves this way? Link client source or describe the observed request/response. -->

## Checklist

- [ ] Edited `protocol.md` (never `index.html` directly — it is generated).
- [ ] If a diagram changed: edited the `.d2`, re-rendered with `./diagrams/render.sh`, committed the `.svg`.
- [ ] Ran `python3 build.py` and committed the updated `index.html`.
- [ ] Wording is precise and implementation-neutral (no framework-specific API).
