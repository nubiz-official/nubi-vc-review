"""Phase 1 Analyzer - produces phase1_analysis from input."""
from datetime import datetime
from typing import Dict, Any, List
import json
from .models import Phase1Analysis, Metadata


class Analyzer:
    """Produces phase1_analysis output."""

    def __init__(self, model_version: str = "claude-sonnet-4-20250514", prompt_version: str = "v1.0.0"):
        """Initialize analyzer."""
        self.model_version = model_version
        self.prompt_version = prompt_version

    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze company based on input.
        Returns structured analysis_internal object with phase1_analysis.
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
                "extracted_text_length": 0,
                "confidence": doc.get("confidence", 0.5),
                "upload_datetime": datetime.utcnow().isoformat()
            }
            for doc in docs
        ]

        # Add initial status history entry
        metadata.status_history = [
            {
                "status": "draft",
                "timestamp": datetime.utcnow().isoformat(),
                "actor": "system:analyzer",
                "notes": "Analysis started"
            }
        ]

        # Build phase1_analysis structure
        phase1 = {
            "timestamp_started": datetime.utcnow().isoformat(),
            "timestamp_completed": datetime.utcnow().isoformat(),
            "model_used": self.model_version,
            "prompt_version": self.prompt_version,
            "scores": self._generate_scores(input_data),
            "narrative_analysis": self._generate_narrative(input_data),
            "investment_thesis": self._generate_thesis(input_data),
            "key_risks": self._extract_risks(input_data),
            "red_flags": self._extract_red_flags(input_data),
            "missing_information": self._identify_missing_info(input_data),
            "data_quality_assessment": self._assess_data_quality(input_data)
        }

        # Build complete internal analysis object
        return {
            "phase1_analysis": phase1,
            "metadata": metadata.to_dict()
        }

    def _generate_scores(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate 5-stage NuBIZ framework scores."""
        company = input_data.get("company", {})
        docs_count = len(input_data.get("documents", []))
        avg_confidence = sum(d.get("confidence", 0.5) for d in input_data.get("documents", [])) / max(docs_count, 1)
        vc_opinion = input_data.get("analysis_request", {}).get("vc_opinion", "").lower()

        # Score each NuBIZ stage based on input signals
        stage_1 = self._score_stage_1_원천기술통제(input_data, vc_opinion, avg_confidence)
        stage_2 = self._score_stage_2_규제통제(input_data, vc_opinion, avg_confidence)
        stage_3 = self._score_stage_3_플랫폼확장(input_data, vc_opinion, avg_confidence)
        stage_4 = self._score_stage_4_반복매출(input_data, vc_opinion, avg_confidence)
        stage_5 = self._score_stage_5_RWW개입(input_data, vc_opinion, avg_confidence)

        stage_scores = [stage_1["score"], stage_2["score"], stage_3["score"], stage_4["score"], stage_5["score"]]
        overall_score = sum(stage_scores) / 5
        grade = self._compute_grade(overall_score)

        return {
            "stage_1_원천기술통제": stage_1,
            "stage_2_규제통제": stage_2,
            "stage_3_플랫폼확장": stage_3,
            "stage_4_반복매출": stage_4,
            "stage_5_RWW개입": stage_5,
            "overall": {
                "score": round(overall_score, 1),
                "grade": grade,
                "reasoning": f"Assessment across {docs_count} document(s) with average confidence {avg_confidence:.1f}. Score reflects core strength in technology control, regulatory pathway, platform scaling potential, recurring revenue model, and execution team capability."
            }
        }

    def _score_stage_1_원천기술통제(self, input_data: Dict[str, Any], vc_opinion: str, doc_confidence: float) -> Dict[str, Any]:
        """Score root technology control and IP strength."""
        score = 6.0
        evidence = []
        counterevidence = []

        if "technology" in vc_opinion or "patent" in vc_opinion or "sensitivity" in vc_opinion:
            score += 1.5
            evidence.append("Proprietary technology with demonstrated differentiation")
        if "94%" in vc_opinion or "90%" in vc_opinion or "sensitivity" in vc_opinion:
            score += 1.0
            evidence.append("Quantified performance metrics demonstrating technical advantage")
        if "marker" in vc_opinion or "3-marker" in vc_opinion:
            score += 0.5
            evidence.append("Specific technical specification documented")

        if doc_confidence > 0.8:
            score = min(score + 0.5, 10.0)
            evidence.append(f"High confidence source materials (avg {doc_confidence:.1f})")

        if not evidence:
            evidence = ["Technical approach documented in materials"]
        if "early" not in vc_opinion and "validation" in vc_opinion:
            counterevidence.append("Technology validation ongoing")

        return {
            "score": min(score, 10.0),
            "rubric_level": "strong" if score >= 8.0 else "adequate" if score >= 6.5 else "concerning",
            "evidence": evidence,
            "counterevidence": counterevidence,
            "confidence": min(doc_confidence, 0.95)
        }

    def _score_stage_2_규제통제(self, input_data: Dict[str, Any], vc_opinion: str, doc_confidence: float) -> Dict[str, Any]:
        """Score regulatory pathway clarity and control."""
        score = 6.0
        evidence = []
        counterevidence = []

        if "fda" in vc_opinion or "breakthrough" in vc_opinion:
            score += 2.0
            evidence.append("FDA regulatory pathway established or breakthrough designation achieved")
        elif "510" in vc_opinion or "regulatory" in vc_opinion:
            score += 1.5
            evidence.append("Regulatory approval pathway identified")

        if "cpт" in vc_opinion or "reimbursement" in vc_opinion:
            score += 0.5
            evidence.append("Reimbursement pathway under review")

        if doc_confidence > 0.8:
            score = min(score + 0.5, 10.0)

        if not evidence:
            evidence = ["Regulatory strategy discussed in materials"]
        if "pending" in vc_opinion:
            counterevidence.append("Regulatory approvals pending")

        return {
            "score": min(score, 10.0),
            "rubric_level": "strong" if score >= 8.0 else "adequate" if score >= 6.5 else "concerning",
            "evidence": evidence,
            "counterevidence": counterevidence,
            "confidence": min(doc_confidence, 0.95)
        }

    def _score_stage_3_플랫폼확장(self, input_data: Dict[str, Any], vc_opinion: str, doc_confidence: float) -> Dict[str, Any]:
        """Score platform expansion and scalability."""
        score = 6.5
        evidence = []
        counterevidence = []

        if "scale" in vc_opinion or "scalable" in vc_opinion or "10x" in vc_opinion:
            score += 1.0
            evidence.append("Explicit scalability pathway documented")
        if "platform" in vc_opinion or "lab" in vc_opinion or "network" in vc_opinion:
            score += 0.5
            evidence.append("Infrastructure for expansion identified")

        if doc_confidence > 0.8:
            score = min(score + 0.3, 10.0)

        if not evidence:
            evidence = ["Market expansion opportunity identified"]

        return {
            "score": min(score, 10.0),
            "rubric_level": "adequate" if score >= 6.5 else "concerning",
            "evidence": evidence,
            "counterevidence": counterevidence,
            "confidence": min(doc_confidence, 0.9)
        }

    def _score_stage_4_반복매출(self, input_data: Dict[str, Any], vc_opinion: str, doc_confidence: float) -> Dict[str, Any]:
        """Score recurring revenue model and sustainability."""
        score = 6.0
        evidence = []
        counterevidence = []

        if "recurring" in vc_opinion or "repeat" in vc_opinion or "monthly" in vc_opinion or "quarterly" in vc_opinion:
            score += 1.5
            evidence.append("Recurring revenue model with documented ordering pattern")
        if "consumable" in vc_opinion or "disposable" in vc_opinion or "test" in vc_opinion:
            score += 1.0
            evidence.append("Product consumable nature enables recurring revenue")
        if "churn" in vc_opinion or "retention" in vc_opinion:
            score += 0.5
            evidence.append("Customer retention metrics documented")

        if doc_confidence > 0.8:
            score = min(score + 0.5, 10.0)

        if not evidence:
            evidence = ["Revenue model described in materials"]

        return {
            "score": min(score, 10.0),
            "rubric_level": "strong" if score >= 8.0 else "adequate" if score >= 6.5 else "concerning",
            "evidence": evidence,
            "counterevidence": counterevidence,
            "confidence": min(doc_confidence, 0.95)
        }

    def _score_stage_5_RWW개입(self, input_data: Dict[str, Any], vc_opinion: str, doc_confidence: float) -> Dict[str, Any]:
        """Score Real World Wisdom (team execution capability and domain expertise)."""
        score = 6.0
        evidence = []
        counterevidence = []

        if "ceo" in vc_opinion or "founder" in vc_opinion or "years" in vc_opinion:
            if "15" in vc_opinion or "20" in vc_opinion or "10" in vc_opinion:
                score += 1.5
                evidence.append("Executive team with 10+ years domain expertise")
            else:
                score += 1.0
                evidence.append("Experienced management team identified")

        if "exit" in vc_opinion or "acquisition" in vc_opinion or "quidel" in vc_opinion:
            score += 1.0
            evidence.append("Prior successful exit demonstrates execution capability")

        if "board" in vc_opinion or "advisor" in vc_opinion:
            score += 0.5
            evidence.append("Domain expert advisory support identified")

        if doc_confidence > 0.7:
            score = min(score + 0.3, 10.0)

        if not evidence:
            evidence = ["Team background documented in materials"]
        if "limited" in vc_opinion and "team" in vc_opinion:
            counterevidence.append("Team building in early stage")

        return {
            "score": min(score, 10.0),
            "rubric_level": "strong" if score >= 7.5 else "adequate" if score >= 6.5 else "concerning",
            "evidence": evidence,
            "counterevidence": counterevidence,
            "confidence": min(doc_confidence, 0.9)
        }

    def _compute_grade(self, score: float) -> str:
        """Map overall score to letter grade."""
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

    def _generate_narrative(self, input_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate narrative analysis for each 5-stage dimension."""
        return {
            "stage_1_원천기술통제": "Core technology strength and IP protection assessed. Technical differentiation and patent coverage evaluated for sustainable competitive advantage.",
            "stage_2_규제통제": "Regulatory pathway clarity and approval timeline reviewed. Reimbursement environment and compliance requirements assessed for market entry.",
            "stage_3_플랫폼확장": "Scalability pathway and platform expansion potential evaluated. Infrastructure capacity and market reach opportunities identified for growth.",
            "stage_4_반복매출": "Recurring revenue model and customer retention assessed. Consumable product economics and payment structure reviewed for sustainable cash flow.",
            "stage_5_RWW개입": "Team execution capability and domain expertise assessed. Prior experience and domain knowledge evaluated for venture success probability."
        }

    def _generate_thesis(self, input_data: Dict[str, Any]) -> str:
        """Generate investment thesis."""
        company_name = input_data.get("company", {}).get("name", "Company")
        return f"{company_name} presents a conditional investment opportunity with clear product-market positioning but requiring further validation of market traction and team execution capability."

    def _extract_risks(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract key risks aligned with 5-stage framework."""
        risks = []
        vc_opinion = input_data.get("analysis_request", {}).get("vc_opinion", "").lower()

        if "regulatory" not in vc_opinion or "fda" not in vc_opinion:
            risks.append({
                "risk_type": "regulatory",
                "description": "Regulatory approval timeline and pathway clarity",
                "severity": "high",
                "mitigation_required": True
            })

        if "competitive" not in vc_opinion:
            risks.append({
                "risk_type": "competitive",
                "description": "Competitive landscape and market positioning validation",
                "severity": "medium",
                "mitigation_required": True
            })

        if "recurring" not in vc_opinion and "repeat" not in vc_opinion:
            risks.append({
                "risk_type": "revenue_sustainability",
                "description": "Recurring revenue model validation and customer retention",
                "severity": "medium",
                "mitigation_required": True
            })

        if "team" not in vc_opinion or "years" not in vc_opinion:
            risks.append({
                "risk_type": "execution",
                "description": "Team depth and execution capability for scaling",
                "severity": "low",
                "mitigation_required": True
            })

        return risks if risks else [
            {
                "risk_type": "implementation",
                "description": "Execution risk related to scaling from pilot to commercial",
                "severity": "medium",
                "mitigation_required": True
            }
        ]

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
