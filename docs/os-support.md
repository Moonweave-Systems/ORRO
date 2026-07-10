# OS Support Matrix

ORRO is the product and workflow surface. The engines keep their own runtime
implementations:

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

This matrix is product support metadata, not proof, not verifier truth, not
approval, and not assurance.

| Platform | Support level | Scope |
| --- | --- | --- |
| Linux | required | Primary development, CI, proofrun/proofcheck smoke, and release-gate environment. |
| macOS | smoke | Local operator smoke is supported for wrapper, command migration, and engine delegation checks. |
| Windows | unsupported | Native Windows execution is not supported in this phase. Use Linux for required validation. |

## POSIX And A2

POSIX-only paths are capability-gated. In particular, A2 evidence depends on
host capabilities such as separate observer/runner uid facts and observer-owned
paths that are not writable by the runner.

If those capabilities are unavailable, witnessd must not claim A2; the evidence
remains A1 or blocked according to the bytes Depone verifies. macOS smoke may
exercise portable wrapper and delegation paths, but Linux remains required for
the release gate and for POSIX-only A2 capability-gated validation.

Windows is unsupported until the engine repositories define and verify native
Windows capability probes and evidence semantics.
