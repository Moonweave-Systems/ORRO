# ORRO Engine Contract

This document links and summarizes the engine contracts. It does not replace
them.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

- Depone verifier contract is authoritative for proofcheck semantics.
- witnessd runtime contract is authoritative for emitted execution artifacts.
- ORRO must not redefine verifier truth.

## Artifact Classes

| Class | Artifacts |
| --- | --- |
| execution evidence | `team-ledger.json`, `verification-receipt.json` |
| verifier output | `proofcheck-verdict.json`, `team-ledger-verdict.json` |
| intent | `workflow-plan.json`, `role-lane-plan.json`, `verification-recipe.json` |
| wrapper context | `workflow-plan-binding.json`, `role-lane-plan-binding.json`, `workflow-role-dispatch.json`, `orro-continuation-decision.json`, `orro-auto-plan.json`, `orro-auto-receipt.json`, `orro-auto-session.json`, `orro-report.json` |
| review package | `orro-handoff.json` |
| distribution metadata | `orro-engine-lock.json`, `orro-e2e-engine-lock.json`, `orro-release-manifest.v0.json` |

## Trust Rules

- Workflow plan is intent, not proof.
- Role-lane plan is executable intent, not proof.
- Role dispatch is context, not proof.
- Auto artifacts are orchestration metadata, not proof.
- Report is summary, not proof.
- Handoff is review package, not approval.
- Engine-lock is distribution metadata, not proof.
- Release manifest is product/distribution metadata, not proof and not verifier truth.
- Existing proofcheck verdict is verifier output, not an input trust root.
