# Install

`orro` 0.1.0 is published on PyPI, and this repository is its canonical source.
The package metadata declares `witnessd>=2.3.2`, and the package exposes `orro`
plus the `orro-wrapper` compatibility alias.

```bash
python3 -m pip install orro
```

That command installs `orro` 0.1.0 and resolves its `witnessd>=2.3.2`
dependency. Development dogfood may instead use the source checkout and pinned
engine repositories directly.

Current development layout uses the engine repositories directly:

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

The ORRO-owned `orro` command delegates to witnessd. This repository is the
canonical source of the published product/distribution wrapper package.

## Bootstrap Planner

The ORRO repo can plan or check the local engine checkout setup from the pinned
engine lock:

```bash
python3 scripts/bootstrap_orro.py \
  --dry-run \
  --workspace /tmp/orro-workspace \
  --json
```

To inspect existing checkouts without mutation:

```bash
python3 scripts/bootstrap_orro.py \
  --check-existing \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --json
```

The bootstrap is setup/distribution orchestration and setup metadata, not proof.
It contains no engine code, does not verify evidence, does not approve merge,
does not raise assurance, and the executable `orro` command delegates runtime
behavior to witnessd.

## Local E2E Smoke

After installing the ORRO wrapper command and sibling engines, the ORRO
repository can run a local smoke against sibling engine checkouts:

```bash
cd ../ORRO
python3 scripts/orro_e2e_smoke.py \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --require-lock-match \
  --allow-network \
  --workdir /tmp/orro-e2e \
  --json
```

The smoke runner is an orchestration harness only. It calls the current engine
commands and does not implement proofrun, proofcheck, or runtime logic.

The source package provides one user-facing ORRO install and declares
`witnessd>=2.3.2`; pinned-engine e2e metadata continues to govern repository
compatibility validation.

## Packaging Decision

The v0 packaging decision is documented in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json`. It is product metadata, not proof, not
verifier truth, and not package publish.

Current installs use the ORRO-owned thin `orro` command. The `orro` package is
published on PyPI, this repository sources 0.1.0, and the wrapper continues to
contain no engine code.

## Wrapper Distribution Smoke

The local wrapper package can be checked without publishing anything:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json --allow-network
```

This builds and installs a local wheel and verifies `orro` plus `orro-wrapper`.
The flag authorizes pip build isolation to provision the declared wrapper build
dependency; it does not authorize engine checkout or package publication.
