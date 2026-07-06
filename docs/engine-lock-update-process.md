# Engine-Lock Update Process

The ORRO pinned engine lock is updated intentionally by pull request.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

`engine-lock/orro-e2e-engine-lock.json` records the witnessd and Depone engine
pair used by ORRO pinned-engine e2e CI. Engine-lock match is distribution
readiness only, not proof, not verifier truth, not approval, and not assurance.

Depone proofcheck remains verifier truth. witnessd remains runtime truth for
execution artifacts. The ORRO repository does not contain engine code and must
not redefine verifier or runtime semantics.

## Update Rules

- Update the engine lock only in a reviewable PR.
- Prefer `scripts/update_orro_engine_lock.py` so the engine lock, release
  manifest, and compatibility matrix move together.
- State the witnessd commit and Depone commit in the PR.
- Do not update one engine pin blindly if cross-engine e2e fails.
- If witnessd or Depone contract changes, update ORRO engine contract docs and
  examples as needed.
- Keep `release/orro-release-manifest.v0.json` aligned with the engine lock.

## Checklist

1. Run:

   ```bash
   python3 scripts/update_orro_engine_lock.py \
     --witnessd-commit <40-hex-witnessd-commit> \
     --depone-commit <40-hex-depone-commit>
   ```

2. Confirm it updated:

   - `engine-lock/orro-e2e-engine-lock.json`
   - `release/orro-release-manifest.v0.json`
   - `docs/compatibility-matrix.md`

3. Run `python3 scripts/check_orro_repo_contract.py`.
4. Run `python3 scripts/check_orro_release_manifest.py`.
5. Run `python3 scripts/update_orro_engine_lock.py --self-test`.
6. Run `python3 scripts/orro_e2e_smoke.py --engine-lock engine-lock/orro-e2e-engine-lock.json --require-lock-match`.
7. Confirm boundary text.
8. Open a PR with engine commits and test results.
