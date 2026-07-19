# Compatibility Matrix

This matrix records ORRO product/distribution compatibility metadata. It is not
proof, not verifier truth, not approval, and not assurance. It does not replace
Depone or witnessd engine tests, and it does not imply that unlisted future
commits are compatible.

The post-release target state is: `orro` 0.2.11 is published on PyPI. It becomes
true only after `v0.2.11` is tagged and the Trusted-Publishing workflow completes;
until then, PyPI contains the ORRO product line through 0.2.10. This repository is
the canonical 0.2.11 source.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

| Matrix entry | ORRO repo commit | witnessd commit | Depone commit | e2e status | notes |
| --- | --- | --- | --- | --- | --- |
| depone-n-witnessd-n | n/a | `179a7856d8d8d5ff584cc75ddf3a6999cdc25032` | `1932f00802f817822d49c70616e963d11227d7fb` | pass | Current locally validated engine pair; witnessd v2.9.0. |
| depone-n-witnessd-n-1 | n/a | `d601fa86fd8b658e8f4a2cf7fa4b35bde26c554d` | `0e86a55ad10c464d35308a7b6315860a47bcf8a5` | warn | Declared downgrade row, not a release lock. |
| depone-n-1-witnessd-n | n/a | `90d4bc77b71cecf464f1f8a820d9fe17b308211f` | `b203130b5720c6ef6fc9b7492f085ac5ee733786` | warn | Declared downgrade row, not a release lock. |
| orro-rc-locked-triplet | `e3e0b55187cb251cccc6b4f90fd0adeb05a58db5` | `179a7856d8d8d5ff584cc75ddf3a6999cdc25032` | `1932f00802f817822d49c70616e963d11227d7fb` | pass | Matches witnessd v2.9.0, `engine-lock/orro-e2e-engine-lock.json`, `release/orro-release-manifest.v0.json`, and `release/compatibility-matrix.v0.json`. |

The locked witnessd revision is release `v2.9.0` (source version 2.9.0). It
satisfies the ORRO 0.2.11 package requirement `witnessd>=2.4.0,<3.0.0`.

Related files:

- `engine-lock/orro-e2e-engine-lock.json`
- `release/orro-release-manifest.v0.json`
- `release/compatibility-matrix.v0.json`
- `docs/engine-lock-update-process.md`
