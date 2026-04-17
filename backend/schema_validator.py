"""Schema validation for NuBI VC Review v2."""
import json
from typing import Dict, Any, List, Tuple
from .models import StatusEnum, RiskSeverity, ConfidenceLevel


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class SchemaValidator:
    """Validates data against schema definitions."""

    @staticmethod
    def validate_input(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input schema."""
        errors = []

        # Company info
        if "company" not in data:
            errors.append("Missing 'company' section")
        else:
            company = data["company"]
            if not company.get("name") or len(str(company.get("name", "")).strip()) > 200:
                errors.append("company.name required and max 200 chars")
            if company.get("industry") and company["industry"] not in [
                "biotech", "medtech", "saas", "ai_ml", "hardware", "fintech"
            ]:
                errors.append(f"Invalid industry: {company['industry']}")
            if company.get("stage") and company["stage"] not in [
                "seed", "preA", "seriesA", "seriesB", "seriesC", "seriesD_plus"
            ]:
                errors.append(f"Invalid stage: {company['stage']}")

        # Analysis request
        if "analysis_request" not in data:
            errors.append("Missing 'analysis_request' section")
        else:
            req = data["analysis_request"]
            if req.get("purpose") not in [
                "ipo_factor_analysis", "regulatory_verification",
                "comparative_case_study", "general_investment_review"
            ]:
                errors.append(f"Invalid purpose: {req.get('purpose')}")
            if req.get("vc_opinion") and len(str(req["vc_opinion"])) > 5000:
                errors.append("vc_opinion exceeds 5000 chars")

        # Documents
        if "documents" not in data or not data["documents"]:
            errors.append("documents array required with at least 1 file")
        else:
            docs = data["documents"]
            if len(docs) > 10:
                errors.append("Maximum 10 documents allowed")
            for i, doc in enumerate(docs):
                if doc.get("filetype") not in ["pdf", "docx", "txt"]:
                    errors.append(f"Document {i}: invalid filetype {doc.get('filetype')}")
                if not isinstance(doc.get("confidence", 0.5), (int, float)):
                    errors.append(f"Document {i}: confidence must be number")
                elif not (0.0 <= doc["confidence"] <= 1.0):
                    errors.append(f"Document {i}: confidence must be 0.0-1.0")

        return len(errors) == 0, errors

    @staticmethod
    def validate_phase1_analysis(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate phase1 analysis structure."""
        errors = []

        if "phase1_analysis" not in data:
            errors.append("Missing phase1_analysis")
            return False, errors

        phase1 = data["phase1_analysis"]

        # Scores validation
        if "scores" not in phase1:
            errors.append("Missing scores object")
        else:
            scores = phase1["scores"]
            required_stages = [
                "stage_1_원천기술통제", "stage_2_규제통제",
                "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"
            ]
            for stage in required_stages:
                if stage not in scores:
                    errors.append(f"Missing score dimension: {stage}")
                else:
                    score_obj = scores[stage]
                    if "score" in score_obj:
                        s = score_obj["score"]
                        if not (0.0 <= s <= 10.0):
                            errors.append(f"{stage}.score must be 0-10, got {s}")
                    if "evidence" in score_obj:
                        if not isinstance(score_obj["evidence"], list) or len(score_obj["evidence"]) < 1:
                            errors.append(f"{stage}: must have at least 1 evidence item")
                    if "confidence" in score_obj:
                        c = score_obj["confidence"]
                        if not (0.0 <= c <= 1.0):
                            errors.append(f"{stage}.confidence must be 0.0-1.0, got {c}")

            if "overall" in scores:
                overall = scores["overall"]
                if "score" in overall and not (0.0 <= overall["score"] <= 10.0):
                    errors.append(f"overall.score must be 0-10")
                valid_grades = ["A", "A-", "B+", "B", "B-", "C+", "C", "D", "F"]
                if "grade" in overall and overall["grade"] not in valid_grades:
                    errors.append(f"overall.grade must be one of {valid_grades}")

        # Key risks
        if "key_risks" in phase1:
            risks = phase1["key_risks"]
            if len(risks) > 5:
                errors.append("Maximum 5 key risks allowed")
            for risk in risks:
                if risk.get("severity") not in ["critical", "high", "medium", "low"]:
                    errors.append(f"Invalid risk severity: {risk.get('severity')}")

        # Red flags
        if "red_flags" in phase1:
            if len(phase1["red_flags"]) > 3:
                errors.append("Maximum 3 red flags allowed")

        return len(errors) == 0, errors

    @staticmethod
    def validate_report_final(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate final report structure."""
        errors = []

        if "report_final" not in data:
            errors.append("Missing report_final")
            return False, errors

        report = data["report_final"]

        # Executive summary
        if "executive_summary" in report:
            es = report["executive_summary"]
            if "headline" in es and len(str(es["headline"])) > 200:
                errors.append("executive_summary.headline exceeds 200 chars")

        # Early indicators
        if "early_indicators" in report:
            ei = report["early_indicators"]
            if "indicators" in ei:
                if len(ei["indicators"]) < 3 or len(ei["indicators"]) > 5:
                    errors.append("early_indicators must have 3-5 items")

        # 5-stage scorecard
        if "5stage_scorecard" in report:
            scorecard = report["5stage_scorecard"]
            required_stages = [
                "stage_1_원천기술통제", "stage_2_규제통제",
                "stage_3_플랫폼확장", "stage_4_반복매출", "stage_5_RWW개입"
            ]
            for stage in required_stages:
                if stage not in scorecard:
                    errors.append(f"Missing scorecard stage: {stage}")

        # Cross validation
        if "cross_validation" in report:
            cv = report["cross_validation"]
            if "comparable_companies" in cv:
                if len(cv["comparable_companies"]) < 2:
                    errors.append("cross_validation must have at least 2 comparable companies")

        # Scope & limitations
        if "scope_and_limitations" not in report:
            errors.append("Missing scope_and_limitations")

        return len(errors) == 0, errors

    @staticmethod
    def validate_status_transition(
        current_status: str,
        next_status: str,
        analysis_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate status transition rules."""
        errors = []
        valid_statuses = [s.value for s in StatusEnum]

        if current_status not in valid_statuses:
            errors.append(f"Invalid current status: {current_status}")
        if next_status not in valid_statuses:
            errors.append(f"Invalid next status: {next_status}")

        # Transition rules
        if current_status == StatusEnum.DRAFT and next_status == StatusEnum.VALIDATED:
            # Check validator flags
            if "metadata" in analysis_data:
                metadata_int = analysis_data.get("metadata", {})
                validator_flags = metadata_int.get("validator_flags", [])
                if len(validator_flags) > 3:
                    errors.append(f"Too many validator flags ({len(validator_flags)} > 3)")

        elif current_status == StatusEnum.VALIDATED and next_status == StatusEnum.REVIEWED:
            if not analysis_data.get("reviewer"):
                errors.append("reviewer name required for reviewed status")

        elif current_status == StatusEnum.REVIEWED and next_status == StatusEnum.PUBLISHED:
            if "report_final" not in analysis_data:
                errors.append("report_final object required for published status")

        elif current_status not in [s.value for s in StatusEnum]:
            errors.append(f"Cannot transition from {current_status}")

        return len(errors) == 0, errors
