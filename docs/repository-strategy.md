# Repository Strategy

Current phase:

```text
Depone and witnessd remain separate engine repos.
ORRO repo is product/distribution/wrapper repo.
No engine code moves in this skeleton wave.
```

Depone owns verifier semantics. witnessd owns execution runtime behavior. ORRO
owns the user-facing workflow, product docs, examples, distribution planning,
and e2e contracts.

The ORRO repository may contain product checkers, documentation, examples,
packaging drafts, engine-lock examples, and local e2e smoke harnesses that call
engine commands through subprocess. It must not contain Depone verifier logic,
witnessd runtime logic, proofrun/proofcheck implementations, scheduler,
observer, fan-in, team-ledger, or worker execution modules.

The e2e runner is a product smoke harness. It orchestrates local engine
checkouts and records test metadata, but it is not proof and is not an engine.

## Deferred Monorepo Conditions

Only consider a monorepo if:

- engine APIs stabilize
- release/version pin costs dominate
- e2e CI needs one repo
- packaging requires atomic multi-engine release

Those are future conditions, not current instructions. This repository must not
be used to merge engines by accident.
