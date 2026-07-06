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

## Deferred Monorepo Conditions

Only consider a monorepo if:

- engine APIs stabilize
- release/version pin costs dominate
- e2e CI needs one repo
- packaging requires atomic multi-engine release

Those are future conditions, not current instructions. This repository must not
be used to merge engines by accident.
