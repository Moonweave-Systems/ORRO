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
| `560b63f5b7189fa6bb93d76fb382b25bb33e89f3` | `4679ce1833d00fd1812b8ba7e2bc83ac67bd1cc2` | `74cf276c7c85b54b906f1b93755ee705a8f6640a` | pass | Matches `engine-lock/orro-e2e-engine-lock.json` and `release/orro-release-manifest.v0.json`. |

Related files:

- `engine-lock/orro-e2e-engine-lock.json`
- `release/orro-release-manifest.v0.json`
- `docs/engine-lock-update-process.md`
