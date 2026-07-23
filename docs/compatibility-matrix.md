# Compatibility Matrix

This matrix records ORRO product/distribution compatibility metadata. It is not
proof, not verifier truth, not approval, and not assurance. It does not replace
Depone or witnessd engine tests, and it does not imply that unlisted future
commits are compatible.

The post-release target state is: `orro` 0.2.22 is published on PyPI. It becomes
true only after `v0.2.22` is tagged and the Trusted-Publishing workflow completes;
until then, PyPI contains the ORRO product line through 0.2.15. This repository is
the canonical 0.2.22 source.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

| Matrix entry | ORRO repo commit | witnessd commit | Depone commit | e2e status | notes |
| --- | --- | --- | --- | --- | --- |
| depone-n-witnessd-n | n/a | `6d9e4be58297e292bd6e6306f93d432857eaecf1` | `ea1055f756d580784be8448c470ac068518f7568` | pass | Current locally validated engine pair; witnessd v2.21.0. |
| depone-n-witnessd-n-1 | n/a | `d601fa86fd8b658e8f4a2cf7fa4b35bde26c554d` | `0e86a55ad10c464d35308a7b6315860a47bcf8a5` | warn | Declared downgrade row, not a release lock. |
| depone-n-1-witnessd-n | n/a | `90d4bc77b71cecf464f1f8a820d9fe17b308211f` | `b203130b5720c6ef6fc9b7492f085ac5ee733786` | warn | Declared downgrade row, not a release lock. |
| orro-rc-locked-triplet | `b2754b6acb0d8aa22085bb6118e5aced63e00c44` | `6d9e4be58297e292bd6e6306f93d432857eaecf1` | `ea1055f756d580784be8448c470ac068518f7568` | pass | Matches witnessd v2.21.0, `engine-lock/orro-e2e-engine-lock.json`, `release/orro-release-manifest.v0.json`, and `release/compatibility-matrix.v0.json`. |

The locked witnessd revision is release `v2.21.0` (source version 2.21.0). It
satisfies the ORRO 0.2.22 package requirement `witnessd>=2.4.0,<3.0.0`.

Related files:

- `engine-lock/orro-e2e-engine-lock.json`
- `release/orro-release-manifest.v0.json`
- `release/compatibility-matrix.v0.json`
- `docs/engine-lock-update-process.md`
