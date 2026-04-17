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
    "headline": "Recens Medical: B+-Grade Investment — HIFU 플랫폼의 FDA De Novo 경로 확정 + 소모품 20% 구조",
    "investment_case": "Recens Medical은 HIFU 기반 정맥 치료 플랫폼으로 FDA De Novo 경로를 6년간 준비하여 임상 1000+ 케이스를 확보했다. 2017년 창업 이후 모듈형 아키텍처로 소모품 매출 비중 20%를 설계했으며, 규제 실행 조직을 선배치했다. 경쟁사 Intuitive Surgical 대비 적응증 특화로 non-inferiority 확보 가능.",
    "investment_decision": "buy",
    "risk_level": "medium",
    "investment_thesis": "강점: FDA De Novo 경로, 소모품 설계, IP 포트폴리오. 약점: 적응증 제한, IPO 밸류에이션 선반영 우려.",
    "factor_discovery": {
        "platform_evolution": "HIFU 플랫폼은 정맥에서 종양/심혈관 확장 가능",
        "regulatory_pathway": "FDA De Novo (Class II reclassification) 확정",
        "recurring_revenue": "소모품 20%, 유지보수 계약 설계됨",
        "ipo_factors": ["2017 De Novo 준비 착수", "2020 임상 500 케이스 돌파", "2023 소모품 매출 비중 20% 달성"]
    },
    "early_indicators": [
        {"indicator_name": "원천기술 물리적 제어 가능성", "description": "HIFU 주파수/출력 실시간 제어 특허 3건 보유, 경쟁사 대비 제어 정밀도 2배"},
        {"indicator_name": "규제 실행 조직 선배치", "description": "2017년 창업 시점 FDA Regulatory Affairs VP 영입, 6년간 De Novo 준비 전담"},
        {"indicator_name": "제품 아키텍처 모듈화/소모품 설계", "description": "본체-프로브-소모품 3단 분리 구조, 소모품은 1회용 설계로 반복 매출 확보"}
    ],
    "stage_1_원천기술통제": {"score": 9.0, "evidence": ["HIFU 제어 특허 3건", "IP 포트폴리오 15건"], "confidence": 0.9},
    "stage_2_규제통제": {"score": 9.5, "evidence": ["FDA De Novo 경로 확정", "임상 1000+ 케이스 확보"], "confidence": 0.95},
    "stage_3_플랫폼확장": {"score": 8.0, "evidence": ["정맥→종양→심혈관 3개 적응증 확장 가능"], "confidence": 0.85},
    "stage_4_반복매출": {"score": 8.5, "evidence": ["소모품 매출 비중 20%, 유지보수 계약 설계"], "confidence": 0.9},
    "stage_5_RWW개입": {"score": 8.0, "evidence": ["NuBIZ 개입 시 아시아 판로 확장 기대"], "confidence": 0.8},
    "cross_validation": [
        {"company": "Intuitive Surgical (ISRG)", "similarity": "소모품 비중 높은 medtech", "outcome": "IPO 2000, $60B+ 시총", "relevance_to_subject": "소모품 중심 medtech IPO 가능성 입증"},
        {"company": "PROCEPT BioRobotics (PRCT)", "similarity": "FDA De Novo 경로 활용", "outcome": "IPO 2021, $100M+ 매출", "relevance_to_subject": "De Novo 경로 IPO 가속 사례"}
    ],
    "risks": [
        {"risk_type": "regulatory", "description": "FDA 승인 적응증이 정맥으로 한정될 위험", "severity": "high"},
        {"risk_type": "clinical", "description": "non-inferiority 실패 시 급속 가치 하락", "severity": "medium"},
        {"risk_type": "valuation", "description": "IPO 밸류에이션에 성공 시나리오가 선반영", "severity": "medium"}
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

    print("\n" + "=" * 70)
    forbidden = ["Analyzed from IR materials", "Product Market Fit", "Regulatory Pathway Clarity",
                 "Revenue Growth Trajectory", "Team Expansion", "Intuitive Surgical (ISRG)"]
    md = result.get("markdown", "")
    full_text = json.dumps(report_final, ensure_ascii=False) + md
    flagged = [f for f in forbidden if f in full_text]
    # Intuitive Surgical is OK if it comes from mock Claude response (we put it in mock)
    # So filter: only flag if it's the OLD hardcoded template wording
    bad = [f for f in flagged if f in ("Analyzed from IR materials", "Product Market Fit",
                                        "Regulatory Pathway Clarity", "Revenue Growth Trajectory",
                                        "Team Expansion")]
    if bad:
        print(f"FAIL: 하드코딩 템플릿 잔존: {bad}")
    else:
        print("PASS: 하드코딩 템플릿 제거됨. Claude 데이터 정상 반영.")
    print("=" * 70)


if __name__ == "__main__":
    run_mock()
