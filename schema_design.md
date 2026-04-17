# NuBI VC Review v2 — Schema Design & Definitions

**목표**: 입력 → 내부 분석 → 최종 보고서의 완전한 구조를 json-schema 레벨로 정의

**방침**: 각 필드는 "왜 필요한가" "어떤 조건인가" "누가 채우는가" "검증 기준은"을 명시

---

## 1. STATUS ENUM + 진입 조건

```yaml
Status Transitions:

draft:
  진입조건: Analyst가 Phase 1 분석 완료
  내용: phase1_scores + phase1_analysis 작성됨
  누가: analyzer.py에서 자동 저장
  검증: JSON schema 유효성 check only
  다음단계: → validated (수동 승인)

validated:
  진입조건: Validator flags가 없거나 허용 범위 이내
  내용: phase2_validations 작성 + validator_notes 추가
  누가: validator.py에서 자동 저장
  조건: 
    - red_flags 개수 ≤ 3개
    - confidence_score ≥ 0.7
    - missing_info 항목이 "critical" 미만
  다음단계: → reviewed (인간 검토)

reviewed:
  진입조건: 인간 검토자가 검토 완료 및 승인
  내용: reviewer_name + review_notes + sign_off_date 추가
  누가: 인간 (QA/분석가)
  검증: reviewer가 실제 로그인한 사용자여야 함
  다음단계: → published (보고서 생성)

published:
  진입조건: Reporter가 최종 보고서 객체 생성 및 저장 완료
  내용: schema_report_final이 완전히 생성됨
  누가: reporter.py에서 자동 저장
  검증: 모든 필수 섹션 포함 (Executive Summary ~ Appendix)
  의미: 조직 내 공식 문서로 배포 가능
```

---

## 2. METADATA SCHEMA (모든 상태에서 필수)

```json
{
  "metadata": {
    "analysis_id": "uuid (primary key)",
    "company_name": "string (required)",
    "analysis_date": "ISO8601 datetime (auto)",
    "template_type": "enum: [ipo_factor_analysis, regulatory_verification, comparative_case_study]",
    "model_version": "semantic version (e.g., claude-sonnet-4-20250514)",
    "prompt_version": "v1.0.0 of prompt templates",
    "source_docs": [
      {
        "filename": "string",
        "filetype": "pdf|docx|txt",
        "size_bytes": "number",
        "extracted_text_length": "number",
        "confidence": "0.0-1.0 (OCR/parsing quality)",
        "upload_datetime": "ISO8601"
      }
    ],
    "status": "enum: [draft, validated, reviewed, published]",
    "status_history": [
      {
        "status": "draft",
        "timestamp": "ISO8601",
        "actor": "system:analyzer"
      },
      {
        "status": "validated",
        "timestamp": "ISO8601",
        "actor": "system:validator",
        "notes": "all flags within acceptable range"
      }
    ],
    "created_at": "ISO8601 (analyzer started)",
    "updated_at": "ISO8601 (latest change)",
    "created_by": "system:analyzer | user:id",
    "reviewer": "user:id (if reviewed)",
    "review_timestamp": "ISO8601 (if reviewed)",
    "gold_sample_match": "optional reference to baseline (e.g., 'recens_medical')",
    "tags": ["biotech", "seed", "regulatory_risk", "ipo_candidate"],
    "version": "2.0"
  }
}
```

**필드별 설명**:
- `analysis_id`: 추적성을 위해 UUID. 이후 API/대시보드에서 reference key.
- `template_type`: 어떤 분석 목적인지 명시. 같은 biotech도 분석 유형에 따라 출력 구조 다름.
- `model_version`: 나중에 모델 변경 시 이전 분석과 비교 가능.
- `prompt_version`: 프롬프트 업데이트 시 어떤 버전의 프롬프트로 분석됐는지 추적.
- `source_docs`: 입력 문서의 품질 지표 (OCR confidence 등) 저장. 나중에 "이 문서의 quality가 낮아서 결과를 신뢰할 수 없다" 판단 가능.
- `status_history`: 상태 전환을 시간순으로 기록. 감사 추적(audit trail).
- `gold_sample_match`: "이 분석이 gold sample과 얼마나 유사한가"를 나중에 추적. 자가학습 없이 패턴 라이브러리 강화.

---

## 3. SCHEMA INPUT (사용자/시스템이 제공)

```json
{
  "input": {
    "company": {
      "name": "string (required, max 200 chars)",
      "industry": "enum: [biotech, medtech, saas, ai_ml, hardware, fintech]",
      "stage": "enum: [seed, preA, seriesA, seriesB, seriesC, seriesD_plus]",
      "founded_year": "integer (optional, 1900-2100)",
      "hq_country": "string (2-char ISO code, e.g., 'KR')",
      "description": "string (optional, max 500 chars)"
    },
    "analysis_request": {
      "purpose": "enum: [ipo_factor_analysis, regulatory_verification, comparative_case_study, general_investment_review]",
      "priority": "enum: [low, medium, high] (affects output depth)",
      "context": "string (optional, what decision/timeline, max 1000 chars)",
      "vc_opinion": "string (optional, max 5000 chars, for Phase 2)",
      "vc_firm": "string (optional, e.g., 'Bluepoint Partners')",
      "previous_analysis_id": "uuid (optional, if building on prior work)"
    },
    "documents": [
      {
        "file_id": "string (unique within session)",
        "filename": "string",
        "filetype": "enum: [pdf, docx, txt]",
        "size_bytes": "number",
        "base64_content": "string (base64 encoded)",
        "doc_type": "enum: [ir_deck, pitch_deck, financials, regulatory_filing, market_research, other]",
        "confidence": "float 0.0-1.0 (user assessment of reliability)"
      }
    ],
    "quality_flags": {
      "external_validation_done": "boolean (did user verify with other sources?)",
      "missing_key_info": ["string array, e.g., ['founder_background', 'financial_projections']]",
      "red_flags_already_identified": ["string array, e.g., ['founder_disputes', 'regulatory_action']]"
    }
  }
}
```

**검증 규칙**:
- `company.name` required, trim whitespace
- `analysis_request.purpose` must match template_type
- `documents` array: min 1, max 10 files
- `documents[].filetype` must be supported
- `documents[].base64_content` must be valid base64
- `quality_flags.confidence` 각 문서별 신뢰도 ∈ [0.0, 1.0]

---

## 4. SCHEMA ANALYSIS INTERNAL (Analyzer Output)

```json
{
  "phase1_analysis": {
    "timestamp_started": "ISO8601",
    "timestamp_completed": "ISO8601",
    "model_used": "string (e.g., claude-sonnet-4-20250514)",
    "prompt_version": "string (v1.0.0)",
    
    "scores": {
      "stage_1_원천기술통제": {
        "score": "float 0.0-10.0",
        "rubric_level": "enum: [exceptional, strong, adequate, weak, critical]",
        "evidence": ["string array, min 1 item, max 500 chars each"],
        "counterevidence": ["string array, things that weaken this score"],
        "confidence": "float 0.0-1.0"
      },
      "stage_2_규제통제": { "same structure as stage_1" },
      "stage_3_플랫폼확장": { "same structure as stage_1" },
      "stage_4_반복매출": { "same structure as stage_1" },
      "stage_5_RWW개입": { "same structure as stage_1" },
      "overall": {
        "score": "float 0.0-10.0",
        "grade": "enum: [A, A-, B+, B, B-, C+, C, D, F]",
        "grade_definition": {
          "A": "score ≥ 9.0, exceptional investment case",
          "A-": "score 8.5-8.9, strong investment thesis",
          "B+": "score 8.0-8.4, strong with caveats",
          "B": "score 7.5-7.9, conditional investment, IPO-quality structure",
          "B-": "score 7.0-7.4, conditional investment",
          "C+": "score 6.5-6.9, requires significant validation",
          "C": "score 6.0-6.4, requires further validation",
          "D": "score 5.0-5.9, significant concerns",
          "F": "score < 5.0, not suitable"
        },
        "reasoning": "string max 1000 chars"
      }
    },
    
    "narrative_analysis": {
      "stage_1_원천기술통제": "string (2-3 paragraphs, 500-1000 chars, describes root technology moat and IP strength)",
      "stage_2_규제통제": "string (2-3 paragraphs, 500-1000 chars, describes regulatory pathway and approval probability)",
      "stage_3_플랫폼확장": "string (2-3 paragraphs, 500-1000 chars, describes platform scalability and market reach)",
      "stage_4_반복매출": "string (2-3 paragraphs, 500-1000 chars, describes recurring revenue model and retention)",
      "stage_5_RWW개입": "string (2-3 paragraphs, 500-1000 chars, describes team execution capability and domain expertise)"
    },
    
    "investment_thesis": "string (executive pitch, max 1500 chars)",
    
    "key_risks": [
      {
        "risk_type": "enum: [market, technical, regulatory, team, financial, operational]",
        "description": "string max 500 chars",
        "severity": "enum: [critical, high, medium, low]",
        "mitigation_required": "boolean"
      }
    ],
    
    "red_flags": [
      {
        "flag": "string (what was concerning)",
        "severity": "enum: [critical, high, medium, low]",
        "evidence": "string (why this matters)",
        "verification_needed": "boolean (can be verified with more info?)"
      }
    ],
    
    "missing_information": [
      {
        "category": "string (e.g., founder_background, market_validation, ip_position)",
        "criticality": "enum: [critical, important, nice_to_have]",
        "impact": "string (why this matters, max 300 chars)"
      }
    ],
    
    "data_quality_assessment": {
      "source_reliability": "enum: [high (official docs), medium (company materials), low (secondary sources)]",
      "completeness": "float 0.0-1.0 (how much of ideal info is available?)",
      "recency": "string (e.g., '2024 data', 'outdated 2021 projections')",
      "concerns": ["string array"]
    }
  },
  
  "phase2_validations": {
    "vc_opinion_summary": "string (paraphrase of VC claim)",
    "claims_extracted": [
      {
        "claim_id": "string (e.g., 'claim_1')",
        "claim_text": "string (the actual VC statement)",
        "underlying_assumption": "string (what does this rely on?)"
      }
    ],
    "claim_assessment": [
      {
        "claim_id": "string",
        "verdict": "enum: [supported, partially_supported, contradicted, insufficient_evidence]",
        "phase1_evidence": "string (cite from Phase 1, max 500 chars)",
        "reasoning": "string (why this verdict, max 500 chars)",
        "confidence": "float 0.0-1.0"
      }
    ],
    "final_recommendation": "string (2-3 sentences, max 500 chars)",
    "investment_decision": "enum: [strong_support, support, neutral, caution, strong_caution]"
  },
  
  "metadata_internal": {
    "status": "draft",
    "validator_flags": [
      {
        "flag_type": "enum: [missing_field, low_confidence, inconsistency, critical_gap]",
        "description": "string",
        "must_resolve": "boolean"
      }
    ],
    "analyzer_notes": "string (optional, internal notes)",
    "ready_for_validation": "boolean (all required fields present and confident?)"
  }
}
```

**필드별 설명**:
- `scores.*.evidence`: 최소 3개의 구체적 근거. "좋다"가 아니라 "DAM 기술이 이미 FDA 승인 3건, 선행 특허 12건" 같은 구체성.
- `scores.*.counterevidence`: 반대 증거도 명시. 균형잡힌 분석.
- `scores.*.confidence`: 0.95 → "확실", 0.6 → "부분적 근거만", 0.3 → "추측 수준"
- `key_risks / red_flags / missing_information`: 세 가지는 다름.
  - Key_risks: 알려진 위험 (founder 부재 등)
  - Red_flags: 뭔가 이상한데 확실하지 않은 신호
  - Missing_information: 없는 정보 (재무제표 미제공 등)
- `data_quality_assessment`: 입력 자료의 신뢰도. "이 분석은 공식 재무제표 기반이 아니라 회사 자체 추정"을 명시.
- `validator_flags`: Validator가 이 draft를 검토할 때 체크 포인트.

---

## 5. SCHEMA REPORT FINAL (Reporter Output)

```json
{
  "report_final": {
    "report_id": "uuid (different from analysis_id)",
    "analysis_id": "uuid (link back)",
    "generated_at": "ISO8601",
    "report_version": "v2.0",
    
    "executive_summary": {
      "headline": "string (1 sentence verdict, max 200 chars)",
      "investment_case": "string (2-3 paragraphs, max 1500 chars)",
      "key_recommendation": "enum: [strong_buy, buy, hold, avoid, strong_avoid]",
      "risk_level": "enum: [low, medium, high, critical]"
    },
    
    "early_indicators": {
      "indicators": [
        {
          "indicator_name": "string (e.g., 'Repeat customer rate')",
          "current_status": "string (what is it now?)",
          "target_status": "string (what should it be?)",
          "timeline": "string (when should this be achieved?)",
          "criticality": "enum: [must_have, should_have, nice_to_have]"
        }
      ],
      "count": "integer (typically 3-5)"
    },
    
    "5stage_scorecard": {
      "stage_1_원천기술통제": {
        "score": "float 0.0-10.0",
        "description": "string (what is being scored)",
        "supporting_factors": ["string array"],
        "risks": ["string array"]
      },
      "stage_2_규제통제": { "same structure" },
      "stage_3_플랫폼확장": { "same structure" },
      "stage_4_반복매출": { "same structure" },
      "stage_5_RWW개입": { "same structure" },
      "overall_score": "float 0.0-10.0 (weighted average)",
      "weightings": {
        "stage_1": 0.25,
        "stage_2": 0.25,
        "stage_3": 0.15,
        "stage_4": 0.20,
        "stage_5": 0.15
      }
    },
    
    "cross_validation": {
      "comparable_companies": [
        {
          "company": "string",
          "similarity": "string (in what way?)",
          "outcome": "string (what happened to them?)",
          "relevance_to_subject": "string (what does this tell us?)"
        }
      ],
      "validation_summary": "string (do Phase 1 & Phase 2 agree? max 500 chars)"
    },
    
    "scope_and_limitations": {
      "data_sources": "string (what was analyzed? what was not?)",
      "analysis_date": "date (when was this done?)",
      "market_snapshot": "string (was market checked? snapshot date?)",
      "external_assumptions": ["string array (what external facts did we assume?)"],
      "not_in_scope": ["string array (what was explicitly not reviewed?)"]
    },
    
    "appendix": {
      "section_required": "boolean (is appendix needed?)",
      "missing_info_to_add": [
        {
          "category": "string (reimbursement, unit_economics, valuation_bridge, etc.)",
          "description": "string",
          "why_important": "string (how would this change the recommendation?)"
        }
      ],
      "external_research_needed": ["string array (what should be researched externally?)"],
      "follow_up_questions": ["string array (what to ask founder?)"]
    },
    
    "document_metadata": {
      "document_title": "string",
      "generated_date": "ISO8601",
      "generated_by": "system:reporter",
      "markdown_version": "string (for export)",
      "audit_trail": [
        {
          "timestamp": "ISO8601",
          "action": "string (created, validated, reviewed, published)",
          "actor": "string"
        }
      ]
    }
  }
}
```

**핵심 섹션 설명**:
- **Executive Summary**: C-level이 30초에 이해하는 결론
- **Early Indicators**: 이 회사가 성공하려면 앞으로 12개월 내에 이것들이 나타나야 한다 (검증 체크리스트)
- **5Stage Scorecard**: 누비즈의 고유 프레임. 모든 분석은 이걸로 수렴.
- **Cross Validation**: 비슷한 회사들이 어떻게 됐나? 이 회사는 어떨 것 같나?
- **Scope & Limitation**: 분석의 한계를 명시. "이 분석은 공식 재무제표 없이 진행됐으므로 이 점 유의" 등.
- **Appendix**: 부족한 정보 목록. "Reimbursement path가 명확하지 않아서 이 부분만으로는 권고 불가" 같은 조건부 명시.

---

## 6. GOLD SAMPLE 선정 조건

| 항목 | 성공형 (규제 강함) | 미완성형 (규제 약함) | 비규제형 (소프트웨어) |
|------|----------------|------------|---------|
| **모델** | 리센스메디컬 | TBD | TBD |
| **규제 요구** | High (FDA, QMS) | Medium (부분) | Low |
| **반복매출** | 강함 (소모품) | 약함 | 강함 (SaaS) |
| **Platform 확장** | 중간 | 제한적 | 높음 |
| **RWW 개입 가능성** | 높음 | 낮음 | 중간 |
| **분석 구조 다양성** | Early Indicators 명확 | 공백 식별 | 다른 KPI |
| **선정 이유** | 성공 케이스, 이미 구조화됨 | 실패 패턴 학습, Appendix 확장 | 템플릿 일반화 검증 |

**선정 기준**:
1. 각 샘플은 다른 문제 구조를 드러내야 함.
2. 리센스: "규제형 biotech의 성공 경로"
3. 미완성: "규제 또는 상업화 미흡으로 인한 평가 공백" (Early Indicators 부재 같은)
4. 비규제형: "같은 5-stage 프레임이 Software에도 적용되는가?" 검증

---

## 7. 검증 기준 (QA Checklist)

### Input Validation
- [ ] company.name: 200자 이하, 공백 정리
- [ ] documents: 최소 1개, 최대 10개
- [ ] documents[].filetype: pdf/docx/txt만
- [ ] documents[].base64_content: 유효한 base64
- [ ] analysis_request.purpose: valid enum
- [ ] quality_flags.confidence: 0.0-1.0 범위

### Phase1 Analysis Validation
- [ ] scores.*.score: 0-10 범위, float
- [ ] scores.*.evidence: 최소 3개, 각각 50-500자
- [ ] scores.*.confidence: 0.0-1.0
- [ ] overall.grade: A/B/C/D 중 하나
- [ ] key_risks: 최소 1개, 최대 5개
- [ ] red_flags: 최소 0개, 최대 3개
- [ ] missing_information: 각 criticality 명시

### Phase2 Validation
- [ ] claims_extracted: VC 의견과 비교
- [ ] claim_assessment: 모든 claim에 대해 verdict 있음
- [ ] final_recommendation: 명확한 판단 (support/caution/etc)

### Report Final Validation
- [ ] executive_summary.headline: 200자 이하
- [ ] early_indicators: 3-5개
- [ ] 5stage_scorecard: 모든 5개 stage 채워짐
- [ ] cross_validation: 최소 2개 comparable company
- [ ] scope_and_limitations: missing info 명시
- [ ] audit_trail: 모든 상태 전환 기록

### Status Transition Validation
- [ ] draft → validated: validator_flags < 허용 수준
- [ ] validated → reviewed: reviewer_name 입력
- [ ] reviewed → published: 최종 보고서 객체 생성

---

## Next Steps

1. **이 스키마에 기반해서 gold sample 3개 정의** (선정 조건표 활용)
2. **schema_input / internal / report_final의 실제 JSON 예시 작성** (리센스 기반)
3. **프롬프트 템플릿 작성** (각 목적별)
4. **SQLite table 정의** (schema 매핑)
5. **Validator.py + Reporter.py 코드 스켈레톤**

