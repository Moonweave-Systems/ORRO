# ORRO E2E Smoke Contract

The ORRO repository now includes a lightweight local smoke harness:

```bash
python3 scripts/orro_e2e_smoke.py \
  --witnessd-root ../witnessd \
  --depone-root ../Depone \
  --engine-lock engine-lock/orro-e2e-engine-lock.json \
  --require-lock-match \
  --workdir /tmp/orro-e2e \
  --json
```

The harness orchestrates local engine checkouts by calling the existing
witnessd-hosted `orro` command. It is not an engine, does not implement
proofrun or proofcheck, and does not approve merge or raise assurance.

## Current Local Smoke

The current runner checks:

- `orro advise`
- `orro init`
- `orro doctor`
- `orro engine-lock --out`
- `orro engine-lock --check`
- `orro flowplan`
- `orro proofrun`
- `orro next`
- `orro auto --until-complete`
- `orro report`
- scout-only artifacts do not proofcheck-pass

The e2e result is test metadata, not proof.

## Pinned-Engine CI

ORRO e2e CI reads `engine-lock/orro-e2e-engine-lock.json`, checks out the pinned
witnessd and Depone commits, requires the local checkout commits to match the
lock, and asserts:

- `orro advise` recommends the smallest safe workflow
- `orro init` creates readiness metadata
- `orro flowplan` writes intent artifacts
- `orro proofrun` emits execution evidence
- `orro proofcheck` delegates verifier semantics to Depone
- `orro handoff` requires a passing bound proofcheck verdict
- `orro report` does not overclaim
- scout-only artifacts do not pass proofcheck
- auto v0 does not run proofrun

The e2e engine lock is distribution and CI metadata, not proof, not verifier
truth, not approval, and not assurance. Future published-package e2e remains
future work.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```
