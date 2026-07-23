# ORRO task worktrees — `orro task begin` + workspace handoff (issue #109 v1)

**Date:** 2026-07-23
**Status:** Design locked → implementation
**Issue:** ORRO #109 (proposal accepted; design position in the issue comment)
**Scope:** witnessd only; Depone unchanged; ORRO re-pin + wrapper sync (`task` is a new public verb).

## Core decision

**A task IS a roadmap item.** No new identifier space. The task worktree
lifecycle composes on #105 machinery: item ids validate against
`.orro/roadmap.json` (reuse `ERR_ORRO_ROADMAP_ITEM_UNKNOWN`), `orro status`
surfaces workspaces, `orro tidy` governs cleanup with the same safety rules.

Two worktree kinds, deliberately distinct:
- **Lane worktrees** (existing): under the run dir, ephemeral execution
  workspaces. Untouched by this design.
- **Task worktrees** (new): persistent, cross-run, one per roadmap item, at
  `<repo>/.orro/worktrees/<item-id>`, branch `orro/<item-id>`.

## `orro task begin <item-id> --repo <repo> [--base <ref>] [--no-open] [--json]`

1. Validate `<item-id>` against `.orro/roadmap.json` (absent ledger or unknown
   id → fail-closed structured blocker, reusing the roadmap error codes).
2. **Create or resume (idempotent):**
   - No worktree, no branch → `git worktree add -b orro/<item-id>
     .orro/worktrees/<item-id> <base>` (`--base` default: current repo HEAD;
     the resolved commit is recorded).
   - Branch exists, worktree missing → attach: `git worktree add
     .orro/worktrees/<item-id> orro/<item-id>` (resume after cleanup).
   - Worktree exists → resume: report it, refresh nothing, re-run the open hook
     unless `--no-open`.
3. **Seal the descriptor** `.orro/worktrees/<item-id>/.orro-task.json`:
   `{kind:"orro-task-descriptor", schema_version:"0.1", item_id, worktree,
   branch, base_commit}` — written create-then-verify-readable (the existing
   seal idiom). The descriptor is the single durable record; `orro status`
   discovers task worktrees by scanning `.orro/worktrees/*/.orro-task.json`
   (no second registry).
4. **Open hook (the entire Herdr adapter):** if env `ORRO_TASK_OPEN_COMMAND`
   is set (e.g. `herdr open {path}`), substitute `{path}` `{item_id}`
   `{branch}` and exec it; record `task-open-receipt.json` beside the
   descriptor `{command, exit_code}`. Unset → report
   `open hook not configured (set ORRO_TASK_OPEN_COMMAND)` — informational,
   not an error. ORRO never knows what Herdr is; failure of the hook is
   reported (nonzero exit surfaces) but does not roll back the worktree.

## `orro status` integration

An item whose task worktree exists gains one line:
`workspace: .orro/worktrees/<id> (branch orro/<id>, clean|dirty)` — dirty from
a live `git status --porcelain` in that worktree. Descriptor unreadable/
mismatched → `workspace: unverified descriptor` (never guessed).

## `orro tidy` integration

Inventory includes `.orro/worktrees/*` (same fields). `--apply` may remove a
task worktree ONLY when (live-check clean) AND (its item is `done (verified)`
— hand-marked `marked-done (unverified)` does NOT qualify). Branch is never
deleted. Everything else `kept: <reason>`. No `--force`, as before.

## Honesty boundaries (from the issue, kept verbatim in help/docs)

- The worktree, its branch, and its commits are workspace state, **not proof**;
  evidence still comes only from observed runs + Depone verdicts.
- `task begin` output is setup metadata — not proof, not verifier truth, not
  approval, not assurance.
- Merge approval and merge execution stay human; ORRO never merges.
- Panes/agent/session state belong to the workspace runtime (Herdr), never
  sealed into evidence.

## Command surface

New public verb: `task` → internal `orro-task` (subcommand `begin`; `list` is
YAGNI — status covers it). ORRO_COMMAND_MAP + witnessd help/tests + (at re-pin)
ORRO wrapper epilog + `check_orro_wrapper.py` authoritative list.

## Testing plan

- Unit: unknown item fail-closed; create/attach/resume idempotency (three
  states); descriptor seal+verify; open hook substitution + receipt + unset →
  informational; status workspace line incl. dirty + unverified-descriptor;
  tidy keeps dirty / keeps non-verified-done / removes clean+verified-done,
  branch preserved.
- LIVE: begin (no hook) → descriptor + status line; dirty the worktree → status
  dirty + tidy keeps; complete the item via a bound verified run → tidy --apply
  removes worktree, branch remains; second `begin` re-attaches on the branch.
- Clean-env full suite; regression delta 0 (4 known env failures). CI ground truth.
