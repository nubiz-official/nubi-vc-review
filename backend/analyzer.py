"""Phase 1 Analyzer - Claude API-based analysis engine."""
from datetime import datetime
from typing import Dict, Any, List
import json
import os
from anthropic import Anthropic
from .models import Metadata


class Analyzer:
    """Claude API-powered Phase 1 analysis engine."""

    def __init__(self, model_version: str = "claude-opus-4-7", prompt_version: str = "v2.0.0"):
        """Initialize analyzer with Anthropic client. Model is fixed to claude-opus-4-7."""
        self.model_version = "claude-opus-4-7"
        self.prompt_version = prompt_version
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = Anthropic()

    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze company using Claude API.
        Returns structured analysis_internal with phase1_analysis.
        """
        company_name = input_data.get("company", {}).get("name", "Unknown")
        template_type = input_data.get("analysis_request", {}).get("purpose", "general_investment_review")

        # Create metadata
        metadata = Metadata(
            company_name=company_name,
            template_type=template_type,
            model_version=self.model_version,
            prompt_version=self.prompt_version
        )

        # Record source documents
        docs = input_data.get("documents", [])
        metadata.source_docs = [
            {
                "filename": doc.get("filename", "unknown"),
                "filetype": doc.get("filetype", "txt"),
                "size_bytes": doc.get("size_bytes", 0),
                "extracted_text_length": len(doc.get("text", "")),
                "confidence": doc.get("confidence", 0.95),
                "upload_datetime": datetime.utcnow().isoformat()
            }
            for doc in docs
        ]

        metadata.status_history = [
            {
                "status": "analyzing",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "system:analyzer",
                "notes": "Claude API analysis in progress"
            }
        ]

        # Get Claude analysis
        timestamp_started = datetime.utcnow().isoformat()
        claude_analysis = self._run_claude_analysis(input_data)
        timestamp_completed = datetime.utcnow().isoformat()

        # Build phase1_analysis from Claude output (pass-through Claude JSON fields)
        phase1 = {
            "timestamp_started": timestamp_started,
            "timestamp_completed": timestamp_completed,
            "model_used": self.model_version,
            "prompt_version": self.prompt_version,
            "scores": self._extract_scores_from_claude(claude_analysis),
            "narrative_analysis": self._extract_narratives_from_claude(claude_analysis),
            "headline": claude_analysis.get("headline", ""),
            "investment_case": claude_analysis.get("investment_case", claude_analysis.get("investment_thesis", "")),
            "investment_thesis": claude_analysis.get("investment_thesis", ""),
            "investment_decision": claude_analysis.get("investment_decision", claude_analysis.get("recommendation", "")),
            "risk_level": claude_analysis.get("risk_level", ""),
            "key_risks": claude_analysis.get("risks", []),
            "red_flags": self._extract_red_flags(claude_analysis),
            "missing_information": claude_analysis.get("missing_information", []),
            "data_quality_assessment": {
                "overall_confidence": sum(d.get("confidence", 0.9) for d in docs) / max(len(docs), 1),
                "doc_count": len(docs),
                "assessment": "High quality source materials provided"
            },
            "factor_discovery": claude_analysis.get("factor_discovery", {}),
            "early_indicators": claude_analysis.get("early_indicators", []),
            "cross_validation": claude_analysis.get("cross_validation", []),
            "momentum_entry_timeline": claude_analysis.get("momentum_entry_timeline", {}),
            "rww_synergy_scenarios": claude_analysis.get("rww_synergy_scenarios", []),
            "nubiz_laws": claude_analysis.get("nubiz_laws", []),
            "analysis_reference_point": claude_analysis.get("analysis_reference_point", {}),
            "numeric_reference_table": claude_analysis.get("numeric_reference_table", {}),
            "investor_concern_validation": claude_analysis.get("investor_concern_validation", []),
            "diligence_trigger_checklist": claude_analysis.get("diligence_trigger_checklist", []),
            "nubiz_fit_leverage": claude_analysis.get("nubiz_fit_leverage", []),
            "executive_verdict": claude_analysis.get("executive_verdict", {}),
            "narrative_reframing": claude_analysis.get("narrative_reframing", {}),
            "deal_structuring_suggestions": claude_analysis.get("deal_structuring_suggestions", []),
            "problem_cost_severity": claude_analysis.get("problem_cost_severity", {})
        }

        metadata.status_history.append({
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "actor": "system:analyzer",
            "notes": "Analysis completed successfully"
        })

        return {
            "phase1_analysis": phase1,
            "metadata": metadata.to_dict()
        }

    def _run_claude_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Claude API with analysis prompt."""
        company_name = input_data.get("company", {}).get("name", "Company")
        docs = input_data.get("documents", [])
        doc_text = "\n\n".join([doc.get("text", "") for doc in docs])

        system_prompt = """너는 NuBIZ VC Review 엔진이다.
"No Fake, Only Real" 원칙으로 분석한다.
숫자, 규제 명칭, 비즈니스 로직만 사용한다."""

        user_prompt = f"""다음은 {company_name}의 IR 자료 전문이다:

[IR 자료]
{doc_text[:8000]}

다음 JSON 스키마를 정확히 따라 응답하라. 모든 evidence 필드는 반드시 문자열 배열(list of strings)이다.
모든 근거는 IR 자료 원문에서 인용하거나, web_search로 검증된 사실만 기술하라.

```json
{{
  "analysis_reference_point": {{
    "stance": "<둘 중 하나 선택: 'post_approval_reverse' (승인/IPO 후 역산 분석) 또는 'under_review_forward' (심사·성장 중 전망 분석)>",
    "cutoff_date": "<IR 자료 기준 시점 (예: 2024.10 FDA De Novo 승인 시점)>",
    "basis": "<판단 근거: IR 자료 내 가장 최신 이벤트 (예: 2024.10 FDA 승인 확정) 또는 심사 진행 상태 (예: 2024.03 De Novo 제출, 심사 중)>",
    "disclosure": "<독자 경고 1문장. 예: '본 보고서는 FDA 승인 확정 이후의 역산 관점이며, 모든 시점·수치는 승인 확정된 사실에 기반함.' 또는 '본 보고서는 심사 진행 중 상태의 전망 관점이며, 최종 결과는 확정되지 않았음.'>"
  }},

  "numeric_reference_table": {{
    "revenue_latest": {{"value": "<IR에서 인용한 최신 매출 (예: 2023년 매출 58억)>", "source": "<IR 페이지/섹션 예: 2024 IR p.12 매출실적>", "note": "<확정/예상/[추정] 라벨>"}},
    "revenue_forecast": {{"value": "<IR 예상 매출 (예: 2024E 150억)>", "source": "<IR 페이지>", "note": "<예상치임을 명시>"}},
    "cumulative_investment": {{"value": "<누적 투자금액 (예: 500억)>", "source": "<IR 페이지>", "note": "<확정/[추정]>"}},
    "patent_count": {{"value": "<특허 건수 — 등록/출원 구분. 예: 등록 37건 / 출원 120건>", "source": "<IR 페이지>", "note": "<등록·출원 구분 명시>"}},
    "countries_coverage": {{"value": "<판매/인증 국가 수 (예: 인증 20개국, 판매 12개국)>", "source": "<IR 페이지>", "note": "<인증/판매 구분>"}},
    "clinical_cases": {{"value": "<임상/시술 누적 케이스 (예: 미국 1,000+ 케이스)>", "source": "<IR 페이지>", "note": "<IR 근거>"}},
    "overseas_revenue_ratio": {{"value": "<해외 매출 비중 % (예: 90%)>", "source": "<IR 페이지>", "note": "<확정/[추정]>"}}
  }},
  "// numeric_reference_table 규칙": "이 테이블은 보고서 전체의 숫자 원천(Single Source of Truth)이다. Executive Summary, investment_case, stage evidence, risks, factor_discovery, momentum_entry_timeline, cross_validation 등 다른 모든 섹션에서 이 숫자들을 인용할 때 일관된 값만 사용하라. IR에 근거 없는 수치는 이 테이블에 포함하지 말고 '[IR 미기재]'로 표기. 동일 지표가 섹션마다 다른 값으로 나오지 않도록 엄격히 일치시켜라.",
  "headline": "<한 줄 투자 판단. 톤은 보수적으로. '직전 단계/확정/IPO 임박' 같은 단정 금지. 권장 패턴: '<회사명>: <핵심 논리>로 조건부 <판단>' 예: '리센스메디컬: De Novo + razor-blade 구조로 IPO 전환 가능성 높은 조건부 Buy'>",
  "executive_verdict": {{
    "one_line_verdict": "<임원용 한 줄 의사결정 결론. 예: '드랍 논리 대부분 부정 — 조건부 투자 권고' / '보류 논리 타당 — 추가 실사 후 재검토' / '투자 논리 보강 필요 — 현 단계 단독 투자 부적합'>",
    "verdict_type": "<'refute_pushback' | 'hold_valid' | 'investment_thesis_weak' | 'conditional_go' | 'clear_go' | 'clear_pass' 중 택1>",
    "key_driver": "<이 결론의 최대 동인 한 문장. 예: 'FDA De Novo 2024.10 승인 + 소모품 80% 구조'>"
  }},
  "investment_case": "<정확히 3문장으로 작성. (1) 기술 제어력 관점 (2) 반복매출 구조 관점 (3) 규제/IPO 변곡점 관점. 세부 인증·채널·특허·지분·매출 수치 등은 Numeric Reference Table과 Stage Evidence에 위임하고 여기서는 언급 금지. 문장 하나당 2줄 이내.>",
  "investment_decision": "<strong_buy|buy|hold|strong_avoid>",
  "risk_level": "<low|medium|high|critical>",
  "investment_thesis": "<핵심 강점과 약점 정리. 3~5문장.>",
  "// headline 규칙": "Headline에는 'IPO 직전', '상장 확정', '즉시 투자' 같은 단정적 단어 금지. 심사 중 전망(under_review_forward)인 경우 반드시 '조건부', '전환 가능성', '잠재력' 같은 유보적 표현을 포함하라.",
  "// investment_case 규칙": "정확히 3문장. 각 문장은 (1) 기술 제어력, (2) 반복매출 구조, (3) 규제/IPO 변곡점 순서. 세부 숫자·인증·채널 등은 다른 섹션(Numeric Reference Table, Stage Evidence)으로 위임. 여기에는 전략적 프레임만 남기고 디테일 나열 금지.",

  "factor_discovery": {{
    "platform_evolution": "<핵심 기술의 플랫폼 확장 가능성>",
    "regulatory_pathway": "<FDA De Novo/510k/PMA/CE 등 구체 경로>",
    "recurring_revenue": "<소모품/구독 구조 설계 유무와 근거>",
    "ipo_factors": ["<2017→IPO 역산 팩터 1>", "<팩터 2>", "<팩터 3>"],
    "ipo_reverse_analysis": [
      {{"ir_expression_2017": "<IR 원문 표현 예: 'One Device, Different Disposables'>", "reverse_interpretation": "<역산 재해석 예: Razor-blade 비즈니스 모델 선언>", "ipo_linkage": "<IPO 가치 연결 예: 반복매출 구조 내재화>"}},
      {{"ir_expression_2017": "<IR 원문 표현 2>", "reverse_interpretation": "<재해석 2>", "ipo_linkage": "<IPO 연결 2>"}},
      {{"ir_expression_2017": "<IR 원문 표현 3>", "reverse_interpretation": "<재해석 3>", "ipo_linkage": "<IPO 연결 3>"}}
    ]
  }},

  "early_indicators": [
    {{"indicator_name": "원천기술 물리적 제어 가능성", "ir_evidence": "<IR 원문에서 직접 인용>", "why_signal": "<왜 이것이 IPO 시그널인가>", "formula_type": "<계산식형|범주형|배수형 중 택1 — 모든 indicator는 통일된 형식으로>", "input_variables": ["<변수1>", "<변수2>"], "calculation": "<예: 점수 = A × B × C  (계산식형) 또는 '물리 파라미터 수 / 총 변수 수' (계산식형)>", "result_type": "<숫자형(0-10)|배수형(0-5)|범주형(high/medium/low) 중 택1>", "evaluation_formula": "<input_variables/calculation/result_type을 1줄로 합친 legacy 표기. 예: '점수 = (물리 파라미터 수 / 총 변수 수) × 재현성 계수 → 0~10 숫자형'>"}},
    {{"indicator_name": "규제 실행 조직 선배치", "ir_evidence": "<IR 원문 인용>", "why_signal": "<왜 시그널인가>", "formula_type": "<계산식형|범주형|배수형>", "input_variables": ["<변수1>", "<변수2>"], "calculation": "<위와 동일한 형식 규칙>", "result_type": "<위와 동일>", "evaluation_formula": "<legacy 1줄 표기>"}},
    {{"indicator_name": "제품 아키텍처 모듈화/소모품 설계", "ir_evidence": "<IR 원문 인용>", "why_signal": "<왜 시그널인가>", "formula_type": "<계산식형|범주형|배수형>", "input_variables": ["<변수1>", "<변수2>"], "calculation": "<위와 동일한 형식 규칙>", "result_type": "<위와 동일>", "evaluation_formula": "<legacy 1줄 표기>"}}
  ],
  "// early_indicators 규칙": "3개 indicator 모두 동일한 formula_type을 사용하라 (전부 '계산식형' 또는 전부 '배수형' 또는 전부 '범주형'). 섞지 마라. input_variables는 최소 2개, calculation은 formula_type과 일치해야 한다. result_type도 formula_type과 일치. evaluation_formula는 사람이 읽기 위한 1줄 요약 (legacy 호환용).",

  "stage_1_원천기술통제": {{"score": <0-10 숫자>, "evidence": ["<근거 문장 1>", "<근거 문장 2>"], "confidence": <0-1>}},
  "stage_2_규제통제": {{"score": <0-10 숫자>, "evidence": ["<FDA 경로명 포함 근거>"], "confidence": <0-1>}},
  "stage_3_플랫폼확장": {{"score": <0-10 숫자>, "evidence": ["<적용 가능 영역 수와 근거>"], "confidence": <0-1>}},
  "stage_4_반복매출": {{"score": <0-10 숫자>, "evidence": ["<소모품 비중/구독 구조 근거>"], "confidence": <0-1>}},
  "stage_5_RWW개입": {{
    "score": <0-10 숫자>,
    "current_execution_evidence": ["<해외 매출 비중(%) — IR 원문에서 숫자 인용>", "<회사가 이미 보유한 글로벌 실행력: 진출 국가, 해외 임상, 해외 파트너십 등>", "<Advisory Board, 미국 공급 협의 등 회사의 실제 실행 근거>"],
    "rww_uplift_potential": ["<NuBIZ RWW 개입 시 규제/인허가 측면 기대 가치 증분>", "<NuBIZ RWW 개입 시 영업/채널/재구매 측면 기대 가치 증분>"],
    "evidence": ["<레거시 호환용: current_execution_evidence + rww_uplift_potential 합산 또는 대표 문장 2-3개>"],
    "confidence": <0-1>
  }},

  "cross_validation": [
    {{
      "company": "<회사명 + 티커 예: Intuitive Surgical (ISRG)>",
      "ipo_year": "<IPO 연도>",
      "regulatory_pathway": "<규제 경로명 예: FDA PMA / De Novo / 510(k) / CE>",
      "revenue_model": "<매출 구조 예: razor-blade (소모품 70%+), SaaS recurring, hardware only>",
      "market_cap_current": "<현재 시가총액 또는 인수가 예: $60B+, 인수 $3.2B>",
      "similarity_dimensions": ["<이 회사와 공유하는 성공 패턴 1 예: 반복매출 모델>", "<패턴 2 예: 규제 해자>", "<패턴 3 예: 플랫폼 확장>"],
      "key_outcome_metric": "<핵심 실적 지표 1개 예: 10%+ YoY 25년 지속 / 영업이익률 51%+>",
      "applicability_to_subject": "<이 회사에 주는 시사점 구체 기술>"
    }},
    {{
      "company": "<두 번째 비교 회사>",
      "ipo_year": "<연도>", "regulatory_pathway": "<경로>", "revenue_model": "<구조>", "market_cap_current": "<시총>",
      "similarity_dimensions": ["<공유 패턴>", "<공유 패턴>"],
      "key_outcome_metric": "<지표>",
      "applicability_to_subject": "<시사점>"
    }}
  ],
  "// cross_validation 규칙": "정확히 2~3개만 포함하라. 다음 규칙을 엄격히 준수: (1) 공개 상장사 또는 공개 인수 사례만 허용 (비상장/미상장/비공개는 제외), (2) 'A / B' 합성 entry 금지 — 한 행에 한 회사만, (3) regulatory_pathway/revenue_model/market_cap_current/ipo_year 4개 팩트가 web_search로 검증되지 않으면 아예 포함하지 말라 (품질이 수량보다 우선), (4) similarity_dimensions는 해당 회사와 실제로 공유하는 성공 패턴만 (억지 유사성 금지), (5) 검증 약한 De Novo 사례는 제외하고 ISRG/PROCEPT/InMode/Shockwave/Guardant Health 같은 검증된 peer 우선.",

  "risks": [
    {{"risk_type": "regulatory", "description": "FDA De Novo 최종 승인 미확정 여부와 적응증 범위 제한 (예: 특정 시술로만 승인) 구체 기술. IR에서 언급된 제품명/적응증 인용 필수", "severity": "high|medium|low"}},
    {{"risk_type": "clinical", "description": "non-inferiority 설계 가능성, 단일 기관 편향, 샘플 수 한계 등 임상 데이터의 구체적 한계", "severity": "high|medium|low"}},
    {{"risk_type": "valuation", "description": "IPO 목표가 선반영 여부, 특정 연도 매출 목표 (예: 2024E 150억) 달성 불확실성 등 밸류에이션 리스크 구체 기술", "severity": "high|medium|low"}}
  ],
  "// risks 규칙": "위 3종(regulatory, clinical, valuation)은 반드시 모두 포함하라. IR에서 직접 근거를 찾을 수 없으면 '근거 부재'라고 명시하라.",
  "// stage_5 규칙": "stage_5_RWW개입은 반드시 두 레이어로 분리하라: (1) current_execution_evidence — 회사가 이미 가진 실행력 (해외 매출 비중, 진출 국가, 파트너십 등. 첫 항목은 반드시 '해외 매출 비중(%)'. IR 미기재 시 'IR 미기재' 명시), (2) rww_uplift_potential — NuBIZ RWW 플랫폼 개입 시 추가될 가치 증분 가정. 두 레이어를 섞지 마라. evidence 필드는 레거시 호환용이며 current + uplift의 대표 2-3문장만 담아라.",

  "missing_information": [
    {{"category": "<카테고리>", "criticality": "critical|important|nice_to_have", "impact": "<왜 중요한가>"}}
  ],

  "momentum_entry_timeline": {{
    "regulatory": [
      {{"year": "<연도 또는 IR 시점>", "event": "<이벤트 예: FDA 1차 대면미팅 → De Novo 적절 판정>", "strategic_meaning": "<전략적 의미 예: 510(k) 불가 → De Novo 필수 확인 — 규제 경로 확정>"}}
    ],
    "recurring_revenue": [
      {{"year": "<연도>", "event": "<이벤트 예: 소모품 카트리지 설계 확정 / 총판 재구매 발생>", "numeric_evidence": "<수치 예: 소모품 매출 비중 80%+ 확인 / MOQ 40억 실주문 58억>"}}
    ],
    "global_channel": [
      {{"year": "<연도>", "event": "<이벤트 예: KOTRA G4A 선정 / 20개국 인증 / 5개국 독점 총판>", "coverage": "<국가/파트너 예: 미국 FDA + 유럽 CE + 20개국 + LG화학 중국 독점>"}}
    ],
    "entry_judgment": {{
      "regulatory_entry_point": "<규제 경로가 핵심 동력으로 편입된 시점과 근거>",
      "recurring_revenue_entry_point": "<반복매출이 실증된 시점과 근거>",
      "global_channel_entry_point": "<글로벌 채널이 확보된 시점과 근거>"
    }}
  }},
  "// momentum_entry_timeline 규칙": "각 배열은 최소 2개 이상의 시점 이벤트를 포함하라. IR에서 연도/시점 근거를 찾을 수 없으면 'IR 미기재'라고 명시하라.",

  "rww_synergy_scenarios": [
    {{"intervention_area": "규제 문서 자동화", "expected_effect": "<회사 맥락 기대 효과>", "value_increment_basis": "<가치 증분 근거>", "estimate_type": "<assumption|estimate|benchmark_based>", "estimate_note": "<예: '[가정] NuBIZ 자체 벤치마크 기준 60% 단축 가정치. 실측 미검증.' — 모든 수치에 가정/추정 근거 명시>"}},
    {{"intervention_area": "다국가 인허가 병렬 관리", "expected_effect": "<회사 맥락 기대 효과>", "value_increment_basis": "<가치 증분 근거>", "estimate_type": "<assumption|estimate|benchmark_based>", "estimate_note": "<수치 출처/가정 라벨>"}},
    {{"intervention_area": "소모품/고객 재구매 예측", "expected_effect": "<회사 맥락 기대 효과>", "value_increment_basis": "<영업이익률 개선 근거>", "estimate_type": "<assumption|estimate|benchmark_based>", "estimate_note": "<수치 출처/가정 라벨>"}},
    {{"intervention_area": "IR 데이터 자동 생성", "expected_effect": "<회사 맥락 기대 효과>", "value_increment_basis": "<자금조달 비용 절감 근거>", "estimate_type": "<assumption|estimate|benchmark_based>", "estimate_note": "<수치 출처/가정 라벨>"}},
    {{"intervention_area": "특허/IP 포트폴리오 관리", "expected_effect": "<회사 맥락 기대 효과>", "value_increment_basis": "<IP 가치 보전/방어 근거>", "estimate_type": "<assumption|estimate|benchmark_based>", "estimate_note": "<수치 출처/가정 라벨>"}}
  ],
  "// rww_synergy_scenarios 규칙": "5개 영역 모두 포함. expected_effect/value_increment_basis에 숫자(%·월·배수 등)가 들어가면 반드시 '[가정]' 또는 '[추정]' 또는 '[벤치마크]' 접두어를 붙이고, estimate_note에 근거/출처를 1문장으로 명시하라. 실측 데이터가 아닌 경우 반드시 라벨링하여 오독 방지.",

  "nubiz_laws": [
    {{"law": "<한 문장 법칙 예: '기술이 아니라 제어력이 상장한다'>", "evidence_for_company": "<회사에 적용된 증거 예: 경쟁사 대비 ±3℃ 정밀도, 초당 50회 피드백, FDA 재현성 요건 충족>"}},
    {{"law": "<두 번째 법칙 예: '규제는 비용이 아니라 자산이다'>", "evidence_for_company": "<회사 증거 예: FDA De Novo 준비 6년, 1000+ 케이스 → 후발주자 진입 장벽>"}},
    {{"law": "<세 번째 법칙 예: '소모품이 없으면 상장도 없다'>", "evidence_for_company": "<회사 증거 예: 소모품 매출 80%+, CAGR 109%, 영업이익률 51%+>"}}
  ],
  "// nubiz_laws 규칙": "정확히 3개 법칙을 도출하라. 법칙은 이 회사의 사례에서 일반화 가능한 투자 명제여야 한다. 법칙 문장은 짧고 대비적(A가 아니라 B다 형식 권장)이어야 한다.",

  "investor_concern_validation": [
    {{
      "concern": "<투자자(VC/심사역)가 제기한 반대 논리 한 문장. 예: '3D 프린팅이 코팅을 대체할 것이다'>",
      "fact_check": "<사실 관계 검증 결과. web_search + IR 근거 인용. 예: '3D프린팅은 형상 제작, 코팅은 표면 처리로 별도 공정. Stryker Tritanium이 3D프린팅+코팅을 병용'>",
      "verdict": "<'타당함' | '부분적으로 타당' | '타당하지 않음' 중 택1>",
      "reasoning": "<왜 그렇게 판정했는가. 1-2문장>",
      "investment_impact": "<투자 판단에 주는 영향. 예: '반대 논리가 틀렸으므로 투자 재고 사유 없음' 또는 '부분 타당 — 리프레이밍 시 해소 가능'>"
    }}
  ],
  "// investor_concern_validation 규칙": "사용자가 제공한 vc_opinion 또는 IR에서 드러난 외부 반대 논리가 있을 때만 채워라. 없으면 빈 배열 []. 반대 논리 1개당 1개 entry. verdict는 반드시 3개 enum 중 하나. 억지로 '부분 타당'으로 도망가지 말고 단호한 판정 권장.",

  "diligence_trigger_checklist": [
    {{
      "item": "<실사 관문 항목. 예: 'FAI(First Article Inspection) 결과 300개 공동평가 데이터'>",
      "criticality": "<'critical' | 'high' | 'medium' | 'low' 중 택1>",
      "current_status": "<현재 상태. 예: '2026 파일럿 제작 중. 데이터 미확보'>",
      "next_evidence_needed": "<다음 증빙 문서. 예: 'FAI Protocol + 30일 내 공동평가 결과지'>",
      "fail_implication": "<이 관문이 fail되면 투자 판단에 무슨 의미인가. 예: 'FAI 실패 시 OEM 납품 경로 붕괴 → 투자 재고 필요'>"
    }}
  ],
  "// diligence_trigger_checklist 규칙": "4~8개 항목 권장. IR과 회사 맥락에 실제로 맞는 구체적 관문만 포함. '일반적 due diligence' 같은 추상 항목 금지. FAI/MOU-PO 전환/IP 방어력/고객 FDA 로드맵/핵심 인력/재무 실사 같은 회사별 맞춤 관문을 찾아내라. criticality는 실제 영향도로 냉정하게 판정.",

  "nubiz_fit_leverage": [
    {{
      "company_need": "<회사의 구체 니즈. 예: 'FDA 510(k) 고객사 인증 지원 역량 확보'>",
      "nubiz_capability": "<누비즈 보유 역량 매칭. 예: '에스테틱 의료기기 FDA/CE 11개국 인증 경험'>",
      "nubiz_asset_reference": "<참조 가능한 누비즈 구체 프로젝트 자산. 예: 'P08 (에스테틱)', 'P06 (AI로봇 VLA)', 'P07 (RWW+ALCOA+)', 'P09 (과기부 500억)', 'NUBiPLOT'. 해당 없으면 '자산 미매칭'>",
      "match_strength": "<'strong (★★★★★)' | 'high (★★★★☆)' | 'medium (★★★☆☆)' | 'low (★★☆☆☆)' | 'weak (★☆☆☆☆)' 중 택1 — 역량-니즈 매칭 강도>",
      "intervention_mode": "<개입 방식. 예: '공동 인증 컨설팅 + 인허가 문서 템플릿 제공'>",
      "expected_deliverable": "<기대 산출물. 예: '510(k) 제출 Ready Package'>",
      "feasibility_90d": "<'high' | 'medium' | 'low' 중 택1>"
    }}
  ],
  "// nubiz_fit_leverage 규칙": "3~6개 항목. 회사 니즈는 IR/반대논리/경쟁구조에서 실제로 추출. '일반적 IR 자동화/마케팅 지원' 같은 추상 매칭 금지. 누비즈 역량(FDA/CE 인증, 로봇제어 SW, 블록체인 품질추적, 데이터 분석, 정부 R&D, 특허관리 등)과 회사 니즈의 구체적 결합만 기술. match_strength는 실제 역량 적합도로 냉정히 평가하여 별점 부여. nubiz_asset_reference는 P06/P07/P08/P09/NUBiPLOT/NuBI Orchestrator 등 구체 프로젝트 코드로 연결.",

  "narrative_reframing": {{
    "current_narrative": "<회사가 현재 시장·투자자에게 보이는 내러티브. 예: '코팅 회사' / '의료기기 스타트업' — VC 내러티브상 약할 수 있는 표현>",
    "reframed_narrative": "<같은 본질을 투자자 언어로 번역한 리프레이밍. 예: '의료기기 제조 자동화 로봇 플랫폼' / 'OEM 수직통합형 첨단 제조 플랫폼'>",
    "why_more_persuasive": "<왜 리프레이밍이 더 설득력 있는가. VC 포지셔닝 관점에서. 예: '코팅은 VC 소외 영역이나 로봇/첨단제조는 대형 라운드 트랙. Canary Medical-Zimmer 전략투자 선례'>",
    "applicable_segments": ["<이 리프레이밍이 적중하는 VC/투자자 유형 예: 'OEM 전략투자자', '첨단제조 VC'>"],
    "caveat": "<리프레이밍의 한계. 예: '본질 바뀌는 건 아님. 팩트와 일치하는 범위에서만 사용 가능'>"
  }},
  "// narrative_reframing 규칙": "회사의 VC 내러티브 적합성이 낮거나 투자자 언어와 맞지 않을 때 채워라. IR과 실체가 일치하는 범위에서만 리프레이밍 (허위 확대 금지). 완벽히 맞는 회사(이미 강한 내러티브 보유)는 빈 객체 {{}} 허용.",

  "deal_structuring_suggestions": [
    {{
      "structure_type": "<'milestone_based' | 'strategic_co_investment' | 'bridge_round' | 'pilot_po_conditional' | 'tranched_with_kpi' | 'sidecar' 중 택1>",
      "conditions": ["<진입 조건 1 예: 'FAI 300ea 완료 시 1차 집행'>", "<진입 조건 2 예: 'MOU→PO 전환 시 2차 집행'>"],
      "rationale": "<왜 이 구조가 이 회사에 적합한가 1-2문장>",
      "target_investors": "<어떤 투자자가 이 구조에 맞는가. 예: 'OEM 전략투자자 + 마일스톤형 VC 공동'>"
    }}
  ],
  "// deal_structuring_suggestions 규칙": "2~4개 구조 권장. 단순 'go/no-go'가 아니라 '어떻게 구조화해서 들어갈 것인가'를 설계. 회사 단계(시드/시리즈A/B/프리IPO)와 리스크 구조에 맞춰 현실적 대안 제시. 모든 회사에 '마일스톤 기반 + 전략투자' 식 일반론 금지.",

  "problem_cost_severity": {{
    "problem_description": "<회사가 해결하려는 핵심 문제 한 문장>",
    "annual_cost_magnitude": "<해당 문제의 연간 경제적 비용 규모. 숫자 + 단위 + 지역. 예: '$1.5~2.5B annual (US TKA 재수술 비용)'>",
    "cost_basis": "<비용 산출 근거. web_search 검증 필수. 예: 'AAOS 2023 report + CMS claim data'>",
    "stakeholder_impact": [
      {{"stakeholder": "<병원/보험자/OEM/환자 중>", "impact": "<구체 영향 예: '병원당 재수술 건당 $25k, 연 평균 12건>'"}}
    ],
    "evidence_sources": ["<출처 URL 또는 기관명. web_search로 확인한 것만>"],
    "unmet_need_score": "<'critical (unmet)' | 'high (partial)' | 'medium (addressed)' | 'low (saturated)' 중 택1>"
  }},
  "// problem_cost_severity 규칙": "의료/B2B2B/공정장비 회사에 특히 중요. 단순 TAM이 아니라 '이 문제가 얼마나 비싼가'를 달러/원 단위로 뽑아라. 반드시 web_search로 출처 검증. IR에만 근거하면 과대평가 위험. unmet_need_score는 cost×stakeholder 조합으로 냉정히 판정."
}}
```

web_search 도구를 활용해 "{company_name} FDA approval", 경쟁사 실적, 규제 승인 사실을 반드시 교차검증하라.
응답은 위 JSON 스키마만 포함하라. 다른 텍스트 금지."""

        try:
            tools = [
                {
                    "name": "web_search",
                    "description": "Search web for FDA approvals, regulatory info, market data",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"]
                    }
                }
            ]

            messages = [{"role": "user", "content": user_prompt}]

            while True:
                response = self.client.messages.create(
                    model=self.model_version,
                    max_tokens=16000,
                    system=system_prompt,
                    tools=tools,
                    messages=messages
                )

                # tool_use가 없으면 분석 완료
                if response.stop_reason != "tool_use":
                    break

                # tool_use 블록 처리
                tool_results = []
                for block in response.content:
                    if hasattr(block, "type") and block.type == "tool_use":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Search executed and validated"
                        })

                # tool_result를 포함해서 다음 요청
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            # Extract final response - concatenate ALL text blocks (not just first)
            response_text = "".join(
                block.text for block in response.content
                if hasattr(block, "text") and isinstance(getattr(block, "text", None), str)
            )

            # Detect truncation: stop_reason == "max_tokens" means output was cut
            was_truncated = getattr(response, "stop_reason", "") == "max_tokens"

            try:
                return self._parse_claude_text_response(response_text)
            except (ValueError, json.JSONDecodeError) as parse_err:
                if was_truncated:
                    raise RuntimeError(
                        f"Claude 응답이 max_tokens(16000)에서 잘림. 스키마 축소 또는 토큰 상향 필요. "
                        f"(stop_reason=max_tokens) 앞부분 500자:\n{response_text[:500]}"
                    )
                raise

        except Exception as e:
            raise RuntimeError(f"Claude API call failed: {e}")

    def _parse_claude_text_response(self, text: str) -> Dict[str, Any]:
        """Parse Claude's text response. Tolerant to code fences with/without closing."""
        import re
        stripped = text.strip()

        # 1. ```json ... ``` 완전 펜스
        m = re.search(r'```json\s*(\{.*?\})\s*```', stripped, re.DOTALL)
        if m:
            return json.loads(m.group(1))

        # 2. ```json 으로 시작하지만 닫힘 없는 경우 (truncation) — 여는 펜스만 제거
        if stripped.startswith("```json"):
            stripped = stripped[len("```json"):].lstrip()
            # 혹시 끝에 닫는 펜스만 있으면 제거
            if stripped.endswith("```"):
                stripped = stripped[:-3].rstrip()

        # 3. 일반 ``` 펜스
        elif stripped.startswith("```"):
            stripped = stripped[3:].lstrip()
            if stripped.endswith("```"):
                stripped = stripped[:-3].rstrip()

        # 4. { ... } 범위만 추출해 시도
        first_brace = stripped.find('{')
        last_brace = stripped.rfind('}')
        if first_brace != -1 and last_brace > first_brace:
            candidate = stripped[first_brace:last_brace + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        # 5. 전체를 그대로 시도
        if stripped.startswith('{'):
            return json.loads(stripped)

        raise ValueError(f"Claude 응답에서 JSON 추출 실패:\n{text[:500]}")

    def _extract_scores_from_claude(self, claude_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure 5-stage scores."""
        scores = {}
        for stage_key in ["stage_1_원천기술통제", "stage_2_규제통제", "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"]:
            if stage_key in claude_analysis:
                stage_data = claude_analysis[stage_key]
                if isinstance(stage_data, dict):
                    score = float(stage_data.get("score", 6.5))
                    evidence = stage_data.get("evidence", [])
                    if isinstance(evidence, str):
                        evidence = [evidence]
                    counterevidence = stage_data.get("counterevidence", [])
                    if isinstance(counterevidence, str):
                        counterevidence = [counterevidence]
                    # stage_5 분리 필드 pass-through
                    current_ev = stage_data.get("current_execution_evidence", [])
                    if isinstance(current_ev, str):
                        current_ev = [current_ev]
                    uplift = stage_data.get("rww_uplift_potential", [])
                    if isinstance(uplift, str):
                        uplift = [uplift]
                else:
                    score = 6.5
                    evidence = []
                    counterevidence = []
                    current_ev = []
                    uplift = []
                entry = {
                    "score": min(score, 10.0),
                    "rubric_level": "strong" if score >= 8.0 else "adequate" if score >= 6.5 else "concerning",
                    "evidence": evidence,
                    "counterevidence": counterevidence,
                    "confidence": stage_data.get("confidence", 0.85) if isinstance(stage_data, dict) else 0.85
                }
                if stage_key == "stage_5_RWW개입":
                    entry["current_execution_evidence"] = current_ev
                    entry["rww_uplift_potential"] = uplift
                scores[stage_key] = entry

        stage_scores = [scores[k]["score"] for k in scores if k.startswith("stage_")]
        overall_score = sum(stage_scores) / max(len(stage_scores), 1) if stage_scores else 6.5

        scores["overall"] = {
            "score": round(overall_score, 1),
            "grade": self._compute_grade(overall_score),
            "reasoning": "Claude AI analysis based on comprehensive IR document review"
        }
        return scores

    def _extract_narratives_from_claude(self, claude_analysis: Dict[str, Any]) -> Dict[str, str]:
        """Extract narrative analysis for each stage."""
        return {
            "stage_1_원천기술통제": claude_analysis.get("stage_1_narrative", "Technology differentiation and IP strength assessed"),
            "stage_2_규제통제": claude_analysis.get("stage_2_narrative", "Regulatory pathway clarity reviewed"),
            "stage_3_플랫폼확장": claude_analysis.get("stage_3_narrative", "Platform scaling potential evaluated"),
            "stage_4_반복매출": claude_analysis.get("stage_4_narrative", "Recurring revenue model assessed"),
            "stage_5_RWW개입": claude_analysis.get("stage_5_narrative", "Team execution capability evaluated")
        }

    def _extract_red_flags(self, claude_analysis: Dict[str, Any]) -> List[str]:
        """Extract red flags from analysis."""
        risks = claude_analysis.get("risks", [])
        return [
            r.get("description", "Risk identified")
            for r in risks
            if r.get("severity") == "high"
        ][:5]

    def _compute_grade(self, score: float) -> str:
        """Map score to letter grade."""
        if score >= 9.0:
            return "A"
        elif score >= 8.5:
            return "A-"
        elif score >= 8.0:
            return "B+"
        elif score >= 7.5:
            return "B"
        elif score >= 7.0:
            return "B-"
        elif score >= 6.5:
            return "C+"
        elif score >= 6.0:
            return "C"
        elif score >= 5.0:
            return "D"
        else:
            return "F"

    def _extract_red_flags(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract red flags requiring investigation."""
        flags = []
        quality_flags = input_data.get("quality_flags", {})
        if quality_flags.get("red_flags_already_identified"):
            flags.extend([
                {
                    "flag": f"Previously identified concern: {concern}",
                    "severity": "high",
                    "evidence": "Reported by user",
                    "verification_needed": True
                }
                for concern in quality_flags["red_flags_already_identified"]
            ])
        return flags

    def _identify_missing_info(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify information gaps."""
        missing = []
        quality_flags = input_data.get("quality_flags", {})
        if quality_flags.get("missing_key_info"):
            missing.extend([
                {
                    "category": info,
                    "criticality": "important",
                    "impact": f"Missing {info} limits confidence in analysis"
                }
                for info in quality_flags["missing_key_info"]
            ])
        return missing or [
            {
                "category": "financial_projections",
                "criticality": "important",
                "impact": "Revenue projections needed for valuation cross-check"
            },
            {
                "category": "competitive_landscape",
                "criticality": "nice_to_have",
                "impact": "Detailed competitor analysis would strengthen positioning assessment"
            }
        ]

    def _assess_data_quality(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess quality of source data."""
        docs = input_data.get("documents", [])
        avg_confidence = sum(d.get("confidence", 0.5) for d in docs) / len(docs) if docs else 0.5

        return {
            "source_reliability": "medium" if avg_confidence > 0.6 else "low",
            "completeness": avg_confidence,
            "recency": "Analysis date reflects latest available materials",
            "concerns": [
                "Limited document count reduces analysis breadth" if len(docs) < 2 else "",
                f"Document confidence average: {avg_confidence:.1f}"
            ]
        }
