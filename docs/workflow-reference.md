# ORRO Workflow Reference

Canonical ORRO flow:

```text
scout -> flowplan -> proofrun -> proofcheck -> handoff
```

Support surfaces:

- `orro advise`: recommend the smallest safe workflow
- `orro init`: setup readiness metadata
- `orro doctor`: readiness check
- `orro engine-lock`: distribution metadata write/check
- `orro flowplan --profile review-only --lane-adapter gemini`: route a
  Gemini read-only review lane through witnessd
- `orro next`: non-executing continuation gate
- `orro auto --dry-run`: recommendation only
- `orro auto --once`: one safe post-run step only
- `orro auto --until-complete`: bounded proofcheck/handoff loop only
- `orro report`: human-facing summary

`orro auto` v0 does not run proofrun or workers.

Formal handoff requires a passing bound `proofcheck-verdict.json`.

The `review-only` profile may produce a Gemini read-only review lane and a
signed `review-receipt`. That receipt is advisory review signal, not proofcheck,
not verifier truth, not execution evidence, and not approval.
