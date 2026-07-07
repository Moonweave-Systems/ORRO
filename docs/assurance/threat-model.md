# ORRO Assurance Threat Model

ORRO is a workflow and harness surface. It does not execute commands, verify evidence, approve merges, or raise assurance by itself.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
Verified acceleration, not blind automation.
Humans retain judgment.
```

## Trust Boundaries

| Boundary | Owner | ORRO rule |
| --- | --- | --- |
| Execution/runtime | witnessd | ORRO may expose commands and reports, but must not implement runtime behavior. |
| Evidence emission | witnessd | ORRO may reference evidence paths, but must not synthesize runtime evidence. |
| Proofcheck truth | Depone | ORRO may display verdicts, but must not reinterpret failed or missing verdicts as pass. |
| Judgment | Human | ORRO may prepare handoff, but handoff is not approval. |
| Summary | ORRO | report is not proof. |

## Threats

The strategic review corpus records short negative language cases for doctrine
confusion, including prompt-injection approval confusion, secret leakage
overclaim, replay/stale evidence overclaim, MCP tool result proof confusion,
prompt profile compliance confusion, and integration-surface assurance
confusion.

### Prompt Injection

Risk: malicious text in workflow-plan, handoff, report, or evidence summary asks the user or agent to treat a summary as approval or proof.

Required response:

- Preserve artifact boundaries.
- Reject wording that says ORRO approves, proves, verifies, or raises assurance.
- Keep Depone as the only verifier semantics owner.

### Secret Leakage

Risk: report or handoff repeats tokens, credentials, private URLs, or signing material from captured output.

Required response:

- Reports must prefer evidence paths over pasted sensitive content.
- Secret-looking content must not be repeated in public-facing summaries.
- SECURITY.md must define disclosure handling before v0.1.

### Replay or Stale Evidence

Risk: old evidence is presented as a new run, or stale evidence is summarized without a freshness warning.

Required response:

- ORRO must distinguish replayed evidence, stale evidence, and current evidence.
- Depone is the only component allowed to emit verifier pass/fail semantics for forged or replayed evidence.
- Until the relevant Depone/witnessd semantics exist, ORRO must label replay/stale evidence as an unresolved risk, not as pass.
- ORRO reports must not convert replay/stale warnings into pass language.

### Handoff Approval Confusion

Risk: handoff text is read as merge, release, or deployment approval.

Required response:

- handoff is not approval.
- Humans retain judgment.
- Formal approval must remain outside generated handoff content.

### Report Proof Confusion

Risk: report text is read as proof or verifier truth.

Required response:

- report is not proof.
- Reports must link to or name evidence and proofcheck verdict paths.
- Reports must not claim stronger truth than the underlying verdict supports.

## Non-Goals

- No ORRO verifier implementation.
- No ORRO execution runtime.
- No ORRO proofrun or proofcheck logic.
- No package publish or command ownership change.
