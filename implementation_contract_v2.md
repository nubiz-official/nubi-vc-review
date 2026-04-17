# NuBI VC Review v2 — Implementation Contract

**대상**: Claude Code (AI 개발 에이전트)
**목적**: Schema 설계를 현재 프로젝트 규칙에 맞게 구현
**방식**: 요구사항 명세서 (코드 지시가 아닌 계약)

---

## 0. 구현 목표

이번 구현은 새 아키텍처 설계가 아니라, **기존 nubi-vc-review 위에 안정적인 분석/검증/저장 구조를 얹는 것**이다.

목표 산출물:
- ✅ 입력 → 내부 분석 → 최종 보고서의 3층 객체 구조
- ✅ draft → validated → reviewed → published 상태 전이
- ✅ metadata + audit_trail 저장
- ✅ 리센스 샘플 1건 end-to-end 생성 가능
- ✅ analyzer / validator / reporter 역할 분리

---

## 1. 구현 원칙

### 1.1 Claude Code의 역할

다음만 수행한다:

1. CLAUDE.md와 현재 repo 구조 읽기
2. schema_design.md 기준에 맞게 코드 구현
3. 모듈 분리: input_parser, analyzer, validator, reporter, persistence
4. 기존 streamlit_app/app.py를 깨지 않고 adapter 형태로 통합
5. SQLite 또는 로컬 저장소 구현

### 1.2 금지 사항

구현하지 말 것:

- ❌ Queen / Swarm 구조
- ❌ 자가학습, SONA, EWC++, ReasoningBank
- ❌ Semantic Router
- ❌ 성능 최적화 (Flash Attention, Int8 Quantization)
- ❌ 전사 배포용 권한 체계
- ❌ 대규모 아키텍처 재작성

이 항목들은 v3+ 보류 범위이다.

---

## 2. 프로젝트 구조 이해

### 2.1 현재 상태

```
services/nubi-vc-review/
├── streamlit_app/
│   ├── app.py (현재 메인 UI, ~580줄)
│   └── .streamlit/config.toml
├── requirements.txt
├── Dockerfile
└── schema_design.md (방금 만든 설계 문서)
```

### 2.2 CLAUDE.md 제약

- 코드 파일 < 500줄 → **모듈 분리 필수**
- /services/<name>/ 구조 유지
- Dockerfile 표준 유지
- 기존 파일 편집 우선

---

## 3. 실제 구현 대상

### 3.1 반드시 구현할 것

#### A. Schema Validation (schema_design.md 기반)

```python
# 다음 3개 스키마를 JSON schema로 구현
✓ schema_input.json spec
✓ schema_analysis_internal.json spec  
✓ schema_report_final.json spec
```

#### B. Status Transition (상태 전이)

```
draft (analyzer 완료)
  ↓ [validator_flags 없음]
validated (validator 완료)
  ↓ [reviewer 승인]
reviewed (인간 검토 완료)
  ↓ [report 생성 완료]
published (최종 저장)
```

각 상태는 진입 조건 + 저장 주체 + 다음 단계를 명시해야 함.

#### C. 3역할 분리

```python
# 최소한 다음 책임이 분리되어야 함:

1. analyzer.py: Phase 1 분석 → analysis_internal 객체 생성
2. validator.py: Phase 2 검증 → validation 객체 생성  
3. reporter.py: 최종 보고서 → report_final 객체 생성
4. persistence.py: DB 저장/조회
5. schema_validator.py: JSON 유효성 검증
```

#### D. Metadata + Audit Trail

```python
# 최소 필드 (schema_design.md metadata 섹션 참조):

metadata = {
    "analysis_id": "uuid",
    "company_name": str,
    "template_type": enum,
    "model_version": str,
    "prompt_version": str,
    "source_docs": list,
    "status": enum,
    "status_history": list,  # 모든 상태 전이 기록
    "created_at": datetime,
    "updated_at": datetime,
    "reviewer": str,
    "report_version": str
}
```

#### E. SQLite 저장

```python
# 최소 테이블:
- analyses (id, company_name, template_type, status, metadata JSON)
- analysis_audit_trail (analysis_id, timestamp, action, actor)
```

### 3.2 이번 단계에서 선택 구현

- API 스펙 초안만 (실제 endpoint는 v2.1)
- 대시보드는 조회 최소 기능 (리스트, 상세보기)
- gold sample 3개 중 리센스만 full end-to-end (다른 2개는 placeholder)

---

## 4. 입력/출력 계약

### 4.1 입력 (Input Schema)

사용자가 제공해야 할 최소 정보:

```json
{
  "company": {
    "name": "string",
    "stage": "enum: [seed, preA, seriesA, ...]",
    "industry": "enum: [biotech, medtech, saas, ...]"
  },
  "analysis_request": {
    "purpose": "enum: [ipo_factor_analysis, regulatory_verification, ...]",
    "vc_opinion": "string (optional)"
  },
  "documents": [
    {
      "filename": "string",
      "filetype": "pdf|docx|txt",
      "base64_content": "string"
    }
  ]
}
```

### 4.2 내부 분석 (Analysis Internal)

Analyzer가 생성해야 할 최소 구조:

```json
{
  "phase1_analysis": {
    "scores": {
      "market": {"score": 0-10, "evidence": [...], "confidence": 0-1},
      "solution": {...},
      "team": {...},
      "scalability": {...}
    },
    "key_risks": [...],
    "red_flags": [...],
    "missing_information": [...]
  },
  "metadata_internal": {
    "status": "draft",
    "validator_flags": [...],
    "ready_for_validation": boolean
  }
}
```

### 4.3 최종 보고서 (Report Final)

Reporter가 생성해야 할 최소 구조:

```json
{
  "report_final": {
    "executive_summary": {...},
    "early_indicators": [3-5 items],
    "5stage_scorecard": {...},
    "cross_validation": {...},
    "scope_and_limitations": {...},
    "appendix": {...}
  }
}
```

---

## 5. 구현 체크리스트

### Phase 1: Foundation

- [ ] schema_validator.py 구현 (input/internal/report 유효성 검증)
- [ ] models.py (dataclass 또는 Pydantic으로 스키마 정의)
- [ ] persistence.py (SQLite 테이블 + CRUD)
- [ ] status transition 로직 (상태 규칙 검증)

### Phase 2: Core Logic

- [ ] analyzer.py (Phase 1 분석 로직)
- [ ] validator.py (Phase 2 검증 로직, validator_flags 기록)
- [ ] reporter.py (최종 보고서 생성, Markdown 출력)

### Phase 3: Integration

- [ ] 기존 app.py 수정 (최소한의 adapter 추가)
- [ ] 입력 → analyzer → validator → reporter → DB 파이프라인
- [ ] audit_trail 저장

### Phase 4: Testing

- [ ] 리센스 샘플 1건 end-to-end 테스트
- [ ] schema 유효성 검증 테스트
- [ ] status transition 테스트

---

## 6. 코드 구조 (제안, Claude가 최종 결정)

```
services/nubi-vc-review/
├── streamlit_app/
│   ├── app.py (기존 UI, 최소한의 변경)
│   └── pages/
│       ├── 1_review.py (입력 폼)
│       └── 2_results.py (결과 표시)
│
├── backend/  (또는 streamlit_app 내부)
│   ├── models.py (데이터 모델)
│   ├── schema_validator.py (JSON 검증)
│   ├── analyzer.py (Phase 1)
│   ├── validator.py (Phase 2)
│   ├── reporter.py (최종 보고서)
│   └── persistence.py (DB)
│
├── samples/
│   ├── sample_input_recens.json
│   ├── sample_analysis_internal_recens.json
│   └── sample_report_final_recens.json
│
├── requirements.txt (필요시 추가 패키지)
├── Dockerfile (변경 없음)
└── schema_design.md (설계 문서)
```

---

## 7. 리센스 샘플 Acceptance Criteria

Claude Code는 리센스 샘플 1건에 대해 아래를 만족해야 한다:

### 입력
```
회사: 리센스메디컬
목적: ipo_factor_analysis
문서: [IR deck, 기술 문서 등]
```

### 출력 (내부 분석)
```
Phase 1 점수 (각 0-10):
- market: ~8 (반복매출+플랫폼 확장 기반)
- solution: ~8 (규제 가능한 기술)
- team: ~7 (도메인 경험)
- scalability: ~7 (확장 경로 명확)
- overall: ~7.5 (Grade B)

Early Indicators (3개):
- 원천기술 제어 가능성
- 규제 실행 조직 선배치
- 기기+디스포저블 설계

5단계 점수:
- 원천기술통제: 8
- 규제통제: 8
- 플랫폼확장: 7
- 반복매출: 8
- RWW개입: 7

Risks / Red Flags:
- FDA 적응증 범위 제한
- non-inferiority 한계
- 경쟁사 기술 동향
```

### 출력 (최종 보고서)
```
Executive Summary: ~500자
Early Indicators: 위 3개 명시
5Stage Scorecard: 위 점수 및 설명
Cross Validation: 유사 기업 2-3개
Scope & Limitation: 부재한 재무제표, 시장 조사 등
Appendix: "Reimbursement path 추가 검증 필요" 등
```

### 저장
```
status: draft → validated → reviewed → published
metadata: 모두 저장됨
audit_trail: 모든 상태 전이 기록됨
```

---

## 8. 최종 체크리스트 (구현 완료 조건)

모두 만족할 때 이번 단계 완료:

- [ ] schema_input / schema_analysis_internal / schema_report_final이 JSON schema로 정의됨
- [ ] 4가지 상태 전이가 코드에 구현되고 테스트됨
- [ ] 리센스 샘플 1건이 input → internal → final로 변환 가능
- [ ] 최종 보고서가 Markdown 형태로 생성됨
- [ ] metadata + audit_trail이 DB에 저장됨
- [ ] 기존 streamlit_app/app.py는 깨지지 않음
- [ ] 변경 파일 목록이 명확히 보고됨

---

## 9. Claude Code에 대한 최종 지시

### Step 1: 현재 상황 파악
1. CLAUDE.md를 읽고 프로젝트 규칙 이해
2. schema_design.md를 읽고 설계 요구사항 이해
3. 이 문서와 충돌하는 부분이 있는지 확인

### Step 2: 최소 변경 원칙
- **새 아키텍처를 강제로 밀어 넣지 말 것**
- **기존 app.py를 깨지 말 것**
- **모듈 분리는 adapter 형태로 (backend/ 디렉터리 추가)**

### Step 3: 구현 순서
1. models.py (데이터 모델 정의)
2. schema_validator.py (유효성 검증)
3. persistence.py (DB 저장)
4. analyzer.py / validator.py / reporter.py (분석 로직)
5. app.py 수정 (최소한의 통합)
6. 리센스 샘플 1건 end-to-end 테스트

### Step 4: 완료 보고

구현 후 다음 3가지를 반드시 보고:

1. **변경 파일 목록**
   ```
   신규: backend/models.py, backend/schema_validator.py, ...
   수정: streamlit_app/app.py (몇 줄)
   ```

2. **상태 전이 구현 방식**
   ```
   draft 상태로 분석 저장 → validator 호출 → validated 상태 변경 → ...
   ```

3. **리센스 샘플 변환 경로**
   ```
   sample_input_recens.json 
   → analyzer.analyze() 
   → sample_analysis_internal_recens.json 
   → reporter.report() 
   → sample_report_final_recens.json
   ```

---

**이 명세서는 계약입니다. 구현할 때 이 기준을 벗어나면 안 됩니다.**
