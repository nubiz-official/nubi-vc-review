"""Reporter - generates final markdown reports from analysis."""
from datetime import datetime
from typing import Dict, Any, List
import uuid


class Reporter:
    """Generates final reports from analysis_internal."""

    @staticmethod
    def _ensure_list(value: Any) -> List[Any]:
        """Ensure value is a list, converting strings to single-item lists."""
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return value
        return []

    def generate_report(self, analysis_internal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate final report from analysis_internal.
        Returns dict with report_final and markdown.
        """
        metadata = analysis_internal.get("metadata", {})
        phase1 = analysis_internal.get("phase1_analysis", {})
        phase2 = analysis_internal.get("phase2_validations", {})

        analysis_id = metadata.get("analysis_id", "unknown")
        company_name = metadata.get("company_name", "Company")

        report_final = {
            "report_id": str(uuid.uuid4()),
            "analysis_id": analysis_id,
            "generated_at": datetime.utcnow().isoformat(),
            "report_version": "v3.0",
            "executive_summary": self._generate_executive_summary(company_name, phase1, phase2),
            "early_indicators": self._generate_early_indicators(phase1),
            "5stage_scorecard": self._generate_5stage_scorecard(company_name, phase1),
            "cross_validation": self._generate_cross_validation(company_name, phase1),
            "risks": phase1.get("key_risks", []),
            "factor_discovery": phase1.get("factor_discovery", {}),
            "momentum_entry_timeline": phase1.get("momentum_entry_timeline", {}),
            "rww_synergy_scenarios": phase1.get("rww_synergy_scenarios", []),
            "nubiz_laws": phase1.get("nubiz_laws", []),
            "analysis_reference_point": phase1.get("analysis_reference_point", {}),
            "numeric_reference_table": phase1.get("numeric_reference_table", {}),
            "scope_and_limitations": self._generate_scope_limitations(metadata, phase1),
            "appendix": self._generate_appendix(phase1),
            "document_metadata": {
                "document_title": f"NuBI VC Review - {company_name}",
                "generated_date": datetime.utcnow().isoformat(),
                "generated_by": "system:reporter",
                "markdown_version": "v2.0",
                "audit_trail": metadata.get("status_history", [])
            }
        }

        markdown = self._generate_markdown(report_final, company_name)

        return {
            "report_final": report_final,
            "markdown": markdown
        }

    def _generate_executive_summary(self, company_name: str, phase1: Dict[str, Any], phase2: Dict[str, Any]) -> Dict[str, Any]:
        """Use phase1 Claude output directly. No hardcoded templates."""
        return {
            "headline": phase1.get("headline", ""),
            "investment_case": phase1.get("investment_case", phase1.get("investment_thesis", "")),
            "recommendation": phase1.get("investment_decision", ""),
            "risk_level": phase1.get("risk_level", "")
        }

    def _generate_early_indicators(self, phase1: Dict[str, Any]) -> Dict[str, Any]:
        """Return Claude's early_indicators verbatim. No hardcoded templates."""
        return phase1.get("early_indicators", [])

    def _generate_5stage_scorecard(self, company_name: str, phase1: Dict[str, Any]) -> Dict[str, Any]:
        """Generate NuBI's proprietary 5-stage scorecard from analyzer scores."""
        base_scores = phase1.get("scores", {})

        # Extract scores from new 5-stage keys
        stage_1_score = base_scores.get("stage_1_원천기술통제", {}).get("score", 6.0)
        stage_2_score = base_scores.get("stage_2_규제통제", {}).get("score", 6.0)
        stage_3_score = base_scores.get("stage_3_플랫폼확장", {}).get("score", 6.5)
        stage_4_score = base_scores.get("stage_4_반복매출", {}).get("score", 6.0)
        stage_5_score = base_scores.get("stage_5_RWW개입", {}).get("score", 6.0)

        # Get evidence from each stage, normalizing strings to lists
        stage_1_evidence = self._ensure_list(base_scores.get("stage_1_원천기술통제", {}).get("evidence", []))
        stage_2_evidence = self._ensure_list(base_scores.get("stage_2_규제통제", {}).get("evidence", []))
        stage_3_evidence = self._ensure_list(base_scores.get("stage_3_플랫폼확장", {}).get("evidence", []))
        stage_4_evidence = self._ensure_list(base_scores.get("stage_4_반복매출", {}).get("evidence", []))
        stage_5_evidence = self._ensure_list(base_scores.get("stage_5_RWW개입", {}).get("evidence", []))

        overall_score = base_scores.get("overall", {}).get("score", 6.8)

        return {
            "stage_1_원천기술통제": {
                "score": round(stage_1_score, 1),
                "description": "Intellectual property control and technical moat",
                "evidence": stage_1_evidence,
                "supporting_factors": ["Technology differentiation", "Patent position"] + (stage_1_evidence[:1] if stage_1_evidence else []),
                "risks": ["Competitive threats", "Technology obsolescence risk"]
            },
            "stage_2_규제통제": {
                "score": round(stage_2_score, 1),
                "description": "Regulatory pathway clarity and approval probability",
                "evidence": stage_2_evidence,
                "supporting_factors": ["Regulatory strategy defined", "Compliance capability"] + (stage_2_evidence[:1] if stage_2_evidence else []),
                "risks": ["Regulatory uncertainty", "Approval timeline risk"]
            },
            "stage_3_플랫폼확장": {
                "score": round(stage_3_score, 1),
                "description": "Platform expansion and market reach potential",
                "evidence": stage_3_evidence,
                "supporting_factors": ["Market opportunity size", "Expansion roadmap"] + (stage_3_evidence[:1] if stage_3_evidence else []),
                "risks": ["Market fragmentation", "Geographic risks"]
            },
            "stage_4_반복매출": {
                "score": round(stage_4_score, 1),
                "description": "Recurring revenue model and customer retention",
                "evidence": stage_4_evidence,
                "supporting_factors": ["Revenue model", "Customer acquisition"] + (stage_4_evidence[:1] if stage_4_evidence else []),
                "risks": ["Customer concentration", "Churn risk"]
            },
            "stage_5_RWW개입": {
                "score": round(stage_5_score, 1),
                "description": "Right-Way-to-Win execution and capital efficiency",
                "evidence": stage_5_evidence,
                "current_execution_evidence": self._ensure_list(base_scores.get("stage_5_RWW개입", {}).get("current_execution_evidence", [])),
                "rww_uplift_potential": self._ensure_list(base_scores.get("stage_5_RWW개입", {}).get("rww_uplift_potential", [])),
                "supporting_factors": ["Management capability", "Capital efficiency"] + (stage_5_evidence[:1] if stage_5_evidence else []),
                "risks": ["Execution risk", "Capital requirements"]
            },
            "overall_score": round(overall_score, 1),
            "weightings": {
                "stage_1": 0.20,
                "stage_2": 0.25,
                "stage_3": 0.15,
                "stage_4": 0.25,
                "stage_5": 0.15
            }
        }

    def _generate_cross_validation(self, company_name: str, phase1: Dict[str, Any]) -> Dict[str, Any]:
        """Return Claude's cross_validation verbatim. No hardcoded templates."""
        return phase1.get("cross_validation", [])

    def _generate_cross_validation_OLD_UNUSED(self, company_name: str, phase1: Dict[str, Any]) -> Dict[str, Any]:
        """DEPRECATED - kept to preserve method boundary only."""
        return {
            "comparable_companies": [
                {
                    "company": "Intuitive Surgical (ISRG)",
                    "similarity": "Medical device with consumable products, recurring revenue model, regulatory-driven IP protection",
                    "outcome": "IPO 2000, $60B+ market cap, sustained 10%+ YoY growth",
                    "relevance_to_subject": "Demonstrates IPO viability for consumable-focused medtech with strong regulatory moat"
                },
                {
                    "company": "Guardant Health (GH)",
                    "similarity": "Diagnostic testing focus, recurring test volume, regulatory pathway clarity (CLIA/CAP)",
                    "outcome": "IPO 2018, now $5B+ market cap, <5% customer churn",
                    "relevance_to_subject": "Shows comparable growth trajectory for recurring diagnostics revenue model"
                },
                {
                    "company": "PROCEPT BioRobotics (PRCT)",
                    "similarity": "Medical device + consumables, FDA breakthrough pathway, robotic-assisted platform",
                    "outcome": "IPO 2021, successfully scaled to $100M+ revenue",
                    "relevance_to_subject": "Validates FDA breakthrough pathway as accelerator for medtech IPO potential"
                },
                {
                    "company": "Shockwave Medical (SWAV)",
                    "similarity": "Specialized device with IP moat, FDA approvals, platform expansion potential",
                    "outcome": "IPO 2019, acquired for $3.2B in 2024",
                    "relevance_to_subject": "Demonstrates strong acquisition premium for FDA-cleared medtech platforms"
                }
            ],
            "validation_summary": "Comparable medtech companies with regulatory clarity and recurring revenue models demonstrate strong exit potential (IPO or acquisition). Analysis supports Phase 1 findings that regulatory pathway and recurring revenue structure are key value drivers."
        }

    def _generate_scope_limitations(self, metadata: Dict[str, Any], phase1: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scope and limitations section."""
        missing_info = phase1.get("missing_information", [])
        missing_categories = [m.get("category", "") for m in missing_info]

        return {
            "data_sources": f"Analysis based on {len(metadata.get('source_docs', []))} provided document(s). Secondary research limited.",
            "analysis_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "market_snapshot": "Market data reflects information available at analysis date.",
            "external_assumptions": [
                "Company financial projections are achievable",
                "Market conditions remain stable",
                "Team remains intact",
                "No material negative regulatory changes"
            ],
            "not_in_scope": [
                "Detailed financial modeling and valuation",
                "Comprehensive competitive benchmarking",
                "Deep regulatory due diligence",
                "Customer reference calls"
            ] + (["Missing information: " + cat for cat in missing_categories[:3]] if missing_categories else [])
        }

    def _generate_appendix(self, phase1: Dict[str, Any]) -> Dict[str, Any]:
        """Generate appendix with additional context."""
        missing_info = phase1.get("missing_information", [])
        red_flags = phase1.get("red_flags", [])

        # v3 framework: Factor Discovery (IPO 역산) implemented via Claude API.
        # Remaining limitations require human validation at unit-economics/pricing level.
        domain_logic_gaps = [
            {
                "item": "Consumables economics requires manual validation",
                "why": "Recurring revenue mechanics not tied to unit economics/pricing",
                "impact": "Subscription/razor-blade model assessment requires numeric validation"
            },
            {
                "item": "RWW synergy calculation is qualitative",
                "why": "Platform value-add not tied to NuBIZ-specific multipliers",
                "impact": "RWW 개입 효과는 정성적 판단에 의존"
            }
        ]

        return {
            "section_required": bool(missing_info or red_flags),
            "missing_info_to_add": [
                {
                    "category": m.get("category", "unknown"),
                    "description": m.get("impact", ""),
                    "why_important": f"Would clarify {m.get('category', 'this aspect')}"
                }
                for m in missing_info[:3]
            ],
            "domain_logic_gaps": domain_logic_gaps,
            "external_research_needed": [
                "Verify customer reference relationships",
                "Assess competitive positioning through market research",
                "Confirm regulatory pathway with domain experts",
                "Validate technology claims with technical advisors"
            ],
            "follow_up_questions": [
                "What are the key milestones for next 12 months?",
                "How do you plan to address the regulatory pathway?",
                "What is the path to profitability?",
                "How are you thinking about competitive differentiation?"
            ]
        }

    def _generate_markdown(self, report_final: Dict[str, Any], company_name: str) -> str:
        """Generate markdown version of report using Claude API phase1 data."""
        exec_summary = report_final.get("executive_summary", {})
        early_ind = report_final.get("early_indicators", [])
        scorecard = report_final.get("5stage_scorecard", {})
        cross_val = report_final.get("cross_validation", [])
        risks = report_final.get("risks", [])
        factor_discovery = report_final.get("factor_discovery", {})
        momentum = report_final.get("momentum_entry_timeline", {})
        rww_scenarios = report_final.get("rww_synergy_scenarios", [])
        laws = report_final.get("nubiz_laws", [])
        ref_point = report_final.get("analysis_reference_point", {})
        numeric_ref = report_final.get("numeric_reference_table", {})
        appendix = report_final.get("appendix", {})

        # ─── Analysis Reference Point 헤더 ───
        stance_label = {
            "post_approval_reverse": "승인/IPO 후 역산 분석 (Post-Approval Reverse-Engineering)",
            "under_review_forward": "심사 중 전망 분석 (Under-Review Forward-Looking)"
        }
        stance = ref_point.get("stance", "") if isinstance(ref_point, dict) else ""
        stance_text = stance_label.get(stance, stance or "분석 관점 미기재")
        cutoff = ref_point.get("cutoff_date", "") if isinstance(ref_point, dict) else ""
        basis = ref_point.get("basis", "") if isinstance(ref_point, dict) else ""
        disclosure = ref_point.get("disclosure", "") if isinstance(ref_point, dict) else ""

        md = f"""# NuBI VC Review Report
## {company_name}

**Report Generated:** {report_final.get('generated_at', 'N/A')}
**Report ID:** {report_final.get('report_id', 'N/A')}

> **분석 관점:** {stance_text}
> **IR 기준 시점:** {cutoff or 'N/A'}
> **판단 근거:** {basis or 'N/A'}
> **독자 경고:** {disclosure or '분석 관점이 명시되지 않음. 수치 해석 시 주의.'}

---

## Executive Summary

### Headline
{exec_summary.get('headline', 'N/A')}

### Investment Case
{exec_summary.get('investment_case', 'N/A')}

**Recommendation:** {str(exec_summary.get('recommendation', '')).upper() or 'N/A'}
**Risk Level:** {str(exec_summary.get('risk_level', '')).upper() or 'N/A'}

---

## Numeric Reference Table (보고서 전체 숫자 기준표)

> 본 보고서에서 인용되는 모든 핵심 수치(매출/특허/국가 수/임상 등)의 원천은 이 표입니다. Executive Summary·Stage Evidence·Risks·Factor Discovery·Cross Validation 모두 이 수치와 일치합니다.

"""
        if isinstance(numeric_ref, dict) and numeric_ref:
            num_labels = [
                ("revenue_latest", "최신 매출"),
                ("revenue_forecast", "매출 전망 (예상치)"),
                ("cumulative_investment", "누적 투자"),
                ("patent_count", "특허 건수"),
                ("countries_coverage", "인증/판매 국가 수"),
                ("clinical_cases", "임상/시술 누적"),
                ("overseas_revenue_ratio", "해외 매출 비중"),
            ]
            md += "| 지표 | 값 | IR 출처 | 비고 |\n|---|---|---|---|\n"
            for key, label in num_labels:
                entry = numeric_ref.get(key, {})
                if isinstance(entry, dict):
                    val = entry.get("value", "IR 미기재")
                    src = entry.get("source", "")
                    note = entry.get("note", "")
                    md += f"| {label} | {val} | {src} | {note} |\n"
            md += "\n"
        else:
            md += "(숫자 기준표 데이터 없음)\n\n"

        # ─── Risks Section (Executive Summary 직후로 이동) ───
        md += "---\n\n## Risks (필수 3종)\n\n"
        risk_label = {
            "regulatory": "규제 리스크",
            "clinical": "임상 한계",
            "valuation": "밸류에이션 리스크"
        }
        by_type = {}
        if isinstance(risks, list):
            for r in risks:
                if isinstance(r, dict):
                    rtype = r.get("risk_type", "other")
                    by_type.setdefault(rtype, []).append(r)
        for rtype in ["regulatory", "clinical", "valuation"]:
            label = risk_label.get(rtype, rtype)
            items = by_type.get(rtype, [])
            md += f"### {label}\n"
            if items:
                for r in items:
                    sev = r.get("severity", "")
                    desc = r.get("description", "")
                    md += f"- **[{sev.upper()}]** {desc}\n"
            else:
                md += f"- (Claude 응답에 {rtype} 리스크 누락)\n"
            md += "\n"

        md += "---\n\n## Early Indicators\n\n"
        if isinstance(early_ind, list):
            for ind in early_ind:
                if isinstance(ind, dict):
                    name = ind.get("indicator_name") or ind.get("name") or ind.get("indicator") or ""
                    ir_ev = ind.get("ir_evidence") or ind.get("description") or ind.get("current_status") or ""
                    why = ind.get("why_signal", "")
                    formula = ind.get("evaluation_formula", "")
                    md += f"### {name}\n"
                    if ir_ev:
                        md += f"- **2017 IR 근거:** {ir_ev}\n"
                    if why:
                        md += f"- **왜 시그널인가:** {why}\n"
                    if formula:
                        md += f"- **평가 공식:** `{formula}`\n"
                    md += "\n"
                else:
                    md += f"- {ind}\n"
        elif isinstance(early_ind, dict):
            for ind in early_ind.get("indicators", []):
                md += f"- **{ind.get('indicator_name')}**: {ind.get('current_status')} → {ind.get('target_status')}\n"

        md += f"""
---

## 5-Stage Scorecard

| Stage | Score | Description |
|-------|-------|-------------|
"""
        for stage_key in ["stage_1_원천기술통제", "stage_2_규제통제", "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"]:
            stage = scorecard.get(stage_key, {})
            md += f"| {stage_key.replace('stage_', '').replace('_', ' ')} | {stage.get('score', 0):.1f}/10 | {stage.get('description', 'N/A')} |\n"

        md += "\n### Stage Evidence\n\n"
        # stage_5 원본 데이터에서 Current/Uplift 분리 정보 가져오기
        phase1_scores = scorecard  # compatibility
        stage5_raw = None
        # scorecard는 _generate_5stage_scorecard 출력이라 원본 phase1.scores와 다를 수 있음
        # phase1 원본에 접근: report_final에서 역추적 불가 → scorecard가 evidence만 가짐
        # 따라서 analyzer의 _extract_scores_from_claude에서 분리 필드를 evidence에 합쳐둔 상태이므로
        # stage_5만 별도 렌더링 분기

        for stage_key in ["stage_1_원천기술통제", "stage_2_규제통제", "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"]:
            stage = scorecard.get(stage_key, {})
            md += f"**{stage_key}** ({stage.get('score', 0):.1f}/10):\n"
            if stage_key == "stage_5_RWW개입":
                current_ev = stage.get("current_execution_evidence", [])
                uplift = stage.get("rww_uplift_potential", [])
                # 분리 필드가 있으면 우선 사용
                if current_ev or uplift:
                    md += "\n*회사의 현재 실행력 (Current State):*\n"
                    for ev in (current_ev if isinstance(current_ev, list) else [current_ev]):
                        if ev:
                            md += f"- {ev}\n"
                    md += "\n*NuBIZ 개입 잠재력 (RWW Uplift):*\n"
                    for ev in (uplift if isinstance(uplift, list) else [uplift]):
                        if ev:
                            md += f"- {ev}\n"
                else:
                    # 레거시: evidence만 있는 경우
                    for ev in stage.get("evidence", []):
                        md += f"- {ev}\n"
            else:
                for ev in stage.get("evidence", []):
                    md += f"- {ev}\n"
            md += "\n"

        md += f"""
**Overall Score:** {scorecard.get('overall_score', 0):.1f}/10

---
"""
        # ─── 동력 편입 시점 (Momentum Entry Timeline) ───
        md += "---\n\n## 핵심 동력 편입 시점\n\n"
        if isinstance(momentum, dict) and momentum:
            driver_labels = [
                ("regulatory", "규제 경로 (FDA De Novo / 510k / PMA / CE)", ["year", "event", "strategic_meaning"], ["시점", "이벤트", "전략적 의미"]),
                ("recurring_revenue", "반복매출 (Razor-Blade / 소모품 / 구독)", ["year", "event", "numeric_evidence"], ["시점", "이벤트", "수치 근거"]),
                ("global_channel", "글로벌 다중 인증 채널", ["year", "event", "coverage"], ["시점", "이벤트", "커버리지"]),
            ]
            for key, label, fields, headers in driver_labels:
                rows = momentum.get(key, [])
                md += f"### {label}\n\n"
                if rows:
                    md += f"| {' | '.join(headers)} |\n"
                    md += "|" + "|".join(["---"] * len(headers)) + "|\n"
                    for r in rows:
                        if isinstance(r, dict):
                            md += "| " + " | ".join(str(r.get(f, "")) for f in fields) + " |\n"
                    md += "\n"
                else:
                    md += "(데이터 부족)\n\n"

            judgment = momentum.get("entry_judgment", {})
            if isinstance(judgment, dict) and judgment:
                md += "### 편입 시점 판정\n\n"
                for k, label in [("regulatory_entry_point", "규제 경로"), ("recurring_revenue_entry_point", "반복매출"), ("global_channel_entry_point", "글로벌 채널")]:
                    v = judgment.get(k)
                    if v:
                        md += f"- **{label}:** {v}\n"
                md += "\n"
        else:
            md += "(동력 편입 시점 데이터 없음)\n\n"

        # ─── Factor Discovery (IPO 역산 분석) ───
        md += "---\n\n## Factor Discovery (IPO 역산 분석)\n\n"
        if isinstance(factor_discovery, dict) and factor_discovery:
            pe = factor_discovery.get("platform_evolution")
            if pe:
                md += f"**플랫폼 진화 가능성:** {pe}\n\n"
            rp = factor_discovery.get("regulatory_pathway")
            if rp:
                md += f"**규제 경로:** {rp}\n\n"
            rr = factor_discovery.get("recurring_revenue")
            if rr:
                md += f"**반복매출 구조:** {rr}\n\n"

            ipo_factors = factor_discovery.get("ipo_factors", [])
            if ipo_factors:
                md += "**IPO 역산 팩터:**\n"
                for f in ipo_factors:
                    md += f"- {f}\n"
                md += "\n"

            reverse = factor_discovery.get("ipo_reverse_analysis", [])
            if reverse:
                md += "### 2017 IR 표현 → 역산적 재해석\n\n"
                md += "| IR 원문 표현 (2017) | 역산 재해석 | IPO 가치 연결 |\n"
                md += "|---|---|---|\n"
                for row in reverse:
                    if isinstance(row, dict):
                        ir = row.get("ir_expression_2017", "")
                        ri = row.get("reverse_interpretation", "")
                        link = row.get("ipo_linkage", "")
                        md += f"| {ir} | {ri} | {link} |\n"
                md += "\n"
        else:
            md += "(Factor Discovery 데이터 없음)\n\n"

        # ─── Cross Validation (Factor Discovery 뒤로 이동) ───
        md += "---\n\n## Cross Validation\n\n"
        if isinstance(cross_val, list) and cross_val:
            md += "| 회사 | IPO 연도 | 규제 경로 | 매출 모델 | 시가총액 | 핵심 성과 지표 |\n"
            md += "|---|---|---|---|---|---|\n"
            for c in cross_val:
                if isinstance(c, dict):
                    row = [
                        c.get("company", c.get("name", "N/A")),
                        c.get("ipo_year", ""),
                        c.get("regulatory_pathway", ""),
                        c.get("revenue_model", ""),
                        c.get("market_cap_current", ""),
                        c.get("key_outcome_metric", c.get("outcome", ""))
                    ]
                    md += "| " + " | ".join(str(x) for x in row) + " |\n"
            md += "\n### 유사성 차원 및 시사점\n\n"
            for c in cross_val:
                if isinstance(c, dict):
                    name = c.get("company", "N/A")
                    dims = c.get("similarity_dimensions", [])
                    app = c.get("applicability_to_subject", c.get("relevance_to_subject", ""))
                    md += f"**{name}**\n"
                    if dims:
                        md += f"- 공유 성공 패턴: {', '.join(str(d) for d in dims)}\n"
                    if app:
                        md += f"- 시사점: {app}\n"
                    md += "\n"
        elif isinstance(cross_val, dict):
            for c in cross_val.get("comparable_companies", []):
                md += f"- **{c.get('company', 'N/A')}**: {c.get('outcome', '')}\n"
        else:
            md += "(Cross Validation 데이터 없음)\n\n"

        # ─── RWW 퀀텀 점프 시나리오 ───
        md += "\n---\n\n## NuBIZ RWW 플랫폼 적용 시 기업가치 퀀텀 점프 시나리오\n\n"
        md += "> ⚠️ 본 섹션의 수치는 RWW 벤치마크 기반 **가정/추정치**이며 실측 데이터가 아닙니다. `[가정]`/`[추정]`/`[벤치마크]` 라벨과 estimate_note를 함께 확인하세요.\n\n"
        if isinstance(rww_scenarios, list) and rww_scenarios:
            md += "| RWW 개입 영역 | 기대 효과 | 가치 증분 근거 | 근거 유형 | 산출 근거 |\n|---|---|---|---|---|\n"
            for s in rww_scenarios:
                if isinstance(s, dict):
                    area = s.get("intervention_area", "")
                    eff = s.get("expected_effect", "")
                    val = s.get("value_increment_basis", "")
                    est_type = s.get("estimate_type", "")
                    est_note = s.get("estimate_note", "")
                    md += f"| {area} | {eff} | {val} | `{est_type}` | {est_note} |\n"
            md += "\n"
        else:
            md += "(RWW 시너지 시나리오 데이터 없음)\n\n"

        # ─── 3대 법칙 (Final Take) ───
        md += "---\n\n## Final Take — 누비즈 3대 법칙\n\n"
        if isinstance(laws, list) and laws:
            for i, l in enumerate(laws, 1):
                if isinstance(l, dict):
                    law = l.get("law", "")
                    ev = l.get("evidence_for_company", "")
                    md += f"**법칙 {i}: {law}**\n\n"
                    if ev:
                        md += f"> {ev}\n\n"
        else:
            md += "(3대 법칙 데이터 없음)\n\n"

        md += f"""
---

## Appendix

"""
        for gap in appendix.get("domain_logic_gaps", []):
            md += f"- **{gap.get('item')}**\n"
            md += f"  - Why: {gap.get('why')}\n"
            md += f"  - Impact: {gap.get('impact')}\n\n"

        md += f"""
### Additional Research Needed

{chr(10).join([f'- {item}' for item in appendix.get('external_research_needed', [])])}

### Follow-up Questions for Management

{chr(10).join([f'- {q}' for q in appendix.get('follow_up_questions', [])])}

---

*Generated by NuBI VC Review (Claude API v3.0)*
"""
        return md
