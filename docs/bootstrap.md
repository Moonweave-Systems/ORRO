# ORRO Bootstrap

`scripts/bootstrap_orro.py` helps prepare or inspect local engine checkouts from
`engine-lock/orro-e2e-engine-lock.json`.

Depone verifies; witnessd executes; ORRO exposes the workflow.

The bootstrap is setup/distribution orchestration. It is not an engine, not a
verifier, and not an execution runtime. It contains no engine code and does not
implement proofrun, proofcheck, scheduling, observing, fan-in, team-ledger, or
verifier logic.

Bootstrap output is setup metadata, not proof, not verifier truth, not merge
approval, and not assurance. The current executable `orro` command remains
witnessd-hosted until a future package exists.

## Dry Run

Dry-run is the default mode. It reads the pinned engine lock and emits an
`orro-bootstrap-plan` without cloning, fetching, installing, or mutating files.

```bash
python3 scripts/bootstrap_orro.py \
  --dry-run \
  --workspace /tmp/orro-workspace \
  --json
```

The plan describes how witnessd and Depone checkouts would be prepared. It does
not run proofrun, proofcheck, handoff, auto, live models, or MCP calls.

## Check Existing

`--check-existing` inspects local engine roots and compares their `HEAD` commits
to the pinned engine lock.

```bash
python3 scripts/bootstrap_orro.py \
  --check-existing \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --json
```

This mode does not mutate the engine repositories. A match is distribution
readiness metadata only; it is not proof and does not verify evidence.

If a checkout is missing or mismatched, bootstrap follows the fail-closed policy
in `docs/pinned-engine-fallback.md`. It reports the blocker and does not silently
use latest `main`, auto-select alternate engine commits, or rewrite the engine
lock during setup.

## Execute

`--execute` is bounded setup. It may prepare local engine checkouts only when
network access is explicitly allowed.

```bash
python3 scripts/bootstrap_orro.py \
  --execute \
  --workspace /tmp/orro-workspace \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --allow-network \
  --json
```

`--execute` may clone witnessd and Depone and check out the pinned commits. It
does not run proofrun, proofcheck, handoff, or auto. Editable witnessd install is
separate and requires the explicit `--install-witnessd` flag:

```bash
python3 scripts/bootstrap_orro.py \
  --execute \
  --workspace /tmp/orro-workspace \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --allow-network \
  --install-witnessd \
  --json
```

Published ORRO package remains future work.

The wrapper distribution smoke is separate from bootstrap:

```bash
python3 scripts/check_orro_wrapper_distribution.py --json
```

It builds and installs a local wheel to verify packaging boundaries. It does not
prepare engine checkouts, does not verify evidence, does not publish a package,
and does not shadow the witnessd-hosted `orro` command.

## Self-Test

The self-test requires no network and no engine checkouts:

```bash
python3 scripts/bootstrap_orro.py --self-test
```

It checks engine-lock validation, mode conflicts, dry-run output shape, mismatch
handling, and that dry-run planned steps do not include proofrun, proofcheck, or
handoff commands.
