# Pinned Engine Fallback Policy

Depone verifies; witnessd executes; ORRO exposes the workflow.

This policy defines what ORRO product tooling may do when the pinned witnessd or
Depone engine commits are unavailable, missing locally, or mismatched.

The fallback policy is product/distribution metadata, not proof, not verifier
truth, not package publish, not approval, and not assurance.

## Default Behavior

Fail closed.

ORRO tooling must not silently replace a pinned engine commit with `main`, a
nearby tag, a cached checkout, or any other unpinned commit. If the pinned engine
cannot be found, checked out, or matched, the correct result is a clear setup
blocker.

## Allowed Responses

- Missing engine root: report the missing root and suggest `bootstrap_orro.py
  --dry-run` or explicit `--execute --allow-network`.
- Commit mismatch: report expected and actual commits, then require checkout
  correction or an intentional engine-lock update PR.
- Network checkout unavailable: stop with a setup blocker and do not silently use
  another commit.

## Forbidden Responses

- silently use latest `main`;
- silently use a nearby tag;
- rewrite `engine-lock/orro-e2e-engine-lock.json` during bootstrap;
- downgrade `--require-lock-match`;
- run proofrun to test setup availability;
- run proofcheck to test setup availability;
- treat fallback as proof;
- treat fallback as verifier truth.

## Human Actions

When a pinned engine is unavailable, the operator may:

1. Correct the local checkout to the pinned commit.
2. Run bootstrap dry-run to inspect setup steps.
3. Run bootstrap execute with explicit `--allow-network` when network checkout is
   intended.
4. Open an engine-lock update PR when ORRO should validate a newer witnessd and
   Depone engine pair.

## Relationship To Bootstrap

`scripts/bootstrap_orro.py` already follows this policy:

- `--dry-run` does not clone, fetch, install, or mutate;
- `--check-existing` reports commit mismatches;
- `--execute` requires explicit `--allow-network` before cloning;
- no mode runs proofrun, proofcheck, handoff, or auto by default.

Bootstrap receipts are setup metadata, not proof. Engine-lock match is
distribution readiness metadata, not verifier truth.

## Relationship To The Published Wrapper

The published thin wrapper follows this policy. It may report missing or
mismatched engines and point to bootstrap/setup commands, but it must not
auto-select different engine commits or rewrite the engine lock outside an
intentional update PR.

The post-release target state is: `orro` 0.2.10 is published on PyPI. It becomes
true only after `v0.2.10` is tagged and the Trusted-Publishing workflow completes;
until then, PyPI contains the ORRO product line through 0.2.9. This repository is
the canonical 0.2.10 source, whose metadata declares `witnessd>=2.4.0,<3.0.0`. The current
engine lock pins witnessd 2.8.0 at tag `v2.8.0`, satisfying that dependency.
