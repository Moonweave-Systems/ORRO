# Review Only

Use `review-only` when the task is to inspect, summarize, or review without executing a change.

```bash
orro advise "review this PR and summarize risks" --repo . --home .witnessd --json
orro flowplan "review this PR and summarize risks" \
  --root . \
  --profile review-only \
  --out .witnessd/workflow-plan.json
```

Review-only intent does not launch proofrun. Formal ORRO handoff still requires a passing bound `proofcheck-verdict.json`; review prose is not approval and not proof.
