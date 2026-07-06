# ORRO Long-Automation Maturity Gates

Long automation is checkpoint expansion, not trust expansion.

## Gate Rules

- A higher level may add automation length, resume behavior, or corpus gates.
- A higher level must not raise assurance without Depone proofcheck truth.
- A higher level must not convert handoff into approval.
- A higher level must not convert report into proof.
- Humans retain judgment at every level.

## Levels

| Level | Name | Entry criteria | Exit criteria | Must not mean |
| --- | --- | --- | --- | --- |
| 0 | Manual checkpoints | User can run each ORRO command manually from docs. | User can locate workflow-plan, proofrun output, proofcheck verdict, handoff, and report paths. | Manual success is not proof. |
| 1 | Assisted flow | ORRO exposes command sequence without hiding engine ownership. | Each step is still explicitly invoked or reviewed. | Command convenience is not trust expansion. |
| 2 | Checkpointed automation | Multi-step flow writes checkpoint artifacts and stop conditions. | Failed checkpoint stops downstream work fail-closed. | Completed automation is not approval. |
| 3 | Resume-aware automation | witnessd emits checkpoint and resume evidence. | ORRO reports resume status without proof overclaim. | Resume is not verifier truth. |
| 4 | Corpus-gated automation | Injection, replay, secret, and regression corpus checks pass. | Corpus result is summarized with evidence paths. | Corpus pass is not proofcheck truth. |
| 5 | Release-gated automation | Engine-lock, release manifest, compatibility matrix, and e2e smoke align. | Human release judgment remains explicit. | Release gate metadata is not approval. |

## Minimum Evidence Per Level

| Level | Required evidence |
| --- | --- |
| 0 | Documentation command path and artifact path examples. |
| 1 | Explicit command transcript or wrapper delegation output. |
| 2 | Checkpoint artifact list and fail-closed stop condition. |
| 3 | Resume receipt or checkpoint/resume evidence path. |
| 4 | Corpus check result and rejected confusion cases. |
| 5 | Engine-lock, release manifest, compatibility matrix, and e2e smoke result paths. |

## Out of Scope for This Foundation

Level 6 continuous operation is intentionally not defined in this document. Continuous operation requires production observability, drift detection, incident response, retention policy, and security review. This foundation stops at release-gated automation.
