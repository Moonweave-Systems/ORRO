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
  --allow-network \
  --workdir /tmp/orro-e2e \
  --json
```

The full smoke creates a fresh virtual environment without system site
packages, removes any interpreter-bundled `setuptools`, confirms it is absent,
and uses pip build isolation to install the wrapper against the build
requirements declared in `pyproject.toml`. Pass `--allow-network` to authorize
that build-dependency bootstrap. The install may use a populated pip cache;
otherwise it requires access to a configured package index. The flag
authorizes only this wrapper build bootstrap and does not allow engine checkout
mutation.

Environment variables are also supported:

```text
ORRO_WITNESSD_ROOT
ORRO_DEPONE_ROOT
```

Resolution order is explicit CLI argument, environment variable, then sibling
checkout candidates.

Use `scripts/bootstrap_orro.py --check-existing` before local smoke runs when
you want to confirm that local engine checkout commits match the pinned engine
lock. The bootstrap is setup/distribution orchestration and setup metadata, not
proof. It contains no engine code and the ORRO-owned executable `orro` command
delegates to the witnessd-hosted engine surface.

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
wrapper install smoke, wrapper distribution smoke, and `--self-test`. The
separate pinned-engine e2e CI checks out the pinned witnessd and Depone commits
from the e2e lock, then runs the full smoke.

The ORRO product line is published on PyPI through 0.2.2. This pinned-engine
smoke validates the 0.2.3 source package without publishing a new release.
