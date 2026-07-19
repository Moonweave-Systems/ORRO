# Compatibility Matrix

This matrix records ORRO product/distribution compatibility metadata. It is not
proof, not verifier truth, not approval, and not assurance. It does not replace
Depone or witnessd engine tests, and it does not imply that unlisted future
commits are compatible.

The post-release target state is: `orro` 0.2.9 is published on PyPI. It becomes
true only after `v0.2.9` is tagged and the Trusted-Publishing workflow completes;
until then, PyPI contains the ORRO product line through 0.2.8. This repository is
the canonical 0.2.9 source.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

| Matrix entry | ORRO repo commit | witnessd commit | Depone commit | e2e status | notes |
| --- | --- | --- | --- | --- | --- |
| depone-n-witnessd-n | n/a | `cd4816756847b24385ea6a58610933a1cec77a6b` | `1932f00802f817822d49c70616e963d11227d7fb` | pass | Current locally validated engine pair; witnessd v2.7.0. |
| depone-n-witnessd-n-1 | n/a | `d601fa86fd8b658e8f4a2cf7fa4b35bde26c554d` | `0e86a55ad10c464d35308a7b6315860a47bcf8a5` | warn | Declared downgrade row, not a release lock. |
| depone-n-1-witnessd-n | n/a | `90d4bc77b71cecf464f1f8a820d9fe17b308211f` | `b203130b5720c6ef6fc9b7492f085ac5ee733786` | warn | Declared downgrade row, not a release lock. |
| orro-rc-locked-triplet | `72f3e1f8685eb8c2e61b8708542b81d40b2f2056` | `cd4816756847b24385ea6a58610933a1cec77a6b` | `1932f00802f817822d49c70616e963d11227d7fb` | pass | Matches witnessd v2.7.0, `engine-lock/orro-e2e-engine-lock.json`, `release/orro-release-manifest.v0.json`, and `release/compatibility-matrix.v0.json`. |

The locked witnessd revision is release `v2.7.0` (source version 2.7.0). It
satisfies the ORRO 0.2.9 package requirement `witnessd>=2.4.0,<3.0.0`.

Related files:

- `engine-lock/orro-e2e-engine-lock.json`
- `release/orro-release-manifest.v0.json`
- `release/compatibility-matrix.v0.json`
- `docs/engine-lock-update-process.md`
