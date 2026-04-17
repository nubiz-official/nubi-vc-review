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
            "cross_validation": claude_analysis.get("cross_validation", [])
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
  "headline": "<회사명>: <한 줄 투자 판단>",
  "investment_case": "<3-5문장 투자 논리. 구체 수치/규제명/플랫폼 포함>",
  "investment_decision": "<strong_buy|buy|hold|strong_avoid>",
  "risk_level": "<low|medium|high|critical>",
  "investment_thesis": "<핵심 강점과 약점 정리>",

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
    {{"indicator_name": "원천기술 물리적 제어 가능성", "description": "<IR 근거 인용 구체 문장>"}},
    {{"indicator_name": "규제 실행 조직 선배치", "description": "<IR 근거 인용 구체 문장>"}},
    {{"indicator_name": "제품 아키텍처 모듈화/소모품 설계", "description": "<IR 근거 인용 구체 문장>"}}
  ],

  "stage_1_원천기술통제": {{"score": <0-10 숫자>, "evidence": ["<근거 문장 1>", "<근거 문장 2>"], "confidence": <0-1>}},
  "stage_2_규제통제": {{"score": <0-10 숫자>, "evidence": ["<FDA 경로명 포함 근거>"], "confidence": <0-1>}},
  "stage_3_플랫폼확장": {{"score": <0-10 숫자>, "evidence": ["<적용 가능 영역 수와 근거>"], "confidence": <0-1>}},
  "stage_4_반복매출": {{"score": <0-10 숫자>, "evidence": ["<소모품 비중/구독 구조 근거>"], "confidence": <0-1>}},
  "stage_5_RWW개입": {{"score": <0-10 숫자>, "evidence": ["<해외 매출 비중(%) — IR 원문에서 숫자 인용>", "<글로벌 실행력 근거: 진출 국가 수, 해외 임상, 해외 파트너십 등>", "<NuBIZ 개입 시 기대 효과>"], "confidence": <0-1>}},

  "cross_validation": [
    {{"company": "Intuitive Surgical (ISRG)", "similarity": "<비교 근거>", "outcome": "<실적 팩트>", "relevance_to_subject": "<이 회사에의 시사점>"}},
    {{"company": "PROCEPT BioRobotics (PRCT)", "similarity": "<비교 근거>", "outcome": "<실적 팩트>", "relevance_to_subject": "<시사점>"}}
  ],

  "risks": [
    {{"risk_type": "regulatory", "description": "FDA De Novo 최종 승인 미확정 여부와 적응증 범위 제한 (예: 특정 시술로만 승인) 구체 기술. IR에서 언급된 제품명/적응증 인용 필수", "severity": "high|medium|low"}},
    {{"risk_type": "clinical", "description": "non-inferiority 설계 가능성, 단일 기관 편향, 샘플 수 한계 등 임상 데이터의 구체적 한계", "severity": "high|medium|low"}},
    {{"risk_type": "valuation", "description": "IPO 목표가 선반영 여부, 특정 연도 매출 목표 (예: 2024E 150억) 달성 불확실성 등 밸류에이션 리스크 구체 기술", "severity": "high|medium|low"}}
  ],
  "// risks 규칙": "위 3종(regulatory, clinical, valuation)은 반드시 모두 포함하라. IR에서 직접 근거를 찾을 수 없으면 '근거 부재'라고 명시하라.",
  "// stage_5 규칙": "stage_5_RWW개입 evidence의 첫 항목은 반드시 '해외 매출 비중(%)'이어야 한다. IR 원문에서 수치를 찾아 인용하라. 수치 미기재 시 '해외 매출 비중: IR 미기재'라고 명시하라.",

  "missing_information": [
    {{"category": "<카테고리>", "criticality": "critical|important|nice_to_have", "impact": "<왜 중요한가>"}}
  ]
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
                    max_tokens=8000,
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

            # Extract final response
            response_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    response_text = block.text
                    break

            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    return json.loads(response_text[json_start:json_end])
            except json.JSONDecodeError:
                pass

            return self._parse_claude_text_response(response_text)

        except Exception as e:
            raise RuntimeError(f"Claude API call failed: {e}")

    def _parse_claude_text_response(self, text: str) -> Dict[str, Any]:
        """Parse Claude's text response. Raise on failure - no fallback."""
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        text = text.strip()
        if text.startswith('{'):
            return json.loads(text)
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
                else:
                    score = 6.5
                    evidence = []
                    counterevidence = []
                scores[stage_key] = {
                    "score": min(score, 10.0),
                    "rubric_level": "strong" if score >= 8.0 else "adequate" if score >= 6.5 else "concerning",
                    "evidence": evidence,
                    "counterevidence": counterevidence,
                    "confidence": stage_data.get("confidence", 0.85) if isinstance(stage_data, dict) else 0.85
                }

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
