# `orro check --health` — Code-Health Axis Design

**Date:** 2026-07-22
**Status:** Design → awaiting owner review before implementation plan
**Verdict model:** health verdict = deterministic gates (falsifiable) · design/naming/"slop" = advisory (never a machine verdict)
**Builds on:** `orro check` companion mode (2026-07-19 spec, shipped witnessd v2.7.0+) and the `policy_conformance` guardrail rollup (Depone v0.2.7).

## Problem

AI-native development produces a lot of code fast, but an operator without deep
dev knowledge cannot tell whether that code is *consistent* — whether the
codebase reads as if one author wrote it, or as if a different self wrote each
part. The maintainer wants: **when I use ORRO, code health is applied
automatically.**

Global consensus (researched 2026-07-22) confirms the instinct and — critically
— tells us exactly how much of it a verifier can honestly own:

- **Consistency is a first-class practitioner pillar.** *Software Engineering at
  Google* ch.8: "It's the consistency of having one answer rather than the
  answer itself that is the valuable part here"
  (<https://abseil.io/resources/swe-book/html/ch08.html>). PEP 8: "Consistency
  within a project is more important." Formatter movement (Black/Prettier/gofmt)
  = consistency-as-tooling.
- **The deterministic / subjective split.** The consistency family
  (formatter · lint · type · complexity · duplication) is byte-re-derivable
  pass/fail — the *only* defensible basis for a machine verdict. Naming,
  design, readability, "AI slop" are irreducibly subjective → advisory only.

ORRO already has the exact substrate for the deterministic half (declared
deterministic checks under observation → Depone verdict), but there is no
first-class **code-health** surface that (a) auto-detects the repo's own quality
gates, (b) runs them as a health verdict, and (c) can apply the provably-safe
fixes.

## Honest verdict semantics (the crux — read first)

Depone is a **stdlib-only non-executing verifier**. It **cannot** re-run
`black`/`ruff`/`mypy`. Therefore the health verdict is **not** crypto
re-derivation (byte-identical recomputation). It is exactly the shape
`policy_conformance` already ships:

> The declared health gates **ran under witnessd observation**, and their
> **exit-code / mutation evidence** supports the claimed pass/fail. Depone
> confirms the evidence is internally consistent and that the gate lane mutated
> nothing it shouldn't.

This is a **guardrail receipt**, not a proof of code correctness. The trust
boundary is: *we trust that `ruff`'s exit code means what it says.* The spec
MUST NOT use "independently re-derived" language for the tool result itself.
`code_health: PASS` means **"the declared gates passed under observation"**, never
"this is good code." That label is stated in the manifest and the human output.

**Scope honesty (do not oversell the operator's exact pain).** Formatters and
linters catch *surface* consistency (whitespace, import order, some naming via
`ruff` `N`-rules). The deep "different ego" structural consistency (module
layout, architectural patterns) is only **partially** gate-able; the rest is the
advisory reviewer's job. The design says so explicitly and never claims the
verdict certifies structural consistency.

## Ground truth (verified 2026-07-22 against synced trees)

Local sibling clones were **stale** at session start (witnessd v2.6.0, Depone
pre-`policy_conformance`); both were fast-forwarded to `origin/main`
(**witnessd d28defd = v2.11.7**, **Depone f6f60a3 = v0.2.7**) before these
anchors were read. All line numbers are from those commits.

**`orro check` companion (the substrate to extend) — `witnessd/cli/companion.py`:**

- `_cmd_orro_check` (`companion.py:230`) requires `--check '<cmd>'` (repeatable);
  no checks → `_emit_blocker(ERR_ORRO_CHECK_NO_CHECKS_DECLARED)` (`:233-241`).
- Pipeline: `init` → `flowplan --profile verification-only … --lane-adapter shell`
  with one `--check` per command (`:300-317`) → `_assert_no_execution_adapter`
  (`:331`, hard-fails any non-`shell` lane) → `proofrun --adapter shell` seals
  `team-ledger.json` (`:334-367`) → `proofcheck` → Depone decision ∈
  `{pass, blocked, blocked-explicit}` (`:369-401`) → optional review-only lane
  (`:405-476`) → `companion-manifest.json` (`:478-496`).
- Manifest (`manifest_partial`, `:135-158`): `kind:"orro-companion-manifest"`,
  `verification_checks_executed_observed:true`,
  `reviewed_work_execution_observed:false`, `execution_adapter_lanes_spawned`,
  `verdict_ref{path,sha256,decision}`, `boundary{…,review_is_advisory:true}`.
- Exit: `0` iff Depone decision `pass`, else `2` (`:502`).

**`policy_conformance` rollup (the pattern to mirror for v2) — `depone/verify/engine.py`:**

- `PolicyAxisConformance{axis, status:"pass"|"fail", enforcement:"block"|"advisory",
  blocks_handoff:bool, error_code, evidence_path}` (`engine.py:125-132`);
  `PolicyConformance{overall:"pass"|"fail"|"inconclusive", axes:[…]}` (`:135-138`);
  carried on `VerificationReport.policy_conformance` (`:167`).
- `_policy_conformance(role_capability_conformance, contract)` (`:314-359`):
  per-axis `enforcement` defaults `block`, becomes `advisory` when the contract
  directive says so (`:323-330`); `blocks_handoff = status=="fail" and not
  advisory_violation` (`:340`); `overall` = `inconclusive` if a required axis is
  undeclared/invalid, else `fail` if any axis failed, else `pass` (`:346-358`).
- **Advisory seam:** an advisory-enforcement failure still records `status:"fail"`
  but `blocks_handoff:false` and does not flip the overall handoff-gating
  decision — it reports without silently agreeing. This is the honest
  non-blocking pattern the health advisory tier will reuse.

**Verification-only lane (the deterministic exit-code engine) — `witnessd/witnessd/orro_workflow.py` + `depone`:**

- `check_commands` allowed only for `profile == "verification-only"`
  (`orro_workflow.py:272-275`, `VALID_LANE_INTENTS = {implementation,
  verification-only}` `:65`); compiled lane has an **empty write region**;
  proofrun runs each as `sh -c <check>`; a non-zero exit blocks the lane; any
  mutation → Depone `ERR_TEAM_LEDGER_VERIFICATION_LANE_MUTATED`.
- Exit-code contract primitive: Depone `required_commands` /
  `expected_exit_code` with `ERR_TEST_EXIT_CODE_MISMATCH`
  (`depone/verify/evidence_contract.py:53, 1539+`) → `any_refuted` → `decision:
  fail`.
- Cache hygiene is already handled: checks run with `PYTHONDONTWRITEBYTECODE=1`
  and per-lane `RUFF_CACHE_DIR`/`MYPY_CACHE_DIR`/pytest `cache_dir` shaping
  outside the worktree (witnessd CLAUDE.md), so `ruff`/`mypy`/`pytest` gates do
  not self-mutate the observed tree.

**`orro demo` deterministic guardrail (the `--fix` write-lane analog) — `witnessd/cli/demo.py`:**

- `orro demo [--violate]` runs a deterministic shell `--command` inside a
  granted `--write-scope`; the observer captures touched files; Depone
  re-derives write-scope PASS/FAIL. This is the exact "run a deterministic
  command that DOES write, bounded by a declared scope, Depone re-derives
  conformance" path the `--fix` lane reuses.

**Schema accept-set — `depone/verify/evidence_contract.py:26-33`:** current max
`v110.advisory_provenance`. A v2 health contract adds **`v111.code_health`** +
its feature gate here (Depone-first, per both engines' CLAUDE.md: "Contract
capability changes land in Depone first, then witnessd consumes them").

## Design

### Split into two shippable phases

**v1 (this spec, buildable now, zero Depone schema change):** a `--health`
preset over the existing `orro check` substrate. Auto-detect the repo's *own*
configured deterministic gates (format · lint · type), expand them into the
verification-only `--check` lane, get the honest Depone verdict, and offer
`--fix` for the provably-safe subset. Tiering in v1 = **which gates are in the
verdict lane** (blocking) vs surfaced as advisory info; complexity/duplication
stay out of the v1 verdict.

**v2 (follow-on, documented not built): Depone `code_health` contract +
`HealthConformance` rollup** mirroring `policy_conformance`, adding advisory
gates (complexity, duplication, architecture fitness) with a real
`enforcement:"block"|"advisory"` + `blocks_handoff` seam. Only build v2 when v1
proves the surface is wanted.

### v1 — command surface

Extend the existing `orro check` (do **not** add a new verb):

| Flag | Default | Meaning |
|---|---|---|
| `--health` | off | Auto-detect the repo's configured deterministic gates and add them to the verification lane. Composes with any explicit `--check`. |
| `--fix` | off | Before verifying, run only the **provably-safe** auto-fixers (formatter, import-sort, lint `--fix`) in a **scope-bounded write lane**; record the diff as evidence; then verify the fixed tree. **Requires `--write-scope`** (below) — the fix scope is never inferred. |
| `--write-scope '<glob>'` (repeatable) | — | Bounds where `--fix` may write (reuses `orro flow`'s existing scope input; same `--write-scope` semantics as a `code-change` lane). Mandatory whenever `--fix` is set; ignored otherwise. |
| `--apply` | off | After the fix lane's diff is **scope-verified by Depone** (fix verdict + `policy_conformance.overall` both `pass`), apply the recorded `health-fix.diff` to the caller's working tree with `git apply`. **Requires `--fix`.** Opt-in, never default; refused (structured blocker) if the fix lane did not pass — an unverified fix is never applied. This is the only mode in which `orro check` mutates the caller's tree, and the manifest records `code_health.fixes_applied.applied_to_worktree:true`. |
| `--health-plan` | off | Print the detected gate plan as JSON and exit `0` **without running** (dry inspection of what `--health` would do). |
| existing `--reviewer/--no-review/--base/--repo/--home/--run-dir/--json/--intent` | — | Unchanged. Advisory review still runs by default and remains non-verdict. |

**Auto-detection (from EXISTING repo config only — never impose a tool):** scan
the repo root for already-adopted quality tools and emit the matching gate
command. Detection sources and the gate each yields:

| Detected signal | Gate command (blocking, verdict lane) |
|---|---|
| `[tool.black]` in `pyproject.toml`, or `black` in deps/pre-commit | `black --check --quiet .` |
| `[tool.ruff]` / `ruff.toml`, or `ruff` in deps/pre-commit | `ruff check .` |
| `[tool.mypy]` / `mypy.ini`, or `mypy` in deps/pre-commit | `mypy .` |
| `.eslintrc*` / `eslint` in `package.json` | `npx --no-install eslint .` |
| `.prettierrc*` / `prettier` in `package.json` | `npx --no-install prettier --check .` |
| `go.mod` present | `gofmt -l .` (non-empty output = fail; wrapped `sh -c 'test -z "$(gofmt -l .)"'`) |

- **Stdlib-only detection, no TOML parser (Python 3.10 floor).** witnessd is
  `python_requires>=3.10` and stdlib+openssl-only; `tomllib` is 3.11+ and `tomli`
  is a forbidden third-party dep. Detection therefore does a **presence scan**,
  not a TOML parse: match `[tool.<X>]` / `[tool.<X>.` section headers by line and
  scan dependency/pre-commit tool names as strings. A presence miss only *omits*
  a gate (never invents one), so a heuristic scan is honest for v1.
- Tool identity + resolved version is recorded in the run so "format-clean" is
  unambiguous (which `black`). Detection reads config; it does **not** install
  anything.
- **Fail-closed on empty detection.** `--health` with no detectable gate and no
  explicit `--check` → structured blocker
  `ERR_ORRO_HEALTH_NO_GATES_DETECTED` (`reason`: health gates are read from the
  repo's own tool config and none was found; `required_input_or_grant`: add tool
  config (e.g. `[tool.ruff]`) or pass `--check '<cmd>'`; `next_command`:
  `python3 -m orro check --health --health-plan …`). Never a silent pass.
- **Tool declared but not installed** in the run environment → the gate lane's
  `sh -c` exits non-zero → Depone `blocked` (honest: we could not confirm the
  gate). The blocker message names the missing tool. Not a silent skip.

### v1 — pipeline (reuses the companion spine verbatim)

```
0. DETECT      scan repo config → gate command list (+ tool versions)   [--health]
               (--health-plan: print the list as JSON and exit 0)

1. FIX         [only if --fix; requires --write-scope, else
                ERR_ORRO_HEALTH_FIX_SCOPE_REQUIRED blocker]
               flowplan --profile code-change --lane-adapter shell
                        --write-scope '<user globs>' --command '<safe fixer>' …
               → proofrun (shell write-lane, observed) → diff captured as evidence
               (safe fixers only: black ., ruff check --fix ., isort/ruff import-sort,
                prettier --write, gofmt -w. NEVER complexity/design rewrites.)
               Depone re-derives the fix lane stayed inside the declared scope
               (orro demo write-scope path); an out-of-scope write is falsified.

1b. APPLY      [only if --apply; requires --fix]
               The apply point is reached ONLY after the fix-pass guard (fix
               decision==pass AND policy_conformance.overall==pass), which returns
               ERR_ORRO_HEALTH_FIX_PROOFCHECK_BLOCKED first otherwise — so an
               unverified/out-of-scope fix is structurally never applied. Then
               `git apply health-fix.diff` to the caller's working tree (empty
               diff → nothing applied). Records fixes_applied.applied_to_worktree.

2. VERIFY      flowplan --profile verification-only --check <each gate> …
               → proofrun (shell, ZERO AI adapters) → proofcheck → Depone verdict
               (existing orro check path; decision pass|blocked)

3. REVIEW      [default on] advisory review-only lane (unchanged)

4. SEAL        companion-manifest.json + a health block (below)
```

The `--fix` lane is a **`code-change` shell lane bounded by a declared
write-scope** (the `orro demo` path), so witnessd observes exactly what the
fixers touched and Depone re-derives that the fixers stayed in scope. The verify
lane runs *after* the fix on the now-clean tree, so a `--fix` PASS is honestly a
PASS on the fixed tree — and the manifest records that fixes were applied.

### v1 — honest labeling (extend `companion-manifest.json`)

Add a `code_health` block to the existing manifest (do not fork the manifest):

```json
"code_health": {
  "applied": true,
  "verdict": "pass",
  "gates": [
    {"gate": "format", "tool": "black", "version": "24.10.0", "command": "black --check --quiet .", "status": "pass"},
    {"gate": "lint",   "tool": "ruff",  "version": "0.6.9",   "command": "ruff check .",           "status": "pass"},
    {"gate": "type",   "tool": "mypy",  "version": "1.11.2",  "command": "mypy .",                 "status": "pass"}
  ],
  "fixes_applied": {"ran": ["black .", "ruff check --fix ."], "diff_ref": {"path": "health-fix.diff", "sha256": "..."}},
  "means": "declared deterministic gates passed under observation; NOT a claim of good design, correct behavior, or structural consistency",
  "verdict_source": "depone-verification-only",
  "structural_consistency_covered": false
}
```

- `verdict` mirrors the Depone verification-only decision for the gate lane
  (pass/blocked) — it does **not** invent a parallel verdict. `means` and
  `structural_consistency_covered:false` are the anti-overclaim guardrails.
- `fixes_applied` is present only under `--fix`; `diff_ref` binds the recorded
  fixer diff so "PASS" is traceable to "PASS after these fixes."

### v1 — human output (add a HEALTH section to the companion summary)

```
orro check — evidence & review for work you already drove

  CODE HEALTH   (Depone verdict, deterministic gates)   ● pass
    ✓ format   black   24.10.0     pass
    ✓ lint     ruff    0.6.9       pass
    ✓ type     mypy    1.11.2      pass
    fixes applied: black ., ruff check --fix .   → health-fix.diff
  REVIEWED   (advisory — not part of verdict)
    → orro-review-summary.json
  BOUNDARY
    "health: pass" = declared gates passed · NOT a claim of good design or correct behavior
    reviewed work was NOT observed-executed · 0 execution-adapter lanes · does not approve merge

  verdict: pass
```

### v1 — exit codes

- `0` — Depone gate verdict `pass` (and review completed or `--no-review`).
- `2` — verdict `blocked` (a gate failed / a declared tool was unavailable), or
  any structured blocker (`ERR_ORRO_HEALTH_NO_GATES_DETECTED`, reviewer
  unavailable while requested, etc.).
- An advisory review raising concerns does **not** change the exit code (an AI
  review must not move a deterministic gate) — unchanged from companion §6.

### v2 — Depone `code_health` tiered rollup (BUILD NOW; mirrors the skill_routing axis)

v2 adds a per-gate **enforcement tier** so advisory gates (complexity,
duplication) and structural gates (architecture fitness) can be **surfaced
without silently blocking** — the exact honest seam `skill_routing` advisory
already ships. It is a clean mirror of how the `v110.role_capability_skill_routing`
axis was added. **Depone-first** (contract + tests before witnessd consumes).

**Mirror template (verified anchors, Depone `depone/verify/`):** the newest axis
`role_capability_skill_routing` is the exact copy source —
`_ROLE_CAPABILITY_SKILL_ROUTING_CONTRACT_SCHEMA_VERSION` (`evidence_contract.py:34`),
`_ERR_ROLE_CAPABILITY_SKILL_ROUTING_VIOLATION` (`:67`), accept-set/feature gate
(`:219,295-301`), `_has_enforcement_directive` (`:194`),
`_validate_role_capability_skill_routing` (`:693-749`), wiring (`:1753`);
rollup `_policy_conformance` (`engine.py:314-359`) with its advisory seam
(`_is_advisory_skill_routing_entry` `:189`, `_blocking_evidence_contract_entries`
`:201`). witnessd emission `substrate.py:339-344`
(`contract["role_capability_skill_routing"] = {...}`) +
`skill_routing_declaration.py`.

**1. Depone (first) — `depone/verify/evidence_contract.py` + `engine.py`:**
- Schema: `_CODE_HEALTH_CONTRACT_SCHEMA_VERSION = "v111.code_health"`; add to the
  accept-set + a feature gate ("code_health requires schema_version v111").
- Contract directive shape (mirrors skill_routing):
  ```json
  "code_health": {
    "gates": [
      {"gate":"format","tool":"black","enforcement":"block","expected_exit_code":0,"exit_code_path":"health/format.exit","log_path":"health/format.log"},
      {"gate":"complexity","tool":"ruff-c901","enforcement":"advisory","expected_exit_code":0,"exit_code_path":"health/complexity.exit","log_path":"health/complexity.log"},
      {"gate":"architecture","tool":"import-linter","enforcement":"block","expected_exit_code":0,"exit_code_path":"health/arch.exit","log_path":"health/arch.log"}
    ]
  }
  ```
- `_validate_code_health(contract, evidence_dir)` mirrors
  `_validate_role_capability_skill_routing`: per gate, read the recorded exit code
  (reuse the exit-code primitive: `_read_exit_code`); if it != `expected_exit_code`,
  emit `_ERR_HEALTH_GATE_VIOLATION` (`"ERR_HEALTH_GATE_VIOLATION"`) carrying the
  gate id + enforcement in the message/detail. Wire it into `run_verification`'s
  validator loop next to the skill_routing one.
- Advisory seam: extend `_has_enforcement_directive` to accept code_health; add an
  `_is_advisory_health_entry(contract, entry)` (an `ERR_HEALTH_GATE_VIOLATION` whose
  gate's declared `enforcement=="advisory"`) and include it in
  `_blocking_evidence_contract_entries` filtering, so **advisory gate failures do
  NOT set `any_refuted`** (decision stays pass) while block gate failures do.
- Rollup: `HealthAxisConformance{gate, tool, status, enforcement, blocks_handoff,
  error_code, evidence_path}` + `HealthConformance{overall, axes}` on
  `VerificationReport`; `_health_conformance(contract, evidence_contract)` mirrors
  `_policy_conformance`: `blocks_handoff = status=="fail" and enforcement=="block"`;
  `overall = "fail" if any axis status=="fail" else "pass"` (a purely-advisory fail
  yields `overall:"fail"` but every advisory axis `blocks_handoff:false` and the
  top-level `decision` stays `pass` — the honest "reported, not gated" seam).
- Tests + a committed fixture (a code_health contract with one block-pass, one
  advisory-fail, one block-fail gate) + a revalidator Depone re-derives.

**2. witnessd (second) — `witnessd/substrate.py` + a `health_declaration.py`:**
- Emit `contract["code_health"] = {gates:[…]}` (mirror the `role_capability_*`
  emission at `substrate.py:339-344`); bump the emitted contract schema to
  `v111.code_health` when health gates are declared.
- The health lane records each gate's exit code + log at the declared paths
  (reuse the verification-only shell run's captured exit codes).
- Gate tiers (default; a repo may override per gate): **block** = format, lint,
  type (v1's gates, now formally tiered); **advisory** = complexity
  (`ruff check --select C901` when ruff + a complexity config is adopted),
  duplication (`pylint --enable=duplicate-code` / `jscpd` when adopted);
  **architecture fitness** = `import-linter` (`lint-imports`) when
  `.importlinter`/`[tool.importlinter]` is adopted — **the strongest answer to
  "each part looks like a different self wrote it"**, default `block`.
- `orro check --health` surfaces the tiered `HealthConformance` in the manifest;
  advisory-fail gates print as `⚠ advisory` and never change the exit code.

**3. Release (3-repo, since Depone changes):** Depone bump+tag+PyPI → witnessd
re-pin(DEFAULT_DEPONE_REF)+bump+PyPI → ORRO re-pin+release. Depone-first ordering
respects "do not add a witnessd-facing schema field unless the Depone contract and
tests define it first."

**v2 scope (YAGNI):** build the mechanism + tier v1 gates + **architecture
fitness** (the structural-consistency verdict) + **complexity** (ruff C901,
advisory). Duplication detection is included only where the tool is already
adopted; if the duplication tooling proves fiddly it is deferred to v2.1 (the
mechanism supports it without further schema change).

## Build location & release

- **v1:** all witnessd (`cli/companion.py` gains `--health/--fix/--health-plan`
  + a new `witnessd/health_detect.py` for config-scan → gate list) + ORRO
  re-pin. **Depone unchanged** (v1 rides the existing verification-only verdict).
  New ERR code `ERR_ORRO_HEALTH_NO_GATES_DETECTED` is witnessd-side (a wrapper
  blocker, not a verifier axis) — allowed without a Depone change.
- Cross-repo order (v1): **witnessd release → ORRO re-pin.**
- Wrapper-help/`ORRO_COMMAND_MAP` already expose `check`; no new verb, so the
  5-place command-surface contract is untouched (flags only).

## Out of scope (YAGNI)

- v2 Depone `code_health` rollup, complexity/duplication/architecture gates
  (documented above; built only after v1 lands).
- A persisted `.orro/health.json` profile file — v1 detects live from repo
  config each run; no new config surface, no inferred safety boundary.
- Auto-fixers beyond the semantics-preserving set (no complexity/design
  rewrites, no codemod).
- Making health gates run automatically inside every `proofrun` (v1 is the
  explicit `orro check --health` entry; default-on is a later decision).
- `--strict-review` gating; folding review into the verdict.

## Testing plan

- **Clean-env full suite** — fresh clone, `PYTHONNOUSERSITE=1`,
  `PYTHONDONTWRITEBYTECODE=1`, trailofbits `python3` shim removed from PATH;
  witnessd suite with `PYTHONPATH=../depone`. CI is ground truth.
- **Detection unit tests** — a fixture repo with `[tool.ruff]`+`[tool.mypy]`
  yields exactly the ruff+mypy gates and records versions; an empty repo yields
  `ERR_ORRO_HEALTH_NO_GATES_DETECTED`; a repo declaring `mypy` without it
  installed yields a `blocked` verdict naming the missing tool.
- **Live smoke** — a real repo with a deliberate format violation:
  `orro check --health` → `code_health.verdict:"blocked"`, exit `2`; then
  `orro check --health --fix` → fixers run in a bounded write lane, `health-fix.diff`
  is recorded, verdict flips to `pass`, exit `0`; manifest shows
  `fixes_applied` and `structural_consistency_covered:false`.
- **Fix-scope mutation test** — a `--fix` lane that writes outside the declared
  scope must be falsified by Depone (reuse the `orro demo --violate` /
  write-scope re-derivation path); disabling the scope bound must turn a test red
  (proves the guard has teeth).
- **Overclaim guard** — assert the manifest/human output never emits
  "independently re-derived" for a tool result and always carries the `means`
  disclaimer.

## Acceptance

- [ ] `orro check --health` auto-detects only the repo's already-configured
      deterministic gates, records tool versions, and fails closed on empty
      detection.
- [ ] The gate verdict is the existing Depone verification-only decision; no new
      Depone schema in v1.
- [ ] `--fix` requires an explicit `--write-scope` (never inferred), runs only
      semantics-preserving fixers in that scope-bounded observed write lane,
      records the diff, verifies the fixed tree, and is falsified by Depone on an
      out-of-scope write.
- [ ] `--apply` (requires `--fix`) applies `health-fix.diff` to the caller's tree
      ONLY after the fix lane is Depone-scope-verified; refuses with a structured
      blocker otherwise; records `applied_to_worktree:true`. It is the only tree-
      mutating mode and is never default.
- [ ] Manifest + human output label `health: pass` as "declared gates passed",
      explicitly disclaim design/behavior/structural-consistency, and never say
      "independently re-derived" of a tool result.
- [ ] Advisory review remains non-verdict; exit codes follow the companion
      contract.
