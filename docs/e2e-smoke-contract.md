# ORRO E2E Smoke Contract

Future e2e smoke checks should:

- install ORRO/witnessd/Depone from pinned refs
- run `orro init`
- run `orro advise`
- run `orro flowplan`
- run `orro proofrun`
- run `orro proofcheck`
- run `orro handoff`
- run `orro report`
- assert scout-only does not pass
- assert report does not overclaim
- assert handoff requires proofcheck
- assert auto v0 does not run proofrun

This document is a contract, not a heavy runner.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```
