# ORRO E2E Smoke Runner

`scripts/orro_e2e_smoke.py` is a local smoke harness for the ORRO product repo.
It orchestrates local witnessd and Depone checkouts through subprocess calls to
the existing witnessd-hosted `orro` command.

```bash
python3 scripts/orro_e2e_smoke.py \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --require-lock-match \
  --workdir /tmp/orro-e2e \
  --json
```

Environment variables are also supported:

```text
ORRO_WITNESSD_ROOT
ORRO_DEPONE_ROOT
```

Resolution order is explicit CLI argument, environment variable, then sibling
checkout candidates.

## Boundary

Depone verifies; witnessd executes; ORRO exposes the workflow.

The runner is not an engine. It does not implement proofrun, proofcheck,
scheduling, observing, fan-in, team-ledger validation, or verifier logic. It
does not approve merge or raise assurance. The e2e result is test metadata, not
proof.

## Engine Lock

`engine-lock/orro-e2e-engine-lock.json` pins the witnessd and Depone commits
used by ORRO repo e2e CI. This engine lock is distribution and CI metadata, not
proof, not verifier truth, not merge approval, and not assurance.

When `--engine-lock` and `--require-lock-match` are supplied, the runner checks
that local engine checkout `HEAD` commits match the pinned commits. It does not
fetch, update, or mutate engine repositories.

## What It Checks

The happy path runs:

```text
advise -> init -> doctor -> engine-lock -> flowplan -> proofrun -> next -> auto --until-complete -> report
```

The negative path checks that scout-only artifacts do not proofcheck-pass or
become handoff-complete.

## CI

ORRO repo boundary CI runs the repository contract checker, script compilation,
and `--self-test`. The separate pinned-engine e2e CI checks out the pinned
witnessd and Depone commits from the e2e lock, then runs the full smoke.

Published ORRO package e2e remains future work.
