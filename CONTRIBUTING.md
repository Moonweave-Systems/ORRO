# Contributing

ORRO is the product, documentation, examples, distribution, and wrapper-planning
home for the user-facing workflow surface.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
Humans retain judgment.
```

handoff is not approval.

report is not proof.

## Scope

Docs, schemas, contract checks, wrapper/distribution metadata, and
harness-surface changes are in scope.

Engine, verifier, runtime, proofrun, proofcheck, scheduler, observer, fan-in,
and package publish changes are out of scope. ORRO command ownership changes
must stay limited to thin wrapper metadata and delegation surfaces.

No new dependencies without explicit approval. Prefer Python stdlib-only scripts
for repository contract and hygiene checks.

## Review Expectations

Pull requests should be small, reviewable, and tied to a specific repository
contract or documentation boundary. They should preserve existing ORRO doctrine:

- Depone owns verifier semantics and proofcheck truth.
- witnessd owns execution runtime behavior and evidence emission.
- ORRO exposes workflow, harness, documentation, wrapper, and distribution
  surfaces.
- Humans retain judgment.

Do not describe reports, handoffs, smoke checks, engine locks, release manifests,
or wrapper metadata as proof, approval, verifier truth, package publish, or
raised assurance.

## Verification

Run the smallest relevant local checks for the changed surface. For repository
boundary changes, prefer:

```bash
python3 scripts/check_orro_repo_contract.py
python3 scripts/check_orro_assurance_contract_fixtures.py
git diff --check
```

If a script does not exist in the current branch, do not invent it only to satisfy
PR wording. State the gap in the PR notes instead.
