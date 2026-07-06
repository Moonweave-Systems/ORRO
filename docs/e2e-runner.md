# ORRO E2E Smoke Runner

`scripts/orro_e2e_smoke.py` is a local smoke harness for the ORRO product repo.
It orchestrates local witnessd and Depone checkouts through subprocess calls to
the existing witnessd-hosted `orro` command.

```bash
python3 scripts/orro_e2e_smoke.py \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
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

## What It Checks

The happy path runs:

```text
advise -> init -> doctor -> engine-lock -> flowplan -> proofrun -> next -> auto --until-complete -> report
```

The negative path checks that scout-only artifacts do not proofcheck-pass or
become handoff-complete.

## CI

ORRO repo CI runs only the repository contract checker, script compilation, and
`--self-test`. Full e2e against pinned engine refs remains future work because
the ORRO repo should not clone or vendor engine code in boundary-checking CI.
