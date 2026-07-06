# ORRO Assurance Harness Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the strategic review spec into enforceable P0/P1 implementation slices for ORRO doctrine, artifact semantics, threat model, confusion corpus, and long-automation gates.

**Architecture:** Keep ORRO as a documentation, distribution, wrapper, and harness surface. Extend the existing `scripts/check_orro_repo_contract.py` contract checker instead of adding a new CI job or dependency. Store canonical assurance guidance under `docs/assurance/` and machine-readable confusion cases under `packaging/`.

**Tech Stack:** Python 3 standard library, Markdown, JSON, existing GitHub Actions CI.

---

## Scope

This plan implements the next foundation layer after `docs/orro-strategic-review-spec.md`. It does not add verifier, runtime, proofrun, proofcheck, scheduler, observer, fan-in, or package publishing behavior.

The first PR should land Tasks 1-3 together because they close the current P0 hole: the strategy spec says the artifact table is canonical, but the contract checker only enforces a few phrases. Tasks 4-5 can land as follow-up PRs if the first PR needs to stay smaller.

## File Structure

- Modify `docs/orro-strategic-review-spec.md`: tighten the trust-boundary wording and link the implementation follow-up surface.
- Modify `scripts/check_orro_repo_contract.py`: enforce strategic spec sections, artifact table rows, assurance docs, and confusion corpus.
- Create `docs/assurance/threat-model.md`: first ORRO threat model focused on prompt injection, secret leakage, replay, report/proof confusion, and handoff/approval confusion.
- Create `docs/assurance/long-automation-maturity.md`: entry/exit criteria for maturity ladder levels 0-5.
- Modify `docs/README.md`: expose the assurance docs.
- Create `packaging/strategic-review-corpus.v0.json`: machine-readable negative cases for doctrine confusion.

## Task 1: Tighten Strategic Spec Trust Wording

**Files:**
- Modify: `docs/orro-strategic-review-spec.md`

- [ ] **Step 1: Locate the loose trust sentence**

Run:

```bash
rg -n "신뢰 상승은 Depone proofcheck와 witnessd가 남긴 evidence에서만 온다" docs/orro-strategic-review-spec.md
```

Expected: one match in the opening section.

- [ ] **Step 2: Replace the sentence with stricter wording**

Change this sentence:

```markdown
ORRO의 역할은 verifier나 execution engine이 되는 것이 아니다. ORRO는 사용자가 긴 자동화를 더 빨리 시작하고 더 안전하게 검토하도록 workflow surface, harness surface, 문서, schema, contract check, report를 제공해야 한다. 신뢰 상승은 Depone proofcheck와 witnessd가 남긴 evidence에서만 온다. Humans retain judgment.
```

to:

```markdown
ORRO의 역할은 verifier나 execution engine이 되는 것이 아니다. ORRO는 사용자가 긴 자동화를 더 빨리 시작하고 더 안전하게 검토하도록 workflow surface, harness surface, 문서, schema, contract check, report를 제공해야 한다. 판단 근거는 witnessd가 남긴 evidence이고, verifier truth는 Depone proofcheck에서만 온다. Humans retain judgment.
```

- [ ] **Step 3: Verify the old sentence is gone and doctrine remains**

Run:

```bash
! rg -n "신뢰 상승은 Depone proofcheck와 witnessd가 남긴 evidence에서만 온다" docs/orro-strategic-review-spec.md
rg -n "판단 근거는 witnessd가 남긴 evidence이고, verifier truth는 Depone proofcheck에서만 온다|Humans retain judgment" docs/orro-strategic-review-spec.md
```

Expected: the first command exits 1 because the old sentence is absent; the second command prints both strict trust wording and `Humans retain judgment`.

- [ ] **Step 4: Run the current contract check**

Run:

```bash
python3 scripts/check_orro_repo_contract.py
```

Expected:

```text
ORRO repo contract: pass
```

- [ ] **Step 5: Commit**

```bash
git add docs/orro-strategic-review-spec.md
git commit -m "Tighten ORRO strategic trust wording"
```

## Task 2: Enforce Strategic Spec Structure and Artifact Table

**Files:**
- Modify: `scripts/check_orro_repo_contract.py`
- Check: `docs/orro-strategic-review-spec.md`

- [ ] **Step 1: Prove the current checker misses artifact table deletion**

Run:

```bash
cp docs/orro-strategic-review-spec.md /tmp/orro-strategic-review-spec.backup.md
python3 - <<'PY'
from pathlib import Path

path = Path("docs/orro-strategic-review-spec.md")
text = path.read_text(encoding="utf-8")
start = text.index("| Artifact | Means | Does not mean |")
end = text.index("문서 작성 규칙:", start)
path.write_text(text[:start] + text[end:], encoding="utf-8")
PY
python3 scripts/check_orro_repo_contract.py
mv /tmp/orro-strategic-review-spec.backup.md docs/orro-strategic-review-spec.md
```

Expected before implementation:

```text
ORRO repo contract: pass
```

This proves the checker does not yet enforce the canonical artifact table.

- [ ] **Step 2: Add required section and artifact constants**

In `scripts/check_orro_repo_contract.py`, after `STRATEGIC_REVIEW_REQUIRED_PHRASES`, add:

```python
STRATEGIC_REVIEW_REQUIRED_SECTIONS = (
    "## 1. 총평",
    "## 2. 철학 적합성 점수",
    "## 3. 가장 잘한 점",
    "## 4. 가장 위험한 점",
    "## 5. 작은 설계 리뷰",
    "## 6. 큰 방향 리뷰",
    "## 7. 하네스 설계안",
    "## 8. 품질 하네스",
    "## 9. 효율 측정안",
    "## 10. 긴 자동화 maturity ladder",
    "## 11. 지금 당장 해야 할 P0",
    "## 12. v0.1 전에 해야 할 P1",
    "## 13. 장기 P2/P3",
    "## 14. 문서에 넣을 철학 선언문",
    "## 15. 최종 판단",
)
STRATEGIC_REVIEW_ARTIFACT_ROWS = (
    ("workflow-plan", "실행 의도와 단계 구조", "proof, approval, verifier truth"),
    ("proofrun", "witnessd가 실행을 수행하고 evidence를 남긴 run", "proofcheck 통과, merge approval"),
    ("proofcheck-verdict", "Depone이 evidence를 검증한 verdict", "사람이 판단을 포기해도 된다는 뜻"),
    ("handoff", "리뷰를 위한 패키징과 다음 행동 요약", "approval, proof, release permission"),
    ("report", "사람이 읽기 쉬운 요약", "proof, verifier truth, approval"),
    ("engine-lock", "pinned engine pair와 distribution metadata", "assurance 상승, evidence proof"),
    ("release-manifest", "release candidate metadata와 validated engine pair 기록", "package publish, proof, approval"),
)
```

- [ ] **Step 3: Add a Markdown table-row helper**

In `scripts/check_orro_repo_contract.py`, after `require_any_contains`, add:

```python
def require_markdown_table_row(
    label: str,
    haystack: str,
    columns: tuple[str, str, str],
) -> None:
    expected = "| " + " | ".join(columns) + " |"
    require_contains(label, haystack, expected)
```

- [ ] **Step 4: Extend strategic spec validation**

Replace `check_strategic_review_spec()` with:

```python
def check_strategic_review_spec() -> None:
    path = "docs/orro-strategic-review-spec.md"
    if not (ROOT / path).is_file():
        fail(f"required strategic review spec missing: {path}")
    text = read_text(path)
    for phrase in STRATEGIC_REVIEW_REQUIRED_PHRASES:
        require_contains(path, text, phrase)
    for section in STRATEGIC_REVIEW_REQUIRED_SECTIONS:
        require_contains(path, text, section)
    require_contains(path, text, "| Artifact | Means | Does not mean |")
    for row in STRATEGIC_REVIEW_ARTIFACT_ROWS:
        require_markdown_table_row(path, text, row)
```

- [ ] **Step 5: Verify artifact table deletion now fails**

Run:

```bash
cp docs/orro-strategic-review-spec.md /tmp/orro-strategic-review-spec.backup.md
python3 - <<'PY'
from pathlib import Path

path = Path("docs/orro-strategic-review-spec.md")
text = path.read_text(encoding="utf-8")
start = text.index("| Artifact | Means | Does not mean |")
end = text.index("문서 작성 규칙:", start)
path.write_text(text[:start] + text[end:], encoding="utf-8")
PY
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-strategic-review-spec.backup.md docs/orro-strategic-review-spec.md
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: docs/orro-strategic-review-spec.md must contain '| Artifact | Means | Does not mean |'
```

- [ ] **Step 6: Verify section deletion now fails**

Run:

```bash
cp docs/orro-strategic-review-spec.md /tmp/orro-strategic-review-spec.backup.md
python3 - <<'PY'
from pathlib import Path

path = Path("docs/orro-strategic-review-spec.md")
text = path.read_text(encoding="utf-8").replace("## 10. 긴 자동화 maturity ladder", "## 10. 긴 자동화")
path.write_text(text, encoding="utf-8")
PY
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-strategic-review-spec.backup.md docs/orro-strategic-review-spec.md
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: docs/orro-strategic-review-spec.md must contain '## 10. 긴 자동화 maturity ladder'
```

- [ ] **Step 7: Verify green state**

Run:

```bash
python3 scripts/check_orro_repo_contract.py
python3 -m py_compile scripts/check_orro_repo_contract.py
git diff --check
```

Expected:

```text
ORRO repo contract: pass
```

`py_compile` and `git diff --check` produce no output and exit 0.

- [ ] **Step 8: Remove generated Python cache**

Run:

```bash
rm -rf scripts/__pycache__
git status --short
```

Expected: no `scripts/__pycache__/` entry.

- [ ] **Step 9: Commit**

```bash
git add scripts/check_orro_repo_contract.py
git commit -m "Enforce ORRO strategic artifact table"
```

## Task 3: Add Assurance Threat Model

**Files:**
- Create: `docs/assurance/threat-model.md`
- Modify: `docs/README.md`
- Modify: `scripts/check_orro_repo_contract.py`

- [ ] **Step 1: Prove the current repo contract does not require the threat model**

Run:

```bash
test ! -f docs/assurance/threat-model.md
python3 scripts/check_orro_repo_contract.py
```

Expected:

```text
ORRO repo contract: pass
```

- [ ] **Step 2: Create the assurance directory and threat model**

Run:

```bash
mkdir -p docs/assurance
```

Create `docs/assurance/threat-model.md` with:

```markdown
# ORRO Assurance Threat Model

ORRO is a workflow and harness surface. It does not execute commands, verify evidence, approve merges, or raise assurance by itself.

```text
Depone verifies; witnessd executes; ORRO exposes the workflow.
Verified acceleration, not blind automation.
Humans retain judgment.
```

## Trust Boundaries

| Boundary | Owner | ORRO rule |
| --- | --- | --- |
| Execution/runtime | witnessd | ORRO may expose commands and reports, but must not implement runtime behavior. |
| Evidence emission | witnessd | ORRO may reference evidence paths, but must not synthesize runtime evidence. |
| Proofcheck truth | Depone | ORRO may display verdicts, but must not reinterpret failed or missing verdicts as pass. |
| Judgment | Human | ORRO may prepare handoff, but handoff is not approval. |
| Summary | ORRO | report is not proof. |

## Threats

### Prompt Injection

Risk: malicious text in workflow-plan, handoff, report, or evidence summary asks the user or agent to treat a summary as approval or proof.

Required response:

- Preserve artifact boundaries.
- Reject wording that says ORRO approves, proves, verifies, or raises assurance.
- Keep Depone as the only verifier semantics owner.

### Secret Leakage

Risk: report or handoff repeats tokens, credentials, private URLs, or signing material from captured output.

Required response:

- Reports must prefer evidence paths over pasted sensitive content.
- Secret-looking content must not be repeated in public-facing summaries.
- SECURITY.md must define disclosure handling before v0.1.

### Replay or Stale Evidence

Risk: old evidence is presented as a new run, or stale evidence is summarized without a freshness warning.

Required response:

- ORRO must distinguish replayed evidence, stale evidence, and current evidence.
- Depone owns verifier rejection for forged or replayed evidence.
- ORRO reports must not convert replay/stale warnings into pass language.

### Handoff Approval Confusion

Risk: handoff text is read as merge, release, or deployment approval.

Required response:

- handoff is not approval.
- Humans retain judgment.
- Formal approval must remain outside generated handoff content.

### Report Proof Confusion

Risk: report text is read as proof or verifier truth.

Required response:

- report is not proof.
- Reports must link to or name evidence and proofcheck verdict paths.
- Reports must not claim stronger truth than the underlying verdict supports.

## Non-Goals

- No ORRO verifier implementation.
- No ORRO execution runtime.
- No ORRO proofrun or proofcheck logic.
- No package publish or command ownership change.
```

- [ ] **Step 3: Link the threat model from docs README**

In `docs/README.md`, add this bullet after `ORRO Strategic Review Spec`:

```markdown
- [Assurance Threat Model](assurance/threat-model.md)
```

- [ ] **Step 4: Extend the repo contract**

In `scripts/check_orro_repo_contract.py`, add this function after `check_strategic_review_spec()`:

```python
def check_assurance_docs() -> None:
    required_paths = [
        "docs/assurance/threat-model.md",
    ]
    for path in required_paths:
        if not (ROOT / path).is_file():
            fail(f"required assurance doc missing: {path}")

    text = combined_text(required_paths + ["docs/README.md"])
    for phrase in (
        "Prompt Injection",
        "Secret Leakage",
        "Replay or Stale Evidence",
        "Handoff Approval Confusion",
        "Report Proof Confusion",
        "handoff is not approval",
        "report is not proof",
        "Humans retain judgment",
        INVARIANT,
    ):
        require_contains("assurance docs", text, phrase)
```

Then call it in `main()` immediately after `check_strategic_review_spec()`:

```python
    check_assurance_docs()
```

- [ ] **Step 5: Prove missing threat model fails**

Run:

```bash
mv docs/assurance/threat-model.md /tmp/orro-threat-model.backup.md
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-threat-model.backup.md docs/assurance/threat-model.md
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: required assurance doc missing: docs/assurance/threat-model.md
```

- [ ] **Step 6: Verify green state**

Run:

```bash
python3 scripts/check_orro_repo_contract.py
python3 -m py_compile scripts/check_orro_repo_contract.py
git diff --check
```

Expected:

```text
ORRO repo contract: pass
```

`py_compile` and `git diff --check` produce no output and exit 0.

- [ ] **Step 7: Remove generated Python cache**

Run:

```bash
rm -rf scripts/__pycache__
git status --short
```

Expected: no `scripts/__pycache__/` entry.

- [ ] **Step 8: Commit**

```bash
git add docs/README.md docs/assurance/threat-model.md scripts/check_orro_repo_contract.py
git commit -m "Add ORRO assurance threat model"
```

## Task 4: Add Strategic Confusion Corpus

**Files:**
- Create: `packaging/strategic-review-corpus.v0.json`
- Modify: `scripts/check_orro_repo_contract.py`

- [ ] **Step 1: Prove the current repo contract does not require a corpus**

Run:

```bash
test ! -f packaging/strategic-review-corpus.v0.json
python3 scripts/check_orro_repo_contract.py
```

Expected:

```text
ORRO repo contract: pass
```

- [ ] **Step 2: Create the corpus file**

Create `packaging/strategic-review-corpus.v0.json` with:

```json
{
  "kind": "orro-strategic-review-corpus",
  "schema_version": "0.1",
  "boundary": {
    "approves_merge": false,
    "contains_engine_logic": false,
    "executes_commands": false,
    "raises_assurance": false,
    "verifies_evidence": false
  },
  "cases": [
    {
      "id": "approval-looking-handoff",
      "artifact": "handoff",
      "risk": "handoff_approval_confusion",
      "phrase": "This handoff approves the merge.",
      "must_reject_as": "handoff is not approval"
    },
    {
      "id": "proof-looking-report",
      "artifact": "report",
      "risk": "report_proof_confusion",
      "phrase": "This report proves the run is safe.",
      "must_reject_as": "report is not proof"
    },
    {
      "id": "orro-verifier-overclaim",
      "artifact": "report",
      "risk": "verifier_boundary_confusion",
      "phrase": "ORRO verified the evidence.",
      "must_reject_as": "Depone verifies; witnessd executes; ORRO exposes the workflow"
    },
    {
      "id": "engine-lock-assurance-overclaim",
      "artifact": "engine-lock",
      "risk": "engine_lock_assurance_confusion",
      "phrase": "The engine lock raises assurance.",
      "must_reject_as": "engine-lock is distribution metadata, not proof"
    },
    {
      "id": "long-run-trust-expansion",
      "artifact": "report",
      "risk": "long_automation_trust_confusion",
      "phrase": "Because the long automation completed, trust is expanded.",
      "must_reject_as": "long automation is checkpoint expansion, not trust expansion"
    }
  ]
}
```

- [ ] **Step 3: Add corpus validation to the repo contract**

In `scripts/check_orro_repo_contract.py`, add this function after `check_assurance_docs()`:

```python
def check_strategic_review_corpus() -> None:
    path = "packaging/strategic-review-corpus.v0.json"
    if not (ROOT / path).is_file():
        fail(f"required strategic review corpus missing: {path}")

    data = load_json(path)
    if data.get("kind") != "orro-strategic-review-corpus":
        fail("strategic review corpus kind must be orro-strategic-review-corpus")
    if data.get("schema_version") != "0.1":
        fail("strategic review corpus schema_version must be 0.1")

    boundary = data.get("boundary", {})
    for key in ("approves_merge", "contains_engine_logic", "executes_commands", "raises_assurance", "verifies_evidence"):
        if boundary.get(key) is not False:
            fail(f"strategic review corpus boundary.{key} must be false")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        fail("strategic review corpus must contain at least five cases")

    required_risks = {
        "handoff_approval_confusion",
        "report_proof_confusion",
        "verifier_boundary_confusion",
        "engine_lock_assurance_confusion",
        "long_automation_trust_confusion",
    }
    seen_risks: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            fail(f"strategic review corpus case {index} must be an object")
        for key in ("id", "artifact", "risk", "phrase", "must_reject_as"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                fail(f"strategic review corpus case {index}.{key} must be a non-empty string")
        seen_risks.add(case["risk"])

    missing = sorted(required_risks - seen_risks)
    if missing:
        fail(f"strategic review corpus missing required risks: {missing}")
```

Then call it in `main()` immediately after `check_assurance_docs()`:

```python
    check_strategic_review_corpus()
```

- [ ] **Step 4: Prove missing corpus fails**

Run:

```bash
mv packaging/strategic-review-corpus.v0.json /tmp/orro-strategic-review-corpus.backup.json
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-strategic-review-corpus.backup.json packaging/strategic-review-corpus.v0.json
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: required strategic review corpus missing: packaging/strategic-review-corpus.v0.json
```

- [ ] **Step 5: Prove incomplete corpus fails**

Run:

```bash
cp packaging/strategic-review-corpus.v0.json /tmp/orro-strategic-review-corpus.backup.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("packaging/strategic-review-corpus.v0.json")
data = json.loads(path.read_text(encoding="utf-8"))
data["cases"] = data["cases"][:1]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-strategic-review-corpus.backup.json packaging/strategic-review-corpus.v0.json
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: strategic review corpus must contain at least five cases
```

- [ ] **Step 6: Verify green state**

Run:

```bash
python3 scripts/check_orro_repo_contract.py
python3 -m py_compile scripts/check_orro_repo_contract.py
git diff --check
```

Expected:

```text
ORRO repo contract: pass
```

`py_compile` and `git diff --check` produce no output and exit 0.

- [ ] **Step 7: Remove generated Python cache**

Run:

```bash
rm -rf scripts/__pycache__
git status --short
```

Expected: no `scripts/__pycache__/` entry.

- [ ] **Step 8: Commit**

```bash
git add packaging/strategic-review-corpus.v0.json scripts/check_orro_repo_contract.py
git commit -m "Add ORRO strategic confusion corpus"
```

## Task 5: Add Long-Automation Maturity Gates

**Files:**
- Create: `docs/assurance/long-automation-maturity.md`
- Modify: `docs/README.md`
- Modify: `scripts/check_orro_repo_contract.py`

- [ ] **Step 1: Prove the current repo contract does not require maturity gates**

Run:

```bash
test ! -f docs/assurance/long-automation-maturity.md
python3 scripts/check_orro_repo_contract.py
```

Expected:

```text
ORRO repo contract: pass
```

- [ ] **Step 2: Create the maturity gate document**

Create `docs/assurance/long-automation-maturity.md` with:

```markdown
# ORRO Long-Automation Maturity Gates

Long automation is checkpoint expansion, not trust expansion.

## Gate Rules

- A higher level may add automation length, resume behavior, or corpus gates.
- A higher level must not raise assurance without Depone proofcheck truth.
- A higher level must not convert handoff into approval.
- A higher level must not convert report into proof.
- Humans retain judgment at every level.

## Levels

| Level | Name | Entry criteria | Exit criteria | Must not mean |
| --- | --- | --- | --- | --- |
| 0 | Manual checkpoints | User can run each ORRO command manually from docs. | User can locate workflow-plan, proofrun output, proofcheck verdict, handoff, and report paths. | Manual success is not proof. |
| 1 | Assisted flow | ORRO exposes command sequence without hiding engine ownership. | Each step is still explicitly invoked or reviewed. | Command convenience is not trust expansion. |
| 2 | Checkpointed automation | Multi-step flow writes checkpoint artifacts and stop conditions. | Failed checkpoint stops downstream work fail-closed. | Completed automation is not approval. |
| 3 | Resume-aware automation | witnessd emits checkpoint and resume evidence. | ORRO reports resume status without proof overclaim. | Resume is not verifier truth. |
| 4 | Corpus-gated automation | Injection, replay, secret, and regression corpus checks pass. | Corpus result is summarized with evidence paths. | Corpus pass is not proofcheck truth. |
| 5 | Release-gated automation | Engine-lock, release manifest, compatibility matrix, and e2e smoke align. | Human release judgment remains explicit. | Release gate metadata is not approval. |

## Minimum Evidence Per Level

| Level | Required evidence |
| --- | --- |
| 0 | Documentation command path and artifact path examples. |
| 1 | Explicit command transcript or wrapper delegation output. |
| 2 | Checkpoint artifact list and fail-closed stop condition. |
| 3 | Resume receipt or checkpoint/resume evidence path. |
| 4 | Corpus check result and rejected confusion cases. |
| 5 | Engine-lock, release manifest, compatibility matrix, and e2e smoke result paths. |
```

- [ ] **Step 3: Link maturity gates from docs README**

In `docs/README.md`, add this bullet after `Assurance Threat Model`:

```markdown
- [Long-Automation Maturity Gates](assurance/long-automation-maturity.md)
```

- [ ] **Step 4: Extend assurance docs contract**

In `check_assurance_docs()`, change `required_paths` to:

```python
    required_paths = [
        "docs/assurance/threat-model.md",
        "docs/assurance/long-automation-maturity.md",
    ]
```

Extend the phrase tuple with:

```python
        "Long-Automation Maturity Gates",
        "Entry criteria",
        "Exit criteria",
        "Must not mean",
        "long automation is checkpoint expansion, not trust expansion",
```

- [ ] **Step 5: Prove missing maturity gates fail**

Run:

```bash
mv docs/assurance/long-automation-maturity.md /tmp/orro-long-automation-maturity.backup.md
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-long-automation-maturity.backup.md docs/assurance/long-automation-maturity.md
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: required assurance doc missing: docs/assurance/long-automation-maturity.md
```

- [ ] **Step 6: Verify green state**

Run:

```bash
python3 scripts/check_orro_repo_contract.py
python3 -m py_compile scripts/check_orro_repo_contract.py
git diff --check
```

Expected:

```text
ORRO repo contract: pass
```

`py_compile` and `git diff --check` produce no output and exit 0.

- [ ] **Step 7: Remove generated Python cache**

Run:

```bash
rm -rf scripts/__pycache__
git status --short
```

Expected: no `scripts/__pycache__/` entry.

- [ ] **Step 8: Commit**

```bash
git add docs/README.md docs/assurance/long-automation-maturity.md scripts/check_orro_repo_contract.py
git commit -m "Add ORRO long automation maturity gates"
```

## Final Verification

Run the full existing ORRO validation set:

```bash
python3 scripts/check_orro_repo_contract.py
python3 scripts/check_orro_command_migration.py
python3 scripts/check_orro_packaging_decision.py
python3 scripts/check_orro_wrapper.py
python3 scripts/check_orro_command_migration_dry_run.py --self-test
python3 scripts/orro_e2e_smoke.py --self-test
python3 -m py_compile scripts/check_orro_repo_contract.py scripts/check_orro_command_migration.py scripts/check_orro_packaging_decision.py scripts/check_orro_wrapper.py scripts/check_orro_command_migration_dry_run.py scripts/orro_e2e_smoke.py
git diff --check
```

Expected:

- `check_orro_repo_contract.py` prints `ORRO repo contract: pass`.
- Command migration, packaging decision, and wrapper checks print `pass`.
- Dry-run and e2e self-tests return JSON with `"decision": "pass"`.
- `py_compile` and `git diff --check` produce no output and exit 0.

Then run:

```bash
rm -rf scripts/__pycache__
git status --short --branch
```

Expected: only intentional tracked changes before final commit, or a clean branch after all commits.

## Pull Request Notes

PR title:

```text
Add ORRO assurance harness foundation
```

PR body must include:

- Boundary statement: `Depone verifies; witnessd executes; ORRO exposes the workflow`.
- No engine/verifier/runtime code added.
- No package publish or ORRO command ownership change.
- Contract checker now enforces strategic sections, artifact table, assurance docs, and corpus shape.
- Tests run from Final Verification.
- Residual risk: this foundation still does not implement runtime replay detection or Depone verifier semantics; it only gives ORRO a stronger harness surface and regression corpus.

## Self-Review

Spec coverage:

- Strategic doctrine phrases are enforced in Task 2.
- Artifact meaning table is enforced in Task 2.
- Threat model and security risks are covered in Task 3.
- Prompt-injection/report-proof/handoff-approval confusion cases are covered in Task 4.
- Long automation maturity entry/exit criteria are covered in Task 5.
- No ORRO engine, verifier, runtime, package publish, or command migration behavior is added.

Type and path consistency:

- New docs live under `docs/assurance/`.
- New machine-readable corpus lives under `packaging/`.
- Existing CI already runs `scripts/check_orro_repo_contract.py`, so no workflow edit is required.

Execution stop condition:

- Stop when all five tasks are committed, full verification passes, generated caches are removed, and the PR clearly states remaining runtime/verifier work is outside this foundation.
