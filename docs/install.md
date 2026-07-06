# Install

Current development layout uses the engine repositories directly:

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

The `orro` command is currently implemented by witnessd. This repository is a
product/distribution skeleton and does not publish a standalone package yet.

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
does not raise assurance, and the executable `orro` command remains
witnessd-hosted.

## Local E2E Smoke

After installing the witnessd-hosted command, the ORRO repository can run a
local smoke against sibling engine checkouts:

```bash
cd ../ORRO
python3 scripts/orro_e2e_smoke.py \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --require-lock-match \
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

Current installs still use the witnessd-hosted `orro` command. Published ORRO
package remains future work, and future wrapper work must contain no engine
code.
