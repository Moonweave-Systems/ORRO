# ORRO E2E Smoke Contract

This directory documents the end-to-end smoke contract. The runnable local
harness lives at:

```text
scripts/orro_e2e_smoke.py
```

The runner calls the existing witnessd-hosted `orro` command against local
witnessd and Depone checkouts. It does not import engine internals and does not
implement proofrun, proofcheck, scheduling, observing, fan-in, team-ledger, or
verifier logic.

Actual engine tests still live in witnessd and Depone. This ORRO repository
owns product-level orchestration smoke checks and e2e contract documentation.

Future pinned-engine smoke checks should:

1. Install witnessd and Depone from pinned refs.
2. Run `orro advise`.
3. Run `orro init`.
4. Run `orro flowplan`.
5. Run `orro proofrun`.
6. Run `orro proofcheck`.
7. Run `orro handoff`.
8. Run `orro report`.
9. Assert scout-only artifacts do not pass proofcheck.
10. Assert report does not overclaim.
11. Assert handoff requires proofcheck.
12. Assert auto v0 does not run proofrun.

Depone verifies; witnessd executes; ORRO exposes the workflow.
