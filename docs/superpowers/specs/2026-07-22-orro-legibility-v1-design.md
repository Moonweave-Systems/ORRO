# ORRO Legibility v1 — `orro status` + roadmap binding + `orro tidy`

**Date:** 2026-07-22
**Status:** Design locked → implementation
**Epic:** ORRO #105 (project-level legibility)
**Scope:** witnessd only; Depone unchanged; ORRO re-pin + command-surface sync after.

## Problem (operator-reported, recurring)

Run-level honesty is solved (evidence, verdicts). Project-level work is
illegible: runs don't declare which roadmap item they serve; "where are we on
the roadmap / what is finished" has no evidence-bound answer; witnessd-created
worktrees pile up with no inventory or cleanup (live incident 2026-07-22: a
stale verification worktree held `main` checked out, silently breaking
`git checkout main` in the primary clone).

## Ground truth (recon 2026-07-22 vs witnessd 09296cf / c69aa2f, identical trees)

- **No run-inventory command exists.** Every subsystem constructs
  `<home>/runs/run-<UTCts>-<monotonic_ns>` (`cli/run.py:413-421`) but nothing
  enumerates `runs/`. `orro status` is greenfield.
- **Continuation state machine to reuse:** `decide_next` (`orro_next.py:59-237`)
  derives `invalid-run-dir | blocked | needs-proofcheck | ready-for-handoff |
  complete | evidence-pending` per run dir, with fail-closed binding checks
  (`_proofcheck_state` :389-418, `_handoff_state` :421-470). `orro status` MUST
  reuse `decide_next` per run rather than re-deriving state.
- **Artifact conventions:** `_ARTIFACT_FILES` registry + `_observed_artifacts`
  (`orro_next.py:40-50, 312-313`); fail-soft loader `_load_optional_json`
  (:502-511).
- **Binding template (cleanest):** the declared-intent sidecar —
  `declared_intent_ref` (`orro_intent.py:96-99`, `{path, sha256, declared:true}`)
  sealed into the run dir + re-hash verification `_verified_declared_intent`
  (`orro_report.py:185-215`). The roadmap binding mirrors this.
- **Worktrees:** created by `create_lane_worktree` (`worktree.py:30-63`) under
  `<run-dir>/worktrees/<lane_id>` (`fanin.py:1672,1796`); receipt
  `depone-worktree-lane-receipt` carries `worktree, branch, base_commit,
  head_commit, dirty, dirty_files, changed_files` (`worktree.py:134-152`);
  ledger lane records `worktree_receipt` path (`fanin.py:1757,1886`). **No GC
  exists** (only merge-attempt tmp worktrees are removed, `fanin.py:661-664`).
- **`.orro/` conventions:** `.orro/health.json` reader/writer
  (`health_detect.py:99-135`) — `_write_health_profile` style
  (`indent=2, sort_keys=True`, trailing newline, lazy mkdir) is the canonical
  ledger write style. `.orro/roadmap.json` copies it.
- **Command registration template:** `orro-demo` (`__main__.py:480-491`) +
  `ORRO_COMMAND_MAP` (`__main__.py:1053-1077`). NOTE: a legacy engine-level
  `status` parser exists at `__main__.py:144` — the internal names must be
  `orro-status` / `orro-tidy` to avoid collision.

## Design

### 1. Roadmap ledger — `.orro/roadmap.json`

Single source of truth, human-editable, seeded/edited by hand or `--init`:

```json
{
  "kind": "orro-roadmap",
  "schema_version": "0.1",
  "items": [
    {"id": "health-v1", "title": "code-health verdict axis", "status": "done", "note": "shipped witnessd 2.12.0"},
    {"id": "legibility-v1", "title": "orro status + roadmap binding + tidy"}
  ]
}
```

- `id` (required, unique, kebab), `title` (required), optional `status: "done"`
  (a **hand-marked claim**), optional `note`, optional `spec` (path).
- Write style copies `_write_health_profile`. Reader validates shape and fails
  soft (absent → no ledger) but raises on malformed (mirror health's strictness).

**Honest status vocabulary (the spine of this feature):**
- `done (verified)` — a bound run exists whose `decide_next` state is
  `complete`, or `ready-for-handoff`+passing proofcheck. Evidence ref attached.
- `in-progress` — bound run(s) exist; show the latest run's `decide_next` state
  and run dir.
- `marked-done (unverified)` — ledger says `status:"done"` but no bound
  evidence. Displayed with that exact honest label — never collapsed into
  "done".
- `not-started` — no bound runs, no hand-mark.

### 2. Run→roadmap binding

- New flag `--roadmap-item <id>` on `proofrun` (and threaded through
  `orro flow` / `orro team go` / `orro check`). Optional — never required,
  never inferred.
- When given: validate the id exists in `.orro/roadmap.json` (fail-closed
  structured blocker `ERR_ORRO_ROADMAP_ITEM_UNKNOWN` if not — a typo must not
  silently create an unbound run), then seal `roadmap-binding.json` into the
  run dir: `{kind:"orro-roadmap-binding", schema_version:"0.1", item_id,
  ledger_path:".orro/roadmap.json", ledger_sha256}` and verify-readable after
  write (the `write_workflow_plan_binding` seal-then-verify idiom,
  `orro_workflow.py:741-746`).
- The binding is **declared intent, not proof** — status surfaces it with the
  usual honesty framing.

### 3. `orro status` (public) → internal `orro-status`

`orro status --repo <repo> --home <home> [--json]`, read-only, non-executing:

1. Read `.orro/roadmap.json` (absent → items list empty, still show runs).
2. Enumerate `<home>/runs/*/` (dirs only). For each run: read
   `roadmap-binding.json` (fail-soft) + `decide_next(run_dir, home)` state.
3. Render per-item: honest status (vocabulary above) + evidence ref (verdict
   path) or latest run dir + its state.
4. **Off-plan section**: runs with no roadmap binding, newest first (visible,
   never blocking).
5. **Workspace section**: run count, total `worktrees/` count and disk size,
   count of dirty worktrees (from receipts where readable, else filesystem
   scan) — the "tidy needed" signal.
6. Boundary line: status is observed state + declared bindings; it is not
   proof, not approval, not assurance; `marked-done (unverified)` items are
   operator claims.

Exit 0 always (status is a report, not a gate) unless the ledger is malformed
(structured blocker, exit 2).

### 4. `orro tidy` (public) → internal `orro-tidy`

Safety-first worktree/run hygiene:

- **Default = dry-run inventory** (no mutation): list per-run `worktrees/*`
  with branch, base/head commit, dirty flag (live `git status --porcelain`
  check, not just the receipt), disk size, and the owning run's `decide_next`
  state. Also list stale non-run worktrees registered in the repo
  (`git worktree list --porcelain`) that live outside `<home>/runs` (the class
  that caused the live incident).
- `--apply`: remove ONLY worktrees that are (a) not dirty per a LIVE
  `git status --porcelain` check, and (b) belong to a run whose state is
  `complete`, OR are registered-but-path-missing (prunable). Uses
  `git worktree remove` (never `--force`) + `git worktree prune`. Anything
  dirty or in-progress is listed as "kept: <reason>" — never touched.
- No `--force` mode in v1. Deleting run dirs themselves is out of scope
  (evidence retention).

### 5. Command-surface sync (contract, 5 places)

Adding public verbs `status` + `tidy` requires the known sync set:
witnessd `ORRO_COMMAND_MAP` + ORRO_HELP surface + witnessd command-surface
tests, and at re-pin time the ORRO wrapper help epilog
(`src/orro_wrapper/cli.py`) + `scripts/check_orro_wrapper.py`
`authoritative_commands` (else the contract tests go red).

## v1.1 — item `steps` (chain legibility, Phase A: non-executing)

**Gap:** an item is usually a SEQUENCE of runs (design→implement→verify), but the
ledger cannot declare it; run chaining lives in the operator's head. Phase A adds
declared step sequences + evidence-derived progress + next-step recommendation.
**Zero new trust surface**: nothing executes; `orro auto`'s
`executes_proofrun:False` boundary is untouched (Phase B, separate decision).

**Schema** — roadmap item gains optional `steps` (ordered):

```json
{"id": "my-feature", "title": "feature work", "steps": [
  {"id": "implement", "profile": "code-change", "write_scope": ["src/**"], "adapter": "codex"},
  {"id": "verify", "profile": "verification-only", "checks": ["pytest -q", "ruff check ."]}
]}
```

- Step keys: `id` (required, kebab, unique within the item), `title?`,
  `profile` (required, one of the 5 existing envelopes — steps do NOT invent
  workflow shapes, they sequence existing ones), `write_scope?` (list),
  `checks?` (list), `commands?` (list), `adapter?` (str). Validation mirrors the
  existing item strictness (`_ITEM_KEYS` idiom, `orro_roadmap.py:23,143-156`);
  unknown keys / wrong types → malformed-ledger error. `status:"done"` and
  `steps` are mutually exclusive on one item (a hand-mark cannot shadow a
  declared sequence).

**Binding** — `--roadmap-step <id>` (requires `--roadmap-item`), threaded
exactly where `--roadmap-item` already is (proofrun/flow/team go/check).
Unknown step → fail-closed `ERR_ORRO_ROADMAP_STEP_UNKNOWN` (early, top-level,
like the item guard). `roadmap-binding.json` gains `step_id`.

**Status derivation (evidence-only, no stored pointer):** a step is
`done (verified)` iff a run bound to (item, step) has verified passing evidence
(same rules as items: decide_next complete/pass, or companion manifest
verdict_ref re-hash pass). Item with steps: `done (verified)` iff ALL steps
verified; else `in-progress (k/n steps)`; `not-started` if none. The **next
step** = first step in declared order without verified pass. State is always
recomputed from evidence — there is no mutable "current step" field anywhere.

**Next-step recommendation (non-executing):** status prints the exact command
for the next step, built from its profile+inputs:
- `verification-only` + checks → `orro check --check '<c>' ... --roadmap-item <i> --roadmap-step <s> --repo <repo>`
- `code-change` → `orro flow "<item title>: <step id>" --write-scope '<g>' --adapter <a> --roadmap-item <i> --roadmap-step <s> --repo <repo>`
- other profiles / missing inputs → show the step + an honest
  `construct the command manually (profile: <p>)` note. Never guessed inputs.
The recommendation is advice, not approval; running it is the operator's act.

**Compat:** items without `steps` behave byte-identically to v1.

## Phase B — bounded chain execution (`orro auto --run-item`) — APPROVED 2026-07-22

**Trust change (stated plainly):** until now `orro auto` never launched proofrun
(`executes_proofrun:False`). Phase B adds ONE new, explicitly invoked mode that
does: it executes the same command `orro status` recommends for the next step —
equivalent trust to the operator copy-pasting the recommendation, extended for
up to `--max-steps` steps without per-step confirmation, always behind evidence
gates. The existing `--dry-run/--once/--until-complete` modes are UNCHANGED and
keep their `executes_proofrun:False` receipts.

**Surface:** `orro auto --run-item <item-id> --repo <repo> --home <home>
--max-steps N [--json]`. `--max-steps` REQUIRED (like `--until-complete`).
Mutually exclusive with the other auto modes and with `run_dir`.

**Loop (per step, at most N iterations):**
1. Recompute item state from evidence (the status derivation — never a stored
   pointer). If all steps verified → stop `complete`.
2. Next step = first without verified pass. Build its command via THE SAME
   builder status uses (`_suggested_step_command`, single source of truth —
   never a second implementation). If the step's inputs are insufficient for a
   full command (the "construct manually" case) → stop fail-closed
   `ERR_ORRO_AUTO_STEP_NOT_EXECUTABLE` (never guess inputs).
3. Execute that command as a subprocess (this is the trust step). Capture exit
   code + the run dir it produced.
4. Evidence gate: re-derive the step's state from evidence. Verified pass →
   continue to next iteration; anything else → stop with the step's actual
   state + the run's blockers surfaced (reuse #103's blocked_reason surfacing).
   Never proceed past a non-verified step.
5. Write an auto-session receipt with HONEST flags for this mode:
   `mode:"run-item"`, `executes_proofrun:true`, `launches_workers:true`,
   `max_steps_enforced:true`, per-step records (command, run_dir, resulting
   state). The receipt is orchestration metadata, not proof — each step's proof
   is its own run evidence.

**Boundaries:** stops at first non-pass; never skips proofcheck (the executed
commands are `orro flow`/`orro check`, which embed it); never repairs/retries a
failed step; never invents inputs; does not approve merge or raise assurance.
Docs statements about `--once`/`--until-complete` never launching proofrun stay
true for those modes; the new mode is documented separately and honestly.

## Out of scope (YAGNI, v1)

- "Wrong document" detection (observed reads vs declared spec) — needs a
  concrete captured instance first (#105 collects them).
- Depone verification of roadmap bindings (v2; binding is declared intent).
- Deleting run dirs / evidence (retention is a separate policy decision).
- Auto-binding runs to items by inference — never inferred.

## Testing plan

- Unit: ledger read/write round-trip + malformed→blocker; binding seal+verify;
  unknown item id → `ERR_ORRO_ROADMAP_ITEM_UNKNOWN`; status vocabulary
  derivation (verified-done vs marked-done vs in-progress vs not-started);
  tidy dry-run never mutates; tidy --apply skips dirty (live-check) and
  non-complete runs.
- LIVE: seed a ledger, run a bound verification-only proofrun to completion →
  `orro status` shows the item `done (verified)` with evidence ref; an unbound
  run appears under off-plan; create a worktree, dirty it → `tidy` keeps it
  with reason; clean+complete → `tidy --apply` removes it.
- Clean-env full suite; regression delta 0 vs main (4 known env failures).
- CI is ground truth.
