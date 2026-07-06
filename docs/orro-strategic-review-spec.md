# ORRO Strategic Review Spec

이 문서는 ORRO를 코드 구현체가 아니라 제품/아키텍처/운영 철학의 표면으로 리뷰한다. 결론은 간단하다.

```text
Verified acceleration, not blind automation.
Depone verifies; witnessd executes; ORRO exposes the workflow.
```

ORRO의 역할은 verifier나 execution engine이 되는 것이 아니다. ORRO는 사용자가 긴 자동화를 더 빨리 시작하고 더 안전하게 검토하도록 workflow surface, harness surface, 문서, schema, contract check, report를 제공해야 한다. 판단 근거는 witnessd가 남긴 evidence이고, verifier truth는 Depone proofcheck에서만 온다. Humans retain judgment.

## 1. 총평

ORRO의 가장 강한 방향성은 "자동화 실행"을 팔지 않고 "검증 가능한 가속"을 판다는 점이다. 현재 README와 engine contract는 이 경계를 이미 잘 잡고 있다. 특히 "Depone verifies; witnessd executes; ORRO exposes the workflow" 문장은 제품 정체성, repo 책임, 보안 경계를 한 줄로 고정한다.

좋은 점:

- ORRO는 사용자 경험과 배포 표면을 담당하고, Depone과 witnessd를 병합하지 않는다.
- handoff, report, engine-lock이 proof나 approval이 아니라는 분리가 이미 문서화되어 있다.
- CI가 repo boundary, packaging, wrapper, migration, e2e smoke를 강제한다.

위험한 점:

- "오케스트레이터"라는 이름은 쉽게 세 번째 엔진처럼 오해된다.
- 긴 자동화가 편해질수록 사용자는 report를 proof로, handoff를 approval로 착각할 수 있다.
- 품질/효율/보안 harness가 아직 전략적으로 한 문서에 묶여 있지 않다.

고쳐야 할 문장:

- "ORRO verifies the workflow" 금지. "ORRO exposes verification checkpoints"로 바꾼다.
- "ORRO proves the run is safe" 금지. "Depone proofcheck evaluates evidence emitted by witnessd"로 바꾼다.
- "The report proves completion" 금지. "report is not proof"로 바꾼다.

새 doctrine:

- Verified acceleration, not blind automation.
- handoff is not approval.
- report is not proof.
- long automation is checkpoint expansion, not trust expansion.
- Humans retain judgment.

## 2. 철학 적합성 점수

현재 점수: 8.2 / 10.

점수를 높게 주는 이유:

- 제품 경계가 명확하다. ORRO는 surface이고 Depone/witnessd는 engine이다.
- artifact 의미 분리가 문서와 계약 검사에 이미 들어가 있다.
- packaging과 command migration이 plan-only / future wave로 제한되어 있다.

감점 이유:

- quality rubric, efficiency metric, replay/regression corpus, prompt-injection threat model이 아직 별도 스펙과 harness로 고정되지 않았다.
- 장시간 자동화의 maturity ladder가 아직 제품 의사결정 기준으로 명문화되지 않았다.
- 보안 신뢰 모델이 "하지 말아야 할 것" 중심이고, 공격 시나리오별 검증 자산은 부족하다.

목표 점수:

- v0.1 전 9.0: 품질/효율/보안 harness 계획과 최소 fixtures가 존재한다.
- v0.2 전 9.5: replay corpus, injection corpus, regression corpus, long-run checkpoints가 CI에 연결된다.

## 3. 가장 잘한 점

첫째, ORRO는 자신이 engine이 아니라는 사실을 반복해서 말한다. 이 반복은 중복이 아니라 안전장치다. 자동화 제품은 경계가 흐려지는 순간 "모델이 스스로 실행하고 스스로 승인하는" 구조로 미끄러진다.

둘째, artifact의 의미를 낮게 잡는다. handoff is not approval. report is not proof. Engine-lock은 distribution metadata이지 verifier truth가 아니다. 이 낮은 의미 부여는 제품을 약하게 만드는 것이 아니라, 신뢰 모델을 정직하게 만든다.

셋째, 사용자 표면을 하나로 만들되 engine을 병합하지 않는다. ORRO는 설치, 문서, command migration, wrapper, report를 다루지만, proofrun/proofcheck/runtime semantics는 witnessd와 Depone에 남긴다.

넷째, CI가 제품 경계를 검사한다. 문서만 좋은 상태가 아니라, repo shape와 forbidden implementation-looking files를 검사한다는 점이 중요하다.

## 4. 가장 위험한 점

가장 큰 위험은 ORRO가 "편한 자동화"로 보이는 순간 "검증된 자동화"라는 차이를 잃는 것이다. 특히 긴 자동화에서는 사용자가 중간 checkpoint를 보지 않고 최종 report만 읽으려 한다.

위험한 혼동:

- proofrun 성공 = proofcheck 통과가 아니다.
- handoff 생성 = merge approval이 아니다.
- report 생성 = evidence proof가 아니다.
- engine-lock 최신화 = assurance 상승이 아니다.
- 긴 run 완주 = 신뢰 확장이 아니다.

보안 위험:

- prompt injection이 workflow-plan이나 report 문구를 통해 approval처럼 보이게 만들 수 있다.
- secret leakage가 report/handoff에 요약되어 재배포될 수 있다.
- replayed evidence가 새 run처럼 보이면 proofcheck 의미가 훼손된다.
- regression corpus가 없으면 같은 허점이 문장만 바꿔 반복된다.

따라서 긴 자동화의 원칙은 "long automation is checkpoint expansion, not trust expansion"이어야 한다. 긴 자동화는 더 많은 단계와 더 나은 복구를 제공할 뿐, 신뢰를 자동으로 올리지 않는다.

## 5. 작은 설계 리뷰

문서 구조는 현재 방향이 좋다. README는 제품 선언, docs/README는 탐색 표면, engine-contract와 evidence-model은 의미 경계를 맡는다. 이번 스펙은 그 위에 전략 리뷰와 실행 우선순위를 얹는다.

작게 고칠 점:

- Documentation 목록에서 strategic review를 먼저 찾을 수 있어야 한다.
- contract check는 핵심 doctrine 문구가 사라지는 것을 막아야 한다.
- 모든 새 문서는 "not proof / not approval / not verifier truth" 계열 문구를 artifact별로 정확히 써야 한다.
- "approve", "prove", "verify" 동사는 주어를 엄격히 제한해야 한다. Depone만 verifier semantics를 가진다.

금지할 설계:

- ORRO repo에 proofcheck implementation 추가.
- ORRO repo에 proofrun/runtime scheduler 추가.
- ORRO report를 merge gate로 승격.
- wrapper smoke나 e2e smoke를 proof로 표현.

허용할 설계:

- ORRO repo에 docs, schemas, reports, contract checks 추가.
- harness surface와 fixture references 추가.
- Depone/witnessd가 소비할 수 있는 wrapper-level metadata 추가.
- 실패 닫힘 policy와 migration readiness criteria 추가.

## 6. 큰 방향 리뷰

ORRO의 큰 방향은 "작업을 대신 판단하는 AI"가 아니라 "판단 가능한 작업 상태를 빠르게 만든 AI workflow surface"다. 사용자는 ORRO를 통해 scout, flowplan, proofrun, proofcheck, handoff, report를 일관된 루프로 다룬다. 그러나 각 단계의 truth owner는 다르다.

책임 경계:

- ORRO: product/workflow surface, harness surface, docs, schemas, contract checks, reports.
- witnessd: execution/runtime/evidence emission.
- Depone: verifier semantics/proofcheck truth.
- Human: judgment, merge approval, release approval, risk acceptance.

큰 방향에서 가장 중요한 문장은 "Humans retain judgment"다. ORRO는 더 많은 evidence와 더 선명한 checkpoint를 제공해야 하지만, 사람의 판단을 대체한다고 말하면 안 된다.

오픈소스 전략:

- ORRO는 작은 wrapper repo로 시작하는 것이 맞다.
- engine repos를 monorepo처럼 끌어오면 contributor trust boundary가 흐려진다.
- public roadmap은 harness와 contract maturity 중심이어야 한다.
- "AI did it"이 아니라 "the workflow left checkable artifacts"를 브랜드 언어로 삼아야 한다.

## 7. 하네스 설계안

이번 foundation은 ORRO 안에 runtime harness를 만들지 않는다. `docs/assurance/`의 threat model, long-automation gate, strategic confusion corpus는 ORRO의 harness surface와 contract reference이고, `harnesses/`, executable JSON schema, prompt-injection fixture runner는 후속 PR의 P0/P1/P2 실행 항목으로 둔다.

로컬 `.omx/` 디렉터리는 agent workflow runtime state다. ORRO 제품 산출물, engine code, verifier code, runtime code가 아니며 repo에 track되면 안 된다. Repo contract checker는 untracked `.omx/`는 로컬 상태로 허용하지만 tracked `.omx` 파일은 contract violation으로 처리한다.

목표:

- ORRO는 harness surface를 정의한다.
- witnessd는 실제 실행과 evidence emission을 담당한다.
- Depone은 evidence를 검증하고 proofcheck truth를 산출한다.

권장 하네스 계층:

1. Contract harness: repo boundary, required doctrine, artifact meaning, forbidden engine code를 검사한다.
2. Replay harness: 이전 run evidence가 새 run처럼 재사용되지 않는지 검사한다.
3. Injection harness: workflow-plan, handoff, report에 주입된 approval/proof 오염 문장을 차단한다.
4. Secret harness: report/handoff가 secret-looking material을 노출하지 않는지 검사한다.
5. Long-run harness: checkpoint/resume/failure recovery가 신뢰 상승처럼 표현되지 않는지 검사한다.
6. Regression harness: 알려진 실패 문장과 artifact 혼동이 되살아나지 않는지 검사한다.

Repo별 책임:

- ORRO: harness entry docs, schemas, contract checks, report templates, readiness criteria.
- witnessd: runtime receipts, command transcripts, evidence directories, resume/checkpoint emission.
- Depone: proofcheck verdict semantics, artifact validation, forged/replayed evidence rejection.

## 8. 품질 하네스

품질 하네스는 "결과가 마음에 드는가"가 아니라 "검토 가능한 품질 신호가 남았는가"를 본다.

Quality rubric:

- Boundary fidelity: ORRO가 engine/verifier/runtime으로 말하지 않았는가.
- Evidence sufficiency: claim이 evidence path, command output, verdict에 묶여 있는가.
- Artifact humility: handoff/report/engine-lock 의미가 과장되지 않았는가.
- Failure clarity: 실패가 사용자에게 actionable하게 드러나는가.
- Regression resistance: 기존 confusion phrases가 다시 들어오지 않았는가.
- Human reviewability: 사람이 빠르게 판단할 수 있는 요약과 원본 경로가 함께 있는가.

P0 품질 체크:

- doctrine phrase contract check.
- artifact meaning table contract check.
- "approval/proof/verifier truth" 오용 phrase corpus.

P1 품질 체크:

- docs/report template lint.
- examples consistency check.
- negative examples: forged report, approval-looking handoff, proof-looking smoke result.

## 9. 효율 측정안

ORRO 효율은 "얼마나 많은 일을 자동으로 했는가"보다 "검증 가능한 상태까지 얼마나 빨리 갔는가"로 측정해야 한다.

Core metrics:

- Time to first useful checkpoint: scout/flowplan/proofrun 중 첫 검토 가능한 artifact까지 걸린 시간.
- Time to proofcheck verdict: evidence emission 이후 Depone verdict까지 걸린 시간.
- Human review compression: reviewer가 원본 evidence로 되돌아가는 데 필요한 click/path 수.
- Rework avoided: failed checkpoint가 downstream work를 막은 횟수.
- False confidence prevented: report/handoff가 proof/approval로 오해될 수 있는 문장을 차단한 횟수.
- Resume cost: 실패 후 마지막 valid checkpoint에서 재개하는 비용.

금지 metric:

- "Lines changed by AI"를 성공 metric으로 삼지 않는다.
- "Run completed"를 assurance metric으로 삼지 않는다.
- "Report generated"를 proof metric으로 삼지 않는다.

효율 doctrine:

- Faster is good only when evidence remains inspectable.
- Automation length is not trust depth.
- Reduced human effort must not remove human judgment.

## 10. 긴 자동화 maturity ladder

긴 자동화는 단계별 maturity gate가 필요하다. 핵심 원칙은 long automation is checkpoint expansion, not trust expansion.

Level 0: Manual checkpoints

- 사용자가 각 단계를 직접 실행한다.
- ORRO는 문서와 command reference만 제공한다.

Level 1: Assisted flow

- ORRO가 scout/flowplan/proofrun/proofcheck/handoff/report command surface를 연결한다.
- 각 단계는 명시적으로 호출된다.

Level 2: Checkpointed automation

- ORRO가 여러 단계를 이어 실행할 수 있지만 checkpoint마다 artifact와 stop condition을 남긴다.
- failure는 fail closed로 멈춘다.

Level 3: Resume-aware automation

- witnessd가 checkpoint/resume evidence를 남긴다.
- ORRO는 resume summary를 노출하지만 proof로 승격하지 않는다.

Level 4: Corpus-gated automation

- injection, replay, secret, regression corpus를 통과해야 긴 자동화가 허용된다.
- corpus 결과는 report에 요약되지만 report is not proof.

Level 5: Release-gated automation

- engine-lock, release manifest, compatibility matrix, e2e smoke가 함께 업데이트된다.
- 이 단계도 approval이 아니다. Humans retain judgment.

## 11. 지금 당장 해야 할 P0

P0 실행 항목:

- 이 전략 스펙을 docs에 추가한다.
- README와 docs/README에서 이 문서를 링크한다.
- repo contract check가 핵심 doctrine 문구를 검사하게 한다.
- artifact meaning table을 기준 문서로 고정한다.
- "handoff is not approval", "report is not proof" 문구를 CI로 보호한다.
- future harness directories는 만들지 않고 계획 항목으로만 둔다.

P0 anti-goals:

- ORRO verifier 구현 금지.
- ORRO runtime 구현 금지.
- 새 dependency 추가 금지.
- 새 harness directory 생성 금지.
- package publish나 command ownership 전환 금지.

## 12. v0.1 전에 해야 할 P1

P1 실행 항목:

- `docs/assurance/` 또는 동등한 문서 표면에 threat model 초안을 추가한다.
- prompt-injection, approval-confusion, report-proof-confusion fixture corpus를 추가한다.
- JSON schema로 workflow-plan/report/handoff boundary fields를 명확히 한다.
- docs/report template lint를 만든다.
- release checklist에 strategic doctrine check를 추가한다.
- SECURITY.md와 CONTRIBUTING.md를 추가해 disclosure와 contribution boundary를 명확히 한다.

P1 acceptance:

- injection corpus가 최소 5개 negative case를 가진다.
- secret-looking token redaction policy가 문서화된다.
- replayed evidence와 stale evidence의 차이가 문서화된다.
- v0.1 release note가 "not proof / not approval / not verifier truth"를 포함한다.

## 13. 장기 P2/P3

P2:

- replay harness와 long-run resume harness를 CI에 연결한다.
- artifact provenance diff viewer를 추가한다.
- failed proofcheck에서 user-facing remediation guide를 생성한다.
- engine-lock update PR에 compatibility matrix diff summary를 자동 생성한다.

P3:

- public benchmark corpus를 운영한다.
- 외부 contributor가 만든 ORRO flows를 corpus로 재현하는 방법을 제공한다.
- release maturity scorecard를 공개한다.
- product telemetry가 필요해질 경우 opt-in, privacy-preserving, no-secret 원칙으로만 설계한다.

장기적으로도 금지:

- ORRO가 Depone proofcheck truth를 대신하지 않는다.
- ORRO가 witnessd runtime evidence를 임의 생성하지 않는다.
- ORRO가 handoff/report를 approval로 승격하지 않는다.
- ORRO가 engine-lock을 assurance로 표현하지 않는다.

## 14. 문서에 넣을 철학 선언문

다음 문장은 ORRO 문서, release note, PR template, report template의 기준 언어로 사용한다.

```text
Verified acceleration, not blind automation.
Depone verifies; witnessd executes; ORRO exposes the workflow.
Humans retain judgment.
handoff is not approval.
report is not proof.
long automation is checkpoint expansion, not trust expansion.
```

Artifact meaning table:

| Artifact | Means | Does not mean |
| --- | --- | --- |
| workflow-plan | 실행 의도와 단계 구조 | proof, approval, verifier truth |
| proofrun | witnessd가 실행을 수행하고 evidence를 남긴 run | proofcheck 통과, merge approval |
| proofcheck-verdict | Depone이 evidence를 검증한 verdict | 사람이 판단을 포기해도 된다는 뜻 |
| handoff | 리뷰를 위한 패키징과 다음 행동 요약 | approval, proof, release permission |
| report | 사람이 읽기 쉬운 요약 | proof, verifier truth, approval |
| engine-lock | pinned engine pair와 distribution metadata | assurance 상승, evidence proof |
| release-manifest | release candidate metadata와 validated engine pair 기록 | package publish, proof, approval |

문서 작성 규칙:

- artifact 의미는 "Means"보다 "Does not mean"을 더 엄격히 쓴다.
- proof/approval/verifier truth는 자동으로 승격되지 않는다.
- ORRO의 좋은 UX는 신뢰 경계를 숨기지 않고 더 잘 보이게 해야 한다.

## 15. 최종 판단

ORRO의 방향은 맞다. 가장 중요한 선택은 engine을 합치지 않고 surface를 강화하는 것이다. 제품은 더 편해져야 하지만, 신뢰 모델은 더 엄격해져야 한다.

최종 판단:

- Keep ORRO as workflow surface, harness surface, docs, schemas, contract checks, and reports.
- Keep witnessd as execution/runtime/evidence emission.
- Keep Depone as verifier semantics/proofcheck truth.
- Keep humans as judgment holders.

이 전략의 성공 기준은 자동화가 길어지는 것이 아니라, 긴 자동화가 더 많은 검토 지점과 더 낮은 오해 가능성을 남기는 것이다. ORRO가 지켜야 할 문장은 마지막까지 같다.

```text
Verified acceleration, not blind automation.
Depone verifies; witnessd executes; ORRO exposes the workflow.
Humans retain judgment.
handoff is not approval.
report is not proof.
long automation is checkpoint expansion, not trust expansion.
```
