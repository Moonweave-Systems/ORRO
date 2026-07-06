# ORRO Assurance Harness Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the strategic review spec into enforceable P0/P1 implementation slices for ORRO doctrine, artifact semantics, threat model, confusion corpus, and long-automation gates.

**Architecture:** Keep ORRO as a documentation, distribution, wrapper, and harness surface. Extend the existing `scripts/check_orro_repo_contract.py` contract checker instead of adding a new CI job or dependency. Store canonical assurance guidance and machine-readable doctrine-confusion cases under `docs/assurance/`.

**Tech Stack:** Python 3 standard library, Markdown, JSON, existing GitHub Actions CI.

---

## Scope

This plan implements the next foundation layer after `docs/orro-strategic-review-spec.md`. It does not add verifier, runtime, proofrun, proofcheck, scheduler, observer, fan-in, or package publishing behavior.

The first PR should land Tasks 1-3 together because they close the current P0 hole: the strategy spec says the artifact table is canonical, but the contract checker only enforces a few phrases. Tasks 4-5 can land as follow-up PRs if the first PR needs to stay smaller.

This document is an implementation plan. Merging this plan alone does not add the assurance docs, corpus, maturity gates, or expanded contract checks. Those changes land only when the task commits below are implemented.

## File Structure

- Modify `docs/orro-strategic-review-spec.md`: tighten the trust-boundary wording and link the implementation follow-up surface.
- Modify `scripts/check_orro_repo_contract.py`: enforce strategic spec sections, artifact table rows, assurance docs, and confusion corpus.
- Create `docs/assurance/threat-model.md`: first ORRO threat model focused on prompt injection, secret leakage, replay, report/proof confusion, and handoff/approval confusion.
- Create `docs/assurance/long-automation-maturity.md`: entry/exit criteria for maturity ladder levels 0-5.
- Modify `docs/README.md`: expose the assurance docs.
- Create `docs/assurance/strategic-review-corpus.v0.json`: machine-readable negative cases for doctrine confusion.

## Task 1: Tighten Strategic Spec Trust Wording

**Files:**
- Modify: `docs/orro-strategic-review-spec.md`

- [ ] **Step 1: Locate the loose trust sentence**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("docs/orro-strategic-review-spec.md")
needle = "신뢰 상승은 Depone proofcheck와 witnessd가 남긴 evidence에서만 온다"
count = path.read_text(encoding="utf-8").count(needle)
if count != 1:
    raise SystemExit(f"expected one match, found {count}")
print(f"{path}: found target trust sentence")
PY
```

Expected:

```text
docs/orro-strategic-review-spec.md: found target trust sentence
```

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
python3 - <<'PY'
from pathlib import Path

path = Path("docs/orro-strategic-review-spec.md")
text = path.read_text(encoding="utf-8")
old = "신뢰 상승은 Depone proofcheck와 witnessd가 남긴 evidence에서만 온다"
new = "판단 근거는 witnessd가 남긴 evidence이고, verifier truth는 Depone proofcheck에서만 온다"

if old in text:
    raise SystemExit("old loose trust sentence still present")
if new not in text:
    raise SystemExit("strict trust wording missing")
if "Humans retain judgment" not in text:
    raise SystemExit("Humans retain judgment missing")
print("strategic trust wording: pass")
PY
```

Expected:

```text
strategic trust wording: pass
```

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
STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS = {
    "workflow-plan": ("실행 의도", "proof", "approval", "verifier truth"),
    "proofrun": ("witnessd", "evidence", "proofcheck 통과", "merge approval"),
    "proofcheck-verdict": ("Depone", "verdict", "판단을 포기"),
    "handoff": ("리뷰", "approval", "proof", "release permission"),
    "report": ("요약", "proof", "verifier truth", "approval"),
    "engine-lock": ("pinned engine", "distribution metadata", "assurance", "proof"),
    "release-manifest": ("release candidate metadata", "package publish", "proof", "approval"),
}
```

- [ ] **Step 3: Add normalized text and artifact semantic helpers**

In `scripts/check_orro_repo_contract.py`, after `require_any_contains`, add:

```python
def normalize_contract_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def require_contains_normalized(label: str, haystack: str, needle: str) -> None:
    normalized_haystack = normalize_contract_text(haystack)
    normalized_needle = normalize_contract_text(needle)
    if normalized_needle not in normalized_haystack:
        fail(f"{label} must contain normalized {needle!r}")


def require_artifact_semantics(
    label: str,
    haystack: str,
    artifact: str,
    required_tokens: tuple[str, ...],
) -> None:
    rows = [
        normalize_contract_text(line)
        for line in haystack.splitlines()
        if line.lstrip().startswith("|") and artifact in line
    ]
    if not rows:
        fail(f"{label} must define artifact semantics for {artifact!r}")
    row_text = " ".join(rows)
    missing = [token for token in required_tokens if token not in row_text]
    if missing:
        fail(f"{label} artifact {artifact!r} missing semantic tokens: {missing}")
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
        require_contains_normalized(path, text, section)
    require_contains(path, text, "| Artifact | Means | Does not mean |")
    for artifact, required_tokens in STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS.items():
        require_artifact_semantics(path, text, artifact, required_tokens)
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

````markdown
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
- Depone is the only component allowed to emit verifier pass/fail semantics for forged or replayed evidence.
- Until the relevant Depone/witnessd semantics exist, ORRO must label replay/stale evidence as an unresolved risk, not as pass.
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
````

- [ ] **Step 3: Link the threat model from docs README**

In `docs/README.md`, add this bullet after `ORRO Strategic Review Spec`:

```markdown
- [Assurance Threat Model](assurance/threat-model.md)
```

- [ ] **Step 4: Extend the repo contract**

In `scripts/check_orro_repo_contract.py`, add this constant after `STRATEGIC_REVIEW_ARTIFACT_REQUIREMENTS`:

```python
ASSURANCE_DOC_REQUIRED_PHRASES = {
    "docs/assurance/threat-model.md": (
        "Prompt Injection",
        "Secret Leakage",
        "Replay or Stale Evidence",
        "Handoff Approval Confusion",
        "Report Proof Confusion",
        "handoff is not approval",
        "report is not proof",
        "Humans retain judgment",
        INVARIANT,
    ),
    "docs/README.md": (
        "[Assurance Threat Model](assurance/threat-model.md)",
    ),
}
```

Then add this function after `check_strategic_review_spec()`:

```python
def check_assurance_docs() -> None:
    for path, phrases in ASSURANCE_DOC_REQUIRED_PHRASES.items():
        if not (ROOT / path).is_file():
            fail(f"required assurance doc missing: {path}")
        text = read_text(path)
        for phrase in phrases:
            require_contains(path, text, phrase)
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
- Create: `docs/assurance/strategic-review-corpus.v0.json`
- Modify: `scripts/check_orro_repo_contract.py`

- [ ] **Step 1: Prove the current repo contract does not require a corpus**

Run:

```bash
test ! -f docs/assurance/strategic-review-corpus.v0.json
python3 scripts/check_orro_repo_contract.py
```

Expected:

```text
ORRO repo contract: pass
```

- [ ] **Step 2: Create the corpus file**

Create `docs/assurance/strategic-review-corpus.v0.json` with:

```json
{
  "kind": "orro-strategic-review-corpus",
  "schema_version": "0.1",
  "orro_boundary": {
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

Run:

```bash
python3 -m json.tool docs/assurance/strategic-review-corpus.v0.json >/dev/null
```

Expected: no output and exit 0.

- [ ] **Step 3: Add corpus validation to the repo contract**

In `scripts/check_orro_repo_contract.py`, add this function after `check_assurance_docs()`:

```python
def check_strategic_review_corpus() -> None:
    path = "docs/assurance/strategic-review-corpus.v0.json"
    if not (ROOT / path).is_file():
        fail(f"required strategic review corpus missing: {path}")

    data = load_json(path)
    if data.get("kind") != "orro-strategic-review-corpus":
        fail("strategic review corpus kind must be orro-strategic-review-corpus")
    if data.get("schema_version") != "0.1":
        fail("strategic review corpus schema_version must be 0.1")

    boundary = data.get("orro_boundary", {})
    for key in ("approves_merge", "contains_engine_logic", "executes_commands", "raises_assurance", "verifies_evidence"):
        if boundary.get(key) is not False:
            fail(f"strategic review corpus orro_boundary.{key} must be false")

    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        fail("strategic review corpus must contain at least five cases")

    allowed_artifacts = {
        "workflow-plan",
        "proofrun",
        "proofcheck-verdict",
        "handoff",
        "report",
        "engine-lock",
        "release-manifest",
    }
    allowed_rejections = {
        "handoff is not approval",
        "report is not proof",
        INVARIANT,
        "engine-lock is distribution metadata, not proof",
        "long automation is checkpoint expansion, not trust expansion",
    }
    required_risks = {
        "handoff_approval_confusion",
        "report_proof_confusion",
        "verifier_boundary_confusion",
        "engine_lock_assurance_confusion",
        "long_automation_trust_confusion",
    }
    allowed_risks = set(required_risks)
    seen_ids: set[str] = set()
    seen_risks: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            fail(f"strategic review corpus case {index} must be an object")
        for key in ("id", "artifact", "risk", "phrase", "must_reject_as"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                fail(f"strategic review corpus case {index}.{key} must be a non-empty string")

        case_id = case["id"]
        if case_id in seen_ids:
            fail(f"strategic review corpus duplicate case id: {case_id}")
        seen_ids.add(case_id)

        if case["artifact"] not in allowed_artifacts:
            fail(f"strategic review corpus case {index}.artifact is not allowed")
        if case["risk"] not in allowed_risks:
            fail(f"strategic review corpus case {index}.risk is not allowed")
        if case["must_reject_as"] not in allowed_rejections:
            fail(f"strategic review corpus case {index}.must_reject_as is not an allowed doctrine rejection")
        if case["phrase"] == case["must_reject_as"]:
            fail(f"strategic review corpus case {index} phrase must differ from rejection")

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
mv docs/assurance/strategic-review-corpus.v0.json /tmp/orro-strategic-review-corpus.backup.json
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-strategic-review-corpus.backup.json docs/assurance/strategic-review-corpus.v0.json
test "$status" -eq 1
```

Expected output includes:

```text
ORRO repo contract violation: required strategic review corpus missing: docs/assurance/strategic-review-corpus.v0.json
```

- [ ] **Step 5: Prove incomplete corpus fails**

Run:

```bash
cp docs/assurance/strategic-review-corpus.v0.json /tmp/orro-strategic-review-corpus.backup.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("docs/assurance/strategic-review-corpus.v0.json")
data = json.loads(path.read_text(encoding="utf-8"))
data["cases"] = data["cases"][:1]
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
python3 scripts/check_orro_repo_contract.py
status=$?
mv /tmp/orro-strategic-review-corpus.backup.json docs/assurance/strategic-review-corpus.v0.json
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
git add docs/assurance/strategic-review-corpus.v0.json scripts/check_orro_repo_contract.py
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

````markdown
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

## Out of Scope for This Foundation

Level 6 continuous operation is intentionally not defined in this document. Continuous operation requires production observability, drift detection, incident response, retention policy, and security review. This foundation stops at release-gated automation.
````

- [ ] **Step 3: Link maturity gates from docs README**

In `docs/README.md`, add this bullet after `Assurance Threat Model`:

```markdown
- [Long-Automation Maturity Gates](assurance/long-automation-maturity.md)
```

- [ ] **Step 4: Extend assurance docs contract**

In `ASSURANCE_DOC_REQUIRED_PHRASES`, add the maturity doc entry and replace the existing `docs/README.md` tuple with the two exact links:

```python
    "docs/assurance/long-automation-maturity.md": (
        "Long-Automation Maturity Gates",
        "Entry criteria",
        "Exit criteria",
        "Must not mean",
        "Long automation is checkpoint expansion, not trust expansion.",
        "Level 6 continuous operation is intentionally not defined",
        "Humans retain judgment",
    ),
    "docs/README.md": (
        "[Assurance Threat Model](assurance/threat-model.md)",
        "[Long-Automation Maturity Gates](assurance/long-automation-maturity.md)",
    ),
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
python3 scripts/check_orro_release_manifest.py
python3 scripts/check_orro_command_migration.py
python3 scripts/check_orro_packaging_decision.py
python3 scripts/check_orro_fallback_policy.py
python3 scripts/check_orro_command_migration_dry_run.py --json
python3 scripts/check_orro_wrapper.py
python3 scripts/check_orro_wrapper_install.py --json
python3 scripts/check_orro_wrapper_distribution.py --json

python3 -m py_compile \
  scripts/check_orro_repo_contract.py \
  scripts/check_orro_release_manifest.py \
  scripts/check_orro_packaging_decision.py \
  scripts/check_orro_fallback_policy.py \
  scripts/check_orro_command_migration.py \
  scripts/check_orro_command_migration_dry_run.py \
  scripts/check_orro_wrapper.py \
  scripts/check_orro_wrapper_install.py \
  scripts/check_orro_wrapper_distribution.py \
  scripts/orro_e2e_smoke.py \
  scripts/update_orro_engine_lock.py \
  scripts/bootstrap_orro.py \
  src/orro_wrapper/__init__.py \
  src/orro_wrapper/__main__.py \
  src/orro_wrapper/cli.py

PYTHONPATH=src python3 -m orro_wrapper self-test
python3 scripts/check_orro_wrapper_install.py --self-test
python3 scripts/check_orro_wrapper_distribution.py --self-test
python3 scripts/check_orro_command_migration_dry_run.py --self-test
python3 scripts/orro_e2e_smoke.py --self-test
python3 scripts/update_orro_engine_lock.py --self-test
python3 scripts/bootstrap_orro.py --self-test

git diff --check
```

Expected:

- `check_orro_repo_contract.py` prints `ORRO repo contract: pass`.
- Release manifest, command migration, packaging decision, fallback policy, and wrapper checks print `pass`.
- JSON checks and self-tests return valid JSON or pass output matching the current script contract.
- `py_compile` and `git diff --check` produce no output and exit 0.

Then run:

```bash
rm -rf scripts/__pycache__ src/orro_wrapper/__pycache__
git status --short --branch
```

Expected: only intentional tracked changes before final commit, or a clean branch after all commits.

## Pull Request Notes

For a plan-only PR, use this PR title:

```text
Plan ORRO assurance harness foundation
```

The plan-only PR body must include:

- This PR adds the implementation plan only.
- It does not yet add assurance docs, corpus, maturity gates, or expanded checker behavior.
- Boundary statement: `Depone verifies; witnessd executes; ORRO exposes the workflow`.
- No engine/verifier/runtime code added.
- No package publish or ORRO command ownership change.

For an implementation PR, use this PR title:

```text
Add ORRO assurance harness foundation
```

The implementation PR body must include:

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
- New machine-readable corpus lives under `docs/assurance/`.
- Existing CI already runs `scripts/check_orro_repo_contract.py`, so no workflow edit is required.

Execution stop condition:

- Stop when all five tasks are committed, full verification passes, generated caches are removed, and the PR clearly states remaining runtime/verifier work is outside this foundation.
