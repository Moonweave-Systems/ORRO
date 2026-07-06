# Release Readiness

Use release-readiness flows to check setup, pinned engines, and post-run state.

```bash
orro doctor --home .witnessd --json
orro engine-lock --home .witnessd --out .witnessd/orro-engine-lock.json
orro engine-lock --home .witnessd --check .witnessd/orro-engine-lock.json --json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

Doctor and engine-lock are readiness and distribution checks only. They are not proof, not approval, and not assurance.
