# Compatibility Matrix

This matrix records ORRO product/distribution compatibility metadata. It is not
proof, not verifier truth, not approval, and not assurance. It does not replace
Depone or witnessd engine tests, and it does not imply that unlisted future
commits are compatible.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

| ORRO repo commit | witnessd commit | Depone commit | e2e status | notes |
| --- | --- | --- | --- | --- |
| pending release manifest | `9225986ca60a23633d97b3f7ab43b274eae81043` | `39c38181e701a3bb5526700dd61f948ca0229b2d` | pass | Matches `engine-lock/orro-e2e-engine-lock.json` and `release/orro-release-manifest.v0.json`. |

Related files:

- `engine-lock/orro-e2e-engine-lock.json`
- `release/orro-release-manifest.v0.json`
- `docs/engine-lock-update-process.md`
