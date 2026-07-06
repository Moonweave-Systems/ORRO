# ORRO

ORRO = Observed Run & Review Orchestrator.

ORRO is the **Observed Run & Review Orchestrator**.

ORRO is the user-facing workflow surface for observed agent execution and
review.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

## What ORRO Is

ORRO turns a goal into an evidence-governed workflow:

```text
advise -> init/doctor/engine-lock -> scout -> flowplan -> proofrun -> proofcheck -> handoff -> report
```

This repository is the product, documentation, examples, distribution, and
wrapper-planning home for ORRO.

## What ORRO Is Not

This repository is not an execution engine, verifier engine, or monorepo
migration.

- No Depone verifier implementation lives here.
- No witnessd runtime implementation lives here.
- No proofcheck logic is duplicated here.
- No proofrun, scheduler, observer, or team-lane logic is duplicated here.
- ORRO does not become a third engine.

## Engine Repositories

- Depone: <https://github.com/Moonweave-Systems/Depone>
- witnessd: <https://github.com/Moonweave-Systems/witnessd>

Current command source: the `orro` command is implemented and hosted by
`witnessd` while ORRO packaging remains in progress.

Future goal: one user-facing ORRO install that pins compatible Depone and
witnessd engine versions without merging the engines.

## Pinned Engine E2E

ORRO repo e2e CI uses `engine-lock/orro-e2e-engine-lock.json` to checkout a
pinned witnessd and Depone engine pair, then runs the local smoke runner against
those checkouts. The e2e engine lock is distribution and CI metadata, not proof,
not verifier truth, not approval, and not assurance.

The runner orchestrates engines but does not implement proofrun, proofcheck,
runtime scheduling, observer, fan-in, team-ledger, or verifier logic.

## Release Metadata

`release/orro-release-manifest.v0.json` records the current ORRO product release
candidate metadata and the pinned engine pair validated by e2e CI. The release
manifest is product/distribution metadata, not proof, not verifier truth, not
approval, and not assurance. No ORRO package is published by this manifest.

Engine-lock update discipline is documented in
[`docs/engine-lock-update-process.md`](docs/engine-lock-update-process.md), and
validated engine pairs are listed in
[`docs/compatibility-matrix.md`](docs/compatibility-matrix.md). Published ORRO
package remains future work.

## Development Install

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

## Normal ORRO Loop

```bash
orro advise "fix parser bug" --repo . --home .witnessd --json
orro init --home .witnessd --depone-root ../Depone
orro doctor --home .witnessd --json
orro engine-lock --home .witnessd --out .witnessd/orro-engine-lock.json
orro scout "fix parser bug" --repo . --home .witnessd
orro flowplan "fix parser bug" --root . --profile code-change --out .witnessd/workflow-plan.json
orro proofrun "fix parser bug" --repo . --home .witnessd --workflow-plan .witnessd/workflow-plan.json
orro proofcheck .witnessd/runs/<run-dir> --home .witnessd --out .witnessd/runs/<run-dir>/proofcheck-verdict.json
orro handoff .witnessd/runs/<run-dir> --out .witnessd/runs/<run-dir>/orro-handoff.json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

## Trust Boundaries

- Workflow plans are intent, not proof.
- Role-lane plans are executable intent, not proof.
- Reports are summaries, not proof.
- Handoff is review packaging, not merge approval.
- Engine-lock is distribution metadata, not proof.
- Depone proofcheck is the verifier.
- witnessd executes and emits evidence.
- ORRO exposes the workflow.

## Documentation

- [Architecture](docs/architecture.md)
- [Install](docs/install.md)
- [Workflow Reference](docs/workflow-reference.md)
- [Workstyle Doctrine](docs/workstyle-doctrine.md)
- [Evidence Model](docs/evidence-model.md)
- [Engine Contract](docs/engine-contract.md)
- [Product Reality Check](docs/product-reality-check.md)
- [E2E Smoke Contract](docs/e2e-smoke-contract.md)
- [E2E Smoke Runner](docs/e2e-runner.md)
- [Engine-Lock Update Process](docs/engine-lock-update-process.md)
- [Compatibility Matrix](docs/compatibility-matrix.md)
- [Repository Strategy](docs/repository-strategy.md)

## Compatibility

Superflow/superflow remains historical compatibility naming in engine repos.
New product documentation should use ORRO/orro.
