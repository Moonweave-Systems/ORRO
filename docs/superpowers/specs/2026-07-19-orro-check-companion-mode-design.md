# `orro check` — Companion Mode Design

**Issue:** ORRO #78 (Main-session companion mode)
**Date:** 2026-07-19
**Status:** Approved design → ready for implementation plan
**Verdict model:** verification = falsifiable verdict; review = advisory (approved)

## Problem

Industry consensus (Anthropic multi-agent, Cognition "Don't Build Multi-Agents",
OpenAI Codex subagent docs): writes stay single-threaded; extra agents contribute
intelligence (review), not actions. A user who already drove codex/claude in their
**main session** should not have to spawn a second executor to get ORRO's value.

Today, execution value requires witnessd to spawn the provider as an observed lane.
There is no first-class path for: *"I already drove the work — review it and verify
it, produce evidence, do NOT spawn another executor."*

The pieces exist but are not wired into one guided command, and one of them is a
naming landmine (see below).

## Ground truth (from recon; anchors for the implementer)

**Architecture.** `orro` (published wrapper `orro_wrapper.cli`) is a thin delegator:
`python -m orro <args>` → witnessd `__main__.py` `ORRO_COMMAND_MAP` (`__main__.py:815`)
→ handlers in `witnessd/cli/*.py`. Depone runs as a subprocess. **This command is
built in witnessd**, exposed via the ORRO command map, then ORRO re-pins.

**Reusable pieces that already work:**

- Deterministic verification-only **shell** lanes: `flowplan --profile verification-only
  --check '<cmd>' --role-lanes-out <plan>` → `_verify_lane_from_role`
  (`orro_workflow.py:989-1008`): `phase:"proofrun", adapter:"shell", region:[],
  may_execute:True, may_verify:False, raises_assurance:False,
  lane_intent:"verification-only", check_commands:[...]`. At proofrun,
  `_role_lane_plan_team_specs` (`cli/run.py:619-666`) converts these to specs with
  `commands=[["sh","-c",check]...]` and **no `adapter` key**, so they take the
  `_run_write_lane` branch (`fanin.py:1009`), never `_run_adapter`. Depone falsifies
  any mutation: `ERR_TEAM_LEDGER_VERIFICATION_LANE_MUTATED`
  (`depone/agent_fabric/team_ledger.py:541-556`).
- Read-only reviewer lanes: `orro review --role-lane-plan <plan>`
  (`orro_review.py:48` `run_review_role_lane_plan`), fully isolated from fanin, sets
  `can_change_evidence_verdict:false, raises_assurance:false, verifies_evidence:false`
  (`orro_review.py:123-133`). Gate requires `workflow_profile ∈ {review-only,
  critic-only}`, `execution_allowed:false`, all lanes `phase:"review"`
  (`orro_review.py:139-184`). A review-only role-lane plan is produced by
  `flowplan --profile review-only --lane-adapter agy|gemini` (`orro_workflow.py:322-331`
  → `_review_lane_from_role` forces `phase:"review", may_execute:False, region:["."]`).
- Evidence seal + Depone verdict: proofrun writes `team-ledger.json`;
  `verify._cmd_proofcheck` (`cli/verify.py:250`) → `_run_depone_json` (`cli/_output.py:39-46`)
  → Depone `build_team_ledger_verdict` → `decision ∈ {pass, blocked, blocked-explicit}`.
  A pure verification-only team-ledger verifies cleanly (empty touched-files allowed).
- Structured blockers in the exact requested shape: `_structured_error(code, message,
  reason, required_input_or_grant, next_command, extra)` (`cli/_output.py:66-84`).
- Engine pinning is automatic via delegation (`distribution.py:33-34`
  `DEFAULT_DEPONE_REF`; engine-lock JSON).

**Landmine (must NOT reuse as-is):** `orro flow --verification-only` (`cli/flow.py:351-373`)
hardcodes `--profile code-change` and only stamps `lane_intent:"verification-only"`. It
compiles a **real AI adapter lane** (codex/claude) with a non-empty write region and
**spawns an execution adapter subprocess** (`fanin.py:993 if spec.get("adapter")` →
`adapter_run._run_adapter:97`), with Depone falsifying mutation only after the fact.
That is the #70 "AI no-mutation lane", not what #78 wants. `orro team go --profile
verification-only` (`cli/team_go.py:107-125`) also cannot supply `--check`. **Two
different lane kinds share the name "verification-only".** Companion uses the
deterministic **shell `--check`** kind exclusively.

**Honest-boundary crux (must be newly built):**

- Assurance A1/A2 (`capture.py:24-31`) describes *observation isolation*, NOT
  execution-vs-verification. There is **no existing field** asserting "observed
  execution" vs "verification/review only". The companion must assert this itself.
- Review receipts (`orro-review-summary.json`) live **outside** the team-ledger /
  proofcheck path — Depone never sees them. So review cannot (and per the approved
  model, must not) enter the pass/fail verdict.

## Design

### 1. Command surface

Public **`orro check`** → witnessd internal `orro-check` (add `check → orro-check` to
`ORRO_COMMAND_MAP`; register in `_build_parser()` like `orro-review`). Concept name:
"companion".

Flags:

| Flag | Default | Meaning |
|---|---|---|
| `--check '<cmd>'` (repeatable, **required**) | — | Deterministic verification command. Same semantics as `flowplan --check`. |
| `--reviewer {agy,gemini,claude}` | `agy` | Read-only reviewer model (independent from the main-session model). |
| `--no-review` | off | Verify-only companion; skips the review lane. |
| `--base <ref>` | auto-detected default branch | Scopes the review to "what changed". Checks run on the current worktree regardless. |
| `--repo`/`--root`, `--home`, `--run-dir`, `--json`, `--timeout-seconds` | as sibling commands | — |

**`--base` mechanism.** `orro_review` does not compute a diff itself — it reviews the
review lane's *prompt* and the reviewer (agy) binds its own `context_binding`
(`orro_review.py:292-297`). So `--base` shapes the generated review-lane **prompt**
(e.g. "review the changes on HEAD relative to `<base>`"); the companion does not
pre-compute or pass a diff. Base auto-detection: `git symbolic-ref refs/remotes/origin/HEAD`
with a `main` fallback.

- **No `--write-scope`.** Verification lanes are `region:[]` (zero write); review is
  read-only. Refusing write-scope is itself the honest boundary.
- No checks declared → structured blocker `ERR_ORRO_CHECK_NO_CHECKS_DECLARED` via
  `_structured_error` (`reason`: checks define what "verified" means and cannot be
  inferred; `required_input_or_grant`: `--check '<cmd>'` (repeatable);
  `next_command`: `python3 -m orro check --check '<cmd>' ...`).
- Review requested (default) but the reviewer binary/auth is unavailable → structured
  blocker `ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE`, **not** a silent skip (silently
  dropping the review the user expected would be dishonest). `required_input_or_grant`:
  install/authenticate the reviewer; `next_command`: re-run with `--no-review` for a
  verify-only companion. The verification half has already produced its verdict, so the
  blocker reports the verdict alongside and exits `2` (review was requested and could
  not run).

### 2. Pipeline (reuse existing spines; new code = orchestration glue + manifest)

```
A. VERIFY (falsifiable verdict)
   flowplan --profile verification-only --check ... --role-lanes-out verify-plan.json
   → proofrun(verify-plan)     # all adapter:shell → _run_write_lane; ZERO AI adapters; seals team-ledger
   → proofcheck → Depone       # existing verification-only verdict path; decision pass|blocked

B. REVIEW (advisory)              [skipped if --no-review]
   flowplan --profile review-only --lane-adapter <reviewer>  → review-plan.json
   → orro review --role-lane-plan review-plan.json           # outside fanin; can_change_evidence_verdict:false

C. SEAL
   companion-manifest.json       # ties A's verdict + B's review-summary with honest labels
```

The companion **assembles its own role-lane plans** and never a code-change lane.
Engine logic and Depone schema are unchanged (goal): a verification-only-only
team-ledger already verifies through the existing proofcheck path.

### 3. Honest labeling — `companion-manifest.json`

```json
{
  "kind": "orro-companion-manifest",
  "scope": "state-verified-and-reviewed",
  "reviewed_work_execution_observed": false,
  "verification_checks_executed_observed": true,
  "execution_adapter_lanes_spawned": 0,
  "verdict_ref": {"path": "proofcheck-verdict.json", "sha256": "...", "decision": "pass|blocked"},
  "review_ref":  {"path": "orro-review-summary.json", "sha256": "...", "advisory": true},
  "boundary": {
    "reviewed_work_execution_observed": false,
    "raises_assurance": false,
    "approves_merge": false,
    "review_is_advisory": true
  }
}
```

**Precision of the honest label (the crux of #78).** The distinction is between two
different executions:

- `reviewed_work_execution_observed: false` — the *work being verified* (what the user
  drove in their main session) was **not** executed under witnessd observation, so it
  cannot claim A1/A2 execution evidence. This is the boundary the issue names ("work
  not executed under witnessd observation").
- `verification_checks_executed_observed: true` — the *declared `--check` commands* DID
  run under observation; that observed execution is exactly what gives the verdict its
  evidence. Saying "nothing executed" would be false.
- `execution_adapter_lanes_spawned: 0` — zero code-producing adapter lanes
  (codex/claude/agy-as-executor). Deterministic shell check lanes are not
  execution-*adapter* lanes; this field names the §4 invariant precisely.

`verdict` reflects the **deterministic checks only** (pass/blocked). Review is carried
as `advisory:true` and never touches pass/fail — consistent with the existing
`can_change_evidence_verdict:false`. `review_ref` is omitted (or `null`) under
`--no-review`. The manifest is the ORRO/witnessd-owned honest frame; Depone stays the
neutral verifier and is untouched.

### 4. Zero-execution enforcement (structural invariant)

Before any lane spec reaches `fanin.run_lane_exec_from_spec` (`fanin.py:993`, the
non-shell-adapter branch), assert **no lane carries a non-shell `adapter`**. Violation
→ hard internal error (unreachable by construction; defense in depth). The manifest's
`execution_adapter_lanes_spawned:0` is the record of this invariant. Review lanes never
enter fanin at all (they run through `orro_review.py`).

### 5. Output UX (acceptance: distinguish "state verified" from "execution observed")

```
orro check — evidence & review for work you already drove

  VERIFICATION   (Depone verdict, deterministic)   ● pass
    ✓ pytest -q                                 pass
    ✓ ruff check .                              pass
  REVIEWED   (agy, advisory — not part of verdict)
    ⚠ 2 concerns raised  → orro-review-summary.json
  BOUNDARY
    reviewed work was NOT observed-executed · 0 execution-adapter lanes · does not approve merge

  verdict: pass   (review advisory: 2 concerns)
```

`--json` emits the `companion-manifest.json` payload.

### 6. Exit codes

- `0` — Depone verdict `pass` **and** the review completed (or `--no-review`).
- `2` — verdict `blocked`, **or** any structured blocker (no checks declared;
  reviewer unavailable while review was requested; etc.).
- Review "fail/concerns" (the reviewer ran and raised concerns) does **not** change the
  exit code — an AI review must not move a deterministic gate; concerns are surfaced in
  output and `review_ref`. This differs from `ERR_ORRO_CHECK_REVIEWER_UNAVAILABLE`,
  which is the reviewer *failing to run at all* (exit `2`). A `--strict-review` opt-in
  (let concerns fail the exit) is **out of scope** (YAGNI).

### 7. Build location & release

- New: witnessd `cli/companion.py` (`_cmd_orro_check`) + registration in `__main__.py`.
  Reuse: flowplan / proofrun / proofcheck / `orro_review` / `_structured_error`.
- **Depone: unchanged** (goal; confirm during implementation — the verification-only
  team-ledger already verifies through the existing path).
- Cross-repo order: **witnessd release → ORRO re-pin**. Depone stays at its current pin
  (1932f00) unless implementation proves a Depone change is unavoidable.
- Docs positioning: "the evidence & review layer for the agent you already drive."

### 8. Chosen defaults (owner may veto)

| Decision | Choice | Rationale |
|---|---|---|
| Command name | `orro check` | Short; "check the work I already drove" mental model. |
| Checks input | `--check` repeatable only (no config file) | ORRO DNA: never infer safety-relevant boundaries; YAGNI. |
| Review | ON by default, reviewer `agy` | "review + verify" is the core; independent model. |
| Diff base | auto-detected default branch | Reasonable default; `--base` overrides. |

### 9. Out of scope (YAGNI)

`.orro/checks.json` config file · `--strict-review` gating · folding review into the
verdict · the #70 AI no-mutation lane (separate mechanism).

## Testing plan

- **Clean-env full suite** — fresh clone, `PYTHONNOUSERSITE=1`,
  `PYTHONDONTWRITEBYTECODE=1`, PATH with the trailofbits `python3` shim removed;
  witnessd suite runs with `PYTHONPATH=../depone`.
- **Mutation** — disable the zero-execution assert and confirm a test turns red
  (proves the guard has teeth).
- **Live smoke** — in a real repo, `orro check --check 'pytest -q' --check 'ruff check .'`
  end-to-end: `companion-manifest.json` shows `reviewed_work_execution_observed:false`,
  `verification_checks_executed_observed:true`, `execution_adapter_lanes_spawned:0`,
  `verdict.decision:pass`; a deliberately failing check
  flips exit to `2`; `--no-review` omits `review_ref`.
- **CI is ground truth.**

## Acceptance (from #78)

- [x] One command with structured blockers (`reason`/`required_input_or_grant`/`next_command`).
- [x] Never launches an execution adapter; only verification-only shell + review lanes.
- [x] Output clearly distinguishes "state verified + reviewed" from "execution observed".
- [x] Docs position it as the evidence & review layer for the agent you already drive.
