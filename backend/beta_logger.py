"""Beta logging for v2 framework - captures user modifications for v3 design."""
from datetime import datetime
from typing import Dict, Any, List


class BetaLogger:
    """Logs user modifications and feedback during beta period for v3 calibration."""

    def __init__(self):
        """Initialize beta logger."""
        self.logs: List[Dict[str, Any]] = []

    def log_early_indicators_modified(self, analysis_id: str, original: List[Dict], modified: List[Dict], actor: str = "user") -> None:
        """Log when user modifies early indicators."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_id": analysis_id,
            "event_type": "early_indicators_modified",
            "original_count": len(original),
            "modified_count": len(modified),
            "changes": self._compute_changes(original, modified),
            "actor": actor,
            "use_case": "Collecting real-world early indicator patterns for v3 calibration"
        })

    def log_stage_score_adjusted(self, analysis_id: str, stage: str, original_score: float, adjusted_score: float, reason: str = "", actor: str = "user") -> None:
        """Log when user adjusts a stage score."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_id": analysis_id,
            "event_type": "stage_score_adjusted",
            "stage": stage,
            "original_score": original_score,
            "adjusted_score": adjusted_score,
            "adjustment_delta": adjusted_score - original_score,
            "reason": reason,
            "actor": actor,
            "use_case": "Collecting domain expert score calibration for v3 stage weights"
        })

    def log_appendix_gap_noted(self, analysis_id: str, gap_item: str, user_comment: str = "", actor: str = "user") -> None:
        """Log when user notes a gap in domain logic."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_id": analysis_id,
            "event_type": "appendix_gap_noted",
            "gap_item": gap_item,
            "user_comment": user_comment,
            "actor": actor,
            "use_case": "Collecting feedback on v2 domain logic gaps for v3 prioritization"
        })

    def log_validator_override(self, analysis_id: str, claim_index: int, original_validation: str, override_validation: str, reason: str = "", actor: str = "user") -> None:
        """Log when validator overrides Phase 2 validation."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_id": analysis_id,
            "event_type": "validator_override",
            "claim_index": claim_index,
            "original_validation": original_validation,
            "override_validation": override_validation,
            "reason": reason,
            "actor": actor,
            "use_case": "Collecting evidence gaps and validation patterns for v3 validator tuning"
        })

    def log_comparative_note_added(self, analysis_id: str, comparable_company: str, note: str = "", actor: str = "user") -> None:
        """Log when user adds comparative analysis notes."""
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_id": analysis_id,
            "event_type": "comparative_note_added",
            "comparable_company": comparable_company,
            "note": note,
            "actor": actor,
            "use_case": "Collecting cross-validation patterns for v3 comparable company expansion"
        })

    def export_beta_insights(self) -> Dict[str, Any]:
        """Export aggregated beta insights for v3 design."""
        return {
            "total_logs": len(self.logs),
            "log_types": self._aggregate_by_type(),
            "logs": self.logs,
            "summary": f"{len(self.logs)} user interactions logged during beta period for v3 calibration"
        }

    def _compute_changes(self, original: List[Dict], modified: List[Dict]) -> Dict[str, int]:
        """Compute changes between original and modified lists."""
        return {
            "added": len([m for m in modified if m not in original]),
            "removed": len([o for o in original if o not in modified]),
            "unchanged": len([o for o in original if o in modified])
        }

    def _aggregate_by_type(self) -> Dict[str, int]:
        """Aggregate logs by event type."""
        agg = {}
        for log in self.logs:
            event_type = log.get("event_type", "unknown")
            agg[event_type] = agg.get(event_type, 0) + 1
        return agg
