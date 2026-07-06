# ORRO Integration Surface Policy

## Purpose

ORRO may expose workflow doctrine, prompt profiles, report and handoff language
boundaries, and assurance harness references through multiple integration
surfaces. ORRO core must not depend on an always-on integration server.

- MCP is an integration surface, not ORRO's core architecture.
- Plugins are integration surfaces, not ORRO's core architecture.
- The ORRO core is docs, contracts, schemas, harnesses, CLI/wrapper, locks, and
  reviewable workflow surfaces.
- Integration surfaces must not collapse the Depone / witnessd / ORRO boundary.

This policy is guidance and a future adapter requirement. It does not enforce
runtime behavior by itself.

## Core Boundary

- Depone verifies.
- witnessd executes.
- ORRO exposes the workflow.
- Humans retain judgment.
- Handoff is not approval.
- Report is not proof.

Also:

- ORRO does not execute workers.
- ORRO does not verify evidence.
- ORRO does not approve merges or releases.
- ORRO does not raise assurance from prompts, transcripts, reports, or handoffs.
- Prompt profiles are instruction doctrine, not proof, approval, verifier truth,
  assurance, or model-compliance guarantees.

## Decision

ORRO should not implement an always-on MCP daemon by default.

Preferred order:

1. Static docs, manifests, schemas, and contract checks.
2. On-demand CLI/plugin commands.
3. Optional stdio MCP adapter.
4. Remote/HTTP MCP only after explicit enterprise/security requirements.
5. Long-running control plane only after security, retention, authorization,
   observability, and incident-response policies exist.

Plugin-first, MCP-optional.

MCP is allowed as an adapter, not as a dependency of ORRO core.

## Why Not MCP-First

MCP itself is not rejected. The problem is making MCP the default architecture
too early.

Risks of making ORRO MCP-first:

- always-on background process overhead
- host/session lifecycle ambiguity
- user confusion about whether ORRO is running
- model-controlled tool overuse
- hidden connectivity expectations
- host-specific MCP behavior differences
- temptation to turn ORRO into an agent tool server
- risk of adding engine/verifier/runtime logic
- risk of overclaiming prompt/profile/tool usage as proof or assurance

## Preferred Integration Model

### 1. Static Contract Surface

Examples:

- docs
- schemas
- manifests
- assurance corpus
- prompt profile manifests
- artifact meaning tables
- long automation maturity gates

Properties:

- no background process
- easy to review
- easy to diff
- CI-checkable
- no runtime authority

### 2. On-Demand CLI / Plugin Surface

Examples:

- prompt profile list/get/hash
- report language lint
- handoff language lint
- artifact table check
- strategic corpus check
- integration policy check

Properties:

- starts only when invoked
- exits after completion
- bounded timeout
- explicit user action
- no daemon
- no hidden network
- no default file watcher
- no automatic repo mutation

### 3. Optional stdio MCP Adapter

Only future, optional, opt-in.

Properties:

- stdio first
- no HTTP by default
- no daemon by default
- no background indexing
- no hidden network access
- clean shutdown when host session ends
- bounded timeout
- user-visible activation
- prompts/resources before tools
- minimal read-only or lint-only tools if tools are added

### 4. Remote / HTTP MCP

Explicitly future and not default.

Require:

- authentication
- authorization
- localhost binding or equivalent network boundary
- origin validation where relevant
- audit logging
- retention policy
- incident response
- secret handling
- enterprise threat model

## MCP Primitive Priority

If ORRO later exposes MCP, priority should be:

1. Prompts
2. Resources
3. Tools

Prompts may expose ORRO-authored instruction profiles.

Resources may expose:

- ORRO doctrine
- artifact meaning table
- threat model
- long automation maturity gate
- strategic review corpus
- prompt profile manifest

Tools, if added later, must be minimal and bounded.

Allowed future tool examples:

- `orro.profile.list`
- `orro.profile.get`
- `orro.profile.hash`
- `orro.report.language_check`
- `orro.handoff.language_check`
- `orro.artifact.meaning_table`

Forbidden MCP tool examples:

- proofrun implementation
- proofcheck implementation
- verifier verdict generation
- runtime scheduling
- background observer
- worker execution
- merge approval
- release approval
- package publishing
- assurance scoring from prose
- hidden repo mutation

## Prompt Profiles

Future prompt profiles are mentioned here as policy scope only. This document
does not implement them.

- Prompt profiles are ORRO-authored instruction doctrine.
- Prompt profiles are not copied/leaked/proprietary provider system prompts.
- Prompt profiles may later be exposed through MCP prompts.
- Prompt profiles may later be composed by an ORRO-owned CLI/gateway.
- Prompt profile hash means text identity only.
- Prompt profile hash does not prove model compliance.
- Prompt profile use should be recorded in reports/handoffs only as metadata,
  not proof.

ORRO cannot control arbitrary MCP host system prompts, and prompt profile usage
must not be described as proof that a model complied with the profile.

## Activation and Resource Policy

Future integration adapters must be:

- opt-in
- activation-scoped
- no always-on daemon by default
- no background indexing by default
- no file watching by default
- no hidden network access
- no automatic repo mutation
- bounded timeout
- clean shutdown
- user-visible invocation
- clear residual risk wording

## Long Automation Rule

Long automation is checkpoint expansion, not trust expansion.

Integration surfaces must not make long automation feel safer merely because a
server is connected. Long automation must be gated by checkpoint, evidence
target, verifier expectation, abort condition, review packet, and human
judgment.

## Artifact Meaning

| Integration artifact | Means | Does not mean |
|---|---|---|
| CLI command | on-demand ORRO surface invocation | proof, approval, verifier truth, assurance |
| Plugin invocation | user-activated integration action | always-on authority, approval |
| MCP prompt | user-selected instruction template | system-prompt guarantee, proof |
| MCP resource | exposed ORRO reference material | verifier truth, approval |
| MCP tool result | bounded adapter output | proofrun, proofcheck, verifier truth, approval, assurance |
| Prompt profile hash | exact profile text identity | model compliance guarantee |
| Integration policy | ORRO boundary guidance | runtime enforcement by itself |

## Current Priority

Current priority:

1. Harden assurance fixtures.
2. Add security/open-source operating files.
3. Improve README/docs status navigation.
4. Expand strategic corpus.
5. Add report/handoff language lint.
6. Add prompt profile foundation.
7. Only then design optional on-demand plugin/MCP adapter surfaces.

## Non-Goals

- no default always-on MCP daemon
- no MCP dependency in ORRO core
- no HTTP MCP server by default
- no hidden background process
- no engine logic
- no verifier logic
- no proofrun/proofcheck implementation
- no scheduler/observer/fan-in logic
- no merge/release approval
- no package publish logic
- no assurance claims from prompt/profile/tool usage

## Required Closing Statement

ORRO is not trying to become an MCP server.
ORRO is trying to make AI-assisted work reviewable across whichever integration
surface is used.

MCP may become one optional adapter.
It must not become the architecture.

Plugin-first, MCP-optional.
Core first, adapters later.
Prompts/resources before tools.
On-demand before always-on.
Checkpoint expansion, not trust expansion.
