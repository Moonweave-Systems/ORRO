# ORRO E2E Smoke Contract

This directory currently documents the future end-to-end smoke contract. It does not contain a heavy runner yet.

Actual engine tests live in witnessd and Depone. This ORRO repository documents
the smoke contract and product expectations only.

Future smoke checks should:

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
