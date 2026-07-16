# `orro` name-claim / wrapper package sources

Version-controlled sources for the public `orro` distributions on PyPI and npm.
These reserve the `orro` name and provide the thin `orro` command surface; they
do not contain execution or verification logic (that lives in the witnessd
runtime and the Depone verifier).

## `pypi/` — PyPI package `orro`

A thin wrapper that owns the `orro` command and delegates every subcommand to the
installed witnessd runtime.

- `src/orro/__main__.py` defines `main()` (the `bin/orro` console-entry contract)
  and delegates to `witnessd.__main__.main(["orro", *args])`. The recognized
  command set is imported from witnessd (single source of truth), so an unknown
  command is named honestly instead of leaking the engine's generic parser error.
- witnessd is a **runtime** requirement resolved at import time, not a hard install
  dependency: the engine is distributed via GitHub releases, not PyPI, so a PyPI
  dependency pin would make `pip install orro` unresolvable. If witnessd is
  missing, `orro` prints an install pointer.

Published: **0.0.2** — https://pypi.org/project/orro/

Build & publish (from a checkout of this directory):

```sh
python3 -m build
python3 -m twine check dist/*
python3 -m twine upload dist/*      # requires a PyPI token
```

History: `0.0.1` shipped an `orro/__main__.py` with no `main()`, which broke
witnessd's `bin/orro` console entry (`ImportError: cannot import name 'main'`)
when installed. `0.0.2` restores the contract and delegates.

## `npm/` — npm package `orro`

A name placeholder on the npm registry (the `orro` CLI itself is Python, not
Node). `index.js` exports project metadata only.

Publish: `npm publish` (requires a granular access token with **Bypass
two-factor authentication** enabled, or an OTP at publish time).

## Notes

- Keep the package `version` here in sync with what is published to each registry.
- Build artifacts (`dist/`, `.venv/`, `.ruff_cache/`, `node_modules/`) are not
  tracked; regenerate them at build time.
