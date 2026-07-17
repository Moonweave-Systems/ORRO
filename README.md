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
- This repository keeps ORRO docs, product boundary, locks, thin wrapper package metadata, assurance contract checks, and integration-surface policy.
- The runnable `orro` command is ORRO-owned and delegates to witnessd.
- The ORRO product line is published on PyPI through 0.2.0, while this repository
  packages the 0.2.1 release candidate. The post-release target state is: `orro`
  0.2.1 is published on PyPI. It becomes true only after `v0.2.1` is tagged and
  the Trusted-Publishing workflow completes. Until then, a normal
  `pip install orro` installs 0.2.0.
- The local wrapper package exposes both `orro` and `orro-wrapper`.

Current focus:
- Make AI-assisted work reviewable.
- Prevent handoff/report/proof/approval confusion.
- Grow automation only through checkpointed workflows.
- Keep integration surfaces plugin-first and MCP-optional.

## Can I use ORRO today?

Yes. The published ORRO product line is installable from PyPI at 0.2.0, and
development dogfood can run the 0.2.1 source directly against pinned Depone and
witnessd checkouts.

Current split:

- ORRO owns the runnable `orro` workflow command surface and delegates execution
  to witnessd.
- This ORRO repository owns the product boundary, documentation, locks, wrapper
  package metadata, and assurance contracts.
- `orro-wrapper` remains a compatibility alias for the same wrapper module.

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

Current command source: the `orro` command is exposed by this ORRO package and
delegates to `python -m orro`.

The 0.2.1 package metadata declares `witnessd>=2.4.0,<3.0.0` while keeping Depone and
witnessd as separate engine repositories.

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
approval, and not assurance. This manifest does not publish a package.

Engine-lock update discipline is documented in
[`docs/engine-lock-update-process.md`](docs/engine-lock-update-process.md), and
validated engine pairs are listed in
[`docs/compatibility-matrix.md`](docs/compatibility-matrix.md). The `orro`
product line is published on PyPI through 0.2.0; this repository sources 0.2.1,
whose publication will be completed as a separate release step after the
`v0.2.1` tag triggers the
Trusted-Publishing workflow. Repository metadata changes do not publish or
rewrite an artifact.

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
run proofrun/proofcheck/handoff by default. The ORRO-owned `orro` command
delegates runtime behavior to witnessd.

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

The current command source is the ORRO-owned `orro` console script. The ORRO
product line is published on PyPI through 0.2.0, and this repository prepares
source version 0.2.1 with a `witnessd>=2.4.0,<3.0.0` dependency. The wrapper contains no
engine code and must not
implement proofrun, proofcheck, scheduler, observer, fan-in, team-ledger, or
verifier logic.

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

## Thin Wrapper

The ORRO-owned `orro` command is the thin wrapper surface in this repository.
`orro-wrapper` remains a compatibility alias. Both can report wrapper boundary
metadata and delegate commands to the existing witnessd engine command.

```bash
python3 -m pip install -e .
orro-wrapper boundary
orro boundary
orro-wrapper self-test
orro-wrapper delegate -- --help
```

The wrapper is not proof, not verifier truth, not package publish, not approval,
and not assurance. It contains no engine code and does not implement proofrun or
proofcheck.

The wrapper install smoke verifies the editable package and installed `orro` and
`orro-wrapper` console scripts without publishing a package or calling engine
repos:

```bash
python3 scripts/check_orro_wrapper_install.py --json
```

The install smoke is setup/test metadata, not proof, not verifier truth, not
package publish, not approval, and not assurance.

## Wrapper Distribution Smoke

The wrapper distribution smoke builds a local wheel, installs it into a
temporary virtual environment, and verifies that `orro` and `orro-wrapper` are
exposed:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json --allow-network
```

The distribution smoke checks that the wheel contains no Depone or witnessd
packages and no proofrun/proofcheck runtime implementation files.
The explicit network flag authorizes pip build isolation to provision the
declared `setuptools>=61` build requirement in a clean build environment.

The distribution smoke is local test metadata, not proof, not verifier truth,
not package publish, not approval, and not assurance.

## ORRO Command Migration

The executable `orro` command is ORRO-owned, thin, and delegates to witnessd.
The command migration is documented in
[`docs/orro-command-migration.md`](docs/orro-command-migration.md).

The migration does not publish a package, does not move engine code, and does
not change verifier or runtime semantics. `orro-wrapper` remains a compatibility
command for the same thin wrapper module.

`scripts/check_orro_command_migration_dry_run.py` is the dry-run harness for
the former plan-only wave. Dry-run metadata is not proof; committed package
metadata is now the command ownership source of truth.

## Install Reality

```bash
git clone https://github.com/Moonweave-Systems/Depone.git
git clone https://github.com/Moonweave-Systems/witnessd.git
cd witnessd
python3 -m pip install -e .
orro init --home .witnessd --depone-root ../Depone
```

For the local ORRO wrapper package:

```bash
cd ORRO
python3 -m pip install -e .
orro-wrapper boundary
orro boundary
orro-wrapper self-test
```

The wrapper is product/distribution metadata and a thin delegation surface. It
is not proof, not verifier truth, not package publish, not approval, and not
assurance.

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
