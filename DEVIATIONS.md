# Deviations

Stopped before commit, push, and PR creation as required by the release task.

The supplied witnessd replacement `3374265a48cf8fc1d8ea4bc6801d5ec3e58e58b`
contains 39 hexadecimal characters, not the required 40 for a Git commit. The
repository's live checkers reject it as invalid:

- `scripts/check_orro_repo_contract.py`: `e2e engine lock witnessd.commit must be a 40-hex commit`
- `scripts/check_orro_assurance_contract_fixtures.py`: baseline contract failed for the same reason
- `scripts/check_orro_release_manifest.py`: `engines.witnessd.commit must be a 40-hex commit`
- `scripts/check_compatibility_matrix.py --metadata-only`: `depone-n-witnessd-n.witnessd_commit must be a 40-hex commit`

The old pin `56dad84ea28c82a28837d96e83c9cd5215da213b` is 40 hexadecimal
characters. No commit or PR was created.

## Wrapper front-door task (2026-07-22)

Stopped before tests, implementation, checker runs, and commit because the
task's grounded current-state description contradicts `91a7356`:

- `src/orro_wrapper/cli.py:154-155` already forwards every bare command that is
  not `boundary`, `self-test`, or `delegate`. Stubbed calls confirmed that both
  `demo --help` and the unknown typo `demmo` call `delegate(None, argv)` and
  return its exit code. Therefore `orro demo` is already routed rather than
  rejected by argparse, while truly unknown verbs are also delegated.
- The requested "existing helpful unknown command + did-you-mean + valid list"
  path does not exist. The only `ERR_ORRO_WRAPPER_COMMAND_UNKNOWN` branch is
  unreachable for a bare unknown verb after the early blanket delegation, and
  the repository contains no did-you-mean implementation.
- The help mirror in `src/orro_wrapper/cli.py` also omits authoritative workflow
  verbs `demo` and `lock`, so it is not currently synchronized with the supplied
  engine command set.

The requested end state remains implementable without engine logic: replace the
blanket forwarding condition with a single mirrored known-command allowlist,
route those commands through the existing `delegate()` subprocess seam, add a
new local unknown-command suggestion/error path, and generate tiered help from
that same command data. No wrapper boundary metadata needs to change. Per the
task's explicit `If a step contradicts the code, STOP -> DEVIATIONS.md`
instruction, no such implementation was attempted and no commit was created.
