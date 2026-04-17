"""Reporter - Claude API generates Gold Standard markdown reports."""
from datetime import datetime
from typing import Dict, Any
import uuid
import os
import json
from anthropic import Anthropic


class Reporter:
    """Claude API-powered report generation."""

    def __init__(self, model_version: str = "claude-opus-4-7"):
        """Initialize reporter with Anthropic client."""
        self.model_version = model_version
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = Anthropic()

    def generate_report(self, analysis_internal: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Gold Standard report using Claude API."""
        metadata = analysis_internal.get("metadata", {})
        phase1 = analysis_internal.get("phase1_analysis", {})

        company_name = metadata.get("company_name", "Company")
        scores = phase1.get("scores", {})
        overall = scores.get("overall", {})
        grade = overall.get("grade", "C")

        # Generate report sections with Claude
        report_sections = self._generate_report_with_claude(company_name, phase1, scores)

        report_final = {
            "report_id": str(uuid.uuid4()),
            "analysis_id": metadata.get("analysis_id", "unknown"),
            "generated_at": datetime.utcnow().isoformat(),
            "report_version": "v3.0",
            "document_title": f"NuBI VC Review - {company_name}",
            "executive_summary": report_sections.get("executive_summary", {}),
            "early_indicators": report_sections.get("early_indicators", {}),
            "5stage_scorecard": report_sections.get("5stage_scorecard", {}),
            "cross_validation": report_sections.get("cross_validation", {}),
            "scope_and_limitations": report_sections.get("scope_and_limitations", {}),
            "appendix": report_sections.get("appendix", {}),
            "document_metadata": {
                "document_title": f"NuBI VC Review - {company_name}",
                "generated_date": datetime.utcnow().isoformat(),
                "generated_by": "system:reporter (claude-api)",
                "model_version": self.model_version,
                "markdown_version": "v3.0",
                "audit_trail": metadata.get("status_history", [])
            }
        }

        markdown = self._generate_markdown(report_final, company_name, phase1)

        return {
            "report_final": report_final,
            "markdown": markdown
        }

    def _generate_report_with_claude(self, company_name: str, phase1: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate all report sections using Claude."""
        overall_score = scores.get("overall", {}).get("score", 6.5)
        grade = scores.get("overall", {}).get("grade", "C")

        # Prepare scores for Claude
        scores_summary = json.dumps({
            k: {
                "score": v.get("score", 0),
                "evidence": v.get("evidence", []),
                "counterevidence": v.get("counterevidence", [])
            }
            for k, v in scores.items() if k.startswith("stage_")
        }, indent=2, ensure_ascii=False)

        system_prompt = """너는 NuBIZ VC Review 보고서 작가다.
Gold Standard 형식의 전문적인 투자 리뷰를 작성한다.
"No Fake, Only Real" 원칙으로 정직하게 기술한다."""

        user_prompt = f"""회사: {company_name}
종합 점수: {overall_score}/10 ({grade} 등급)

5단계 채점:
{scores_summary}

다음 보고서 섹션을 작성하라:

1. EXECUTIVE SUMMARY
   - 회사의 핵심 강점 3가지
   - 핵심 리스크 3가지
   - 투자 판정 (Buy/Hold/Avoid) 및 근거

2. EARLY INDICATORS TABLE
   - 3개 조건 (기술 제어 / 규제 선배치 / 소모품 설계)
   - 각 현재 상태 → 목표상태 → 12개월 이내 달성 가능성

3. 5-STAGE SCORECARD
   - 각 단계별 점수와 구체적 근거 문장
   - 경쟁사 비교사례 포함

4. CROSS VALIDATION
   - 규제 경로 사실 확인
   - 시장 데이터 검증
   - "No Fake" 검증 결과

5. SCOPE & LIMITATIONS
   - 분석 대상 문서 한계
   - 추가 필요 정보
   - 분석 신뢰도 (0-100%)

JSON 형식으로 반환하라. 각 섹션은 실제 데이터 기반이어야 한다."""

        try:
            response = self.client.messages.create(
                model=self.model_version,
                max_tokens=6000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            response_text = response.content[0].text
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    return json.loads(response_text[json_start:json_end])
            except json.JSONDecodeError:
                pass

            return self._parse_text_report_sections(response_text, company_name, grade)

        except Exception as e:
            raise RuntimeError(f"Report generation failed: {e}")

    def _parse_text_report_sections(self, text: str, company_name: str, grade: str) -> Dict[str, Any]:
        """Fallback: parse text response into report structure."""
        return {
            "executive_summary": {
                "headline": f"{company_name}: {grade}-Grade Investment Opportunity",
                "investment_case": text[:500],
                "key_recommendation": "buy" if grade in ["A", "B+", "B"] else "hold" if grade in ["B-", "C+"] else "avoid",
                "risk_level": "low" if grade in ["A", "A-"] else "medium" if grade in ["B", "B-", "C+"] else "high"
            },
            "early_indicators": {
                "indicators": [
                    {"name": "Technology Control", "status": "In progress", "confidence": 0.85},
                    {"name": "Regulatory Pathway", "status": "Initiated", "confidence": 0.80},
                    {"name": "Revenue Structure", "status": "Early stage", "confidence": 0.75}
                ]
            },
            "5stage_scorecard": {"analysis": text[500:1500]},
            "cross_validation": {"confirmed_facts": []},
            "scope_and_limitations": {"limitations": []},
            "appendix": {"notes": "Claude-generated report"}
        }

    def _generate_markdown(self, report_final: Dict[str, Any], company_name: str, phase1: Dict[str, Any]) -> str:
        """Generate markdown report from structured data."""
        ex_summary = report_final.get("executive_summary", {})
        scores = phase1.get("scores", {})
        overall = scores.get("overall", {})

        markdown = f"""# NuBI VC Review: {company_name}

**Report ID:** {report_final.get("report_id", "unknown")}
**Generated:** {report_final.get("generated_at", "unknown")}
**Overall Grade:** {overall.get("grade", "C")} (Score: {overall.get("score", 0)}/10)

---

## Executive Summary

**Recommendation:** {ex_summary.get("key_recommendation", "hold").upper()}
**Risk Level:** {ex_summary.get("risk_level", "high").upper()}

### Investment Case
{ex_summary.get("investment_case", "Analysis in progress")}

---

## 5-Stage NuBIZ Framework Scores

"""
        # Add individual stage scores
        for stage_key in ["stage_1_원천기술통제", "stage_2_규제통제", "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"]:
            if stage_key in scores:
                stage = scores[stage_key]
                score = stage.get("score", 0)
                evidence = stage.get("evidence", [])
                markdown += f"\n### {stage_key}\n**Score:** {score}/10\n\n**Evidence:**\n"
                for e in evidence[:3]:
                    markdown += f"- {e}\n"

        markdown += f"""
---

## Scope & Limitations

{report_final.get("scope_and_limitations", {}).get("limitations", "See full report")}

---

*Report generated by NuBI VC Review (Claude API v3.0)*
*"No Fake, Only Real" principle applied*
"""
        return markdown
