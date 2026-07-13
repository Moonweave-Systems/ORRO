# Install

Standalone ORRO package publish remains future work. Current dogfood and
development use installs witnessd and Depone directly. This repository's local
wrapper exposes `orro` and `orro-wrapper`.

Current development layout uses the engine repositories directly:

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

The ORRO-owned `orro` command delegates to witnessd. This repository is a
product/distribution wrapper package and does not publish a standalone package
yet.

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

Future packaging should provide one user-facing ORRO install with pinned Depone
and witnessd engine versions.

## Packaging Decision

The v0 packaging decision is documented in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json`. It is product metadata, not proof, not
verifier truth, and not package publish.

Current installs use the ORRO-owned thin `orro` command. Published ORRO package
remains future work, and future wrapper work must contain no engine code.

## Wrapper Distribution Smoke

The local wrapper package can be checked without publishing anything:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json
```

This builds and installs a local wheel and verifies `orro` plus `orro-wrapper`.
