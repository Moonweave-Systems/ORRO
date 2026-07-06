# Code Change

Use the `code-change` profile when the goal likely changes source behavior.

```bash
orro advise "fix parser bug" --repo . --home .witnessd --json
orro flowplan "fix parser bug" \
  --root . \
  --profile code-change \
  --out .witnessd/workflow-plan.json \
  --role-lanes-out .witnessd/role-lane-plan.json
orro proofrun "fix parser bug" \
  --repo . \
  --home .witnessd \
  --workflow-plan .witnessd/workflow-plan.json \
  --role-lane-plan .witnessd/role-lane-plan.json
orro proofcheck .witnessd/runs/<run-dir> \
  --home .witnessd \
  --out .witnessd/runs/<run-dir>/proofcheck-verdict.json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

The workflow plan is intent, not proof. Actual proof starts with witnessd evidence and Depone proofcheck.
