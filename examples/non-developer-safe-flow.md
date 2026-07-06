# Non-Developer Safe Flow

For a non-developer operator, start with advice and report rather than unbounded automation.

```bash
orro advise "make the documentation clearer" --repo . --home .witnessd --json
orro flowplan "make the documentation clearer" --root . --profile docs-change --out .witnessd/workflow-plan.json
```

After any observed run exists:

```bash
orro next .witnessd/runs/<run-dir> --home .witnessd --json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

Safe interpretation:

- If report says `needs-proofcheck`, run proofcheck next.
- If report says `ready-for-handoff`, package handoff next.
- If report says `blocked`, stop for human or verifier intervention.
- Do not treat report, handoff prose, model confidence, or workflow plans as proof.
