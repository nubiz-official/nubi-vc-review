"""Data models for NuBI VC Review v2 - using dataclasses for schema definitions."""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid
import json


class StatusEnum(str, Enum):
    """Analysis status lifecycle."""
    DRAFT = "draft"
    VALIDATED = "validated"
    REVIEWED = "reviewed"
    PUBLISHED = "published"


class TemplateType(str, Enum):
    """Analysis purpose types."""
    IPO_FACTOR_ANALYSIS = "ipo_factor_analysis"
    REGULATORY_VERIFICATION = "regulatory_verification"
    COMPARATIVE_CASE_STUDY = "comparative_case_study"
    GENERAL_INVESTMENT_REVIEW = "general_investment_review"


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    """Analysis confidence levels."""
    EXCEPTIONAL = "exceptional"
    STRONG = "strong"
    ADEQUATE = "adequate"
    WEAK = "weak"
    CRITICAL = "critical"


class InvestmentDecision(str, Enum):
    """Investment recommendation."""
    STRONG_SUPPORT = "strong_support"
    SUPPORT = "support"
    NEUTRAL = "neutral"
    CAUTION = "caution"
    STRONG_CAUTION = "strong_caution"


class RecommendationLevel(str, Enum):
    """Final recommendation levels."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    AVOID = "avoid"
    STRONG_AVOID = "strong_avoid"


class RiskLevel(str, Enum):
    """Overall risk assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StatusHistoryEntry:
    """Record of status transition."""
    status: str
    timestamp: str
    actor: str
    notes: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class SourceDoc:
    """Document metadata in analysis."""
    filename: str
    filetype: str
    size_bytes: int
    extracted_text_length: int
    confidence: float
    upload_datetime: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Metadata:
    """Complete metadata for an analysis."""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str = ""
    analysis_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    template_type: str = TemplateType.GENERAL_INVESTMENT_REVIEW
    model_version: str = "claude-sonnet-4-20250514"
    prompt_version: str = "v1.0.0"
    source_docs: List[Dict[str, Any]] = field(default_factory=list)
    status: str = StatusEnum.DRAFT
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "system:analyzer"
    reviewer: Optional[str] = None
    review_timestamp: Optional[str] = None
    gold_sample_match: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    version: str = "2.0"

    def to_dict(self):
        return asdict(self)


@dataclass
class Score:
    """Individual dimension score."""
    score: float
    rubric_level: str = ConfidenceLevel.ADEQUATE
    evidence: List[str] = field(default_factory=list)
    counterevidence: List[str] = field(default_factory=list)
    confidence: float = 0.5

    def to_dict(self):
        return asdict(self)


@dataclass
class OverallScore:
    """Overall investment grade."""
    score: float = 0.0
    grade: str = "C"
    reasoning: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class KeyRisk:
    """Identified risk factor."""
    risk_type: str
    description: str
    severity: str
    mitigation_required: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class RedFlag:
    """Concerning signal that needs verification."""
    flag: str
    severity: str
    evidence: str
    verification_needed: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class MissingInfo:
    """Information gap in analysis."""
    category: str
    criticality: str
    impact: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Phase1Analysis:
    """Internal analysis output from analyzer."""
    timestamp_started: str
    timestamp_completed: str
    model_used: str
    prompt_version: str
    scores: Dict[str, Dict[str, Any]]
    narrative_analysis: Dict[str, str]
    investment_thesis: str
    key_risks: List[Dict[str, Any]]
    red_flags: List[Dict[str, Any]]
    missing_information: List[Dict[str, Any]]
    data_quality_assessment: Dict[str, Any]

    def to_dict(self):
        return asdict(self)


@dataclass
class Phase2Validations:
    """Validation analysis from validator."""
    vc_opinion_summary: str
    claims_extracted: List[Dict[str, Any]]
    claim_assessment: List[Dict[str, Any]]
    final_recommendation: str
    investment_decision: str

    def to_dict(self):
        return asdict(self)


@dataclass
class AnalysisInternal:
    """Complete internal analysis object (analyzer output)."""
    phase1_analysis: Phase1Analysis
    phase2_validations: Optional[Phase2Validations] = None
    metadata: Metadata = field(default_factory=Metadata)

    def to_dict(self):
        result = {
            "phase1_analysis": self.phase1_analysis.to_dict(),
            "metadata": self.metadata.to_dict()
        }
        if self.phase2_validations:
            result["phase2_validations"] = self.phase2_validations.to_dict()
        return result


@dataclass
class ReportFinal:
    """Final report output from reporter."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    analysis_id: str = ""
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    report_version: str = "v2.0"
    executive_summary: Dict[str, Any] = field(default_factory=dict)
    early_indicators: Dict[str, Any] = field(default_factory=dict)
    scorecard_5stage: Dict[str, Any] = field(default_factory=dict)
    cross_validation: Dict[str, Any] = field(default_factory=dict)
    scope_and_limitations: Dict[str, Any] = field(default_factory=dict)
    appendix: Dict[str, Any] = field(default_factory=dict)
    document_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)
