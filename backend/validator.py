"""Phase 2 Validator - validates VC opinion against phase1_analysis."""
from datetime import datetime
from typing import Dict, Any, List


class Validator:
    """Validates VC opinion and produces phase2_validations."""

    def validate(self, analysis_internal: Dict[str, Any], vc_opinion: str = "") -> Dict[str, Any]:
        """
        Validate VC opinion against phase1_analysis.
        Returns phase2_validations object.
        """
        phase1 = analysis_internal.get("phase1_analysis", {})

        # Extract claims from VC opinion
        claims = self._extract_claims(vc_opinion)

        # Assess each claim against phase1 analysis
        claim_assessments = self._assess_claims(claims, phase1)

        # Generate final recommendation
        final_recommendation = self._generate_recommendation(claim_assessments, phase1)

        # Determine investment decision
        investment_decision = self._determine_decision(claim_assessments, phase1)

        return {
            "phase2_validations": {
                "vc_opinion_summary": vc_opinion[:500] if vc_opinion else "No VC opinion provided",
                "claims_extracted": claims,
                "claim_assessment": claim_assessments,
                "final_recommendation": final_recommendation,
                "investment_decision": investment_decision
            },
            "validator_flags": self._generate_validator_flags(claim_assessments, phase1),
            "ready_for_validation": len(self._generate_validator_flags(claim_assessments, phase1)) <= 3
        }

    def _extract_claims(self, vc_opinion: str) -> List[Dict[str, Any]]:
        """Extract distinct claims from VC opinion."""
        if not vc_opinion:
            return []

        # Split by common claim patterns
        claims = []
        sentences = [s.strip() for s in vc_opinion.split('.') if s.strip()]

        for i, sentence in enumerate(sentences[:5]):  # Max 5 claims
            claims.append({
                "claim_id": f"claim_{i+1}",
                "claim_text": sentence,
                "underlying_assumption": self._extract_assumption(sentence)
            })

        return claims

    def _extract_assumption(self, claim_text: str) -> str:
        """Extract underlying assumption from claim."""
        if not claim_text:
            return "Unknown assumption"

        # Simplified assumption extraction
        if "will" in claim_text.lower():
            return "Company will achieve projected performance"
        elif "have" in claim_text.lower() or "has" in claim_text.lower():
            return "Stated capabilities are accurate"
        elif "better" in claim_text.lower() or "best" in claim_text.lower():
            return "Competitive advantage is sustainable"
        else:
            return "Claim-specific assumption applies"

    def _assess_claims(self, claims: List[Dict[str, Any]], phase1: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess each claim against phase1 analysis."""
        assessments = []
        scores = phase1.get("scores", {})
        overall_score = scores.get("overall", {}).get("score", 6.0)

        for claim in claims:
            affected_stages = self._identify_affected_stages(claim, scores)
            verdict = self._determine_verdict(claim, phase1, affected_stages)
            confidence = self._calculate_confidence(verdict, scores, affected_stages)

            assessments.append({
                "claim_id": claim["claim_id"],
                "claim_text": claim.get("claim_text", ""),
                "affected_stages": affected_stages,
                "verdict": verdict,
                "phase1_evidence": self._find_supporting_evidence(claim, phase1, affected_stages),
                "reasoning": self._generate_reasoning(claim, verdict, affected_stages),
                "confidence": confidence
            })

        return assessments

    def _identify_affected_stages(self, claim: Dict[str, Any], scores: Dict[str, Any]) -> List[str]:
        """Identify which 5-stage axes the claim affects."""
        claim_text = claim.get("claim_text", "").lower()
        stages = []

        # Stage 1: Root technology
        if any(word in claim_text for word in ["technology", "patent", "ip", "innovation", "differentiation", "sensitivity", "marker", "algorithm"]):
            stages.append("stage_1_원천기술통제")

        # Stage 2: Regulatory
        if any(word in claim_text for word in ["fda", "regulatory", "approval", "clearance", "breakthrough", "510", "cpt", "reimbursement"]):
            stages.append("stage_2_규제통제")

        # Stage 3: Platform expansion
        if any(word in claim_text for word in ["scale", "platform", "infrastructure", "expand", "scalable", "lab", "network", "capacity"]):
            stages.append("stage_3_플랫폼확장")

        # Stage 4: Recurring revenue
        if any(word in claim_text for word in ["recurring", "repeat", "revenue", "consumable", "disposable", "monthly", "quarterly", "churn", "retention"]):
            stages.append("stage_4_반복매출")

        # Stage 5: Team/RWW
        if any(word in claim_text for word in ["team", "ceo", "founder", "experience", "exit", "acquisition", "leadership", "expertise", "background", "board"]):
            stages.append("stage_5_RWW개입")

        return stages if stages else ["stage_overall"]

    def _determine_verdict(self, claim: Dict[str, Any], phase1: Dict[str, Any], affected_stages: List[str] = None) -> str:
        """Determine verdict for a claim based on affected stages."""
        if affected_stages is None:
            affected_stages = []

        claim_text = claim.get("claim_text", "").lower()
        scores = phase1.get("scores", {})

        # If claim maps to specific stages, check those stage scores
        if affected_stages and affected_stages[0] != "stage_overall":
            stage_scores = [scores.get(stage, {}).get("score", 5) for stage in affected_stages if stage in scores]
            if stage_scores:
                avg_stage_score = sum(stage_scores) / len(stage_scores)
                if avg_stage_score >= 8.0:
                    return "supported"
                elif avg_stage_score >= 7.0:
                    return "partially_supported"
                elif avg_stage_score >= 6.0:
                    return "partially_supported"
                else:
                    return "contradicted"

        # Fallback to general assessment
        if any(word in claim_text for word in ["strong", "excellent", "leader"]):
            avg_score = sum(s.get("score", 5) for s in scores.values()) / len(scores) if scores else 5
            if avg_score > 7:
                return "supported"
            else:
                return "partially_supported"
        elif any(word in claim_text for word in ["weak", "poor", "risk"]):
            risks = phase1.get("key_risks", [])
            if len(risks) > 2:
                return "supported"
            else:
                return "partially_supported"
        else:
            return "partially_supported"

    def _calculate_confidence(self, verdict: str, scores: Dict[str, Any], affected_stages: List[str] = None) -> float:
        """Calculate confidence in verdict based on affected stages."""
        if affected_stages is None:
            affected_stages = []

        base_confidence = {
            "supported": 0.85,
            "partially_supported": 0.65,
            "contradicted": 0.70,
            "insufficient_evidence": 0.40
        }

        confidence = base_confidence.get(verdict, 0.50)

        # Boost confidence if multiple stage scores align
        if affected_stages and affected_stages[0] != "stage_overall":
            stage_scores = [scores.get(stage, {}).get("score", 5) for stage in affected_stages if stage in scores]
            if stage_scores:
                consistency = len(stage_scores) / max(len(affected_stages), 1)
                if consistency > 0.66:
                    confidence += 0.1

        return min(confidence, 1.0)

    def _find_supporting_evidence(self, claim: Dict[str, Any], phase1: Dict[str, Any], affected_stages: List[str] = None) -> str:
        """Find phase1 evidence relevant to claim."""
        if affected_stages is None:
            affected_stages = []

        scores = phase1.get("scores", {})
        evidence_parts = []

        # Gather evidence from affected stages
        if affected_stages and affected_stages[0] != "stage_overall":
            for stage in affected_stages:
                if stage in scores and scores[stage].get("evidence"):
                    evidence_parts.extend(scores[stage]["evidence"][:1])
        else:
            # General evidence gathering
            for dim, score_obj in scores.items():
                if dim != "overall" and score_obj.get("evidence"):
                    evidence_parts.extend(score_obj["evidence"][:1])

        return "; ".join(evidence_parts[:2]) if evidence_parts else "See overall investment thesis"

    def _generate_reasoning(self, claim: Dict[str, Any], verdict: str, affected_stages: List[str] = None) -> str:
        """Generate reasoning for verdict with stage awareness."""
        if affected_stages is None:
            affected_stages = []

        stage_names = {
            "stage_1_원천기술통제": "root technology control",
            "stage_2_규제통제": "regulatory pathway",
            "stage_3_플랫폼확장": "platform expansion",
            "stage_4_반복매출": "recurring revenue",
            "stage_5_RWW개입": "team execution"
        }

        stage_text = ""
        if affected_stages and affected_stages[0] != "stage_overall":
            readable_stages = [stage_names.get(s, s) for s in affected_stages]
            stage_text = f" (affects: {', '.join(readable_stages)})"

        reasoning_map = {
            "supported": f"Phase 1 analysis supports this claim with evidence{stage_text}.",
            "partially_supported": f"Claim has some basis in Phase 1 analysis but requires further validation{stage_text}.",
            "contradicted": f"Phase 1 analysis raises concerns about this claim{stage_text}.",
            "insufficient_evidence": f"Insufficient data in Phase 1 analysis to validate this claim{stage_text}."
        }
        return reasoning_map.get(verdict, "Assessment inconclusive.")

    def _generate_recommendation(self, claim_assessments: List[Dict[str, Any]], phase1: Dict[str, Any]) -> str:
        """Generate final validation recommendation."""
        if not claim_assessments:
            return "No VC opinion provided. Proceed with Phase 1 analysis recommendation."

        supported_count = sum(1 for a in claim_assessments if a["verdict"] == "supported")
        total_claims = len(claim_assessments)

        if supported_count >= total_claims * 0.75:
            return "VC opinion is well-supported by Phase 1 analysis. Recommend moving to review stage."
        elif supported_count >= total_claims * 0.5:
            return "VC opinion is partially supported. Recommend addressing gaps before review stage."
        else:
            return "VC opinion requires significant additional validation. Further investigation recommended."

    def _determine_decision(self, claim_assessments: List[Dict[str, Any]], phase1: Dict[str, Any]) -> str:
        """Determine overall investment decision."""
        if not claim_assessments:
            scores = phase1.get("scores", {})
            avg_score = sum(s.get("score", 5) for s in scores.values()) / len(scores) if scores else 5
            if avg_score >= 8:
                return "strong_support"
            elif avg_score >= 7:
                return "support"
            elif avg_score >= 5:
                return "neutral"
            else:
                return "caution"

        supported_count = sum(1 for a in claim_assessments if a["verdict"] == "supported")
        contradicted_count = sum(1 for a in claim_assessments if a["verdict"] == "contradicted")
        total = len(claim_assessments)

        if supported_count > total * 0.75:
            return "strong_support"
        elif supported_count > total * 0.5:
            return "support"
        elif contradicted_count > total * 0.3:
            return "strong_caution"
        else:
            return "neutral"

    def _generate_validator_flags(self, claim_assessments: List[Dict[str, Any]], phase1: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate validator flags for human review with risk detection."""
        flags = []
        scores = phase1.get("scores", {})
        vc_opinion = ""
        for claim in claim_assessments:
            if "claim_text" in claim:
                vc_opinion += " " + claim.get("claim_text", "").lower()

        # Check for insufficient evidence
        insufficient = sum(1 for a in claim_assessments if a["verdict"] == "insufficient_evidence")
        if insufficient > 0:
            flags.append({
                "flag_type": "missing_field",
                "description": f"{insufficient} claim(s) lack supporting evidence",
                "severity": "medium",
                "must_resolve": False
            })

        # Check for contradictions
        contradicted = sum(1 for a in claim_assessments if a["verdict"] == "contradicted")
        if contradicted > 0:
            flags.append({
                "flag_type": "inconsistency",
                "description": f"{contradicted} claim(s) contradict Phase 1 findings",
                "severity": "high",
                "must_resolve": True
            })

        # Check missing information impact
        missing = phase1.get("missing_information", [])
        critical_missing = sum(1 for m in missing if m.get("criticality") == "critical")
        if critical_missing > 0:
            flags.append({
                "flag_type": "critical_gap",
                "description": f"{critical_missing} critical information gap(s) identified",
                "severity": "high",
                "must_resolve": True
            })

        # RISK DETECTION: Strong cases should still have concerns
        # Check for regulatory risk in medtech/biotech
        stage_2_score = scores.get("stage_2_규제통제", {}).get("score", 0)
        if stage_2_score >= 8.0 and "limitation" not in vc_opinion and "indication" not in vc_opinion:
            flags.append({
                "flag_type": "regulatory_assumption",
                "description": "High regulatory score assumed but specific indication/limitation scope not mentioned in opinion",
                "severity": "medium",
                "must_resolve": False
            })

        # Check for non-inferiority / comparative efficacy risk
        if any(word in vc_opinion for word in ["efficacy", "sensitivity", "performance", "superiority"]):
            if "inferiority" not in vc_opinion and "comparison" not in vc_opinion:
                flags.append({
                    "flag_type": "comparative_claim_gap",
                    "description": "Product performance claims present but comparative non-inferiority data not mentioned",
                    "severity": "medium",
                    "must_resolve": False
                })

        # Check for recurring revenue sustainability
        stage_4_score = scores.get("stage_4_반복매출", {}).get("score", 0)
        if stage_4_score >= 8.0 and "churn" not in vc_opinion and "retention" not in vc_opinion:
            flags.append({
                "flag_type": "retention_validation",
                "description": "Strong recurring revenue score but customer retention/churn metrics not explicitly discussed",
                "severity": "low",
                "must_resolve": False
            })

        # Check for execution risk even in strong teams
        stage_5_score = scores.get("stage_5_RWW개입", {}).get("score", 0)
        if stage_5_score >= 7.0 and "scaling" not in vc_opinion:
            flags.append({
                "flag_type": "team_scaling_risk",
                "description": "Strong executive team identified but scaling/team expansion plan not explicitly mentioned",
                "severity": "low",
                "must_resolve": False
            })

        # Check overall confidence
        low_confidence = sum(1 for s in scores.values() if s.get("confidence", 0.5) < 0.5)
        if low_confidence > 1:
            flags.append({
                "flag_type": "low_confidence",
                "description": f"{low_confidence} stage(s) have low confidence (<0.5)",
                "severity": "medium",
                "must_resolve": False
            })

        # STAGE-AWARE FLAG GENERATION: Check for low scores indicating gaps/risks
        stage_metadata = {
            "stage_1_원천기술통제": {
                "name": "기술 통제",
                "low_score_flag": "technology_gap",
                "description": "Root technology control or IP protection inadequate (score < 6.0). Technical differentiation or patent position needs strengthening.",
                "why_important": "Technology moat is the foundation for sustainable competitive advantage; weak IP position enables rapid competitive erosion.",
                "severity": "high"
            },
            "stage_2_규제통제": {
                "name": "규제 통제",
                "low_score_flag": "regulatory_gap",
                "description": "Regulatory pathway clarity inadequate (score < 6.0). FDA classification, approval timeline, or regulatory engagement needs clarification.",
                "why_important": "Regulatory approval is typically the critical path for medtech/biotech; unclear pathway delays commercialization 12-36 months.",
                "severity": "high"
            },
            "stage_3_플랫폼확장": {
                "name": "플랫폼 확장",
                "low_score_flag": "platform_gap",
                "description": "Platform expansion potential unclear (score < 6.0). Multi-indication, multi-product strategy or market reach needs definition.",
                "why_important": "Platform scalability drives enterprise valuation; single-product companies have limited exit appeal.",
                "severity": "medium"
            },
            "stage_4_반복매출": {
                "name": "반복 매출",
                "low_score_flag": "recurring_revenue_gap",
                "description": "Recurring revenue model unproven or undefined (score < 6.0). Unit economics, customer retention, or consumable/subscription strategy needs definition.",
                "why_important": "Recurring revenue structure is essential for IPO-quality valuation multiples; one-time sales model limits enterprise value.",
                "severity": "high"
            },
            "stage_5_RWW개입": {
                "name": "RWW 개입",
                "low_score_flag": "execution_gap",
                "description": "Right-Way-to-Win execution capability unclear (score < 6.0). Team scaling plan or capital efficiency strategy needs strengthening.",
                "why_important": "Execution risk at Series A scale determines success probability; unclear scaling path increases failure likelihood.",
                "severity": "medium"
            }
        }

        for stage_key, metadata in stage_metadata.items():
            stage_score = scores.get(stage_key, {}).get("score", 0)
            if stage_score < 6.0:
                flags.append({
                    "flag_type": metadata["low_score_flag"],
                    "description": metadata["description"],
                    "severity": metadata["severity"],
                    "affected_stage": stage_key,
                    "why_important": metadata["why_important"],
                    "must_resolve": metadata["severity"] == "high"
                })

        return flags if flags else self._generate_default_flags()

    def _generate_default_flags(self) -> List[Dict[str, Any]]:
        """Generate baseline flags when no issues found (ensures validator always checks something)."""
        return [
            {
                "flag_type": "validation_complete",
                "description": "Analysis validated against Phase 1 findings. All core dimensions assessed.",
                "severity": "low",
                "must_resolve": False
            }
        ]
