# ORRO Architecture

```text
user
  -> ORRO wrapper/product surface
      -> witnessd execution runtime
          -> evidence artifacts
      -> Depone verifier
          -> verdict artifacts
      -> ORRO report/handoff
```

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

## Responsibilities

ORRO exposes the user workflow, docs, examples, packaging plan, marketplace
drafts, engine locks, and e2e contracts.

ORRO is not a verifier engine, not an execution engine, and not a third engine.

witnessd executes `proofrun`, team lanes, adapters, observers, and evidence
emission.

Depone verifies persisted evidence bytes and emits verifier verdicts.

## Forbidden Call Graphs

- Depone must not depend on the witnessd runtime.
- Depone must not launch workers.
- witnessd must not duplicate Depone proofcheck logic.
- ORRO must not create a new execution engine.
- ORRO must not create a new verifier engine.
- ORRO must not redefine verifier truth.

## Why Engines Stay Separate

Verifier independence matters. The component that executes work must not be the
component that raises trust from evidence.

The split preserves:

- execution and verdict separation
- evidence contract stability
- independent verifier review
- clear failure boundaries
- resistance to third-engine drift
