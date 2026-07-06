# Verification Only

Use `verification-only` when evidence already exists and the task is to verify it.

```bash
orro advise "verify existing evidence" --repo . --home .witnessd --json
orro proofcheck .witnessd/runs/<run-dir> \
  --home .witnessd \
  --out .witnessd/runs/<run-dir>/proofcheck-verdict.json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

Verification-only should recommend proofcheck over proofrun. Depone verifies persisted evidence bytes; ORRO does not become the verifier.
