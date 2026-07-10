# ORRO

ORRO = Observed Run & Review Orchestrator.

ORRO is the **Observed Run & Review Orchestrator**.

ORRO is the user-facing workflow surface for observed agent execution and
review.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

## Current Status

Today:
- ORRO is the product and workflow surface for observed run and review.
- This repository keeps ORRO docs, product boundary, locks, wrapper skeleton, assurance contract checks, and integration-surface policy.
- The runnable `orro` command is still witnessd-hosted.
- No standalone ORRO package has been published.
- The local wrapper skeleton exposes `orro-wrapper`, not `orro`.

Current focus:
- Make AI-assisted work reviewable.
- Prevent handoff/report/proof/approval confusion.
- Grow automation only through checkpointed workflows.
- Keep integration surfaces plugin-first and MCP-optional.

## Can I use ORRO today?

Yes for development dogfood through Depone and witnessd. No as a standalone
published ORRO package.

Current split:

- witnessd hosts the runnable `orro` workflow command.
- This ORRO repository owns the product boundary, documentation, locks, wrapper
  skeleton, and assurance contracts.
- `orro-wrapper` is the transitional wrapper boundary exposed by this
  repository.

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

Use `scripts/update_orro_engine_lock.py` for future pin updates so the e2e
engine lock, release manifest, and compatibility matrix stay aligned. The
helper edits metadata only; it does not fetch, execute engines, verify evidence,
approve merge, or raise assurance.

## Bootstrap Setup Planner

`scripts/bootstrap_orro.py` reads the pinned e2e engine lock and can produce a
local setup plan, check existing witnessd and Depone checkouts, or explicitly
prepare pinned checkouts when `--execute --allow-network` is supplied.

The bootstrap is setup/distribution orchestration. Bootstrap output is setup
metadata, not proof, not verifier truth, not approval, and not assurance. It
contains no engine code, does not implement proofrun or proofcheck, and does not
run proofrun/proofcheck/handoff by default. The current executable `orro`
command remains witnessd-hosted.

```bash
python3 scripts/bootstrap_orro.py \
  --dry-run \
  --workspace /tmp/orro-workspace \
  --json
```

## Packaging Decision

`docs/packaging-decision.md` and `packaging/wrapper-package-plan.v0.json`
record the v0 wrapper packaging decision. The packaging decision is product
metadata, not proof, not verifier truth, not package publish, not approval, and
not assurance.

The current command source remains the witnessd-hosted `orro` console script.
Published ORRO package remains future work. Future wrapper work must contain no
engine code and must not implement proofrun, proofcheck, scheduler, observer,
fan-in, team-ledger, or verifier logic.

## Pinned Engine Fallback

`docs/pinned-engine-fallback.md` and
`packaging/pinned-engine-fallback-policy.v0.json` define the fail-closed
fallback when pinned witnessd or Depone engines are missing, mismatched, or
unavailable.

The fallback policy is product/distribution metadata, not proof, not verifier
truth, not package publish, not approval, and not assurance. It forbids silently
using latest `main`, rewriting the engine lock during bootstrap, or
auto-selecting alternate engine commits. Moving to a different engine pair
requires an intentional engine-lock update PR.

## Thin Wrapper Skeleton

`orro-wrapper` is the first thin wrapper skeleton in this repository. It does
not replace the witnessd-hosted `orro` command. It can report wrapper boundary
metadata and explicitly delegate commands to the existing engine command.

```bash
python3 -m pip install -e .
orro-wrapper boundary
orro-wrapper self-test
orro-wrapper delegate -- --help
```

The wrapper is not proof, not verifier truth, not package publish, not approval,
and not assurance. It contains no engine code and does not implement proofrun or
proofcheck.

The wrapper install smoke verifies the editable package and installed
`orro-wrapper` console script without publishing a package or calling engine
repos:

```bash
python3 scripts/check_orro_wrapper_install.py --json
```

The install smoke is setup/test metadata, not proof, not verifier truth, not
package publish, not approval, and not assurance.

## Wrapper Distribution Smoke

The wrapper distribution smoke builds a local wheel, installs it into a
temporary virtual environment, and verifies that only `orro-wrapper` is exposed:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json
```

The distribution smoke checks that the wheel contains no Depone or witnessd
packages, no proofrun/proofcheck runtime implementation files, and no `orro`
console script. The current executable `orro` command remains witnessd-hosted,
and this package does not shadow `orro`.

The distribution smoke is local test metadata, not proof, not verifier truth,
not package publish, not approval, and not assurance. Future migration to an
ORRO-owned `orro` command requires a separate migration wave.

## ORRO Command Migration

The current executable `orro` command remains witnessd-hosted. ORRO-owned `orro`
command migration is plan-only and documented in
[`docs/orro-command-migration.md`](docs/orro-command-migration.md).

The migration plan does not add an `orro` console script, does not publish a
package, does not move engine code, and does not change verifier or runtime
semantics. `orro-wrapper` remains the transitional ORRO repo command. The ORRO
package must not shadow `orro` until a separate migration wave proves
compatibility, rollback, and pinned-engine e2e through the migrated command.

`scripts/check_orro_command_migration_dry_run.py` is the dry-run harness for
that future wave. It uses a temporary source copy to simulate
`orro = orro_wrapper.cli:main`, verifies both `orro` and `orro-wrapper` remain
thin wrapper surfaces, and runs a rollback simulation by reinstalling the
current `orro-wrapper`-only package shape. Dry-run metadata is not proof and
does not make ORRO own `orro`.

## Install Reality

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

The orro command above is currently witnessd-hosted.

For the local ORRO wrapper skeleton:

```bash
cd ORRO
python3 -m pip install -e .
orro-wrapper boundary
orro-wrapper self-test
```

The wrapper is product/distribution metadata and a thin delegation surface. It
does not replace the witnessd-hosted `orro` command and is not proof, not
verifier truth, not package publish, not approval, and not assurance.

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

## Phase 0 Evidence Limitations

The current Phase 0 safety patch makes release claims narrower while the
evidence substrate is being hardened. ORRO version metadata, wrapper smokes, and
engine locks are product/distribution checks. They are not proof of code
correctness, complete artifact binding, full tamper resistance, or verifier
truth. Evidence-core gaps such as complete artifact indexing, runlog
chain-hardening, and provider event normalization remain Phase 1 work.

## Documentation

- [Architecture](docs/architecture.md)
- [Install](docs/install.md)
- [Workflow Reference](docs/workflow-reference.md)
- [ORRO Strategic Review Spec](docs/orro-strategic-review-spec.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Workstyle Doctrine](docs/workstyle-doctrine.md)
- [Evidence Model](docs/evidence-model.md)
- [Engine Contract](docs/engine-contract.md)
- [Product Reality Check](docs/product-reality-check.md)
- [E2E Smoke Contract](docs/e2e-smoke-contract.md)
- [E2E Smoke Runner](docs/e2e-runner.md)
- [Engine-Lock Update Process](docs/engine-lock-update-process.md)
- [Compatibility Matrix](docs/compatibility-matrix.md)
- [Bootstrap](docs/bootstrap.md)
- [Packaging Decision](docs/packaging-decision.md)
- [Pinned Engine Fallback](docs/pinned-engine-fallback.md)
- [ORRO Command Migration](docs/orro-command-migration.md)
- [Thin Wrapper](docs/thin-wrapper.md)
- [Wrapper Distribution Smoke](docs/wrapper-distribution.md)
- [Repository Strategy](docs/repository-strategy.md)

## Compatibility

Superflow/superflow remains historical compatibility naming in engine repos.
New product documentation should use ORRO/orro.
