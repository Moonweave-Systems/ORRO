# ORRO Evidence Model

ORRO distinguishes intent, execution evidence, verifier output, and review
packaging.

Intent documents describe what should happen. They are not proof.

Execution evidence records what witnessd observed during a run.

Verifier output is emitted by Depone after it re-derives what persisted evidence
bytes support.

Review packaging helps humans inspect the result. It is not merge approval.

Examples:

- `workflow-plan.json`: intent, not proof
- `role-lane-plan.json`: executable intent, not proof
- `team-ledger.json`: execution evidence candidate
- `verification-receipt.json`: execution evidence when valid
- `proofcheck-verdict.json`: verifier output
- `orro-report.json`: summary, not proof
- `orro-handoff.json`: review package, not approval
- `orro-engine-lock.json`: distribution metadata, not proof
