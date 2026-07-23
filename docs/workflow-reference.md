# ORRO Workflow Reference

Golden path:

```bash
orro setup --home .witnessd --json
orro flow "<goal>" --write-scope "<glob>" --adapter codex --json
orro check --home .witnessd --json
```

`orro demo` shows the whole guardrail idea in 30 seconds with no AI adapter.
Use `orro status` for roadmap/evidence-bound progress.

Canonical ORRO flow:

```text
setup -> flow -> check -> handoff
```

## Advanced: manual composition

For explicit composition, use `orro flow` or `orro team go`; proofrun and
proofcheck must share one run directory.

```bash
orro advise "fix parser bug" --repo . --home .witnessd --json
orro init --home .witnessd --depone-root ../Depone
orro doctor --home .witnessd --json
orro engine-lock --home .witnessd --out .witnessd/orro-engine-lock.json
orro scout "fix parser bug" --repo . --home .witnessd
orro flowplan "fix parser bug" --root . --profile code-change --out .witnessd/workflow-plan.json
orro proofrun "fix parser bug" --repo . --home .witnessd --workflow-plan .witnessd/workflow-plan.json
orro proofcheck .witnessd/runs/<run-dir> --home .witnessd --out .witnessd/runs/<run-dir>/proofcheck-verdict.json
orro handoff .witnessd/runs/<run-dir> --out .witnessd/runs/<run-dir>/orro-handoff.json
orro report .witnessd/runs/<run-dir> --home .witnessd
```

Support surfaces:

- `orro advise`: recommend the smallest safe workflow
- `orro init`: setup readiness metadata
- `orro doctor`: readiness check
- `orro engine-lock`: distribution metadata write/check
- `orro flowplan --profile review-only --lane-adapter gemini`: route a
  Gemini read-only review lane through witnessd
- `orro flowplan --profile review-only --lane-adapter agy`: route a
  Google Antigravity read-only review lane through witnessd
- `orro next`: non-executing continuation gate
- `orro auto --dry-run`: recommendation only
- `orro auto --once`: one safe post-run step only
- `orro auto --until-complete`: bounded proofcheck/handoff loop only
- `orro report`: human-facing summary

`orro auto` v0 does not run proofrun or workers.

Formal handoff requires a passing bound `proofcheck-verdict.json`.

The `review-only` profile may produce a Gemini or Antigravity read-only review
lane and a signed `review-receipt`. That receipt is advisory review signal,
not proofcheck, not verifier truth, not execution evidence, and not approval.
