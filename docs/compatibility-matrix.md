# Compatibility Matrix

This matrix records ORRO product/distribution compatibility metadata. It is not
proof, not verifier truth, not approval, and not assurance. It does not replace
Depone or witnessd engine tests, and it does not imply that unlisted future
commits are compatible.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

| Matrix entry | ORRO repo commit | witnessd commit | Depone commit | e2e status | notes |
| --- | --- | --- | --- | --- | --- |
| depone-n-witnessd-n | n/a | `d601fa86fd8b658e8f4a2cf7fa4b35bde26c554d` | `b203130b5720c6ef6fc9b7492f085ac5ee733786` | pass | Current Phase 2 engine pair. |
| depone-n-witnessd-n-1 | n/a | `04740e4e37b621163313e11b35e37addea42f576` | `b203130b5720c6ef6fc9b7492f085ac5ee733786` | warn | Declared downgrade row, not a release lock. |
| depone-n-1-witnessd-n | n/a | `d601fa86fd8b658e8f4a2cf7fa4b35bde26c554d` | `068a664490cc481eeb65947c10b4ef1b0372d410` | warn | Declared downgrade row, not a release lock. |
| orro-rc-locked-triplet | `5e96038311622f612109b78a17b2008509093e92` | `d601fa86fd8b658e8f4a2cf7fa4b35bde26c554d` | `b203130b5720c6ef6fc9b7492f085ac5ee733786` | pass | Matches `engine-lock/orro-e2e-engine-lock.json`, `release/orro-release-manifest.v0.json`, and `release/compatibility-matrix.v0.json`. |

Related files:

- `engine-lock/orro-e2e-engine-lock.json`
- `release/orro-release-manifest.v0.json`
- `release/compatibility-matrix.v0.json`
- `docs/engine-lock-update-process.md`
