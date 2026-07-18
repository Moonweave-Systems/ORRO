# Install

The ORRO product line is published on PyPI through 0.2.4, while this repository
packages 0.2.5. The post-release target state is: `orro` 0.2.5 is published on
PyPI. It becomes true only after `v0.2.5` is tagged and the Trusted-Publishing
workflow completes. The 0.2.5 package metadata declares `witnessd>=2.4.0,<3.0.0`, and
the package exposes `orro` plus the `orro-wrapper` compatibility alias.

```bash
python3 -m pip install orro
```

Until the `v0.2.5` workflow completes, that command installs `orro` 0.2.4.
Development dogfood may instead use the 0.2.5 source checkout and pinned engine
repositories directly.

For the shared pinned-engine development layout, run bootstrap with the shared
virtual environment's Python. Bootstrap prepares the pinned
`Moonweave-Systems/witnessd` and `Moonweave-Systems/Depone` checkouts:

```bash
/usr/bin/python3 -m venv ~/.local/share/orro/venv
~/.local/share/orro/venv/bin/python scripts/bootstrap_orro.py \
  --execute \
  --workspace ~/.local/share/orro/engines \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --allow-network \
  --install-witnessd \
  --json
```

The ORRO-owned `orro` command delegates to witnessd. This repository is the
canonical source of the published product/distribution wrapper package.
Both distributions install an `orro` console script, so bootstrap installs the
ORRO wrapper after the pinned editable witnessd install and then explicitly
links both the shared environment's `bin/orro` and `~/.local/bin/orro` to
`bin/orro-wrapper`. Bootstrap verifies the `orro_wrapper.cli:main` entry-point
metadata, the non-engine wrapper boundary, and real `flowplan --help`
delegation before it succeeds. `orro-wrapper` remains available, and the pinned
witnessd compatibility shim remains reachable with `python -m orro`.

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
`witnessd>=2.4.0,<3.0.0`; pinned-engine e2e metadata continues to govern repository
compatibility validation.

## Packaging Decision

The v0 packaging decision is documented in `docs/packaging-decision.md` and
`packaging/wrapper-package-plan.v0.json`. It is product metadata, not proof, not
verifier truth, and not package publish.

Current installs use the ORRO-owned thin `orro` command. The ORRO product line is
published on PyPI through 0.2.4, this repository prepares source 0.2.5 for the
tag-triggered workflow, and the wrapper continues to contain no engine code.

## Wrapper Distribution Smoke

The local wrapper package can be checked without publishing anything:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json --allow-network
```

This builds and installs a local wheel and verifies `orro` plus `orro-wrapper`.
The flag authorizes pip build isolation to provision the declared wrapper build
dependency; it does not authorize engine checkout or package publication.
