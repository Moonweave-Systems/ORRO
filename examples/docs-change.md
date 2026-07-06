# Docs Change

Use the `docs-change` profile for documentation edits. ORRO should still avoid overclaiming.

```bash
orro advise "update README setup steps" --repo . --home .witnessd --json
orro flowplan "update README setup steps" \
  --root . \
  --profile docs-change \
  --out .witnessd/workflow-plan.json
```

If the change needs formal observed execution, run `proofrun` and then `proofcheck` before handoff. Do not treat edited prose, workflow plans, or reports as proof.
