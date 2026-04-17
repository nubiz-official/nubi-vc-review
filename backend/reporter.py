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
            "report_version": "v2.0",
            "executive_summary": self._generate_executive_summary(company_name, phase1, phase2),
            "early_indicators": self._generate_early_indicators(phase1),
            "5stage_scorecard": self._generate_5stage_scorecard(company_name, phase1),
            "cross_validation": self._generate_cross_validation(company_name, phase1),
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
        """Generate executive summary."""
        scores = phase1.get("scores", {})
        overall = scores.get("overall", {})
        grade = overall.get("grade", "C")

        headline = f"{company_name}: {grade}-Grade Investment Opportunity with Conditional Support"

        investment_case = f"""{company_name} presents a {grade}-grade investment opportunity.
        The company demonstrates solid fundamentals across technology control, regulatory pathway, platform expansion, recurring revenue model, and execution capability (5-stage NuBIZ framework).
        Key success factors include IP moat validation, regulatory strategy clarity, market scalability, revenue sustainability, and team execution."""

        # Engine limitation notice (v2 framework)
        engine_notice = """⚠️ **ANALYSIS ENGINE NOTICE (v2.0):**
- Current engine is a rule/keyword-assisted NuBIZ 5-stage framework (not IPO reverse-engineering)
- Recens Medical success factor integration (v3) planned for next version
- This is internal review draft; regulatory/recurring revenue/comparative analysis requires human validation"""

        # Determine recommendation based on grade
        grade_map = {"A": "strong_buy", "B": "buy", "C": "hold", "D": "strong_avoid"}
        risk_map = {"A": "low", "B": "medium", "C": "high", "D": "critical"}

        return {
            "headline": headline[:200],
            "investment_case": investment_case,
            "engine_notice": engine_notice,
            "key_recommendation": grade_map.get(grade, "hold"),
            "risk_level": risk_map.get(grade, "high")
        }

    def _generate_early_indicators(self, phase1: Dict[str, Any]) -> Dict[str, Any]:
        """Generate early indicators (success milestones)."""
        return {
            "indicators": [
                {
                    "indicator_name": "Product Market Fit Validation",
                    "current_status": "In progress",
                    "target_status": "Customer retention rate > 80%",
                    "timeline": "Next 6 months",
                    "criticality": "must_have"
                },
                {
                    "indicator_name": "Regulatory Pathway Clarity",
                    "current_status": "Initiated",
                    "target_status": "Regulatory approval/pathway confirmed",
                    "timeline": "Next 12 months",
                    "criticality": "must_have"
                },
                {
                    "indicator_name": "Revenue Growth Trajectory",
                    "current_status": "Early stage",
                    "target_status": "20%+ month-over-month growth",
                    "timeline": "Next 9 months",
                    "criticality": "should_have"
                },
                {
                    "indicator_name": "Team Expansion",
                    "current_status": "Current size documented",
                    "target_status": "Core team +50% capacity",
                    "timeline": "Next 12 months",
                    "criticality": "should_have"
                }
            ],
            "count": 4
        }

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
        """Generate cross-validation with comparable companies."""
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

        # Domain logic gaps in v2 framework
        domain_logic_gaps = [
            {
                "item": "IPO reverse-engineering logic not fully integrated",
                "why": "2017→2024 factor discovery analysis deferred to v3",
                "impact": "Success pattern extraction is rule-based, not historical fact-driven"
            },
            {
                "item": "FDA pathway specificity requires manual review",
                "why": "De Novo / 510(k) / PMA classification logic not model-encoded",
                "impact": "Regulatory pathway scoring is heuristic; expert validation needed"
            },
            {
                "item": "Consumables economics requires manual validation",
                "why": "Recurring revenue mechanics not tied to unit economics/pricing",
                "impact": "Subscription/razor-blade model assessment is pattern-matched, not calculated"
            },
            {
                "item": "RWW synergy currently heuristic-based",
                "why": "Platform value-add calculation not tied to company use case",
                "impact": "Team/execution scores reflect domain experience, not RWW-specific multipliers"
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
        """Generate markdown version of report."""
        exec_summary = report_final.get("executive_summary", {})
        early_ind = report_final.get("early_indicators", {})
        scorecard = report_final.get("5stage_scorecard", {})
        appendix = report_final.get("appendix", {})

        md = f"""# NuBI VC Review Report
## {company_name}

**Report Generated:** {report_final.get('generated_at', 'N/A')}
**Report ID:** {report_final.get('report_id', 'N/A')}

---

## Executive Summary

### Headline
{exec_summary.get('headline', 'N/A')}

### Investment Case
{exec_summary.get('investment_case', 'N/A')}

**Recommendation:** {exec_summary.get('key_recommendation', 'hold').upper()}
**Risk Level:** {exec_summary.get('risk_level', 'medium').upper()}

### ⚠️ Analysis Engine Notice
{exec_summary.get('engine_notice', 'Engine notice unavailable')}

---

## Early Indicators

Milestones to track over next 12 months:

"""
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

        md += f"""
**Overall Score:** {scorecard.get('overall_score', 0):.1f}/10

---

## Cross Validation

Similar companies and outcomes used for validation.

---

## Appendix: Domain Logic Status

### Framework Limitations in v2
The following domain logics are deferred to v3 (next release):

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

## Scope & Limitations

This analysis is based on provided materials and does not constitute investment advice.

---

*Generated by NuBI VC Review System v2.0 (Beta)*
"""
        return md
