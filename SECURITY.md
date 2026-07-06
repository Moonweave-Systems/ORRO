# Security Policy

ORRO is a workflow and harness surface. It is not an execution engine, verifier
engine, approval system, or third engine.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

## Disclosure Handling

Use GitHub security advisories or a private maintainer channel for reports that
include sensitive repository, credential, signing, or infrastructure details.
Do not paste secrets in public issues, pull requests, reports, handoffs, or
workflow examples.

Prefer evidence paths and redacted excerpts over raw command output when a
report may include tokens, private URLs, keys, cookies, signing material, or
other credential-like values. Secret-looking material is not proof.

## ORRO Boundary

- ORRO does not execute commands.
- ORRO does not verify evidence.
- ORRO does not approve merges.
- ORRO does not raise assurance.
- ORRO does not implement proofrun or proofcheck.
- ORRO does not own Depone verifier semantics or witnessd runtime semantics.

Security reports may describe risk in ORRO documentation, schemas, contract
checks, wrapper/distribution metadata, or harness surfaces. They must not ask
ORRO to reinterpret missing, failed, stale, or forged verifier output as pass.

## Replay And Stale Evidence

Replay or stale evidence is an unresolved risk unless the relevant Depone and
witnessd semantics exist. ORRO reports and handoffs may name evidence paths and
warnings, but they must not convert replay, stale evidence, or warning states
into approval, proof, verifier truth, or raised assurance.

## Public Report Guidance

When a public report is appropriate:

- include affected paths, commands, and redacted excerpts;
- name the artifact boundary involved, such as workflow-plan, proofrun,
  proofcheck-verdict, handoff, report, engine-lock, or release-manifest;
- keep credentials and private evidence out of the report;
- avoid wording that says ORRO proves, approves, verifies, executes, or raises
  assurance.
