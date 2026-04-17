"""Mock pipeline test - verify pipeline with simulated Claude JSON response.
Used to check reporter outputs actual Claude data (not hardcoded templates).
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


MOCK_CLAUDE_JSON = {
    "analysis_reference_point": {
        "stance": "post_approval_reverse",
        "cutoff_date": "2024.10 FDA De Novo 승인 시점",
        "basis": "IR 최신 이벤트가 2024.10 FDA De Novo 승인 (KBR 보도 확인). 상장/승인 확정 사실 기반 역산.",
        "disclosure": "본 보고서는 FDA 승인 확정 이후의 역산 관점이며, 모든 시점·수치는 승인 확정 사실에 기반함."
    },
    "numeric_reference_table": {
        "revenue_latest": {"value": "2023 매출 58억", "source": "2024 IR p.12", "note": "확정"},
        "revenue_forecast": {"value": "2024E 150억", "source": "2024 IR p.13", "note": "예상치"},
        "cumulative_investment": {"value": "500억+", "source": "2024 IR p.4", "note": "확정"},
        "patent_count": {"value": "등록 37건 / 출원 113건", "source": "2024 IR p.7", "note": "등록·출원 구분"},
        "countries_coverage": {"value": "인증 20개국 / 판매 12개국", "source": "2024 IR p.10", "note": "인증·판매 구분"},
        "clinical_cases": {"value": "미국 10개 병원 1,000+ 케이스", "source": "2024 IR p.8", "note": "De Novo 임상"},
        "overseas_revenue_ratio": {"value": "90%", "source": "2024 IR p.14", "note": "확정"}
    },
    "headline": "리센스메디컬: De Novo + razor-blade 구조로 IPO 전환 가능성 높은 조건부 Buy",
    "investment_case": "기술 제어력 축에서 HIFU 기반 정밀 온도 제어 알고리즘이 FDA 재현성 요건을 구조적으로 충족한다. 반복매출 축에서 razor-blade 모델이 기기 설계 단계(카트리지 180g)부터 내재화되어 소모품 매출 비중 80%+를 확보했다. 규제 축에서 2018년 De Novo 전환을 거쳐 2024.10 승인을 달성하여 IPO 변곡점을 지났다.",
    "investment_decision": "buy",
    "risk_level": "medium",
    "investment_thesis": "강점: FDA De Novo 경로, 소모품 설계, IP 포트폴리오. 약점: 적응증 제한, IPO 밸류에이션 선반영 우려.",
    "factor_discovery": {
        "platform_evolution": "HIFU 플랫폼은 정맥에서 종양/심혈관 확장 가능",
        "regulatory_pathway": "FDA De Novo (Class II reclassification) 확정",
        "recurring_revenue": "소모품 20%, 유지보수 계약 설계됨",
        "ipo_factors": ["2017 De Novo 준비 착수", "2020 임상 500 케이스 돌파", "2023 소모품 매출 비중 20% 달성"],
        "ipo_reverse_analysis": [
            {"ir_expression_2017": "One Device, Different Disposables", "reverse_interpretation": "Razor-blade 비즈니스 모델 선언", "ipo_linkage": "반복매출 구조 내재화"},
            {"ir_expression_2017": "FDA De Novo 경로 준비", "reverse_interpretation": "Class II 신규 분류 선점 전략", "ipo_linkage": "독점 경로 확보"}
        ]
    },
    "early_indicators": [
        {
            "indicator_name": "원천기술 물리적 제어 가능성",
            "ir_evidence": "CEO 김건호 Nature Materials 2013/2015 논문, 초당 50회 피드백 제어",
            "why_signal": "물리 제어는 FDA 재현성 요건을 구조적으로 충족",
            "formula_type": "계산식형",
            "input_variables": ["물리 파라미터 수", "총 변수 수", "재현성 계수"],
            "calculation": "점수 = (물리 파라미터 수 / 총 변수 수) × 재현성 계수",
            "result_type": "숫자형 (0-10)",
            "evaluation_formula": "점수 = (물리 파라미터 수 / 총 변수 수) × 재현성 계수 → 0~10 숫자형"
        },
        {
            "indicator_name": "규제 실행 조직 선배치",
            "ir_evidence": "RA 경력 20년 백종환 COO, 100개 제품 인허가 경력",
            "why_signal": "규제를 R&D와 병렬 실행할 때만 IPO 타이밍 확보",
            "formula_type": "계산식형",
            "input_variables": ["RA 합류 시점(창업 후 개월)", "창업 후 경과월", "규제 경로 난이도"],
            "calculation": "점수 = (RA 합류 시점 / 창업 후 경과월) × 규제 경로 난이도",
            "result_type": "숫자형 (0-10)",
            "evaluation_formula": "점수 = (RA 합류 시점 / 창업 후 경과월) × 규제 경로 난이도 → 0~10 숫자형"
        },
        {
            "indicator_name": "제품 아키텍처 모듈화/소모품 설계",
            "ir_evidence": "'One Device, Different Disposables' — 카트리지 분리 설계",
            "why_signal": "모듈화는 반복매출 + 빠른 규제 확장의 동시 조건",
            "formula_type": "계산식형",
            "input_variables": ["소모품 SKU 수", "적용 임상 영역 수", "기기 플랫폼 수"],
            "calculation": "점수 = (소모품 SKU 수 × 임상 영역 수) / 기기 플랫폼 수",
            "result_type": "숫자형 (0-10)",
            "evaluation_formula": "점수 = (소모품 SKU 수 × 임상 영역 수) / 기기 플랫폼 수 → 0~10 숫자형"
        }
    ],
    "momentum_entry_timeline": {
        "regulatory": [
            {"year": "2018", "event": "FDA 1차 대면미팅 → De Novo 적절 판정", "strategic_meaning": "510(k) 불가 확인 → De Novo 경로 확정 전환점"},
            {"year": "2023.03", "event": "De Novo 제출", "strategic_meaning": "한국 최초 FDA De Novo 신청"},
            {"year": "2024.10", "event": "FDA De Novo 승인", "strategic_meaning": "IPO 기술특례상장 핵심 트리거"}
        ],
        "recurring_revenue": [
            {"year": "2019", "event": "TargetCool 소형 카트리지 180g 설계 확정", "numeric_evidence": "대형 탱크(40kg) 대신 소형 카트리지 설계 결정"},
            {"year": "2022 Q4", "event": "유럽/동남아/중동 재구매 발생", "numeric_evidence": "소모품 매출 비중 80%+ 확인"},
            {"year": "2023", "event": "MOQ 40억 달성 / 실주문 58억", "numeric_evidence": "2023 매출 50억+, 영업이익률 51%+ 전환"}
        ],
        "global_channel": [
            {"year": "2017", "event": "Bayer-KOTRA G4A 선정", "coverage": "글로벌 제약사 네트워크 진입"},
            {"year": "2021", "event": "국내 식약처 + 유럽 MDAC + 미국 FDA 인증", "coverage": "주요 3대 시장 규제 확보"},
            {"year": "2023-24", "event": "LG화학(중국), IDS(동남아), IMDAD(중동) 독점 총판", "coverage": "20개국 인증 + 5대 독점 총판"}
        ],
        "entry_judgment": {
            "regulatory_entry_point": "2018년. 창업 2년차에 FDA 직접 접촉하여 De Novo 경로 확보. 이후 6년간 규제가 IPO 핵심 자산으로 전환.",
            "recurring_revenue_entry_point": "2022 Q4. 하드웨어 설계는 2019년 확정되었으나 실제 반복매출 검증은 해외 총판 재구매 시점.",
            "global_channel_entry_point": "2021. 3대 규제 동시 확보로 글로벌 독점 총판 확장 가능성 현실화."
        }
    },
    "rww_synergy_scenarios": [
        {"intervention_area": "규제 문서 자동화", "expected_effect": "[가정] FDA/CE/KGMP 문서 생성 시간 60% 단축", "value_increment_basis": "[가정] 인허가 달성 시점 6-12개월 앞당김 → 매출 조기 발생", "estimate_type": "assumption", "estimate_note": "NuBIZ 내부 벤치마크 기반 가정치. 실측 미검증."},
        {"intervention_area": "다국가 인허가 병렬 관리", "expected_effect": "[추정] 20개국 인증을 체계적으로 추적/관리", "value_increment_basis": "[추정] 시장 진입 속도 × 매출 = 밸류에이션 프리미엄", "estimate_type": "estimate", "estimate_note": "회사의 기존 20개국 인증 실적 기반 추정."},
        {"intervention_area": "소모품/고객 재구매 예측", "expected_effect": "[가정] 총판별 재구매 패턴 분석 → 재고/생산 최적화", "value_increment_basis": "[가정] 영업이익률 추가 5~10%p 개선 가능", "estimate_type": "assumption", "estimate_note": "경쟁사 razor-blade 모델 벤치마크 기반 가정. 회사 고유 상황 미반영."},
        {"intervention_area": "IR 데이터 자동 생성", "expected_effect": "[추정] 실시간 매출/임상 데이터 기반 IR 자료 업데이트", "value_increment_basis": "[추정] 투자자 커뮤니케이션 효율화 → 자금 조달 비용 절감", "estimate_type": "estimate", "estimate_note": "정성적 효과. 정량 지표 미산출."},
        {"intervention_area": "특허/IP 포트폴리오 관리", "expected_effect": "[벤치마크] 150건+ 글로벌 특허의 만료/갱신/침해 모니터링", "value_increment_basis": "[추정] IP 가치 보전 및 방어적 라이센싱 수익", "estimate_type": "benchmark_based", "estimate_note": "회사 실제 특허 건수(IR 기재) 기반. 라이센싱 수익은 추정."}
    ],
    "nubiz_laws": [
        {"law": "기술이 아니라 제어력이 상장한다", "evidence_for_company": "경쟁사 대비 ±3℃ 정밀도, 초당 50회 피드백, -50℃~+5℃ 범위 제어가 FDA 재현성 요건을 충족"},
        {"law": "규제는 비용이 아니라 자산이다", "evidence_for_company": "FDA De Novo 준비 6년, 임상 1000+ 케이스가 후발주자 진입 장벽으로 전환 — IPO 시 기업가치 3,000억 핵심 드라이버"},
        {"law": "소모품이 없으면 상장도 없다", "evidence_for_company": "경쟁사 대형탱크(40kg) vs 소형카트리지(180g) 설계 차이 → 소모품 매출 80%+, CAGR 109%, 영업이익률 51%+ 달성"}
    ],
    "stage_1_원천기술통제": {"score": 9.0, "evidence": ["HIFU 제어 특허 3건", "IP 포트폴리오 15건"], "confidence": 0.9},
    "stage_2_규제통제": {"score": 9.5, "evidence": ["FDA De Novo 경로 확정", "임상 1000+ 케이스 확보"], "confidence": 0.95},
    "stage_3_플랫폼확장": {"score": 8.0, "evidence": ["정맥→종양→심혈관 3개 적응증 확장 가능"], "confidence": 0.85},
    "stage_4_반복매출": {"score": 8.5, "evidence": ["소모품 매출 비중 20%, 유지보수 계약 설계"], "confidence": 0.9},
    "stage_5_RWW개입": {
        "score": 8.0,
        "current_execution_evidence": [
            "해외 매출 비중 90% (IR 2024 연결재무제표)",
            "글로벌 실행력: 미국/유럽/일본 진출, 해외 임상 3건, 20개국 인증",
            "Advisory Board 보유, 미국 공급 협의 진행 중"
        ],
        "rww_uplift_potential": [
            "NuBIZ 개입 시 아시아 판로 확장 기대 (가치 증분: [가정] 매출 20~30% 추가)",
            "규제 문서 자동화로 인허가 사이클 단축 잠재력"
        ],
        "evidence": ["해외 매출 비중 90%", "20개국 인증 진출", "NuBIZ 개입 시 아시아 확장 잠재"],
        "confidence": 0.8
    },
    "cross_validation": [
        {
            "company": "Intuitive Surgical (ISRG)",
            "ipo_year": "2000",
            "regulatory_pathway": "FDA PMA",
            "revenue_model": "razor-blade (소모품 70%+)",
            "market_cap_current": "$60B+",
            "similarity_dimensions": ["반복매출 모델", "규제 해자", "플랫폼 확장"],
            "key_outcome_metric": "10%+ YoY 25년 지속",
            "applicability_to_subject": "소모품 중심 medtech의 장기 IPO/시총 확장 모델 입증"
        },
        {
            "company": "PROCEPT BioRobotics (PRCT)",
            "ipo_year": "2021",
            "regulatory_pathway": "FDA De Novo",
            "revenue_model": "razor-blade (디바이스+소모품)",
            "market_cap_current": "[추정] $2B+ (2024년 기준)",
            "similarity_dimensions": ["FDA De Novo 경로", "소모품 반복매출"],
            "key_outcome_metric": "IPO 후 $100M+ 매출 달성",
            "applicability_to_subject": "De Novo 경로가 IPO 가속 장치가 된 최근 사례. 리센스의 De Novo 전략과 직접 비교 가능."
        }
    ],
    "risks": [
        {"risk_type": "regulatory", "description": "FDA De Novo 최종 승인 미확정, 적응증 범위 제한 (OcuCool → IVT만 승인)", "severity": "high"},
        {"risk_type": "clinical", "description": "non-inferiority 설계 가능성, 단일 기관 편향 여부", "severity": "medium"},
        {"risk_type": "valuation", "description": "IPO 목표가 선반영 여부, 2024E 150억 달성 불확실성", "severity": "medium"}
    ],
    "missing_information": [
        {"category": "financial_projections", "criticality": "important", "impact": "매출 전망치 없음"}
    ]
}


def make_mock_response(json_body):
    block = MagicMock()
    block.type = "text"
    block.text = json.dumps(json_body, ensure_ascii=False)
    response = MagicMock()
    response.content = [block]
    response.stop_reason = "end_turn"
    return response


def run_mock():
    print("=" * 70)
    print("MOCK Pipeline Test — Claude API simulated")
    print("=" * 70)

    samples_dir = Path(__file__).parent.parent / "samples"
    input_data = json.loads((samples_dir / "sample_input_recens.json").read_text(encoding="utf-8"))

    import os
    os.environ["ANTHROPIC_API_KEY"] = "sk-mock-test-key"

    from .analyzer import Analyzer
    from .reporter import Reporter

    mock_response = make_mock_response(MOCK_CLAUDE_JSON)

    with patch("anthropic.Anthropic") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_client_cls.return_value = mock_client

        analyzer = Analyzer()
        analyzer.client = mock_client
        analysis_internal = analyzer.analyze(input_data)

        reporter = Reporter()
        result = reporter.generate_report(analysis_internal)

    report_final = result["report_final"]

    print("\n--- 검증 지점 ---")

    ei = report_final.get("early_indicators", [])
    print("\n[1] Early Indicators 첫 번째 항목 전문:")
    if isinstance(ei, list) and ei:
        print(f"    {json.dumps(ei[0], ensure_ascii=False, indent=2)}")
    else:
        print(f"    (비어있음 or 잘못된 형식) {ei}")

    sc = report_final.get("5stage_scorecard", {})
    s1 = sc.get("stage_1_원천기술통제", {})
    print("\n[2] stage_1 evidence 첫 번째 항목 전문:")
    ev = s1.get("evidence", [])
    if ev:
        print(f"    {repr(ev[0])}")
    else:
        print(f"    (비어있음)")

    cv = report_final.get("cross_validation", [])
    print("\n[3] Cross Validation 첫 번째 항목 전문:")
    if isinstance(cv, list) and cv:
        print(f"    {json.dumps(cv[0], ensure_ascii=False, indent=2)}")
    else:
        print(f"    (비어있음 or 잘못된 형식) {cv}")

    print("\n--- 헤드라인 ---")
    es = report_final.get("executive_summary", {})
    print(f"headline: {es.get('headline')}")
    print(f"investment_case: {es.get('investment_case')[:120]}...")
    print(f"recommendation: {es.get('recommendation')}")

    print("\n--- [4] Risks 섹션 3종 확인 ---")
    md = result.get("markdown", "")
    risk_checks = {
        "규제 리스크": "규제 리스크" in md and ("FDA De Novo" in md or "OcuCool" in md),
        "임상 한계": "임상 한계" in md and "non-inferiority" in md,
        "밸류에이션 리스크": "밸류에이션 리스크" in md and ("IPO 목표가" in md or "150억" in md),
    }
    for k, v in risk_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [5] Factor Discovery 역산 테이블 확인 ---")
    fd_checks = {
        "역산 테이블 헤더": "IR 원문 표현" in md and "역산 재해석" in md and "IPO 가치 연결" in md,
        "Razor-blade 재해석": "Razor-blade" in md,
    }
    for k, v in fd_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [6] stage_5 해외 매출 비중 확인 ---")
    overseas_checks = {
        "해외 매출 비중 문구": "해외 매출 비중" in md,
        "90% 수치": "90%" in md or "90 %" in md,
    }
    for k, v in overseas_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [7] Appendix obsolete 문구 제거 확인 ---")
    obsolete_checks = {
        "IPO reverse-engineering obsolete 문구 제거": "IPO reverse-engineering logic not fully integrated" not in md,
        "v3 planned obsolete 문구 제거": "deferred to v3" not in md,
    }
    for k, v in obsolete_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    # ─── Wave 1 gate ───
    print("\n--- [W1-A] 동력 편입 시점 타임라인 확인 ---")
    wave1a_checks = {
        "섹션 헤더": "핵심 동력 편입 시점" in md,
        "규제 경로 표": "FDA 1차 대면미팅" in md and "2018" in md,
        "반복매출 표": "소모품 매출 비중 80" in md,
        "글로벌 채널 표": "LG화학" in md or "20개국" in md,
        "편입 시점 판정": "편입 시점 판정" in md,
    }
    for k, v in wave1a_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-B] Early Indicators why_signal + 평가 공식 확인 ---")
    wave1b_checks = {
        "왜 시그널인가": "왜 시그널인가" in md,
        "평가 공식": "평가 공식" in md,
        "공식 예시 포함": "재현성 계수" in md or "RA 합류 시점" in md,
    }
    for k, v in wave1b_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-C] RWW 퀀텀 점프 시나리오 확인 ---")
    wave1c_checks = {
        "섹션 헤더": "RWW 플랫폼 적용 시 기업가치 퀀텀 점프 시나리오" in md,
        "규제 문서 자동화": "규제 문서 자동화" in md,
        "다국가 인허가 병렬 관리": "다국가 인허가 병렬 관리" in md,
        "재구매 예측": "재구매" in md,
        "IR 자동 생성": "IR 데이터 자동 생성" in md,
        "IP 관리": "IP 포트폴리오 관리" in md,
    }
    for k, v in wave1c_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-D] 3대 법칙 (Final Take) 확인 ---")
    wave1d_checks = {
        "섹션 헤더": "Final Take" in md and "3대 법칙" in md,
        "법칙 1 (제어력)": "제어력이 상장한다" in md,
        "법칙 2 (규제 자산)": "규제는 비용이 아니라 자산이다" in md,
        "법칙 3 (소모품)": "소모품이 없으면 상장도 없다" in md,
    }
    for k, v in wave1d_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-E] 분석 기준 시점 통일 확인 ---")
    wave1e_checks = {
        "분석 관점 헤더": "분석 관점" in md,
        "승인 후 역산 라벨": "승인/IPO 후 역산" in md or "Post-Approval" in md,
        "IR 기준 시점": "2024.10" in md,
        "독자 경고": "독자 경고" in md and "승인 확정" in md,
    }
    for k, v in wave1e_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-F] RWW 시나리오 가정/추정 라벨 확인 ---")
    wave1f_checks = {
        "[가정] 라벨": "[가정]" in md,
        "[추정] 라벨": "[추정]" in md,
        "[벤치마크] 라벨": "[벤치마크]" in md,
        "근거 유형 컬럼": "근거 유형" in md,
        "산출 근거 컬럼": "산출 근거" in md,
        "경고 문구": "가정/추정치" in md,
    }
    for k, v in wave1f_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-G] Cross Validation 구조화 확인 ---")
    wave1g_checks = {
        "표 헤더 (IPO 연도)": "IPO 연도" in md,
        "표 헤더 (규제 경로)": "규제 경로" in md and "FDA PMA" in md,
        "표 헤더 (매출 모델)": "razor-blade" in md,
        "시가총액 컬럼": "$60B+" in md,
        "유사성 차원 섹션": "유사성 차원 및 시사점" in md,
        "공유 성공 패턴": "공유 성공 패턴" in md,
    }
    for k, v in wave1g_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-H] Numeric Reference Table 확인 ---")
    wave1h_checks = {
        "섹션 헤더": "Numeric Reference Table" in md or "숫자 기준표" in md,
        "최신 매출 행": "최신 매출" in md and "58억" in md,
        "특허 등록/출원 구분": "등록 37건" in md and "출원" in md,
        "국가 인증/판매 구분": "인증 20개국" in md and "판매 12개국" in md,
        "IR 출처 컬럼": "IR 출처" in md and "2024 IR" in md,
    }
    for k, v in wave1h_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-I] stage_5 Current / RWW Uplift 분리 확인 ---")
    wave1i_checks = {
        "현재 실행력 헤더": "회사의 현재 실행력" in md or "Current State" in md,
        "RWW Uplift 헤더": "NuBIZ 개입 잠재력" in md or "RWW Uplift" in md,
        "Advisory Board (현재)": "Advisory Board" in md,
        "가치 증분 가정 (Uplift)": "가치 증분" in md and "가정" in md,
    }
    for k, v in wave1i_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-K] Headline 톤 보수화 확인 ---")
    headline = es.get("headline", "")
    wave1k_checks = {
        "단정 표현 배제 (IPO 직전)": "IPO 직전" not in headline,
        "단정 표현 배제 (상장 확정)": "상장 확정" not in headline,
        "유보 표현 존재 (조건부/전환/가능성/잠재력 중 하나)": any(t in headline for t in ["조건부", "전환 가능성", "가능성", "잠재력"]),
    }
    for k, v in wave1k_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-L] Investment Case 3문장 압축 확인 ---")
    ic = es.get("investment_case", "")
    # 문장 수 계산 (마침표 기준, 마지막 마침표 후 빈 문장 제외)
    sentences = [s for s in ic.split(".") if s.strip()]
    wave1l_checks = {
        "3문장 전후 (3~4개)": 3 <= len(sentences) <= 4,
        "기술 제어력 축 언급": "제어력" in ic or "제어" in ic,
        "반복매출 축 언급": "반복매출" in ic or "razor-blade" in ic.lower() or "razor" in ic.lower(),
        "규제/IPO 변곡점 언급": "IPO" in ic and ("변곡점" in ic or "승인" in ic or "De Novo" in ic),
    }
    for k, v in wave1l_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-M] Early Indicators 공식 포맷 통일 확인 ---")
    # mock에서 phase1_analysis의 early_indicators 직접 확인
    phase1 = analysis_internal.get("phase1_analysis", {})
    raw_inds = phase1.get("early_indicators", [])
    f_types = [ind.get("formula_type") for ind in raw_inds if isinstance(ind, dict)]
    unique_ft = set(t for t in f_types if t)
    wave1m_checks = {
        "3개 indicator 전부 formula_type 존재": len(f_types) == 3 and all(t for t in f_types),
        "formula_type 통일": len(unique_ft) == 1,
        "입력변수 필드 존재": all(ind.get("input_variables") for ind in raw_inds if isinstance(ind, dict)),
        "계산식 필드 존재": all(ind.get("calculation") for ind in raw_inds if isinstance(ind, dict)),
        "결과타입 필드 존재": all(ind.get("result_type") for ind in raw_inds if isinstance(ind, dict)),
        "마크다운에 입력 변수 라벨": "입력 변수" in md,
        "마크다운에 계산식 라벨": "계산식" in md,
        "마크다운에 결과 타입 라벨": "결과 타입" in md,
    }
    for k, v in wave1m_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n--- [W1-J] 섹션 순서 재배치 확인 (Risks가 Early Indicators 앞) ---")
    exec_pos = md.find("## Executive Summary")
    num_pos = md.find("## Numeric Reference Table")
    risks_pos = md.find("## Risks (필수 3종)")
    early_pos = md.find("## Early Indicators")
    factor_pos = md.find("## Factor Discovery")
    cross_pos = md.find("## Cross Validation")
    rww_pos = md.find("## NuBIZ RWW")
    final_pos = md.find("## Final Take")
    wave1j_checks = {
        "Exec < Numeric": exec_pos >= 0 and num_pos > exec_pos,
        "Numeric < Risks": num_pos >= 0 and risks_pos > num_pos,
        "Risks < Early Indicators": risks_pos >= 0 and early_pos > risks_pos,
        "Factor Discovery < Cross Validation": factor_pos >= 0 and cross_pos > factor_pos,
        "Cross Validation < RWW": cross_pos >= 0 and rww_pos > cross_pos,
        "RWW < Final Take": rww_pos >= 0 and final_pos > rww_pos,
    }
    for k, v in wave1j_checks.items():
        print(f"    {'OK' if v else 'FAIL'}: {k}")

    print("\n" + "=" * 70)
    forbidden = ["Analyzed from IR materials", "Product Market Fit", "Regulatory Pathway Clarity",
                 "Revenue Growth Trajectory", "Team Expansion"]
    full_text = json.dumps(report_final, ensure_ascii=False) + md
    bad = [f for f in forbidden if f in full_text]
    all_risks_ok = all(risk_checks.values())
    all_fd_ok = all(fd_checks.values())
    all_overseas_ok = all(overseas_checks.values())
    all_obsolete_ok = all(obsolete_checks.values())
    all_w1a = all(wave1a_checks.values())
    all_w1b = all(wave1b_checks.values())
    all_w1c = all(wave1c_checks.values())
    all_w1d = all(wave1d_checks.values())
    all_w1e = all(wave1e_checks.values())
    all_w1f = all(wave1f_checks.values())
    all_w1g = all(wave1g_checks.values())
    all_w1h = all(wave1h_checks.values())
    all_w1i = all(wave1i_checks.values())
    all_w1j = all(wave1j_checks.values())
    all_w1k = all(wave1k_checks.values())
    all_w1l = all(wave1l_checks.values())
    all_w1m = all(wave1m_checks.values())
    if bad:
        print(f"FAIL: 하드코딩 템플릿 잔존: {bad}")
    elif not all_risks_ok:
        print("FAIL: Risks 3종 중 일부 누락")
    elif not all_fd_ok:
        print("FAIL: Factor Discovery 역산 테이블 누락")
    elif not all_overseas_ok:
        print("FAIL: stage_5 해외 매출 비중 누락")
    elif not all_obsolete_ok:
        print("FAIL: Appendix obsolete 문구 잔존")
    elif not all_w1a:
        print("FAIL: Wave 1-A (동력 편입 시점) 누락")
    elif not all_w1b:
        print("FAIL: Wave 1-B (why_signal/평가공식) 누락")
    elif not all_w1c:
        print("FAIL: Wave 1-C (RWW 시나리오) 누락")
    elif not all_w1d:
        print("FAIL: Wave 1-D (3대 법칙) 누락")
    elif not all_w1e:
        print("FAIL: Wave 1-E (분석 기준 시점 통일) 누락")
    elif not all_w1f:
        print("FAIL: Wave 1-F (RWW 가정/추정 라벨) 누락")
    elif not all_w1g:
        print("FAIL: Wave 1-G (Cross Validation 구조화) 누락")
    elif not all_w1h:
        print("FAIL: Wave 1-H (Numeric Reference Table) 누락")
    elif not all_w1i:
        print("FAIL: Wave 1-I (stage_5 Current/Uplift 분리) 누락")
    elif not all_w1j:
        print("FAIL: Wave 1-J (섹션 순서 재배치) 누락")
    elif not all_w1k:
        print("FAIL: Wave 1-K (Headline 톤 보수화) 누락")
    elif not all_w1l:
        print("FAIL: Wave 1-L (Investment Case 3문장 압축) 누락")
    elif not all_w1m:
        print("FAIL: Wave 1-M (Early Indicators 공식 통일) 누락")
    else:
        print("PASS: 모든 항목 + Wave 1 (A~D) + 다듬기 (E~G) + 개선 (H~J) + 2차 다듬기 (K~M) 전부 정상")
    print("=" * 70)


if __name__ == "__main__":
    run_mock()
